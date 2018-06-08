from .settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'database2': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test1',
        'USER': 'root',
        "PASSWORD": 'root',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


NOSE_ARGS = ['--nocapture',
             '--nologcapture', ]
