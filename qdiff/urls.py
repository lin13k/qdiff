from django.urls import path
from django.conf.urls import url
from qdiff import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    url(r'^tasks/?$',
        views.task_list_view, name='task_list'),
    url(r'^tasks?/(?P<pk>[0-9]+)/?$',
        views.task_detail_view, name='task_detail'),
    url(r'^tasks?/create/?$',
        views.task_create_view, name='task_create'),
    url(r'^configs?/create/?$',
        views.database_config_file_view, name='create_config_file'),

]
