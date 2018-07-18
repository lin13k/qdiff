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
    url(r'^configs?/create/api/?$',
        views.Database_Config_APIView.as_view(),
        name='create_config_file_upload'),
    url(r'^reports?/(?P<task_id>\d+)/api/?$',
        views.Agregated_Report_APIView.as_view(),
        name='AggregatedReportGenerator_api'),
    url(r'^aggregated_reports?/(?P<task_id>\d+)/?$',
        views.aggregated_report_view, name='AggregatedReportGenerator'),
]
