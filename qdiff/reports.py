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

    def factory(className, *args, **kwargs):
        if className == "AggregatedReportGenerator":
            return AggregatedReportGenerator(*args, **kwargs)
        raise InvalidClassNameException('')
    factory = staticmethod(factory)

    def __init__(self, reportModel):
        self._reportModel = reportModel
        self.parameters = json.loads(self._reportModel.parameters)

        # get data
        taskModel = self._reportModel.task
        tableName1, tableName2 = getConflictRecordTableNames(taskModel)
        self.conflictRecords = []
        crr1 = ConflictRecordReader(tableName1)
        result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
                   for item in crr1.getConflictRecords()]
        crr2 = ConflictRecordReader(tableName2)
        result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
                   for item in crr2.getConflictRecords()]
        self.conflictRecords.extend(result1)
        self.conflictRecords.extend(result2)
        self.conflictRecordColumns = crr1.getColumns()

    def generate(self):
        reportObj = self._process(
            self.getConflictRecords(),
            self.getConflictRecordColumn())
        return self._saveReportFileWithObject(reportObj)

    def _process(self, data, columns):
        raise NotImplementedError('Should implement this generate function')

    def getFileName(self):
        return settings.REPORT_FILENAME_FORMAT.format(
            task_id=self._reportModel.task.id,
            report_type=self.__class__.__name__,
        )

    def _saveReportFileWithObject(self, obj):
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
        self._reportModel.file.name = filePath
        self._reportModel.save()

    def getParameter(self, key):
        return self.parameters.get(key, None)

    def getConflictRecords(self):
        return self.conflictRecords

    def getConflictRecordColumn(self):
        return self.conflictRecordColumns


class AggregatedReportGenerator(ReportGenerator):
    def _process(self, data, columns):

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
        dic = defaultdict(list)
        for row in data:
            key = tuple(row[i] for i in grouping_index)
            dic[key].append(row)

        # count the difference by group
        leftUnpairedRecords = []
        leftUnpairedCount = 0
        rightUnpairedRecords = []
        rightUnpairedCount = 0
        columnCounts = [0 for i in columns]
        columnRecords = [[] for i in columns]
        leftDuplicatedCount = 0
        leftDuplicatedRecords = []
        rightDuplicatedCount = 0
        rightDuplicatedRecords = []
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
            if len(leftRecords) > 1:
                leftDuplicatedCount += 1
                leftDuplicatedRecords.append(
                    tuple(leftRecords[0][i] for i in grouping_index))
            token = ConflictRecord.POSITION_IN_TASK_RIGHT
            rightRecords = [i for i in value if i[-1] == token]
            if len(rightRecords) > 1:
                rightDuplicatedCount += 1
                rightDuplicatedRecords.append(
                    tuple(leftRecords[0][i] for i in grouping_index))
            if len(leftRecords) > 1 or len(rightRecords) > 1:
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
                    columnRecords[index].append(pair)

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
