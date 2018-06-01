from django.test import TestCase
from django.db import connection
from qdiff.comparator import ValueComparator
from qdiff.readers import DatabaseReader
from qdiff.writers import DatabaseWriter


class TestWriter:
    def __init__(self):
        self.data = []

    def writeAll(self, rows):
        self.data.extend(rows)


class TestReader:
    def __init__(self, data):
        self.data = data

    def getRowsList(self):
        return self.data


class ComparatorTestCase(TestCase):
    def setUp(self):
        # setup database for readers
        with connection.cursor() as cursor:
            # create table
            cursor.execute('''CREATE TABLE r1 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
            # insert data
            query = '''INSERT INTO r1 (col1, col2)
                    VALUES (%s, %s)
                '''
            cursor.executemany(query, [
                (
                    str(i),
                    str(i)
                )
                for i in range(10)])
            cursor.execute('''CREATE TABLE r2 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
            # insert data
            query = '''INSERT INTO r2 (col1, col2)
                    VALUES (%s, %s)
                '''
            cursor.executemany(query, [
                (
                    str(i),
                    str(i)
                )
                for i in range(11)])
        # setup database for writers
        with connection.cursor() as cursor:
            cursor.execute('''CREATE TABLE w1 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
            cursor.execute('''CREATE TABLE w2 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')

    def testSameDataComparisonWithDatabase(self):
        DbConfig = {}
        DbConfig['id'] = 'default'
        DbConfig['ENGINE'] = 'django.db.backends.sqlite3'
        DbConfig['NAME'] = ':memory:'
        query_sql1 = 'SELECT * FROM r1;'
        r1 = DatabaseReader(DbConfig, query_sql1)
        query_sql2 = 'SELECT * FROM r2;'
        r2 = DatabaseReader(DbConfig, query_sql2)

        w1 = DatabaseWriter(DbConfig, 'w1')
        w2 = DatabaseWriter(DbConfig, 'w2')

        comparator = ValueComparator(r1, r2, w1, w2, [])
        comparator.compare()

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM w1;')
            records1 = list(cursor.fetchall())
            cursor.execute('SELECT * FROM w2;')
            records2 = list(cursor.fetchall())
            self.assertEqual(len(records1), 0)
            self.assertEqual(len(records2), 1)

    def testDataLogic1(self):
        r1 = TestReader([1, 2, 3, 4, 5])
        r2 = TestReader([1, 2, 3, 4, 5])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        comparator.compare()
        self.assertEqual(len(w1.data), 0)
        self.assertEqual(len(w2.data), 0)

    def testDataLogic2(self):
        r1 = TestReader([1, 2, 4, 5])
        r2 = TestReader([1, 2, 3, 4, 5])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        comparator.compare()
        self.assertEqual(len(w1.data), 0)
        self.assertEqual(len(w2.data), 1)

    def testDataLogic3(self):
        r1 = TestReader([1, 2, 4, 5, 6, 8])
        r2 = TestReader([1, 2, 3, 4, 5, 9])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        comparator.compare()
        self.assertEqual(len(w1.data), 2)
        self.assertEqual(len(w2.data), 2)
