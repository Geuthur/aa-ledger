"""PvE Views"""

from datetime import datetime

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ledger.hooks import get_extension_logger

# Ledger
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger_index(request):
    """Alliance Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    try:
        alliance_id = request.user.profile.main_character.alliance_id
    except AttributeError:
        messages.error(request, "You do not have an alliance.")
        return redirect("ledger:index")
    return redirect("ledger:alliance_ledger", alliance_id)


@login_required
@permission_required("ledger.basic_access", "ledger.advanced_access")
def alliance_ledger(request, alliance_id):
    """
    Corporation Ledger
    """
    # pylint: disable=duplicate-code
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "years": years,
        "entity_pk": alliance_id,
        "entity_type": "alliance",
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/allyledger/alliance_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access", "ledger.advanced_access")
def alliance_admin(request):
    """
    Corporation Admin
    """
    context = {}
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/allyledger/admin/alliance_admin.html", context=context
    )
