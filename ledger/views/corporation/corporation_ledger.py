"""PvE Views"""

import logging
from datetime import datetime

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

# Ledger
from ledger.view_helpers.core import add_info_to_context

logger = logging.getLogger(__name__)


@login_required
@permission_required("ledger.advanced_access")
def corporation_ledger_index(request):
    """Corporation Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:corporation_ledger", request.user.profile.main_character.corporation_id
    )


@login_required
@permission_required("ledger.advanced_access")
def corporation_ledger(request, corporation_id=None):
    """
    Corporation Ledger
    """
    if corporation_id is None:
        corporation_id = request.user.profile.main_character.corporation_id

    # pylint: disable=duplicate-code
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "title": "Corporation Ledger",
        "years": years,
        "entity_pk": corporation_id,
        "corporation_id": corporation_id,
        "entity_type": "corporation",
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/corpledger/corporation_ledger.html", context=context)


@login_required
@permission_required("ledger.advanced_access")
def corporation_overview(request):
    """
    Corporation Overview
    """
    context = {"title": "Corporation Overview"}
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/corpledger/admin/corporation_overview.html", context=context
    )
