"""PvE Views"""

from datetime import datetime

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

# Voices of War
from ledger.app_settings import LEDGER_MEMBERAUDIT_USE
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.basic_access")
def ledger_index(request):
    context = {
        "memberaudit": LEDGER_MEMBERAUDIT_USE,
    }
    return render(request, "ledger/index.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def ratting_index(request):
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "memberaudit": LEDGER_MEMBERAUDIT_USE,
        "years": years,
    }
    return render(request, "ledger/corpledger/corp_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def ratting_char_index(request):
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "memberaudit": LEDGER_MEMBERAUDIT_USE,
        "years": years,
    }
    return render(request, "ledger/charledger/char_ledger.html", context=context)
