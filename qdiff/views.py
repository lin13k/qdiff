from django.shortcuts import render
from django.core.paginator import Paginator
from qdiff.models import Task



def task_list_view(request):
    context = {}
    taskList = Task.objects.all()
    taskList.reverse()
    context['tasks'] = taskList
    return render(request, 'qdiff/task_list.html', context)
