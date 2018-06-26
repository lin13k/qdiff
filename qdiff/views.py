from django.shortcuts import render, get_object_or_404
from qdiff.models import Task, ConflictRecord
from qdiff.readers import DatabaseReader
from django.conf import settings


def task_list_view(request):
    context = {}
    taskList = Task.objects.all()
    taskList.reverse()
    context['tasks'] = taskList
    return render(request, 'qdiff/task_list.html', context)


def task_detail_view(request, pk):
    context = {}
    task = get_object_or_404(Task, id=pk)
    defaultConfigs = settings.DATABASES['default'].copy()
    tableName1 = '%s_TASK_%s_%s' % (
        settings.GENERATED_TABLE_PREFIX,
        str(task.id),
        ConflictRecord.POSITION_IN_TASK_LEFT
    )
    tableName2 = '%s_TASK_%s_%s' % (
        settings.GENERATED_TABLE_PREFIX,
        str(task.id),
        ConflictRecord.POSITION_IN_TASK_RIGHT
    )
    datareader1 = DatabaseReader(
        defaultConfigs,
        'SELECT * FROM %s;' % (tableName1))
    result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
               for item in datareader1.getRowsList()]
    datareader2 = DatabaseReader(
        defaultConfigs,
        'SELECT * FROM %s;' % (tableName2))
    result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
               for item in datareader2.getRowsList()]
    conflictResults = result1 + result2
    columns = datareader1.getColumns()
    context['task'] = task
    context['columns'] = columns
    context['conflictResults'] = conflictResults
    return render(request, 'qdiff/task_detail.html', context)
