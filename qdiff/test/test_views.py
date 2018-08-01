from django.test import TestCase, Client
from django.urls import reverse
from qdiff.models import Task
from io import StringIO
from rest_framework.status import HTTP_200_OK
import json


class TaskViewTestCase(TestCase):
    def setUp(self):
        # given
        self.client = Client()
        self.taskModel = Task.objects.create(
            summary='NAME_OF_THE_TASK_QQQQ',
            left_source='dummy', right_source='dummy')

    def testTaskListView(self):
        # when
        response = self.client.get(reverse('task_list'))

        # then
        self.assertTrue('NAME_OF_THE_TASK_QQQQ' in response.content.decode())

    def testTaskDetailView(self):
        # when
        response = self.client.get(
            reverse('task_detail', kwargs={'pk': self.taskModel.id}))
        # then
        self.assertTrue('NAME_OF_THE_TASK_QQQQ' in response.content.decode())

    def testTaskCreateViewWithTwoCsv(self):
        # given
        tmpFile1 = StringIO()
        tmpFile1.write('key,col1,col2\n')
        tmpFile1.write('key1,value2,value3\n')
        tmpFile1.write('key2,value4,value5\n')
        tmpFile1.flush()
        tmpFile1.seek(0)

        tmpFile2 = StringIO()
        tmpFile2.write('key,col1,col2\n')
        tmpFile2.write('key1,value2,value3\n')
        tmpFile2.write('key2,value4,value5\n')
        tmpFile2.flush()
        tmpFile2.seek(0)

        # when
        response = self.client.post(
            reverse('task_create'),
            {
                'file1': tmpFile1,
                'file2': tmpFile2,
                'summary': 'summary for test! TEST'
            }
        )
        # then
        self.assertRedirects(response, reverse(
            'task_detail', kwargs={'pk': self.taskModel.id + 1}))


class DatabaseConfigTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def testGetDbConfigPage(self):
        # when
        response = self.client.get(reverse('create_config_file'))

        # then
        self.assertEqual(response.status_code, HTTP_200_OK)

    def testPostDbConfigPage(self):
        # given
        data = {}
        data['table_data[0][]'] = ['ENGINE', 'django.db.backends.sqlite3']
        data['table_data[1][]'] = ['NAME', ':memory:']

        # when
        response = self.client.post(reverse('create_config_file_upload'), data)

        # then
        self.assertEqual(response.status_code, HTTP_200_OK)

        # given result from previous step
        returnObj = response.data
        key = returnObj['key']

        # when
        response = self.client.get(
            reverse('create_config_file_upload') + '?key=' + key)

        # then
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename=":memory:__databaseConfig.txt"')
        self.assertEqual(response.status_code, HTTP_200_OK)
