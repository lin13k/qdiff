from django.test import TestCase, TransactionTestCase
from django.db import connection
from random import randint
from qdiff.readers import DatabaseReader, CsvReader


class DatabaseReaderTestCase(TransactionTestCase):

    def setUp(self):

        with connection.cursor() as cursor:
            # create table
            try:
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
            except Exception as e:
                pass

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

    def testGetColumns(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        query_sql = 'SELECT * FROM temp;'
        r = DatabaseReader(newDBConfig, query_sql)
        columns = r.getColumns()
        r.close()
        self.assertEqual(columns, ['col1', 'col2'])

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

    def testGetSchema(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        query_sql = 'SELECT * FROM temp;'
        r = DatabaseReader(newDBConfig, query_sql)
        schema = r.getSchema()
        self.assertEqual(
            schema,
            {'fields': [
                {'name': 'col1', 'type': 'integer',
                                 'format': 'default'},
                {'name': 'col2', 'type': 'integer', 'format': 'default'}]})


class CsvReaderTestCase(TestCase):

    def setUp(self):
        pass

    def testGetColumns(self):
        r = CsvReader('qdiff/test/testcsv.csv')
        columns = r.getColumns()
        self.assertEqual(
            columns,
            ['id', 'address', 'price', 'qan', 'start'])

    def testRequery(self):
        r = CsvReader('qdiff/test/testcsv.csv')
        row1 = r.getRow()
        r.requery()
        row2 = r.getRow()
        self.assertEqual(row1, row2)

    def testGetRow(self):
        r = CsvReader('qdiff/test/testcsv.csv')
        row = r.getRow()
        self.assertEqual(len(row), 5)

    def testGetRowList(self):
        r = CsvReader('qdiff/test/testcsv.csv')
        self.assertEqual(len(r.getRowsList()), 5)

    def testGetSchema(self):
        r = CsvReader('qdiff/test/testcsv.csv')
        self.assertEqual(
            r.getSchema(),
            {'fields': [
                {'name': 'id', 'type': 'integer', 'format': 'default'},
                {'name': 'address', 'type': 'string', 'format': 'default'},
                {'name': 'price', 'type': 'string', 'format': 'default'},
                {'name': 'qan', 'type': 'integer', 'format': 'default'},
                {'name': 'start', 'type': 'date', 'format': 'default'}],
             'missingValues': ['']})
