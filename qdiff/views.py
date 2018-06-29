from django.shortcuts import render, get_object_or_404, redirect, reverse
from qdiff.models import Task, ConflictRecord
from qdiff.readers import DatabaseReader
from django.conf import settings
from qdiff.utils.model import getMaskedSources
from qdiff.tasks import compareCommand
from qdiff.utils.validations import Validator
from qdiff.utils.files import saveUploadedFile
import os


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
    conflictResults = []
    columns = []
    # condition for pending case
    if task.status == Task.STATUS_OF_TASK_COMPLETED:
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

    context['source1'], context['source2'] = getMaskedSources(task)
    context['task'] = task
    context['columns'] = columns
    context['detail'] = task.result_detail.replace(
        settings.RESULT_SPLITTING_TOKEN, '<br>') if task.result_detail else ''
    context['conflictResults'] = conflictResults
    return render(request, 'qdiff/task_detail.html', context)


def task_create_view(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'qdiff/task_create.html', context)
    # save the csv if file uploaded
    rds1 = rds2 = path1 = path2 = None
    file1 = request.FILES.get('file1', None)
    if file1:
        path1 = saveUploadedFile(file1)
        rds1 = settings.SOURCE_TYPE_CSV_PREFIX + path1
    file2 = request.FILES.get('file2', None)
    if file2:
        path2 = saveUploadedFile(file2)
        rds2 = settings.SOURCE_TYPE_CSV_PREFIX + path2

    # validate the input
    ignore1 = request.POST.get('ignoreList1', None)
    ignore2 = request.POST.get('ignoreList2', None)
    summary = request.POST.get('summary', None)

    # TODO support database
    # database1 = request.POST.get('database1', None)
    # database2 = request.POST.get('database2', None)
    sql1 = request.POST.get('sql1', None)
    sql2 = request.POST.get('sql2', None)
    wds1 = request.POST.get('wds1', None)
    wds2 = request.POST.get('wds2', None)

    v = Validator(
        summary, rds1, rds2,
        sql1, sql2, ignore1, ignore2,
        wds1, wds2)
    errs = v.validate()
    if len(errs) > 0:
        # delete the file if not valid
        if path1:
            os.remove(path1)
        if path2:
            os.remove(path2)
        context['errors'] = errs
        # passing original value back
        return render(request, 'qdiff/task_create.html', context)

    # create model
    model = Task.objects.create(
        summary=summary,
        left_source=rds1,
        left_query_sql=sql1,
        left_ignore_fields=ignore1,
        right_source=rds2,
        right_query_sql=sql2,
        right_ignore_fields=ignore2,
    )
    # invoke async compare_command with model id
    compareCommand.delay(model.id, wds1, wds2)
    # return submitted view ??
    return redirect(reverse('task_detail', kwargs={'pk': model.id}))
    # return render(request, 'qdiff/task_create.html', context)
