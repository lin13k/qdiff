from celery import Celery
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')
app = Celery('qdiff')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
