from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def page(request):  # pylint: disable=unused-argument
    return HttpResponse("Hello I am the Test!")
