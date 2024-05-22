"""PvE Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.conf import settings

# Voices of War
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

@login_required
@permission_required("ledger.basic_access")
def ledger_index(request):
    context = {
        'memberaudit': settings.LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/index.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def ratting_index(request):
    context = {
        'memberaudit': settings.LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/corpledger/corp_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def ratting_char_index(request):
    context = {
        'memberaudit': settings.LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/charledger/char_ledger.html", context=context)
