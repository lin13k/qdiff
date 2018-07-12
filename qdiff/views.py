from django.shortcuts import render, get_object_or_404, redirect, reverse
from qdiff.models import Task, ConflictRecord
from django.conf import settings
from qdiff.utils.model import ConflictRecordReader
from qdiff.tasks import compareCommand
from qdiff.utils.validations import Validator
from qdiff.utils.files import saveUploadedFile
from qdiff.utils.convertors import listInPostDataToList
from django.http import HttpResponse
from wsgiref.util import FileWrapper
import os
from io import StringIO
from rest_framework.views import APIView, Response
from rest_framework.permissions import AllowAny
from rest_framework import status
import json
from qdiff.utils.ciphers import FernetCipher, decodedContent
from qdiff.utils.model import getMaskedSourceFromString
from qdiff.utils.validations import isAllHex
from qdiff.readers import DatabaseReader
from hashlib import sha256


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
    conflictResults = []
    columns = []
    crr1 = ConflictRecordReader(tableName1)
    result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
               for item in crr1.getConflictRecords()]
    crr2 = ConflictRecordReader(tableName2)
    result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
               for item in crr2.getConflictRecords()]
    conflictResults = result1 + result2
    columns = crr1.getColumns()

    # not required masking, since remove the pw before saving into DB
    context['source1'] = task.left_source
    context['source2'] = task.right_source
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
    dbfile1 = request.FILES.get('dbfile1', None)
    if dbfile1:
        rds1 = settings.SOURCE_TYPE_DATABASE_PREFIX + decodedContent(dbfile1)
    dbfile2 = request.FILES.get('dbfile2', None)
    if dbfile2:
        rds2 = settings.SOURCE_TYPE_DATABASE_PREFIX + decodedContent(dbfile2)

    # validate the input
    ignore1 = request.POST.get('ignoreList1', None)
    ignore2 = request.POST.get('ignoreList2', None)
    summary = request.POST.get('summary', None)

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
        left_source=getMaskedSourceFromString(rds1),
        left_query_sql=sql1,
        left_ignore_fields=ignore1,
        right_source=getMaskedSourceFromString(rds2),
        right_query_sql=sql2,
        right_ignore_fields=ignore2,
    )
    # invoke async compare_command with model id
    # TODO send source for read
    compareCommand.delay(model.id, rds1, rds2, wds1, wds2)
    # return submitted view ??
    return redirect(reverse('task_detail', kwargs={'pk': model.id}))
    # return render(request, 'qdiff/task_create.html', context)


def database_config_file_view(request):
    context = {}
    return render(request, 'qdiff/create_config.html', context)


class Database_Config_APIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        errors = []
        configsList = listInPostDataToList(request.POST)
        configDict = {config[0]: config[1] for config in configsList}
        # memoryFile = StringIO()
        # DatabaseReader to test if it can show table
        try:
            dr = DatabaseReader(configDict, 'show tables')
            if dr.getCursor() is None:
                errors.append('Cannot access the database')
        except Exception as e:
            errors.append('Invalid database configuration')

        if len(errors) > 0:
            return Response({'errors': errors})
        fc = FernetCipher()
        configJsonStr = json.dumps(configDict)
        code = fc.encode(configJsonStr)
        filename = (str(configDict.get('NAME', None)) +
                    '_' +
                    str(configDict.get('HOST', None)) +
                    '_')
        filename += sha256(configJsonStr.encode()).hexdigest()
        if not os.path.exists('tmp'):
            os.makedirs('tmp')

        with open(os.path.join('tmp', filename + '.csv'), 'w+') as f:
            f.write(code)
            f.flush()
            f.seek(0)

        return Response({'key': filename})

    def get(self, request, format=None):
        key = request.GET.get('key', None)

        # clean the key
        if key is None or not isAllHex(key):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            memoryFile = StringIO()
            filename = '_'.join(key.split('_')[:2])
            with open(os.path.join('tmp', key + '.csv'), 'r') as f:
                memoryFile.write(f.read())
                memoryFile.flush()
                memoryFile.seek(0)
            os.remove(os.path.join('tmp', key + '.csv'))
            r = HttpResponse(
                FileWrapper(memoryFile), content_type='text/plain')
            r['Content-Disposition'
              ] = 'attachment; filename="' + filename + '_databaseConfig.txt"'
            return r
        except Exception as e:
            print(e)
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)
