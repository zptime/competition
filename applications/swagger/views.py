# coding:utf-8

from django.shortcuts import render


def api_index(request):
    return render(request, 'swagger/index.html')


def api_docs(request):
    return render(request, 'swagger/swagger.yaml')




