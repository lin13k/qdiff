from django.urls import path
from django.conf.urls import url
from qdiff import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    url(r'^task_list/?$', views.task_list_view)
]
