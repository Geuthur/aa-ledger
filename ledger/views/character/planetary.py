"""
Planetary Audit
"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.core import add_info_to_context

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
