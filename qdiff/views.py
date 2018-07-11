from django.shortcuts import render, get_object_or_404
from qdiff.models import Task, ConflictRecord
from django.conf import settings
from qdiff.utils import getMaskedSources, ConflictRecordReader


def task_list_view(request):
    context = {}
    taskList = Task.objects.all()
    taskList.reverse()
    context['tasks'] = taskList
    return render(request, 'qdiff/task_list.html', context)


def task_detail_view(request, pk):
    context = {}
    task = get_object_or_404(Task, id=pk)
    tableName1 = settings.CONFLICT_TABLE_NAME_FORMAT.format(
        prefix=settings.GENERATED_TABLE_PREFIX,
        id=str(task.id),
        position=ConflictRecord.POSITION_IN_TASK_LEFT
    )
    tableName2 = settings.CONFLICT_TABLE_NAME_FORMAT.format(
        prefix=settings.GENERATED_TABLE_PREFIX,
        id=str(task.id),
        position=ConflictRecord.POSITION_IN_TASK_RIGHT
    )
    crr1 = ConflictRecordReader(tableName1)
    result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
               for item in crr1.getConflictRecords()]
    crr2 = ConflictRecordReader(tableName2)
    result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
               for item in crr2.getConflictRecords()]
    conflictResults = result1 + result2
    columns = crr1.getColumns()

    context['source1'], context['source2'] = getMaskedSources(task)
    context['task'] = task
    context['columns'] = columns
    context['conflictResults'] = conflictResults
    return render(request, 'qdiff/task_detail.html', context)


def task_create_view(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'qdiff/task_create.html', context)
    if request.POST:
        print(request.POST)
    if request.FILES:
        print(request.FILES)
    return render(request, 'qdiff/task_create.html', context)
