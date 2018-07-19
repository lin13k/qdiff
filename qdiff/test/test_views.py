from django.test import TestCase, Client
from django.urls import reverse
from qdiff.models import Task
from io import StringIO


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
        tmpFile = StringIO()
        tmpFile.write('key,col1,col2\n')
        tmpFile.write('key1,value2,value3\n')
        tmpFile.write('key2,value4,value5\n')
        tmpFile.flush()
        tmpFile.seek(0)

        # when
        response = self.client.post(
            reverse('task_create'),
            {
                'file1': tmpFile,
                'file2': tmpFile,
                'summary': 'summary for test! TEST'
            }
        )
        # then
        self.assertRedirects(response, reverse(
            'task_detail', kwargs={'pk': self.taskModel.id + 1}))
