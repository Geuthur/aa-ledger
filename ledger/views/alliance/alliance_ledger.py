"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, forms
from ledger.api.helpers.core import (
    get_all_corporations_from_alliance,
    get_alliance_or_none,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.advanced_access")
def alliance_ledger(
    request: WSGIRequest, alliance_id: int, year=None, month=None, day=None
):
    """
    Alliance Ledger
    """
    perms = get_alliance_or_none(request, alliance_id)[0]

    context = {
        "title": "Alliance Ledger",
        "alliance_id": alliance_id,
        "disabled": True,
    }

    kwargs = {
        "alliance_id": alliance_id,
    }

    # pylint: disable=duplicate-code
    if request.POST:
        year = request.POST.get("year") or None
        month = request.POST.get("month") or None
        day = request.POST.get("day") or None
        # Ensure that if only day is provided, month is also provided
        if day is not None and month is None:
            month = timezone.now().month

    if year is not None:
        kwargs["year"] = year
    if month is not None:
        kwargs["month"] = month
    if day is not None:
        kwargs["day"] = day

    # Redirect to the same view with updated parameters
    if request.POST:
        return redirect("ledger:alliance_ledger", **kwargs)

    ledger_url = reverse("ledger:api:get_alliance_ledger", kwargs=kwargs)

    context = {
        "title": "Alliance Ledger",
        "alliance_id": alliance_id,
        "ledger_url": ledger_url,
        "forms": {
            "alliance_dropdown": forms.AllianceDropdownForm(
                alliance_id=alliance_id,
                year=year,
                month=month,
                day=day,
            ),
        },
    }

    if perms is None:
        msg = _("Alliance not found.")
        messages.info(request, msg)
        return redirect("ledger:alliance_overview")

    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:alliance_overview")
    return render(request, "ledger/view-alliance-ledger.html", context=context)


@login_required
@permission_required("ledger.advanced_access")
def alliance_overview(request):
    """
    Alliance Overview
    """
    context = {
        "title": "Alliance Overview",
        "year": timezone.now().year,
        "month": timezone.now().month,
    }
    return render(request, "ledger/view-alliance-overview.html", context=context)


@login_required
@permission_required("ledger.manage_access")
def alliance_administration(request, alliance_id):
    """
    Alliance Administration
    """
    perm, alliance = get_alliance_or_none(request, alliance_id)

    if perm is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:alliance_overview")
    if perm is None:
        msg = _("Alliance not found.")
        messages.info(request, msg)
        return redirect("ledger:alliance_overview")

    corporations = get_all_corporations_from_alliance(request, alliance.alliance_id)[1]
    all_corporations = EveCorporationInfo.objects.filter(
        alliance__alliance_id=alliance_id
    ).order_by("corporation_name")

    corp_audit_ids = corporations.values_list(
        "eve_corporation__corporation_id", flat=True
    )
    missing_corporations = all_corporations.exclude(
        corporation_id__in=corp_audit_ids
    ).order_by("corporation_name")

    context = {
        "alliance_id": alliance_id,
        "title": "Alliance Administration",
        "alliance": alliance,
        "corporations": corporations,
        "missing_corporations": missing_corporations,
    }
    return render(
        request,
        "ledger/view-alliance-administration.html",
        context=context,
    )
