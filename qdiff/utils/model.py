from django.conf import settings
import json
from qdiff.readers import DatabaseReader
from qdiff.models import ConflictRecord


def getMaskedSources(task):
    '''
    input, a task model
    output, tuple contains two masked data source config
    if the source type is database, remove the password and user name
    '''
    source1 = ''
    source2 = ''
    if task.left_source.lower().startswith(settings.SOURCE_TYPE_CSV_PREFIX):
        source1 = task.left_source[
            len(settings.SOURCE_TYPE_CSV_PREFIX):]
    elif task.left_source.lower().startswith(
            settings.SOURCE_TYPE_DATABASE_PREFIX):
        tmpObj = json.loads(task.left_source[
            len(settings.SOURCE_TYPE_DATABASE_PREFIX):])
        if 'PASSWORD' in tmpObj:
            tmpObj.pop('PASSWORD')
        if 'USER' in tmpObj:
            tmpObj.pop('USER')
        source1 = tmpObj
    else:
        pass

    if task.right_source.lower().startswith(settings.SOURCE_TYPE_CSV_PREFIX):
        source2 = task.right_source[
            len(settings.SOURCE_TYPE_CSV_PREFIX):]
    elif task.right_source.lower().startswith(
            settings.SOURCE_TYPE_DATABASE_PREFIX):
        tmpObj = json.loads(task.right_source[
            len(settings.SOURCE_TYPE_DATABASE_PREFIX):])
        if 'PASSWORD' in tmpObj:
            tmpObj.pop('PASSWORD')
        if 'USER' in tmpObj:
            tmpObj.pop('USER')
        source2 = tmpObj
    else:
        pass

    return (source1, source2)


def getMaskedSourceFromString(readSource):
    maskedSource = ''
    if readSource.lower().startswith(settings.SOURCE_TYPE_CSV_PREFIX):
        maskedSource = readSource[
            len(settings.SOURCE_TYPE_CSV_PREFIX):]
    elif readSource.lower().startswith(
            settings.SOURCE_TYPE_DATABASE_PREFIX):
        tmpObj = json.loads(readSource[
            len(settings.SOURCE_TYPE_DATABASE_PREFIX):])
        if 'PASSWORD' in tmpObj:
            tmpObj.pop('PASSWORD')
        if 'USER' in tmpObj:
            tmpObj.pop('USER')
        maskedSource = tmpObj
    else:
        pass
    return maskedSource


class ConflictRecordReader:
    def __init__(self, tableName):
        defaultConfigs = settings.DATABASES['default'].copy()
        self.dr = DatabaseReader(
            defaultConfigs,
            'SELECT * FROM %s;' % (tableName))

    def getConflictRecords(self):
        return self.dr.getRowsList()

    def getColumns(self):
        return self.dr.getColumns()


def getConflictRecordTableNames(taskModel):
    tableName1 = settings.CONFLICT_TABLE_NAME_FORMAT.format(
        prefix=settings.GENERATED_TABLE_PREFIX,
        id=str(taskModel.id),
        position=ConflictRecord.POSITION_IN_TASK_LEFT
    )
    tableName2 = settings.CONFLICT_TABLE_NAME_FORMAT.format(
        prefix=settings.GENERATED_TABLE_PREFIX,
        id=str(taskModel.id),
        position=ConflictRecord.POSITION_IN_TASK_RIGHT
    )
    return (tableName1, tableName2)
