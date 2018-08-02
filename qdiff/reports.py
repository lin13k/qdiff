# from qdiff.models import ReportGenerator
from django.conf import settings
from qdiff.utils.model import getConflictRecordTableNames
from qdiff.utils.model import ConflictRecordReader
from qdiff.models import ConflictRecord
import os
import json
from qdiff.exceptions import InvalidParametersException
from qdiff.exceptions import InvalidClassNameException
from qdiff.exceptions import MissingParametersException
import errno
from collections import defaultdict


class ReportGenerator:
    '''
    base class for report generators
    it provides the factory design pattern
    '''

    def factory(className, *args, **kwargs):
        if className == "AggregatedReportGenerator":
            return AggregatedReportGenerator(*args, **kwargs)
        raise InvalidClassNameException('')
    factory = staticmethod(factory)

    def __init__(self, reportModel):
        '''
        init the generator with the reportModel
        including following items
        1. parameters loading
        2. conflict records loading
        3. columns list loading
        '''
        self._reportModel = reportModel
        self.parameters = json.loads(self._reportModel.parameters)

        # get data
        taskModel = self._reportModel.task
        tableName1, tableName2 = getConflictRecordTableNames(taskModel)
        self.conflictRecords1 = []
        self.conflictRecords2 = []
        crr1 = ConflictRecordReader(tableName1)
        result1 = [tuple(item + (ConflictRecord.POSITION_IN_TASK_LEFT,))
                   for item in crr1.getConflictRecords()]
        crr2 = ConflictRecordReader(tableName2)
        result2 = [tuple(item + (ConflictRecord.POSITION_IN_TASK_RIGHT,))
                   for item in crr2.getConflictRecords()]
        self.conflictRecords1.extend(result1)
        self.conflictRecords2.extend(result2)
        self.conflictRecordColumns = crr1.getColumns()

    def generate(self):
        '''
        invoke the _process function and save the result into file
        '''
        reportObj = self._process(
            self.conflictRecords1,
            self.conflictRecords2,
            self.getConflictRecordColumn())
        return self._saveReportFileWithObject(reportObj)

    def _process(self, data1, data2, columns):
        '''
        main logic for the report generator
        Positional arguements
        data1 -- conflict records from left source
        data2 -- conflict records from right source
        columns -- column name list

        this function should return dictionary like object
        '''
        raise NotImplementedError('Should implement this _process function')

    def getFileName(self):
        '''return the filename of the report'''
        return settings.REPORT_FILENAME_FORMAT.format(
            task_id=self._reportModel.task.id,
            report_type=self.__class__.__name__,
        )

    def _saveReportFileWithObject(self, obj):
        '''save the report object and return the file path'''
        filePath = os.path.join(settings.REPORT_FOLDER, self.getFileName())
        if not os.path.exists(os.path.dirname(filePath)):
            try:
                os.makedirs(os.path.dirname(filePath))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise exc
        with open(filePath, 'w+') as f:
            f.write(json.dumps(obj))
        self._reportModel.file.name = filePath
        self._reportModel.save()
        return filePath

    def _saveReportFileWithExistFile(self, filePath):
        '''update the model path with given file path'''
        self._reportModel.file.name = filePath
        self._reportModel.save()

    def getParameter(self, key):
        return self.parameters.get(key, None)

    def getConflictRecords(self):
        return self.conflictRecords1 + self.conflictRecords2

    def getConflictRecordColumn(self):
        return self.conflictRecordColumns


class AggregatedReportGenerator(ReportGenerator):
    '''
    This groups the difference from two souce
        with the parameter 'grouping_fields'

    In normal case, each group should contain only two records, one
    from left source, another one from right source. Then the
    generator will check over the two records and put the difference
    into each field's difference list.

    If a group contains only one record,
        the single record is considered as unpaired one
    If a group contains more than one record from the same source,
        these records are considered as duplicateds

    '''

    def _process(self, data1, data2, columns):

        # get grouping index, the index of the grouping fields
        grouping_fields = self.getParameter('grouping_fields')
        if grouping_fields is None:
            raise MissingParametersException('grouping_fields is required')

        grouping_index = []
        for field in grouping_fields.split(','):
            try:
                grouping_index.append(columns.index(field))
            except Exception as e:
                continue
        if len(grouping_index) == 0:
            raise InvalidParametersException(
                'grouping_fields is invalid: %s' % grouping_fields)

        # map the rows into dict with the grouping index
        data = data1 + data2
        dic = defaultdict(list)
        for row in data:
            key = tuple(row[i] for i in grouping_index)
            dic[key].append(row)

        leftUnpairedRecords = []
        leftUnpairedCount = 0
        rightUnpairedRecords = []
        rightUnpairedCount = 0

        # counts of differences in every column
        columnCounts = [0 for i in columns]
        # differences in every column
        columnRecords = [[] for i in columns]
        leftDuplicatedCount = 0
        leftDuplicatedRecords = []
        rightDuplicatedCount = 0
        rightDuplicatedRecords = []

        # count the difference by group
        for key, value in dic.items():
            # non-paired record
            if len(value) < 2:
                if value[0][-1] == ConflictRecord.POSITION_IN_TASK_LEFT:
                    leftUnpairedRecords.append(
                        [value[0][i] for i in grouping_index])
                    leftUnpairedCount += 1
                else:
                    rightUnpairedRecords.append(
                        [value[0][i] for i in grouping_index])
                    rightUnpairedCount += 1
                continue

            # records more than one pair
            token = ConflictRecord.POSITION_IN_TASK_LEFT
            leftRecords = [i for i in value if i[-1] == token]
            token = ConflictRecord.POSITION_IN_TASK_RIGHT
            rightRecords = [i for i in value if i[-1] == token]
            if len(leftRecords) > 1 or len(rightRecords) > 1:
                if len(leftRecords) > 1:
                    leftDuplicatedCount += 1
                    leftDuplicatedRecords.append(
                        tuple(leftRecords[0][i] for i in grouping_index))
                if len(rightRecords) > 1:
                    rightDuplicatedCount += 1
                    rightDuplicatedRecords.append(
                        tuple(rightRecords[0][i] for i in grouping_index))
                continue

            # normal case, two records in the group
            zipPairs = list(zip(* value))
            # check records by field
            for index, pair in enumerate(zipPairs):
                # check if the two elemets in this field(index) are the same
                if index in grouping_index or index >= len(columns):
                    # if it's grouping field, skip the comparison
                    # skip the last element, which are LF/RT
                    continue
                if pair.count(pair[0]) != len(pair):
                    # diff occurs in this field
                    # field count increases
                    columnCounts[index] += 1
                    # append the value into records
                    # only when count <= max pair number
                    keyWithPair = [
                        tuple(value[0][i] for i in grouping_index)]\
                        + list(pair)
                    columnRecords[index].append(keyWithPair)

        # write report
        reportObj = {}
        reportObj['leftUnpairedRecords'] = leftUnpairedRecords
        reportObj['leftUnpairedCount'] = leftUnpairedCount
        reportObj['rightUnpairedRecords'] = rightUnpairedRecords
        reportObj['rightUnpairedCount'] = rightUnpairedCount
        reportObj['columns'] = columns
        reportObj['columnCounts'] = columnCounts
        reportObj['columnRecords'] = columnRecords
        reportObj['leftDuplicatedCount'] = leftDuplicatedCount
        reportObj['leftDuplicatedRecords'] = leftDuplicatedRecords
        reportObj['rightDuplicatedCount'] = rightDuplicatedCount
        reportObj['rightDuplicatedRecords'] = rightDuplicatedRecords
        return reportObj


def reportList():
    for cls in ReportGenerator.__subclasses__():
        yield cls.__name__
