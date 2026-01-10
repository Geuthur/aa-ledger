"""PvE Views"""

# Standard Library
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, forms
from ledger.api.helpers.core import (
    get_corporationowner_or_none,
    get_manage_corporation,
)
from ledger.models.corporationaudit import (
    CorporationOwner,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.advanced_access")
def corporation_ledger(
    request: WSGIRequest,
    corporation_id: int,
    division_id: int = None,
    year: int = None,
    month: int = None,
    day: int = None,
):
    """
    Corporation Ledger
    """
    perms = get_corporationowner_or_none(request, corporation_id)[0]

    kwargs = {
        "corporation_id": corporation_id,
    }

    if request.POST:
        division_id = request.POST.get("division") or None
        year = request.POST.get("year") or None
        month = request.POST.get("month") or None
        day = request.POST.get("day") or None
        # Ensure that if only day is provided, month is also provided
        if day is not None and month is None:
            month = timezone.now().month

    if division_id is not None:
        kwargs["division_id"] = division_id
    if year is not None:
        kwargs["year"] = year
    if month is not None:
        kwargs["month"] = month
    if day is not None:
        kwargs["day"] = day

    # Redirect to the same view with updated parameters
    if request.POST:
        return redirect("ledger:corporation_ledger", **kwargs)

    ledger_url = reverse("ledger:api:get_corporation_ledger", kwargs=kwargs)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
        "ledger_url": ledger_url,
        "forms": {
            "corporation_dropdown": forms.CorporationDropdownForm(
                corporation_id=corporation_id,
                division_id=division_id,
                year=year,
                month=month,
                day=day,
            ),
        },
    }

    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_overview")

    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:corporation_overview")
    return render(request, "ledger/view-corporation-ledger.html", context=context)


@login_required
@permission_required("ledger.advanced_access")
def corporation_overview(request):
    """
    Corporation Overview
    """
    context = {
        "title": "Corporation Overview",
        "year": timezone.now().year,
        "month": timezone.now().month,
    }
    return render(request, "ledger/view-corporation-overview.html", context=context)


@login_required
@permission_required("ledger.manage_access")
def corporation_administration(request, corporation_id):
    """
    Corporation Administration
    """
    perm, corporation = get_manage_corporation(request, corporation_id)

    if perm is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:corporation_overview")

    if perm is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_overview")

    # TODO Get Missing Characters from esi-corporations.read_corporation_membership.v1 ?
    corp_characters = CharacterOwnership.objects.filter(
        character__corporation_id=corporation.eve_corporation.corporation_id
    ).order_by("character__character_name")

    context = {
        "corporation_id": corporation_id,
        "title": "Corporation Administration",
        "year": timezone.now().year,
        "month": timezone.now().month,
        "corporation": corporation,
        "characters": corp_characters,
    }
    return render(
        request,
        "ledger/view-corporation-administration.html",
        context=context,
    )


@login_required
@permission_required("ledger.manage_access")
@require_POST
def corporation_delete(request, corporation_id):
    """
    Character Delete
    """
    perms = get_manage_corporation(request, corporation_id)[0]

    if perms is False:
        msg = _("Permission Denied")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.FORBIDDEN, safe=False
        )
    if perms is None:
        msg = _("Corporation not found")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.NOT_FOUND, safe=False
        )

    audit = CorporationOwner.objects.get(eve_corporation__corporation_id=corporation_id)
    audit.delete()

    msg = _(f"{audit.eve_corporation.corporation_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )
