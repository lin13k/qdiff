from django.conf import settings
from django.db import connections
from qdiff.comparators import ValueComparator
from qdiff.exceptions import NotImplementedException
from qdiff.models import Task, ConflictRecord
from qdiff.readers import DatabaseReader
from qdiff.writers import DatabaseWriter
import json
import re


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

    def __init__(self, taskModel, writeSource1=None, writeSource2=None):
        self._model = taskModel
        try:
            # make sure the model is persistant
            self._model.save()
        except Exception as e:
            raise e
        self._ws1 = writeSource1
        self._ws2 = writeSource2

    def compare(self):
        self._setUpReaders()
        self._setUpWriters()
        self._changeStatus(Task.STATUS_OF_TASK_RUNNING)
        if not self._compareFields():
            self._changeStatus(Task.STATUS_OF_TASK_ERROR)
        else:
            self._compareValues()
            self._changeStatus(Task.STATUS_OF_TASK_COMPLETED)

    def getTableNames(self):
        tableName1 = '%s_%s_%s' % (
            settings.GENERATED_TABLE_PREFIX,
            str(self.task),
            ConflictRecord.POSITION_IN_TASK_LEFT
        )
        tableName2 = '%s_%s_%s' % (
            settings.GENERATED_TABLE_PREFIX,
            str(self.task),
            ConflictRecord.POSITION_IN_TASK_RIGHT
        )
        return (tableName1, tableName2)

    def _setUpReaders(self):
        if not hasattr(self, 'reader1'):
            if re.match('^' + settings.SOURCE_TYPE_DATABASE_PREFIX,
                        self._model.left_source, re.I):
                # left config is database source
                self.reader1 = DatabaseReader(
                    json.loads(
                        self._model.left_source[len(
                            settings.SOURCE_TYPE_DATABASE_PREFIX):]),
                    self._model.left_query_sql
                )
            else:
                # TODO CSV reader
                self.reader1 = None

        if not hasattr(self, 'reader2'):
            if re.match('^' + settings.SOURCE_TYPE_DATABASE_PREFIX,
                        self._model.right_source, re.I):
                # right config is database source
                self.reader2 = DatabaseReader(
                    json.loads(
                        self._model.right_source[len(
                            settings.SOURCE_TYPE_DATABASE_PREFIX):]),
                    self._model.right_query_sql
                )
            else:
                # TODO CSV reader
                self.reader2 = None
        return (self.reader1, self.reader2)

    def _getCreateSql(self, columns, tableName):
        tmpCol = []
        for col in columns:
            tmpCol.append(col + ' VARCHAR(%s)' %
                          settings.DEFAULT_DATA_LENGTH)

        colSql = ', '.join(tmpCol)

        return '''
            CREATE TABLE %s (%s);
        ''' % (tableName, colSql)

    def _setUpWriters(self):
        if not hasattr(self, 'reader1') or not hasattr(self, 'reader2'):
            self._setUpReaders()
        columns1 = self.reader1.getColumns()
        columns2 = self.reader2.getColumns()
        tableName1, tableName2 = self.getTableNames()
        dbConfig = settings.DATABASES['default'].copy()
        dbConfig['id'] = 'default'
        with connections['defaut'].cursor() as cursor:
            if not self._ws1:
                cursor.execute(self._getCreateSql(
                    columns1, tableName1))
                self.writer1 = DatabaseWriter(dbConfig, tableName1)
                ConflictRecord.objects.create(
                    raw_table_name=tableName1,
                    task=self._model,
                    data_source='database:' + json.dumps(dbConfig),
                    position=ConflictRecord.POSITION_IN_TASK_LEFT
                )
            else:
                raise NotImplementedException(
                    'external write source not support yet')
            if not self._ws2:
                cursor.execute(self._getCreateSql(
                    columns2, tableName2))
                self.writer2 = DatabaseWriter(dbConfig, tableName2)
                ConflictRecord.objects.create(
                    raw_table_name=tableName2,
                    task=self._model,
                    data_source=(settings.SOURCE_TYPE_DATABASE_PREFIX +
                                 json.dumps(dbConfig)),
                    position=ConflictRecord.POSITION_IN_TASK_RIGHT
                )
            else:
                raise NotImplementedException(
                    'external write source not support yet')
        return (self.writer1, self.writer2)

    def _compareValues(self):
        comparator = ValueComparator(
            self.data_reader1, self.data_reader2,
            self.writer1, self.writer2,
            self._model.left_ignore_fields, self._model.right_ignore_fields)
        comparator.compare()

    def _compareFields(self):
        return True

    def _changeStatus(self):
        pass
