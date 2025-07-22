"""PvE Views"""

# Standard Library
import logging
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Ledger
# Ledger
from ledger.api.helpers import get_character_or_none
from ledger.helpers.core import add_info_to_context
from ledger.models.characteraudit import CharacterAudit

logger = logging.getLogger(__name__)


@login_required
@permission_required("ledger.basic_access")
def character_ledger_index(request):
    """Character Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:character_ledger", request.user.profile.main_character.character_id
    )


@login_required
@permission_required("ledger.basic_access")
def character_ledger(request, character_id=None):
    """
    Character Ledger
    """
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "title": "Character Ledger",
        "years": years,
        "entity_pk": character_id,
        "character_id": character_id,
        "entity_type": "character",
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/charledger/character_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def character_ledger_new(request, character_id, year=None, month=None, day=None):
    """
    Character Ledger
    """
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    perms, character = get_character_or_none(request, character_id)

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:character_ledger_index")

    existing_years = character.ledger_character_journal.values_list(
        "date__year", flat=True
    ).distinct()

    filter_date = Q(date__year=year) if year else Q(date__year=timezone.now().year)
    view = "year"

    if month:
        filter_date &= Q(date__month=month)
        view = "month"
    if day:
        filter_date &= Q(date__day=day)
        view = "day"

    # Set current year if no year is provided
    current_year = year if year else datetime.now().year

    characters = CharacterAudit.objects.filter(
        eve_character__character_id__in=character.alts.values_list(
            "character_id", flat=True
        )
    ).order_by("eve_character__character_name")

    # Pre-calculate aggregated values for each character
    characters_with_data = []
    for character in characters:
        char_data = {
            "character": character,
            "journal": character.ledger_character_journal.filter(filter_date),
            "ess": character.ledger_character_journal.filter(
                filter_date
            ).aggregate_bounty()
            * Decimal(0.667),  # Assuming 2/3 of bounty is ESS
            "mining": character.ledger_character_mining.filter(filter_date),
            # Add other aggregated values as needed
        }
        characters_with_data.append(char_data)

    context = {
        "title": "Character Ledger",
        "years": existing_years,
        "characters": characters_with_data,
        "entity_pk": character_id,
        "character_id": character_id,
        "year": year,
        "month": month,
        "day": day,
        "view": view,
        "current_year": current_year,
        "entity_type": "character",
    }

    context = add_info_to_context(request, context)
    return render(
        request, "ledger/charledger/character_ledger_new.html", context=context
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
        return redirect("ledger:character_ledger_index")

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
