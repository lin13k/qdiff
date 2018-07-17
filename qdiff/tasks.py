from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from qdiff.models import Task
from qdiff.managers import TaskManager


@task(name="test_task")
def test(s):
    return str(s) + 'complete'


@task(name="compare_command")
def compareCommand(
        taskId, rds1, rds2,
        wds1=None, wds2=None):

    # init the model
    model = Task.objects.get(id=taskId)
    # call manager and compare
    try:
        manager = TaskManager(
            model,
            rds1,
            rds2,
            wds1,
            wds2)
        manager.compare()
    except Exception as e:
        # traceback.print_exc(e)
        model.result = Task.STATUS_OF_TASK_ERROR
        model.result_detail = str(e)
        if hasattr(e, 'errors'):
            model.result_detail = str(e) + ':' + ' '.join(map(str, e.errors))
        model.save()
    finally:
        # delete db config
        pass
