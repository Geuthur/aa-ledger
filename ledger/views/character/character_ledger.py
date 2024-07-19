"""PvE Views"""

from datetime import datetime

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from ledger.hooks import get_extension_logger

# Ledger
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.basic_access")
def character_ledger(request, character_pk):
    """
    Character Ledger
    """
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "years": years,
        "character_pk": character_pk,
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/charledger/character_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def character_admin(request):
    """
    Character Admin
    """

    context = {}
    context = add_info_to_context(request, context)

    return render(
        request, "ledger/charledger/admin/character_admin.html", context=context
    )
