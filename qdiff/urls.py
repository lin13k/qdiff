from django.conf.urls import url
from qdiff import views

urlpatterns = [
    url(r'^$',
        views.task_list_view, name='index'),
    url(r'^tasks/?$',
        views.task_list_view, name='task_list'),
    url(r'^tasks?/(?P<pk>[0-9]+)/?$',
        views.task_detail_view, name='task_detail'),
    url(r'^tasks?/create/?$',
        views.task_create_view, name='task_create'),

    # database configuration page
    url(r'^configs?/create/?$',
        views.database_config_file_view, name='create_config_file'),
    # database configuration ajax api
    url(r'^configs?/create/api/?$',
        views.Database_Config_APIView.as_view(),
        name='create_config_file_upload'),

    # statics pie report
    url(r'^report/statics_pie_reports?/(?P<taskId>\d+)/?$',
        views.statics_pie_report_view, name='static_pie_report'),

    # aggregated report page
    url(r'^report/aggregated_reports?/(?P<taskId>\d+)/?$',
        views.aggregated_report_view, name='AggregatedReportGenerator'),
    #                                 name from class
    # aggregated report data content
    url(r'^report/aggregated_reports?/(?P<taskId>\d+)/api/?$',
        views.Agregated_Report_APIView.as_view(),
        name='AggregatedReportGenerator_api'),
    # aggregated report csv download
    url(r'^report/aggregated_reports?/(?P<taskId>\d+)/download/?$',
        views.Agregated_Report_CSV_Download_APIVIEW.as_view(),
        name='AggregatedReportGenerator_download'),
]
