from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from qdiff.models import Task
from qdiff.managers import TaskManager


@task(name="test_task")
def test(s):
    return str(s) + 'complete'


@task(name="compare_command")
def compareCommand(
        taskId,
        wds1, wds2):

    # init the model
    model = Task.objects.get(id=taskId)
    # call manager and compare
    try:
        manager = TaskManager(
            model,
            wds1,
            wds2)
        manager.compare()
    except Exception as e:
        model.result = Task.STATUS_OF_TASK_ERROR
        model.result_detail = str(e)
        model.save()
