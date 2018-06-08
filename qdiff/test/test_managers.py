from django.db import connection
from django.test import TestCase, TransactionTestCase
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
            try:
                cursor.execute('DROP TABLE gen_task_1_lf;')
                cursor.execute('DROP TABLE gen_task_1_rt;')
            except Exception as e:
                pass

        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        self.taskModel = Task.objects.create(
            summary='test_task',
            left_source='database:' + json.dumps(newDBConfig),
            left_query_sql='SELECT * FROM ds1;',
            right_source='database:' + json.dumps(newDBConfig),
            right_query_sql='SELECT * FROM ds2;',
        )

    def testGetTableNames(self):
        m = TaskManager(self.taskModel)
        self.assertEqual(m.getTableNames(),
                         tuple(
            [settings.GENERATED_TABLE_PREFIX + '_TASK_1_LF',
             settings.GENERATED_TABLE_PREFIX + '_TASK_1_RT']))

    def test_changeStatusWithValidStatus(self):
        m = TaskManager(self.taskModel)
        m._changeStatus('CM')
        self.assertEqual(self.taskModel.status, 'CM')

    def test_changeStatus1(self):
        m = TaskManager(self.taskModel)
        m._changeStatus('XX')
        self.assertEqual(self.taskModel.status, 'PN')

    def test_setupReaders(self):
        m = TaskManager(self.taskModel)
        r1, r2 = m._setUpReaders()
        self.assertEqual(len(r1.getRowsList()), 10)
        self.assertEqual(len(r2.getRowsList()), 10)

    def test_setupWriters(self):

        m = TaskManager(self.taskModel)
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
        m = TaskManager(self.taskModel)
        self.assertEqual(
            m._getCreateSql(['col1', 'col2'], 'test_table'),
            ('CREATE TABLE test_table (col1 VARCHAR(%s), col2 VARCHAR(%s));' %
             (settings.DEFAULT_DATA_LENGTH, settings.DEFAULT_DATA_LENGTH)))

    def testCompare(self):
        m = TaskManager(self.taskModel)
        m.compare()
        t1, t2 = m.getTableNames()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM %s;' % t1)
            self.assertEqual(len(cursor.fetchall()), 0)
            cursor.execute('SELECT * FROM %s;' % t2)
            self.assertEqual(len(cursor.fetchall()), 0)
