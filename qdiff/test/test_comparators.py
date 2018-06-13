from django.test import TransactionTestCase, TestCase
from django.db import connection
from qdiff.comparators import ValueComparator, FieldComparator
from qdiff.readers import DatabaseReader
from qdiff.writers import DatabaseWriter
from qdiff.models import Task
from tableschema import Schema


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

    def getColumns(self):
        return [str(i) for i in range(1, len(self.data[0]) + 1)]

    def getSchema(self):
        s = Schema()
        return s.infer(self.data)


class ValueComparatorTestCase(TransactionTestCase):
    def setUp(self):
        # setup database for readers
        with connection.cursor() as cursor:
            # create table
            try:
                cursor.execute('''CREATE TABLE r1 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
                query = '''INSERT INTO r1 (col1, col2)
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
            # insert data
            # create table
            try:
                cursor.execute('''CREATE TABLE r2 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
                query = '''INSERT INTO r2 (col1, col2)
                    VALUES (%s, %s)
                    '''
                cursor.executemany(query, [
                    (
                        str(i),
                        str(i)
                    )
                    for i in range(11)])
            except Exception as e:
                pass
            # insert data
        # setup database for writers
        with connection.cursor() as cursor:
            try:
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

            except Exception as e:
                pass

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
        isSame = comparator.isSame()

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM w1;')
            records1 = list(cursor.fetchall())
            cursor.execute('SELECT * FROM w2;')
            records2 = list(cursor.fetchall())
            self.assertEqual(len(records1), 0)
            self.assertEqual(len(records2), 1)
            self.assertEqual(isSame, False)

    def testDataLogic1(self):
        r1 = TestReader([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
        r2 = TestReader([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        isSame = comparator.isSame()
        self.assertEqual(len(w1.data), 0)
        self.assertEqual(len(w2.data), 0)
        self.assertEqual(isSame, True)

    def testDataLogic2(self):
        r1 = TestReader([(1, 1), (2, 2), (4, 4), (5, 5)])
        r2 = TestReader([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        isSame = comparator.isSame()
        self.assertEqual(len(w1.data), 0)
        self.assertEqual(len(w2.data), 1)
        self.assertEqual(isSame, False)

    def testDataLogic3(self):
        r1 = TestReader([(1, 1), (2, 2), (4, 4), (5, 5), (6, 6), (8, 8)])
        r2 = TestReader([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (9, 9)])
        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2)
        isSame = comparator.isSame()
        self.assertEqual(len(w1.data), 2)
        self.assertEqual(len(w2.data), 2)
        self.assertEqual(isSame, False)

    def testWriteResultIntoModel(self):
        r1 = TestReader([(1, 1), (2, 2), (4, 4), (5, 5), (6, 6), (8, 8)])
        r2 = TestReader([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (9, 9)])
        w1 = TestWriter()
        w2 = TestWriter()

        model = Task.objects.create(
            summary='test_task',
            left_source='database:dummy',
            left_query_sql='SELECT * FROM ds1;',
            right_source='database:dummy',
            right_query_sql='SELECT * FROM ds2;',
        )
        comparator = ValueComparator(r1, r2, w1, w2, taskModel=model)
        isSame = comparator.isSame()
        self.assertEqual(len(w1.data), 2)
        self.assertEqual(len(w2.data), 2)
        self.assertEqual(isSame, False)
        self.assertEqual(model.result, 'Record difference found!')
        self.assertEqual(model.result_detail, 'Found total 4 differences.')

    def testDataLogicWithIgnoredFields1(self):
        r1 = TestReader([[
            'row1', 'data1', 'ignore*', ], [
            'row2', 'data2', 'ignore*', ], [
            'row3', 'data3', 'ignore*', ], [
            'row4', 'data4', 'ignore*', ], [
            'row5', 'data5', 'ignore*', ], [
            'row6', 'data6', 'ignore*',
        ]])
        r2 = TestReader([[
            'row1', 'ignore&', 'data1', ], [
            'row2', 'ignore&', 'data2', ], [
            'row3', 'ignore&', 'data3', ], [
            'row4', 'ignore&', 'data4', ], [
            'row5', 'ignore&', 'data5', ], [
            'row6', 'ignore&', 'data6',
        ]])

        w1 = TestWriter()
        w2 = TestWriter()
        comparator = ValueComparator(r1, r2, w1, w2, ['3'], ['2'])
        isSame = comparator.isSame()
        self.assertEqual(len(w1.data), 0)
        self.assertEqual(len(w2.data), 0)
        self.assertEqual(isSame, True)


class FieldComparatorTestCase(TransactionTestCase):
    def setUp(self):
        with connection.cursor() as cursor:
            # create table
            try:
                cursor.execute('''CREATE TABLE r1 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
                query = '''INSERT INTO r1 (col1, col2)
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
            # insert data
            # create table
            try:
                cursor.execute('''CREATE TABLE r2 (
                        col1 VARCHAR(10),
                        col2 VARCHAR(10)
                    );
                ''')
                query = '''INSERT INTO r2 (col1, col2)
                    VALUES (%s, %s)
                    '''
                cursor.executemany(query, [
                    (
                        str(i),
                        str(i)
                    )
                    for i in range(11)])
            except Exception as e:
                pass
            # insert data
        # setup database for writers
        with connection.cursor() as cursor:
            try:
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

            except Exception as e:
                pass

    def testDataType1(self):
        r1 = TestReader([[
            'col1', 'datacol', 'igfield', ], [
            'row1', 'data1', 'ignore*', ], [
            'row2', 'data2', 'ignore*', ], [
            'row3', 'data3', 'ignore*', ], [
            'row4', 'data4', 'ignore*', ], [
            'row5', 'data5', 'ignore*', ], [
            'row6', 'data6', 'ignore*',
        ]])
        r2 = TestReader([[
            'col1', 'igfield2', 'datacol', ], [
            'row1', 'ignore&', 'data1', ], [
            'row2', 'ignore&', 'data2', ], [
            'row3', 'ignore&', 'data3', ], [
            'row4', 'ignore&', 'data4', ], [
            'row5', 'ignore&', 'data5', ], [
            'row6', 'ignore&', 'data6',
        ]])
        comparator = FieldComparator(r1, r2, ['igfield'], ['igfield2'])
        self.assertTrue(comparator.isSame())

    def testDataType2(self):
        r1 = TestReader([[
            'col1', 'datacol', 'igfield', ], [
            'row1', 'data1', 'ignore*', ], [
            'row2', 'data2', 'ignore*', ], [
            'row3', 'data3', 'ignore*', ], [
            'row4', 'data4', 'ignore*', ], [
            'row5', 'data5', 'ignore*', ], [
            'row6', 'data6', 'ignore*',
        ]])
        r2 = TestReader([[
            'col1', 'igfield2', 'datacol', ], [
            'row1', 'ignore&', 'data1', ], [
            'row2', 'ignore&', 'data2', ], [
            'row3', 'ignore&', 'data3', ], [
            'row4', 'ignore&', 'data4', ], [
            'row5', 'ignore&', 'data5', ], [
            'row6', 'ignore&', 'data6',
        ]])
        model = Task.objects.create(
            summary='test_task',
            left_source='database:dummy',
            left_query_sql='SELECT * FROM ds1;',
            right_source='database:dummy',
            right_query_sql='SELECT * FROM ds2;',
        )
        comparator = FieldComparator(r1, r2, taskModel=model)
        self.assertTrue(not comparator.isSame())
        self.assertEqual(model.result, 'Fields are inconsistent!')
        # self.assertEqual(model.result, 'Fields are inconsistent!')
        self.assertEqual(
            model.result_detail,
            "+ {'name': 'igfield2', 'type': 'string', 'format': 'default'}"
            "<@#$>- {'name': 'igfield', 'type': 'string', 'format': 'default'}"
        )

    def testDataType3(self):
        DbConfig = {}
        DbConfig['id'] = 'default'
        DbConfig['ENGINE'] = 'django.db.backends.sqlite3'
        DbConfig['NAME'] = ':memory:'
        query_sql1 = 'SELECT * FROM r1;'
        r1 = DatabaseReader(DbConfig, query_sql1)
        r2 = TestReader([[
            'col1', 'igfield2', 'datacol', ], [
            'row1', 'ignore&', 'data1', ], [
            'row2', 'ignore&', 'data2', ], [
            'row3', 'ignore&', 'data3', ], [
            'row4', 'ignore&', 'data4', ], [
            'row5', 'ignore&', 'data5', ], [
            'row6', 'ignore&', 'data6',
        ]])
        model = Task.objects.create(
            summary='test_task',
            left_source='database:dummy',
            left_query_sql='SELECT * FROM r1;',
            right_source='database:dummy',
            right_query_sql='SELECT * FROM ds2;',
        )
        comparator = FieldComparator(r1, r2, taskModel=model)
        self.assertTrue(not comparator.isSame())
        self.assertEqual(model.result, 'Fields are inconsistent!')

    def testDataType4(self):
        DbConfig = {}
        DbConfig['id'] = 'default'
        DbConfig['ENGINE'] = 'django.db.backends.sqlite3'
        DbConfig['NAME'] = ':memory:'
        query_sql1 = 'SELECT * FROM r1;'
        r1 = DatabaseReader(DbConfig, query_sql1)
        r2 = TestReader([[
            'col1', 'igfield2', 'col2', ], [
            '1', 'ignore&', '1', ], [
            '2', 'ignore&', '2', ], [
            '3', 'ignore&', '3', ], [
            '4', 'ignore&', '4', ], [
            '5', 'ignore&', '5', ], [
            '6', 'ignore&', '6',
        ]])
        model = Task.objects.create(
            summary='test_task',
            left_source='database:dummy',
            left_query_sql='SELECT * FROM r1;',
            right_source='database:dummy',
            right_query_sql='SELECT * FROM ds2;',
        )
        comparator = FieldComparator(r1, r2, [], ['igfield2'], taskModel=model)
        self.assertTrue(comparator.isSame())
