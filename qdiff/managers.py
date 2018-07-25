from django.conf import settings
from django.db import connection
from qdiff.comparators import ValueComparator, FieldComparator
from qdiff.exceptions import NotImplementedException
from qdiff.exceptions import InvalidDataSourceException
from qdiff.models import Task, ConflictRecord
from qdiff.readers import DatabaseReader, CsvReader
from qdiff.writers import DatabaseWriter
from qdiff.reports import ReportGenerator
import json
import re
import logging
logging.basicConfig(filename='managers.log', level=logging.DEBUG)


class TaskManager:
    """
    This class will manage the whole process of a comparison task
    It handles following jobs:
            1. setup table for conflicted results
            2. field comparison
            3. value comparison
            4. provide information for report generator
                4.1 field information
                4.2 task information( or report generator get the data from db)
            5. set the task as running before run
            6. set the task as completed/error after run
    """

    def __init__(self, taskModel, rds1, rds2,
                 writeSource1=None, writeSource2=None):
        self._taskModel = taskModel
        self._taskModel.save()
        self._rds1 = rds1
        self._rds2 = rds2
        self._ws1 = writeSource1
        self._ws2 = writeSource2

    def compare(self):
        logging.debug('start compare')
        self._changeStatus(Task.STATUS_OF_TASK_RUNNING)
        self._setUpReaders()
        self._setUpWriters()
        if not self._isFieldsSame():
            self._changeStatus(Task.STATUS_OF_TASK_ERROR)
        else:
            self._isValuesSame()
            self._changeStatus(Task.STATUS_OF_TASK_COMPLETED)
            self._generateReports()

    def getTableNames(self):
        tableName1 = '%s_TASK_%s_%s' % (
            settings.GENERATED_TABLE_PREFIX,
            str(self._taskModel.id),
            ConflictRecord.POSITION_IN_TASK_LEFT
        )
        tableName2 = '%s_TASK_%s_%s' % (
            settings.GENERATED_TABLE_PREFIX,
            str(self._taskModel.id),
            ConflictRecord.POSITION_IN_TASK_RIGHT
        )
        return (tableName1, tableName2)

    def _generateReports(self):
        errors = []
        for report in self._taskModel.reports.all():
            try:
                reportGenerator = ReportGenerator.factory(
                    report.report_generator, report)
                reportGenerator.generate()
            except Exception as e:
                errors.append(str(e))
        if len(errors) > 0:
            self._taskModel.result_detail += \
                settings.RESULT_SPLITTING_TOKEN.join(errors)
            self._taskModel.save()

    def _setUpReaders(self):
        logging.debug('start setup readers')
        if not hasattr(self, 'reader1'):
            if re.match('^' + settings.SOURCE_TYPE_DATABASE_PREFIX,
                        self._rds1, re.I):
                # left config is database source
                self.reader1 = DatabaseReader(
                    json.loads(
                        self._rds1[len(
                            settings.SOURCE_TYPE_DATABASE_PREFIX):]),
                    self._taskModel.left_query_sql
                )
            elif re.match('^' + settings.SOURCE_TYPE_CSV_PREFIX,
                          self._rds1, re.I):
                self.reader1 = CsvReader(
                    self._rds1[len(
                        settings.SOURCE_TYPE_CSV_PREFIX):])
            else:
                raise InvalidDataSourceException(
                    self._rds1 + ' is not a valid source type')

        if not hasattr(self, 'reader2'):
            if re.match('^' + settings.SOURCE_TYPE_DATABASE_PREFIX,
                        self._rds2, re.I):
                # right config is database source
                self.reader2 = DatabaseReader(
                    json.loads(
                        self._rds2[len(
                            settings.SOURCE_TYPE_DATABASE_PREFIX):]),
                    self._taskModel.right_query_sql
                )
            elif re.match('^' + settings.SOURCE_TYPE_CSV_PREFIX,
                          self._rds2, re.I):
                self.reader2 = CsvReader(
                    self._rds2[len(
                        settings.SOURCE_TYPE_CSV_PREFIX):])
            else:
                raise InvalidDataSourceException(
                    self._rds2 + ' is not a valid source type')

        return (self.reader1, self.reader2)

    def _getCreateSql(self, columns, tableName):
        tmpCol = []
        for col in columns:
            tmpCol.append(col + ' VARCHAR(%s)' %
                          settings.DEFAULT_DATA_LENGTH)

        colSql = ', '.join(tmpCol)

        return ('''
            CREATE TABLE %s (%s);
        ''' % (tableName, colSql)).strip()

    def _getDropSql(self, tableName):
        return "DROP TABLE `qdiff`.`%s`" % tableName

    def _setUpWriters(self):
        logging.debug('start setup writers')
        if not hasattr(self, 'reader1') or not hasattr(self, 'reader2'):
            self._setUpReaders()
        columns1 = self.reader1.getColumns()
        columns2 = self.reader2.getColumns()
        tableName1, tableName2 = self.getTableNames()
        dbConfig = settings.DATABASES['default'].copy()
        dbConfig['id'] = 'default'
        if not self._ws1:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(self._getCreateSql(
                        columns1, tableName1))
                except Exception as e:
                    # if table exists
                    cursor.execute(self._getDropSql(tableName1))
                    cursor.execute(self._getCreateSql(
                        columns1, tableName1))
                self.writer1 = DatabaseWriter(dbConfig, tableName1)
                ConflictRecord.objects.create(
                    raw_table_name=tableName1,
                    task=self._taskModel,
                    position=ConflictRecord.POSITION_IN_TASK_LEFT
                )
        else:
            raise NotImplementedException(
                'external write source not support yet')
        if not self._ws2:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(self._getCreateSql(
                        columns2, tableName2))
                except Exception as e:
                    # if table exists
                    cursor.execute(self._getDropSql(tableName2))
                    cursor.execute(self._getCreateSql(
                        columns2, tableName2))
                self.writer2 = DatabaseWriter(dbConfig, tableName2)
                ConflictRecord.objects.create(
                    raw_table_name=tableName2,
                    task=self._taskModel,
                    position=ConflictRecord.POSITION_IN_TASK_RIGHT
                )
        else:
            raise NotImplementedException(
                'external write source not support yet')
        return (self.writer1, self.writer2)

    def _isValuesSame(self):
        comparator = ValueComparator(
            self.reader1, self.reader2,
            self.writer1, self.writer2,
            (self._taskModel.left_ignore_fields.split(',')
                if self._taskModel.left_ignore_fields else []),
            (self._taskModel.right_ignore_fields.split(',')
                if self._taskModel.right_ignore_fields else []),
            self._taskModel)
        r = comparator.isSame()
        logging.debug('_isValuesSame:' + str(r))
        return r

    def _isFieldsSame(self):
        comparator = FieldComparator(
            self.reader1, self.reader2,
            (self._taskModel.left_ignore_fields.split(',')
                if self._taskModel.left_ignore_fields else []),
            (self._taskModel.right_ignore_fields.split(',')
                if self._taskModel.right_ignore_fields else []),
            self._taskModel)
        r = comparator.isSame()
        logging.debug('_isFieldsSame:' + str(r))
        return r

    def _changeStatus(self, status):
        validStatus = [choice[0] for choice in Task.STATUS_OF_TASK_CHOICES]
        if status in validStatus:
            self._taskModel.status = status
            self._taskModel.save()
