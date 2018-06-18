from django.shortcuts import render


def task_list_view(request):
    context = {}
    return render(request, 'qdiff/task_list.html', context)
