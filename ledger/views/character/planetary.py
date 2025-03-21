"""
Planetary Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ledger import forms
from ledger.api.helpers import get_alts_queryset, get_character
from ledger.hooks import get_extension_logger
from ledger.models.planetary import CharacterPlanetDetails
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required("ledger.advanced_access")
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
        "character_id": character_id,
        "forms": {
            "confirm": forms.ConfirmForm(),
        },
    }
    context = add_info_to_context(request, context)
    return render(request, "ledger/planetary/planetary_ledger.html", context=context)


@login_required
@permission_required("ledger.basic_access")
def planetary_admin(request):
    """
    Planetary Admin
    """

    context = {}
    context = add_info_to_context(request, context)

    return render(
        request, "ledger/planetary/admin/character_admin.html", context=context
    )


@login_required
@permission_required("ledger.basic_access")
@require_POST
def switch_alarm(request, character_id: list, planet_id: int):
    # Check Permission
    perm, main = get_character(request, character_id)
    form = forms.ConfirmForm(request.POST)

    if form.is_valid():
        if not perm:
            msg = _("Permission Denied")
            messages.error(request, msg)
            return redirect("ledger:planetary_ledger", character_id=character_id)

        character_id = int(form.cleaned_data["character_id"])
        planet_id = int(form.cleaned_data["planet_id"])

        if character_id == 0:
            characters = get_alts_queryset(main)
            characters = characters.values_list("character_id", flat=True)
        else:
            characters = [character_id]

        filters = Q(planet__character__character__character_id__in=characters)
        if planet_id != 0:
            filters &= Q(planet__planet__id=planet_id)
        try:
            planets = CharacterPlanetDetails.objects.filter(filters)

            if planets:
                for p in planets:
                    p.notification = not p.notification
                    p.save()
            else:
                raise CharacterPlanetDetails.DoesNotExist

            msg = _("Alarm/s successfully switched")
            messages.info(request, msg)
        except CharacterPlanetDetails.DoesNotExist:
            msg = _("Planet/s not found")
            messages.error(request, msg)
            return redirect("ledger:planetary_ledger", character_id=character_id)
        return redirect("ledger:planetary_ledger", character_id=character_id)

    msg = "Invalid Form"
    messages.error(request, msg)
    return redirect("ledger:planetary_ledger", character_id=character_id)
