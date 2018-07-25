from django.test import TransactionTestCase
from qdiff.reports import ReportGenerator
from qdiff.exceptions import InvalidClassNameException
from qdiff.reports import AggregatedReportGenerator
from qdiff.models import Report, Task, ConflictRecord
from qdiff.utils.model import getConflictRecordTableNames
from django.db import connection
import json
import os
from pathlib import Path
from django.conf import settings


class ReportGeneratorTestCase(TransactionTestCase):
    def setUp(self):
        self.task = Task.objects.create(
            summary='summary', left_source='dummy', right_source='dummy')
        self.report = Report.objects.create(
            task=self.task, report_generator='AggregatedReportGenerator',
            parameters='{"grouping_fields":"field1,field2"}')
        tableName1, tableName2 = getConflictRecordTableNames(self.task)
        ConflictRecord.objects.create(
            data_source='dummy', raw_table_name=tableName1, task=self.task,
            position=ConflictRecord.POSITION_IN_TASK_LEFT)
        ConflictRecord.objects.create(
            data_source='dummy', raw_table_name=tableName1, task=self.task,
            position=ConflictRecord.POSITION_IN_TASK_RIGHT)

        # create raw_table
        columns = [
            'unique_name', 'age', 'dept'
        ]
        data1 = [
            ['jeming', '30', 'dif1'],
            ['jeming1', '20', 'webapps'],
            ['jeming2', '30', 'dif3'],
            ['lone_in_1', '30', 'webapps'],
            ['duplicate1', '30', 'webapps'],
            ['duplicate1', '30', 'webapps'],
        ]
        data2 = [
            ['jeming', '30', 'dif2'],
            ['jeming1', '30', 'webapps'],
            ['jeming2', '30', 'dif4'],
            ['lone_in_2', '30', 'webapps'],
            ['duplicate2', '30', 'webapps'],
            ['duplicate2', '30', 'webapps'],
        ]
        with connection.cursor() as cursor:
            # create table
            try:
                cursor.execute('''CREATE TABLE ''' + tableName1 + ''' (
                        unique_name VARCHAR(10),
                        age VARCHAR(10),
                        dept VARCHAR(10)
                    );''')
                cursor.execute('''CREATE TABLE ''' + tableName2 + ''' (
                        unique_name VARCHAR(10),
                        age VARCHAR(10),
                        dept VARCHAR(10)
                    );''')

                query = 'INSERT INTO ' + tableName1 + \
                    ' (' + ','.join(columns) + ') VALUES (%s, %s, %s)'
                cursor.executemany(query, data1)
                query = 'INSERT INTO ' + tableName2 + \
                    ' (' + ','.join(columns) + ') VALUES (%s, %s, %s)'
                cursor.executemany(query, data2)
            except Exception as e:
                pass

    def tearDown(self):
        with connection.cursor() as cursor:
            tableName1, tableName2 = getConflictRecordTableNames(self.task)
            cursor.execute('DROP TABLE ' + tableName1 + ';')
            cursor.execute('DROP TABLE ' + tableName2 + ';')

    def testNotExistClassFactory(self):
        # given
        className = 'NotExistClassName'

        try:
            # when
            obj = ReportGenerator.factory(className)
            obj.doSomething()
        except Exception as e:
            # then
            self.assertTrue(type(e) is InvalidClassNameException)

    def testExistClassFactory(self):
        # given
        className = 'AggregatedReportGenerator'

        try:
            # when
            obj = ReportGenerator.factory(className, self.report)
            self.assertEqual(type(obj), AggregatedReportGenerator)
        except Exception as e:
            # then
            self.assertTrue(type(e) is InvalidClassNameException)


class AggregatedReportGeneratorTestCase(TransactionTestCase):
    def setUp(self):
        self.task = Task.objects.create(
            # id=999,
            summary='summary', left_source='dummy', right_source='dummy')
        self.report = Report.objects.create(
            task=self.task, report_generator='AggregatedReportGenerator',
            parameters='{"grouping_fields":"unique_name"}')
        tableName1, tableName2 = getConflictRecordTableNames(self.task)
        ConflictRecord.objects.create(
            data_source='dummy', raw_table_name=tableName1, task=self.task,
            position=ConflictRecord.POSITION_IN_TASK_LEFT)
        ConflictRecord.objects.create(
            data_source='dummy', raw_table_name=tableName1, task=self.task,
            position=ConflictRecord.POSITION_IN_TASK_RIGHT)

        # create raw_table
        self.columns = [
            'unique_name', 'age', 'dept'
        ]
        data1 = [
            ['jeming', '30', 'dif1'],
            ['jeming1', '20', 'webapps'],
            ['jeming2', '30', 'dif3'],
            ['lone_in_1', '30', 'webapps'],
            ['duplicate1', '30', 'webapps'],
            ['duplicate1', '30', 'webapps'],
            ['duplicate2', '30', 'webapps'],
        ]
        data2 = [
            ['jeming', '30', 'dif2'],
            ['jeming1', '30', 'webapps'],
            ['jeming2', '30', 'dif4'],
            ['lone_in_2', '30', 'webapps'],
            ['duplicate1', '30', 'webapps'],
            ['duplicate2', '30', 'webapps'],
            ['duplicate2', '30', 'webapps'],
        ]
        with connection.cursor() as cursor:
            # create table
            try:
                cursor.execute('''CREATE TABLE ''' + tableName1 + ''' (
                        unique_name VARCHAR(10),
                        age VARCHAR(10),
                        dept VARCHAR(10)
                    );''')
                cursor.execute('''CREATE TABLE ''' + tableName2 + ''' (
                        unique_name VARCHAR(10),
                        age VARCHAR(10),
                        dept VARCHAR(10)
                    );''')

                query = 'INSERT INTO ' + tableName1 + \
                    ' (' + ','.join(self.columns) + ') VALUES (%s, %s, %s)'
                cursor.executemany(query, data1)
                query = 'INSERT INTO ' + tableName2 + \
                    ' (' + ','.join(self.columns) + ') VALUES (%s, %s, %s)'
                cursor.executemany(query, data2)
            except Exception as e:
                pass

    def tearDown(self):
        with connection.cursor() as cursor:
            tableName1, tableName2 = getConflictRecordTableNames(self.task)
            cursor.execute('DROP TABLE ' + tableName1 + ';')
            cursor.execute('DROP TABLE ' + tableName2 + ';')

    def testGetColumns(self):
        # given
        className = 'AggregatedReportGenerator'
        obj = ReportGenerator.factory(className, self.report)
        self.assertEqual(type(obj), AggregatedReportGenerator)
        # when
        # then
        self.assertEqual(self.columns, obj.getConflictRecordColumn())

    def testLogic1(self):
        # given
        className = 'AggregatedReportGenerator'
        obj = ReportGenerator.factory(className, self.report)
        data1 = obj.conflictRecords1
        data2 = obj.conflictRecords2
        columns = obj.getConflictRecordColumn()
        # when
        report = obj._process(data1, data2, columns)
        # then
        self.assertEqual(json.dumps(report), json.dumps(json.loads('''{
            "leftUnpairedRecords": [
                ["lone_in_1"]
            ],
            "leftUnpairedCount": 1,
            "rightUnpairedRecords": [
                ["lone_in_2"]
            ],
            "rightUnpairedCount": 1,
            "columns": ["unique_name", "age", "dept"],
            "columnCounts": [0, 1, 2],
            "columnRecords": [
                [],
                [
                    [
                        ["jeming1"], "20", "30"
                    ]
                ],
                [
                    [
                        ["jeming"], "dif1", "dif2"
                    ],
                    [
                        ["jeming2"], "dif3", "dif4"
                    ]
                ]
            ],
            "leftDuplicatedCount": 1,
            "leftDuplicatedRecords": [
                ["duplicate1"]
            ],
            "rightDuplicatedCount": 1,
            "rightDuplicatedRecords": [
                ["duplicate2"]
            ]
        }''')))

    def testSaveFile(self):
        # given
        className = 'AggregatedReportGenerator'
        obj = ReportGenerator.factory(className, self.report)
        try:
            # when
            path = obj.generate()
            # then
            f = Path(path)
            # check file exist
            self.assertTrue(f.exists())
            self.assertEqual(
                path,
                os.path.join(settings.REPORT_FOLDER, obj.getFileName()))
        except Exception as e:
            raise e
        finally:
            try:
                os.remove(
                    os.path.join(settings.REPORT_FOLDER, obj.getFileName()))
            except Exception as e:
                pass
