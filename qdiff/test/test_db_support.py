from django.test import TestCase
from django.db import connection, connections
from random import randint
from logging import Logger

logger = Logger('test')


class DbSupportTestCase(TestCase):

    def setUp(self):

        with connection.cursor() as cursor:
            # create table
            cursor.execute('''CREATE TABLE temp (
                    col1 VARCHAR(10),
                    col2 VARCHAR(10)
                );
            ''')

            # insert data
            query = '''INSERT INTO temp (col1, col2)
                VALUES (%s, %s)
            '''
            cursor.executemany(query, [
                (
                    str(randint(0, 1)),
                    str(randint(0, 10))
                )
                for i in range(10)])

    '''
    test if django can fetch the fields information of the table
    '''

    def testGetTableSchema(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * from temp LIMIT 1;")
            self.assertEqual(cursor.description[0][0], 'col1')
            self.assertEqual(cursor.description[1][0], 'col2')

    '''
    test if django can access new db in the runtime
    this requires additional setup for running testcase
    '''

    def testAccessNewDB(self):
        newDBConfig = {}
        ''' tested mysql config
        newDBConfig['id'] = 'new'
        newDBConfig['ENGINE'] = 'django.db.backends.mysql'
        newDBConfig['NAME'] = 'test2'
        newDBConfig['PASSWORD'] = 'root'
        newDBConfig['USER'] = 'root'
        newDBConfig['HOST'] = 'localhost'
        newDBConfig['PORT'] = '3306'
        '''
        newDBConfig['id'] = 'database2'
        newDBConfig['NAME'] = ':memory:'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        connections._databases[newDBConfig['id']] = newDBConfig
        del connections.databases
        with connections['database2'].cursor() as cursor:
            # write
            cursor.execute('''CREATE TABLE temp (
                col1 VARCHAR(10),
                col2 VARCHAR(10)
            );''')
            query = '''INSERT INTO temp (col1, col2)
                VALUES (%s, %s)
            '''
            cursor.executemany(query, [
                (
                    str(randint(0, 1)),
                    str(randint(0, 10))
                )
                for i in range(10)])
            # read
            cursor.execute("SELECT * from temp LIMIT 1;")
