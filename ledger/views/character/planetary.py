"""
Planetary Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as trans
from django.views.decorators.http import require_POST

from ledger.api.helpers import get_alts_queryset, get_character
from ledger.hooks import get_extension_logger
from ledger.models.planetary import CharacterPlanetDetails
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


@login_required
@permission_required(["ledger.basic_access"])
def planetary_ledger(request, character_pk):
    context = {
        "character_pk": character_pk,
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
    # Retrieve character_pk from GET parameters
    character_pk = int(request.POST.get("character_pk", 0))

    # Check Permission
    perm, main = get_character(request, character_id)

    if not perm:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect("ledger:planetary_ledger", character_pk=character_pk)

    if character_id == 0:
        characters = get_alts_queryset(main)
        characters = characters.values_list("character_id", flat=True)
    else:
        characters = [main.character_id]

    filters = Q(planet__character__character__character_id__in=characters)
    if not planet_id == 0:
        filters &= Q(planet__planet__id=planet_id)

    try:
        planets = CharacterPlanetDetails.objects.filter(filters)
        if planets:
            for p in planets:
                p.notification = not p.notification
                p.save()
        else:
            raise CharacterPlanetDetails.DoesNotExist
    except CharacterPlanetDetails.DoesNotExist:
        print("LUL")
        msg = trans("Planet/s not found")
        messages.error(request, msg)
        return redirect("ledger:planetary_ledger", character_pk=character_pk)

    msg = trans("Alarm/s successfully switched")
    messages.info(request, msg)

    return redirect("ledger:planetary_ledger", character_pk=character_pk)
