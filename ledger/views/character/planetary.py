"""
Planetary Audit
"""

# Standard Library
from http import HTTPStatus

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, forms
from ledger.api.helpers import get_character_or_none
from ledger.helpers.core import add_info_to_context
from ledger.models.planetary import CharacterPlanetDetails

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.basic_access")
def planetary_ledger_index(request):
    """Character Ledger Index View"""
    context = {}
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:planetary_ledger", request.user.profile.main_character.character_id
    )


@login_required
@permission_required(["ledger.basic_access"])
def planetary_ledger(request, character_id=None):
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    context = {
        "title": "Planetary Ledger",
        "character_id": character_id,
        "forms": {
            "confirm": forms.ConfirmForm(),
        },
    }
    context = add_info_to_context(request, context)
    return render(
        request, "ledger/charledger/planetary/planetary_ledger.html", context=context
    )


@login_required
@permission_required("ledger.basic_access")
def planetary_overview(request):
    """
    Planetary Overview
    """

    context = {
        "title": "Planetary Overview",
    }
    context = add_info_to_context(request, context)

    return render(
        request,
        "ledger/charledger/planetary/admin/planetary_overview.html",
        context=context,
    )


@login_required
@permission_required("ledger.basic_access")
@require_POST
def switch_alarm(request):
    # Check Permission
    form = forms.ConfirmForm(request.POST)

    if form.is_valid():
        is_all = False
        character_id = int(form.cleaned_data["character_id"])
        planet_id = int(form.cleaned_data["planet_id"])

        if character_id == 0:  # pylint: disable=duplicate-code
            character_id = request.user.profile.main_character.character_id
            is_all = True

        perm, character = get_character_or_none(
            request, character_id
        )  # pylint: disable=duplicate-code

        if not perm:
            msg = _("Permission Denied")
            return JsonResponse(
                {"success": True, "message": msg},
                status=HTTPStatus.FORBIDDEN,
                safe=False,
            )

        if is_all:
            characters = character.alts.values_list("character_id", flat=True)
        else:
            characters = [character_id]

        filters = Q(planet__character__eve_character__character_id__in=characters)
        if planet_id != 0:
            filters &= Q(planet__planet__id=planet_id)
        try:
            planets = CharacterPlanetDetails.objects.filter(filters)

            if planets.exists():
                # Determine the majority state
                on_count = planets.filter(notification=True).count()
                off_count = planets.filter(notification=False).count()
                majority_state = on_count > off_count

                # Set all to the opposite of the majority state
                for p in planets:
                    p.notification = not majority_state
                    p.save()

                msg = _("All alarms successfully switched")
            else:
                raise CharacterPlanetDetails.DoesNotExist

        except CharacterPlanetDetails.DoesNotExist:
            msg = _("Planet/s not found")
            return JsonResponse(
                {"success": True, "message": msg},
                status=HTTPStatus.NOT_FOUND,
                safe=False,
            )

        return JsonResponse(
            {"success": True, "message": msg}, status=HTTPStatus.OK, safe=False
        )

    msg = "Invalid Form"
    return JsonResponse(
        {"success": False, "message": msg}, status=HTTPStatus.BAD_REQUEST, safe=False
    )
