"""PvE Views"""

# Standard Library
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.helpers import get_character_or_none
from ledger.helpers.character import CharacterData
from ledger.helpers.core import add_info_to_context
from ledger.models.characteraudit import (
    CharacterAudit,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.basic_access")
def character_ledger(
    request: WSGIRequest, character_id: int, year=None, month=None, day=None
):
    """
    Character Ledger
    """
    perms, character = get_character_or_none(request, character_id)

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        context = {
            "error": msg,
            "character_id": character_id,
        }
        context = add_info_to_context(request, context)
        return render(
            request, "ledger/charledger/character_ledger.html", context=context
        )

    character_data = CharacterData(
        request=request, character=character, year=year, month=month, day=day
    )

    # Create the ledger data
    context = character_data.generate_ledger_data()
    # Add additional information to the context
    context = add_info_to_context(request, context)

    return render(request, "ledger/charledger/character_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def character_details(request, character_id, year=None, month=None, day=None):
    """
    Character Details
    """
    perms, character = get_character_or_none(request, character_id)

    # pylint: disable=duplicate-code
    if perms is False:
        msg = _("Permission Denied")
        return render(
            request,
            "ledger/partials/information/view_character_content.html",
            {
                "error": msg,
                "character_id": character_id,
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
                "character_id": character_id,
            },
        )

    character_data = CharacterData(request, character, year, month, day)

    amounts = character_data._create_character_details()
    details = character_data._add_average_details(request, amounts, day)

    context = {
        "title": f"Character Details - {character.eve_character.character_name}",
        "type": "character",
        "character": details,
        "information": f"Character Details - {character_data.get_details_title}",
    }
    context = add_info_to_context(request, context)

    return render(
        request,
        "ledger/partials/information/view_character_content.html",
        context=context,
    )


@login_required
@permission_required("ledger.basic_access")
def character_overview(request):
    """
    Character Overview
    """

    context = {
        "title": "Character Overview",
    }
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/charledger/admin/character_overview.html", context=context
    )


@login_required
@permission_required("ledger.basic_access")
def character_administration(request, character_id=None):
    """
    Character Administration
    """
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    perms, character = get_character_or_none(request, character_id)

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:index")

    linked_characters_ids = character.alts.values_list("character_id", flat=True)

    characters = CharacterAudit.objects.filter(
        eve_character__character_id__in=linked_characters_ids
    ).order_by("eve_character__character_name")
    characters_ids = characters.values_list("eve_character__character_id", flat=True)

    missing_characters = (
        EveCharacter.objects.filter(character_id__in=linked_characters_ids)
        .exclude(character_id__in=characters_ids)
        .order_by("character_name")
    )

    context = {
        "character_id": character_id,
        "title": "Character Administration",
        "characters": characters,
        "missing_characters": missing_characters,
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/charledger/admin/character_administration.html",
        context=context,
    )


@login_required
@permission_required("ledger.basic_access")
@require_POST
def character_delete(request, character_id):
    """
    Character Delete
    """
    perms = get_character_or_none(request, character_id)[0]
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.FORBIDDEN, safe=False
        )

    try:
        audit = CharacterAudit.objects.get(eve_character__character_id=character_id)
    except CharacterAudit.DoesNotExist:
        msg = _("Character not found")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.NOT_FOUND, safe=False
        )

    audit.delete()

    msg = _(f"{audit.eve_character.character_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )
