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

    def writeReport(self, data):
        self._reportModel.file.save(
            os.path.join(
                settings.REPORT_FOLDER, self.getFileName()),
            data
        )

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
        unpairedRecords = []
        unpairedCount = 0
        unpairedCountFromDatasource1 = 0
        unpairedCountFromDatasource2 = 0
        columnCounts = [0 for i in columns]
        columnRecords = [[] for i in columns]
        for key, value in dic.items():
            if len(value) < 2:
                unpairedRecords.append(value)
                unpairedCount += 1
                if value[-1] == ConflictRecord.POSITION_IN_TASK_LEFT:
                    unpairedCountFromDatasource1 += 1
                else:
                    unpairedCountFromDatasource2 += 1
                continue
            zipPairs = zip(* value)




def reportList():
    for cls in ReportGenerator.__subclasses__():
        yield cls.__name__
