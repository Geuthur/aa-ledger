"""PvE Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

# Voices of War
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.basic_access")
def index_pve(request):
    context = {"text": ""}
    return render(request, "ledger/pve/index.html", context)


@login_required
@permission_required("ledger.basic_access")
def ledger_index(request):
    return render(request, "ledger/ledger/index.html")


@login_required
@permission_required("ledger.basic_access")
def ratting_index(request):
    return render(request, "ledger/ledger/corpledger/corp_ledger.html")


@login_required
@permission_required("ledger.basic_access")
def ratting_char_index(request):
    return render(request, "ledger/ledger/charledger/char_ledger.html")
