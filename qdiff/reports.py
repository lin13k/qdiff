# from qdiff.models import ReportGenerator
from django.conf import settings
from qdiff.utils.model import getConflictRecordTableNames
from qdiff.utils.model import ConflictRecordReader
from qdiff.models import ConflictRecord
import os
import json
from qdiff.exceptions import InvalidParametersException
from collections import defaultdict


class ReportGenerator:

    def factory(className):
        if className == "StaticsReportGenerator":
            return StaticsReportGenerator()
    factory = staticmethod(factory)

    def __init__(self, reportModel):
        self._reportModel = reportModel
        self.parameters = json.loads(self._reportModel.parameters)

    def generate(self):
        raise NotImplementedError('Should implement this generate function')

    def getFileName(self):
        return settings.REPORT_FILENAME_FORMAT.format(
            task_id=self._reportModel.task.id,
            report_type=self.__class__.__name__,
        )

    def saveReportFile(self, file):
        # self._reportModel.file.save(
        #     os.path.join(
        #         settings.REPORT_FOLDER, self.getFileName()),
        #     file
        # )
        # self._reportModel.file.name =
        pass

    def getParameter(self, key):
        return self.parameters[key]


class StaticsReportGenerator(ReportGenerator):
    def generate(self):
        taskModel = self._reportModel.task

        # get data
        tableName1, tableName2 = getConflictRecordTableNames(taskModel)
        data = []
        crr1 = ConflictRecordReader(tableName1)
        result1 = [(*item, ConflictRecord.POSITION_IN_TASK_LEFT)
                   for item in crr1.getConflictRecords()]
        crr2 = ConflictRecordReader(tableName2)
        result2 = [(*item, ConflictRecord.POSITION_IN_TASK_RIGHT)
                   for item in crr2.getConflictRecords()]
        columns = crr1.getColumns()
        data.extend(result1)
        data.extend(result2)

        # get grouping index, the index of the grouping fields
        grouping_fields = self.getParameter('grouping_fields').split(',')
        grouping_index = []
        for field in grouping_fields:
            try:
                grouping_index.append(columns.index(field))
            except Exception as e:
                continue
        if len(grouping_index) == 0:
            raise InvalidParametersException('')

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
                if value[-1][-1] == ConflictRecord.POSITION_IN_TASK_LEFT:
                    leftUnpairedRecords.append(* value)
                    leftUnpairedCount += 1
                else:
                    rightUnpairedRecords.append(* value)
                    rightUnpairedCount += 1
                continue

            # records more than one pair
            if len(value) > 2:
                token = settings.POSITION_IN_TASK_LEFT
                leftRecords = [i for i in value if i[-1] == token]
                if len(leftRecords) > 1:
                    leftDuplicatedCount += 1
                    leftDuplicatedRecords.append(leftRecords)
                token = settings.POSITION_IN_TASK_RIGHT
                rightRecords = [i for i in value if i[-1] == token]
                if len(rightRecords) > 1:
                    rightDuplicatedCount += 1
                    rightDuplicatedRecords.append(rightRecords)
                continue

            # normal case, two records in the group
            zipPairs = zip(* value)
            # check records by field
            for index, pair in enumerate(zipPairs):
                # check if the two elemets in this field(index) are the same
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
        reportObj['columnCounts'] = columnCounts
        reportObj['columnRecords'] = columnRecords
        reportObj['leftDuplicatedCount'] = leftDuplicatedCount
        reportObj['leftDuplicatedRecords'] = leftDuplicatedRecords
        reportObj['rightDuplicatedCount'] = rightDuplicatedCount
        reportObj['rightDuplicatedRecords'] = rightDuplicatedRecords

        filePath = os.path.join(settings.REPORT_FOLDER, self.getFileName())
        with open(filePath) as f:
            f.write(json.dumps(reportObj).encode())
            self._reportModel.file.name = filePath
            self._reportModel.save()


def reportList():
    for cls in ReportGenerator.__subclasses__():
        yield cls.__name__
