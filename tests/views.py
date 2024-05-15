from django.http import HttpResponse


def page(request):  # pylint: disable=unused-argument
    return HttpResponse("Hello I am the Test!")
