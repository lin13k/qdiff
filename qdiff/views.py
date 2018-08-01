from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect, reverse
from hashlib import sha256
from io import StringIO
from qdiff.models import Task, ConflictRecord, Report
from qdiff.readers import DatabaseReader
from qdiff.tasks import compareCommand
from qdiff.utils.ciphers import FernetCipher, decodedContent
from qdiff.utils.convertors import listInPostDataToList
from qdiff.utils.files import saveUploadedFile
from qdiff.utils.model import ConflictRecordReader
from qdiff.utils.model import getConflictRecordTableNames
from qdiff.utils.model import getMaskedSourceFromString
from qdiff.utils.validations import isValidFileName
from qdiff.utils.validations import Validator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response
from rest_framework.status import HTTP_404_NOT_FOUND
from wsgiref.util import FileWrapper
import json
import os
import csv


def task_list_view(request):
    '''view for providing task list'''
    context = {}
    taskList = Task.objects.all()
    taskList.reverse()
    context['tasks'] = taskList
    return render(request, 'qdiff/task_list.html', context)


def task_detail_view(request, pk):
    '''
    view for providing task detail view
    Positional arguements
    pk -- primary key for task model
    '''
    context = {}
    task = get_object_or_404(Task, id=pk)
    tableName1, tableName2 = getConflictRecordTableNames(task)
    conflictResults = []
    columns = []
    if task.status == Task.STATUS_OF_TASK_COMPLETED:
        crr1 = ConflictRecordReader(tableName1)
        result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
                   for item in crr1.getConflictRecords()]
        crr2 = ConflictRecordReader(tableName2)
        result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
                   for item in crr2.getConflictRecords()]
        conflictResults = result1 + result2
        columns = crr1.getColumns()

    context['source1'] = task.left_source
    context['source2'] = task.right_source
    context['task'] = task
    context['columns'] = columns
    context['detail'] = task.result_detail.replace(
        settings.RESULT_SPLITTING_TOKEN, '<br>') if task.result_detail else ''
    context['conflictResults'] = conflictResults
    return render(request, 'qdiff/task_detail.html', context)


def task_create_view(request):
    '''
    view for creating task
    it does following items
    1. save the file
    2. validate the input
    3. create models
    4. invoke async function call, compareCommand

    '''
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
    grouping_fields = request.POST.get('grouping_fields', None)

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
    # create report model
    if grouping_fields and len(grouping_fields) > 0:
        Report.objects.create(
            report_generator='AggregatedReportGenerator',
            parameters='{"grouping_fields":"%s"}' % grouping_fields,
            task=model)

    # invoke async compare_command with model id
    compareCommand.delay(model.id, rds1, rds2, wds1, wds2)
    return redirect(reverse('task_detail', kwargs={'pk': model.id}))


def database_config_file_view(request):
    '''view for configuration'''
    context = {}
    return render(request, 'qdiff/create_config.html', context)


def aggregated_report_view(request, taskId=None):
    '''view for aggregated report'''
    context = {}
    try:
        taskModel = Task.objects.get(id=taskId)
    except ObjectDoesNotExist as e:
        return Response(status=HTTP_404_NOT_FOUND)
    context['task'] = taskModel
    return render(request, 'qdiff/aggregated_report.html', context)


def statics_pie_report_view(request, taskId=None):
    '''view for pie chart in task detail page'''
    context = {}
    taskId = taskId
    try:
        taskModel = Task.objects.get(id=taskId)
    except ObjectDoesNotExist as e:
        return Response(status=HTTP_404_NOT_FOUND)
    context['identical_rows_number'] = (
        taskModel.total_left_count + taskModel.total_right_count -
        taskModel.left_diff_count - taskModel.right_diff_count)
    context['different_rows_number'] = taskModel.left_diff_count +\
        taskModel.right_diff_count
    return render(request, 'qdiff/statics_pie_report.html', context)


class Database_Config_APIView(APIView):
    '''
    this class is from drf
    it receive database configurations in post method
    and provide download link as get method
    '''
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        '''
        create configuration file for download and return the file name.
        it also encrypt the file.
        '''
        errors = []
        configsList = listInPostDataToList(request.POST)
        configDict = {config[0]: config[1] for config in configsList}
        # DatabaseReader to test if it can show table
        try:
            dr = DatabaseReader(configDict, 'show tables')
            if dr.getCursor() is None:
                errors.append('Cannot access the database')
        except Exception as e:
            errors.append('Invalid database configuration')
            errors.append(str(e))

        if len(errors) > 0:
            return Response({'errors': errors},
                            status=status.HTTP_400_BAD_REQUEST)
        fc = FernetCipher()
        configJsonStr = json.dumps(configDict)
        code = fc.encode(configJsonStr)
        filename = (str(configDict.get('NAME', None)) +
                    '_' +
                    str(configDict.get('HOST', None)) +
                    '_')
        filename += sha256(configJsonStr.encode()).hexdigest()
        if not os.path.exists(settings.TEMP_FOLDER):
            os.makedirs(settings.TEMP_FOLDER)

        with open(os.path.join(
                settings.TEMP_FOLDER, filename + '.csv'), 'w+') as f:
            f.write(code)
            f.flush()
            f.seek(0)

        return Response({'key': filename})

    def get(self, request, format=None):
        '''return the configuration file and delete it'''
        key = request.GET.get('key', None)
        # clean the key
        if key is None or not isValidFileName(key):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            memoryFile = StringIO()
            filename = '_'.join(key.split('_')[:2])
            with open(
                os.path.join(
                    settings.TEMP_FOLDER, key + '.csv'), 'r') as f:
                memoryFile.write(f.read())
                memoryFile.flush()
                memoryFile.seek(0)
            os.remove(os.path.join(settings.TEMP_FOLDER, key + '.csv'))
            r = HttpResponse(
                FileWrapper(memoryFile), content_type='text/plain')
            r['Content-Disposition'
              ] = 'attachment; filename="' + filename + '_databaseConfig.txt"'
            return r
        except Exception as e:
            print(e)
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)


class Agregated_Report_APIView(APIView):
    '''
    this class is from drf
    it provide the data in json format for the aggregated report
    '''
    permission_classes = (AllowAny,)

    def get(self, request, format=None, taskId=None):
        taskId = taskId
        try:
            taskModel = Task.objects.get(id=taskId)
        except ObjectDoesNotExist as e:
            return Response(status=HTTP_404_NOT_FOUND)
        sReportModel = taskModel.reports.filter(
            report_generator='AggregatedReportGenerator').last()
        if sReportModel is None:
            return Response(status=HTTP_404_NOT_FOUND)
        with open(sReportModel.file.path, 'r') as f:
            report = f.read()

        reportObj = json.loads(report)

        returnObj = {'name': 'Root', 'children': []}
        lurObj = {'name': 'Left Unpaired Records'}
        lurObj['children'] = [
            {'name': i, 'size': 1} for i in reportObj['leftUnpairedRecords']]
        returnObj['children'].append(lurObj)

        rurObj = {'name': 'Right Unpaired Records'}
        rurObj['children'] = [
            {'name': i, 'size': 1} for i in reportObj['rightUnpairedRecords']]
        returnObj['children'].append(rurObj)

        fbdOjb = {'name': 'Field Based Difference', 'children': []}
        for index, column in enumerate(reportObj['columns']):
            columnObj = {'name': column, 'children': []}
            for diff in reportObj['columnRecords'][index]:
                columnObj['children'].append(
                    {'name': diff[0][0] + '\t' + str(diff[1:]), 'size': 1})
            fbdOjb['children'].append(columnObj)
        returnObj['children'].append(fbdOjb)

        ldrObj = {'name': 'Left Duplicated Records'}
        ldrObj['children'] = [
            {'name': i, 'size': 1} for i in reportObj['leftDuplicatedRecords']]
        returnObj['children'].append(ldrObj)

        ldrObj = {'name': 'Right Duplicated Records'}
        ldrObj['children'] = [
            {'name': i, 'size': 1} for i in reportObj[
                'rightDuplicatedRecords']]
        returnObj['children'].append(ldrObj)

        return Response(returnObj)


class Agregated_Report_CSV_Download_APIVIEW(APIView):
    '''
    this class is from drf
    it provide the data in json format for downloading the report
    '''
    permission_classes = (AllowAny,)

    def get(self, request, format=None, taskId=None):
        taskId = taskId
        try:
            taskModel = Task.objects.get(id=taskId)
        except ObjectDoesNotExist as e:
            return Response(status=HTTP_404_NOT_FOUND)
        sReportModel = taskModel.reports.filter(
            report_generator='AggregatedReportGenerator').last()
        if sReportModel is None:
            return Response(status=HTTP_404_NOT_FOUND)
        with open(sReportModel.file.path, 'r') as f:
            report = f.read()

        reportObj = json.loads(report)
        memoryFile = StringIO()
        indent = ['']
        csvWriter = csv.writer(
            memoryFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        with open(sReportModel.file.path) as f:
            csvWriter.writerow(
                ['Field Based Differences ' +
                 str(sum(map(len, reportObj['columnRecords']))),
                 'Field Name', 'Differences'])
            for index, column in enumerate(reportObj['columns']):
                csvWriter.writerow(
                    indent +
                    [column, len(reportObj['columnRecords'][index])])
                for record in reportObj['columnRecords'][index]:
                    csvWriter.writerow(indent * 2 + record)
            csvWriter.writerow([])
            csvWriter.writerow(
                ['Left Unpaired Records ' +
                 str(len(reportObj['leftUnpairedRecords'])),
                 'Keys'])
            for record in reportObj['leftUnpairedRecords']:
                csvWriter.writerow(indent + record)
            csvWriter.writerow([])
            csvWriter.writerow(
                ['Right Unpaired Records ' +
                 str(len(reportObj['rightUnpairedRecords'])),
                 'Keys'])
            for record in reportObj['rightUnpairedRecords']:
                csvWriter.writerow(indent + record)
            csvWriter.writerow([])
            csvWriter.writerow(
                ['Left Duplicated Records ' +
                 str(len(reportObj['leftDuplicatedRecords'])),
                 'keys'])
            for record in reportObj['leftDuplicatedRecords']:
                csvWriter.writerow(indent + record)
            csvWriter.writerow([])
            csvWriter.writerow(
                ['Right Duplicated Records ' +
                 str(len(reportObj['rightDuplicatedRecords'])),
                 'keys'])
            for record in reportObj['rightDuplicatedRecords']:
                csvWriter.writerow(indent + record)
        memoryFile.flush()
        memoryFile.seek(0)
        r = HttpResponse(
            FileWrapper(memoryFile), content_type='text/plain')
        r['Content-Disposition'
          ] = 'attachment; filename="TASK_%s_Report.csv"' % taskId
        return r
