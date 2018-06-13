from .settings import *


DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': ':memory:',
    # },
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'qdiff_test',
        'USER': 'root',
        "PASSWORD": 'root',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


NOSE_ARGS = ['--nocapture',
             '--nologcapture', ]
