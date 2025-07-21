"""PvE Views"""

# Standard Library
import logging
from datetime import datetime
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Ledger
from ledger.api.helpers import get_manage_corporation
from ledger.helpers.core import add_info_to_context

# Ledger
from ledger.models.corporationaudit import CorporationAudit

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
        return redirect("ledger:corporation_ledger_index")
    if perm is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return redirect("ledger:corporation_ledger_index")
    # TODO Get Missing Characters from esi-corporations.read_corporation_membership.v1 ?
    corp_characters = CharacterOwnership.objects.filter(
        character__corporation_id=corporation.corporation.corporation_id
    ).order_by("character__character_name")

    context = {
        "corporation_id": corporation_id,
        "title": "Corporation Administration",
        "corporation": corporation,
        "characters": corp_characters,
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/corpledger/admin/corporation_administration.html",
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

    audit = CorporationAudit.objects.get(corporation__corporation_id=corporation_id)
    audit.delete()

    msg = _(f"{audit.corporation.corporation_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )
