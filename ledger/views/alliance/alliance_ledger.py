"""PvE Views"""

# Standard Library
import logging
from datetime import datetime

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# AA Ledger
from ledger.api.helpers import get_all_corporations_from_alliance, get_alliance
from ledger.helpers.core import add_info_to_context

logger = logging.getLogger(__name__)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger_index(request):
    """Alliance Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    try:
        alliance_id = request.user.profile.main_character.alliance_id
        if alliance_id is None:
            raise AttributeError
    except AttributeError:
        messages.error(request, "You do not have an alliance.")
        return redirect("ledger:index")
    return redirect("ledger:alliance_ledger", alliance_id)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger(request, alliance_id):
    """
    Alliance Ledger
    """
    # pylint: disable=duplicate-code
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "title": "Alliance Ledger",
        "years": years,
        "alliance_id": alliance_id,
        "entity_pk": alliance_id,
        "entity_type": "alliance",
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/allyledger/alliance_ledger.html", context=context)


@login_required
@permission_required("ledger.advanced_access")
def alliance_overview(request):
    """
    Alliance Overview
    """
    context = {
        "title": "Alliance Overview",
    }
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/allyledger/admin/alliance_overview.html", context=context
    )


@login_required
@permission_required("ledger.admin_access")
def alliance_administration(request, alliance_id):
    """
    Alliance Administration
    """
    perm, alliance = get_alliance(request, alliance_id)

    if perm is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:alliance_ledger_index")
    if perm is None:
        msg = _("Alliance not Found")
        messages.info(request, msg)
        return redirect("ledger:alliance_ledger_index")

    corporations = get_all_corporations_from_alliance(request, alliance.alliance_id)[1]
    all_corporations = EveCorporationInfo.objects.filter(
        alliance__alliance_id=alliance_id
    ).order_by("corporation_name")

    corp_audit_ids = corporations.values_list("corporation__corporation_id", flat=True)
    missing_corporations = all_corporations.exclude(
        corporation_id__in=corp_audit_ids
    ).order_by("corporation_name")

    context = {
        "alliance_id": alliance_id,
        "title": "Alliance Administration",
        "corporations": corporations,
        "missing_corporations": missing_corporations,
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/allyledger/admin/alliance_administration.html",
        context=context,
    )
