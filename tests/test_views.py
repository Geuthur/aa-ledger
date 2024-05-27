from django.conf import settings
from django.shortcuts import render

def test_settings(request):
    context = {
        "memberaudit": settings.LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/corpledger/corp_ledger.html", context=context)
