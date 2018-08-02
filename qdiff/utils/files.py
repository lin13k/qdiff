from django.utils.timezone import now
from django.conf import settings
import os


def saveUploadedFile(f):
    """
    save the given file into FILE_UPLOAD_FOLDER
    in format '%Y-%m-%d--%H:%M:%S:%f-FILENAME'
    return saved file path
    """
    time = now()
    prefix = time.strftime("%Y-%m-%d--%H-%M-%S-%f")
    fileName = prefix + '-' + (f.name if hasattr(f, 'name') else '')
    fullPath = os.path.join(settings.FILE_UPLOAD_FOLDER, fileName)
    with open(fullPath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return fullPath
