from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings


def page(request):  # pylint: disable=unused-argument
    return HttpResponse("Hello I am the Test!")

def test_settings(request):
    context = {
        "memberaudit": settings.LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/corpledger/corp_ledger.html", context=context)
