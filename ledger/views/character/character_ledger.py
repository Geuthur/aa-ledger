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
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, forms
from ledger.api.helpers.core import get_characterowner_or_none
from ledger.helpers.core import add_info_to_context
from ledger.models.characteraudit import CharacterOwner
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.basic_access")
def character_ledger(
    request: WSGIRequest,
    character_id: int,
    year=None,
    month=None,
    day=None,
    section=None,
):
    """
    Character Ledger
    """
    perms = get_characterowner_or_none(request, character_id)[0]

    kwargs = {
        "character_id": character_id,
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
    if section is not None:
        kwargs["section"] = section

    # Redirect to the same view with updated parameters
    if request.POST:
        return redirect("ledger:character_ledger", **kwargs)

    ledger_url = reverse("ledger:api:get_character_ledger", kwargs=kwargs)

    context = {
        "title": "Character Ledger",
        "character_id": character_id,
        "ledger_url": ledger_url,
        "forms": {
            "character_dropdown": forms.CharacterDropdownForm(
                character_id=character_id,
                year=year,
                month=month,
                day=day,
            ),
        },
    }

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        context = add_info_to_context(request, context)
        return render(request, "ledger/view-character-ledger.html", context=context)

    # Add additional information to the context
    context = add_info_to_context(request, context)

    return render(request, "ledger/view-character-ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def character_overview(request):
    """
    Character Overview
    """

    context = {
        "title": "Character Overview",
        "year": timezone.now().year,
        "month": timezone.now().month,
        "section": "summary",
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/view-character-overview.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def character_administration(request, character_id=None):
    """
    Character Administration
    """
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    perms, character = get_characterowner_or_none(request, character_id)

    if not perms:
        msg = _("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:index")

    characters = CharacterOwner.objects.filter(
        eve_character__character_id__in=character.alt_ids
    ).order_by("eve_character__character_name")
    characters_ids = characters.values_list("eve_character__character_id", flat=True)

    missing_characters = (
        EveCharacter.objects.filter(character_id__in=character.alt_ids)
        .exclude(character_id__in=characters_ids)
        .order_by("character_name")
    )

    context = {
        "title": "Character Administration",
        "character_id": character_id,
        "year": timezone.now().year,
        "month": timezone.now().month,
        "section": "summary",
        "characters": characters,
        "missing_characters": missing_characters,
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/view-character-administration.html",
        context=context,
    )


@login_required
@permission_required("ledger.basic_access")
@require_POST
def character_delete(request, character_id):
    """
    Character Delete
    """
    perms = get_characterowner_or_none(request, character_id)[0]
    if not perms:
        msg = _("Permission Denied")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.FORBIDDEN, safe=False
        )

    try:
        audit = CharacterOwner.objects.get(eve_character__character_id=character_id)
    except CharacterOwner.DoesNotExist:
        msg = _("Character not found")
        return JsonResponse(
            {"success": False, "message": msg}, status=HTTPStatus.NOT_FOUND, safe=False
        )

    audit.delete()

    msg = _(f"{audit.eve_character.character_name} successfully deleted")
    return JsonResponse(
        {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
    )
