from django.test import TransactionTestCase
from django.db import connection
from django.core.management import call_command
from django.conf import settings
from qdiff.models import Task
import json


class CompareCommandTestCase(TransactionTestCase):
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
            try:
                cursor.execute('''CREATE TABLE r3 (
                        id INTEGER,
                        address VARCHAR(200),
                        price DECIMAL(6,3) NULL,
                        qan INTEGER,
                        start DATE
                    );
                ''')
                data = [('1', '230 N. Craig St. Apt. 605',
                         '23.5', '5', '2018-06-07'),
                        ('2', '230 N. Craig St. Apt. 605',
                         '23', '50', '2018-06-07'),
                        ('3', '230 N. Craig St. Apt. 605',
                         '23.99', '12', '2018-06-07'),
                        ('4', '230 N. Madrea St. Apt. 605',
                         '5', '21', '2018-06-07'),
                        ('5', '230 N. Craig St. Apt. 605',
                         None, '5', '2018-06-07')]
                query = '''INSERT INTO r3 (id, address, price, qan, start)
                    VALUES (%s, %s, %s, %s, %s)
                '''
                cursor.executemany(query, data)

            except Exception as e:
                pass
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

        with connection.cursor() as cursor:
            try:
                cursor.execute('DROP TABLE GEN_TASK_1_LF;')
                cursor.execute('DROP TABLE GEN_TASK_1_RT;')
            except Exception as e:
                pass

    def testCompare1(self):
        with open('qdiff/test/test_compare_command_output.txt', 'w') as f:
            call_command(
                'compare',
                '--summary=test task',
                "--rds1=database:" +
                json.dumps(settings.DATABASES['default']),
                "--sql1=select * from r3",
                "--rds2=database:" +
                json.dumps(settings.DATABASES['default']),
                "--sql2=select * from r3",
                stdout=f,
            )
        task = Task.objects.all()[-1]
        self.assertEqual(task.result, 'No difference found, congrats')
        self.assertEqual(
            task.result_detail,
            'Searched total 10 records')

    def testCompare2(self):
        with open('qdiff/test/test_compare_command_output.txt', 'w') as f:
            call_command(
                'compare',
                '--summary=test task',
                "--rds2=database:" +
                json.dumps(settings.DATABASES['default']),
                "--sql2=select * from r3",
                "--rds1=csv:qdiff/test/testcsv.csv",
                stdout=f,
            )
