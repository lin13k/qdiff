from django.db import connection
from django.test import TransactionTestCase
from qdiff.managers import TaskManager
from qdiff.models import Task
from django.conf import settings
import json


class TaskManagerTestCase(TransactionTestCase):
    def setUp(self):

        with connection.cursor() as cursor:
            try:
                # create table
                cursor.execute('''CREATE TABLE ds1 (
                            col1 VARCHAR(10),
                            col2 VARCHAR(10)
                        );
                    ''')

                # insert data
                query = '''INSERT INTO ds1 (col1, col2)
                        VALUES (%s, %s)
                    '''
                cursor.executemany(query, [
                    (
                        str(i),
                        str(i)
                    )
                    for i in range(10)])
                cursor.execute('''CREATE TABLE ds2 (
                            col1 VARCHAR(10),
                            col2 VARCHAR(10)
                        );
                    ''')

                # insert data
                query = '''INSERT INTO ds2 (col1, col2)
                        VALUES (%s, %s)
                    '''
                cursor.executemany(query, [
                    (
                        str(i),
                        str(i)
                    )
                    for i in range(10)])
            except Exception as e:
                pass

        newDBConfig = settings.DATABASES['default'].copy()
        if not hasattr(self, 'taskModel'):
            self.taskModel = Task.objects.create(
                summary='test_task',
                left_source=(settings.SOURCE_TYPE_DATABASE_PREFIX +
                             json.dumps(newDBConfig)),
                left_query_sql='SELECT * FROM ds1;',
                right_source=(settings.SOURCE_TYPE_DATABASE_PREFIX +
                              json.dumps(newDBConfig)),
                right_query_sql='SELECT * FROM ds2;',
            )
        self.rds1 = (settings.SOURCE_TYPE_DATABASE_PREFIX +
                     json.dumps(newDBConfig))
        self.rds2 = (settings.SOURCE_TYPE_DATABASE_PREFIX +
                     json.dumps(newDBConfig))

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE ds1;')
            cursor.execute('DROP TABLE ds2;')
            try:
                cursor.execute(
                    'DROP TABLE ' +
                    settings.GENERATED_TABLE_PREFIX + '_TASK_1_LF;')
                cursor.execute(
                    'DROP TABLE ' +
                    settings.GENERATED_TABLE_PREFIX + '_TASK_1_RT;')
            except Exception as e:
                pass

    def testGetTableNames(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        n = m.getTableNames()
        c = tuple(
            [settings.GENERATED_TABLE_PREFIX + '_TASK_1_LF',
             settings.GENERATED_TABLE_PREFIX + '_TASK_1_RT'])
        self.assertEqual(
            n[0][:len(settings.GENERATED_TABLE_PREFIX + '_TASK_')],
            c[0][:len(settings.GENERATED_TABLE_PREFIX + '_TASK_')])
        self.assertEqual(
            n[0][-3:],
            c[0][-3:])

    def test_changeStatusWithValidStatus(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        m._changeStatus('CM')
        self.assertEqual(self.taskModel.status, 'CM')

    def test_changeStatus1(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        m._changeStatus('XX')
        self.assertEqual(self.taskModel.status, 'PN')

    def test_setupReaders(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        r1, r2 = m._setUpReaders()
        self.assertEqual(len(r1.getRowsList()), 10)
        self.assertEqual(len(r2.getRowsList()), 10)

    def test_setupWriters(self):

        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        w1, w2 = m._setUpWriters()
        w1.writeAll([('w_row1', 'w_r1data'), ('w_row1', 'w_r1data')])
        w2.writeAll([('w_row1', 'w_r1data'), ('w_row1', 'w_r1data')])
        t1, t2 = m.getTableNames()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM %s;' % t1)
            self.assertEqual(len(cursor.fetchall()), 2)
            cursor.execute('SELECT * FROM %s;' % t2)
            self.assertEqual(len(cursor.fetchall()), 2)

    def test_getCreateSql(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        self.assertEqual(
            m._getCreateSql(['col1', 'col2'], 'test_table'),
            ('CREATE TABLE test_table (col1 VARCHAR(%s), col2 VARCHAR(%s));' %
             (settings.DEFAULT_DATA_LENGTH, settings.DEFAULT_DATA_LENGTH)))

    def testCompare(self):
        m = TaskManager(self.taskModel, self.rds1, self.rds2)
        m.compare()
        t1, t2 = m.getTableNames()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM %s;' % t1)
            self.assertEqual(len(cursor.fetchall()), 0)
            cursor.execute('SELECT * FROM %s;' % t2)
            self.assertEqual(len(cursor.fetchall()), 0)
