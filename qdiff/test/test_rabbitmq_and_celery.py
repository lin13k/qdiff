from django.test import TestCase
import pytest
from qdiff.models import Task
from qdiff.tasks import compareCommand, test
from django.conf import settings
import sys
if sys.version_info > (3,):
    from unittest.mock import patch
else:
    from mock import patch


class CompareCommandTestCase(TestCase):
    @patch('qdiff.tasks.TaskManager')
    def testCallManagerSuccess(self, manager):
        task = Task.objects.create(
            summary='test',
            left_source='csv:dummy.csv',
            right_source='csv:dummy.csv',
        )
        compareCommand(task.pk, 'csv:dummy', 'csv:dummy')
        manager.assert_called_with(task, 'csv:dummy', 'csv:dummy', None, None)

    @patch('qdiff.tasks.TaskManager.compare')
    def testCallCompareSuccess(self, compareFunction):
        task = Task.objects.create(
            summary='test',
            left_source='csv:dummy.csv',
            right_source='csv:dummy.csv',
        )
        compareCommand(task.pk, 'csv:dummy', 'csv:dummy')
        compareFunction.assert_called_with()

    @pytest.mark.celery(result_backend=settings.CELERY_RESULT_BACKEND)
    def testTaskQueueAvailable(self):
        self.assertEqual(test.delay('Input').get(timeout=10), 'Inputcomplete')

    # @patch('proj.tasks.Task.order')
    # @patch('proj.tasks.send_order.retry')
    # def test_failure(self, send_order_retry, task_order):
    #     task = Task.objects.create(
    #         name='Foo',
    #     )

    #     # Set a side effect on the patched methods
    #     # so that they raise the errors we want.
    #     send_order_retry.side_effect = Retry()
    #     task_order.side_effect = OperationalError()

    #     with raises(Retry):
    #         send_order(task.pk, 3, Decimal(30.6))
