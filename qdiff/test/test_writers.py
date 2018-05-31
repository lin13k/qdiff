from django.test import TestCase
from qdiff.writers import DBWriter
from random import randint
from django.db import connection


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
        print(w.getInsertStatement())
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
