"""PvE Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from ledger.hooks import get_extension_logger

# Ledger
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.basic_access")
def ledger_index(request):
    context = {}
    context = add_info_to_context(request, context)

    return render(request, "ledger/index.html", context=context)
