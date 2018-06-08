from django.test import TestCase, TransactionTestCase
from qdiff.writers import DatabaseWriter, CsvWriter
from random import randint
from django.db import connection
from csv import reader
import os


class DatabaseWriterTestCase(TransactionTestCase):

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

    def testGetColumns(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        w = DatabaseWriter(newDBConfig, 'temp')
        self.assertEquals(w.getColumns(), ['col1', 'col2'])

    def testInsertStatement(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        w = DatabaseWriter(newDBConfig, 'temp')
        self.assertEquals(
            w.getInsertStatement(),
            '''INSERT INTO temp (col1, col2) VALUES (%s, %s)''')

    def testInsert(self):
        newDBConfig = {}
        newDBConfig['id'] = 'default'
        newDBConfig['ENGINE'] = 'django.db.backends.sqlite3'
        newDBConfig['NAME'] = ':memory:'
        w = DatabaseWriter(newDBConfig, 'temp')
        w.writeAll([
            (
                str(randint(0, 1)),
                str(randint(0, 10))
            )
            for i in range(10)])
        with connection.cursor() as cursor:
            cursor.execute('''SELECT * FROM temp;''')
            rows = cursor.fetchall()
            self.assertEquals(len(rows), 20)


class CsvWriterTestCase(TestCase):

    def setUp(self):
        pass

    def testWriteWithoutHeaders(self):
        with open('test_csvwriter.txt', 'w+', newline='') as csvfile:
            w = CsvWriter(csvfile, delimiter=',', quotechar='\\')
            w.writeAll([['row1', 'data1'], ['row2', 'data2']])
        with open('test_csvwriter.txt', newline='') as csvfile:
            w = reader(csvfile, delimiter=',', quotechar='\\')
            r = '\n'.join([str(x) for x in list(w)])
            os.remove('test_csvwriter.txt')
            self.assertEquals(r, "['row1', 'data1']\n['row2', 'data2']")

    def testWriteWithHeaders(self):
        with open('test_csvwriter.txt', 'w+', newline='') as csvfile:
            w = CsvWriter(
                csvfile, delimiter=',',
                quotechar='\\', headers=['h1', 'h2'])
            w.writeAll([['row1', 'data1'], ['row2', 'data2']])
        with open('test_csvwriter.txt', newline='') as csvfile:
            w = reader(csvfile, delimiter=',', quotechar='\\')
            r = '\n'.join([str(x) for x in list(w)])
            os.remove('test_csvwriter.txt')
            self.assertEquals(
                r,
                "['h1', 'h2']\n['row1', 'data1']\n['row2', 'data2']")
