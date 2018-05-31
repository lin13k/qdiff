from django.test import TestCase
from qdiff.writers import DBWriter, CSVWriter
from random import randint
from django.db import connection
from csv import reader
import os


class DbWriterTestCase(TestCase):

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

    def testGetColumns(self):
        w = DBWriter(connection, 'temp')
        self.assertEquals(w.getColumns(), ['col1', 'col2'])

    def testInsertStatement(self):
        w = DBWriter(connection, 'temp')
        self.assertEquals(
            w.getInsertStatement(),
            '''INSERT INTO temp (col1, col2) VALUES (%s, %s)''')

    def testInsert(self):
        w = DBWriter(connection, 'temp')
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


class CSVWriterTestCase(TestCase):

    def setUp(self):
        pass

    def testWriteWithoutHeaders(self):
        with open('test_csvwriter.txt', 'w+', newline='') as csvfile:
            w = CSVWriter(csvfile, delimiter=',', quotechar='\\')
            w.writeAll([['row1', 'data1'], ['row2', 'data2']])
        with open('test_csvwriter.txt', newline='') as csvfile:
            w = reader(csvfile, delimiter=',', quotechar='\\')
            r = '\n'.join([str(x) for x in list(w)])
            os.remove('test_csvwriter.txt')
            self.assertEquals(r, "['row1', 'data1']\n['row2', 'data2']")

    def testWriteWithHeaders(self):
        with open('test_csvwriter.txt', 'w+', newline='') as csvfile:
            w = CSVWriter(
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
