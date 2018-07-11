from django.conf import settings
import json


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
