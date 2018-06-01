from django.test import TestCase
from django.db import connection, connections
from random import randint
from qdiff.readers import DatabaseReader


class DatabaseReaderTestCase(TestCase):

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

    def testGetRow(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        query_sql = 'SELECT * FROM temp;'
        r = DatabaseReader(newDBConfig, query_sql)
        row = r.getRow()
        r.close()
        self.assertEquals(2, len(row))

    '''
    this require additional mysql setup
    '''
    '''
    def testGetRowsListWithMysql(self):
        newDBConfig = {}
        newDBConfig['id'] = 'new'
        newDBConfig['ENGINE'] = 'django.db.backends.mysql'
        newDBConfig['NAME'] = 'test2'
        newDBConfig['PASSWORD'] = 'root'
        newDBConfig['USER'] = 'root'
        newDBConfig['HOST'] = 'localhost'
        newDBConfig['PORT'] = '3306'
        query_sql = 'SELECT * FROM group2;'
        r = DatabaseReader(newDBConfig, query_sql)
        rows = r.getRowsList()
        self.assertEquals(2, len(rows))
    '''

    def testGetRowsListWithSqlite(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        query_sql = 'SELECT * FROM temp;'
        r = DatabaseReader(newDBConfig, query_sql)
        rows = r.getRowsList()
        self.assertEquals(10, len(rows))
        r.close()
