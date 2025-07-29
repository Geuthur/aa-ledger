"""PvE Views"""

# Standard Library
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.helpers import (
    get_corporation,
    get_manage_corporation,
)
from ledger.helpers.core import add_info_to_context
from ledger.helpers.corporation import CorporationData, LedgerEntity
from ledger.models.corporationaudit import CorporationAudit

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
def corporation_ledger(
    request: WSGIRequest, corporation_id, year=None, month=None, day=None
):
    """
    Corporation Ledger
    """

    perms, corporation = get_corporation(request, corporation_id)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
    }

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return render(
            request, "ledger/corpledger/corporation_ledger.html", context=context
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Corporation not found")
        messages.info(request, msg)
        return render(
            request, "ledger/corpledger/corporation_ledger.html", context=context
        )

    corporation_data = CorporationData(
        request=request, corporation=corporation, year=year, month=month, day=day
    )

    # Create the Corporation ledger data
    context = corporation_data.generate_ledger_data()
    # Add additional information to the context
    context = add_info_to_context(request, context)

    return render(request, "ledger/corpledger/corporation_ledger.html", context=context)


# pylint: disable=too-many-positional-arguments
@login_required
@permission_required("ledger.advanced_access")
def corporation_details(
    request: WSGIRequest,
    corporation_id,
    entity_id,
    year=None,
    month=None,
    day=None,
):
    """
    Corporation Details
    """
    perms, corporation = get_corporation(request, corporation_id)

    context = {
        "title": "Corporation Ledger",
        "corporation_id": corporation_id,
    }

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "corporation_id": corporation_id,
            },
        )
    # pylint: disable=duplicate-code
    if perms is None:
        msg = _("Corporation not found")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "corporation_id": corporation_id,
            },
        )

    corporation_data = CorporationData(
        request=request, corporation=corporation, year=year, month=month, day=day
    )

    # Create the Entity for the ledger
    entity = LedgerEntity(
        entity_id=entity_id,
    )

    amounts = corporation_data._create_corporation_details(entity=entity)
    details = corporation_data._add_average_details(request, amounts, day)

    context = {
        "title": f"Corporation Details - {corporation.corporation_name}",
        "type": "corporation",
        "character": details,
        "information": f"Corporation Details - {corporation_data.get_details_title}",
    }
    context = add_info_to_context(request, context)
    # pylint: disable=duplicate-code
    return render(
        request,
        "ledger/partials/information/view_character_content.html",
        context=context,
    )


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
