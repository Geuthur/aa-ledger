"""PvE Views"""

import logging
from datetime import datetime

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

# Ledger
from ledger.view_helpers.core import add_info_to_context

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

    context = {
        "title": "Character Admin",
    }
    context = add_info_to_context(request, context)
    return render(
        request,
        "ledger/charledger/admin/character_administration.html",
        context=context,
    )
