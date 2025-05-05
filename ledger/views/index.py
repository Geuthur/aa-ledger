"""PvE Views"""

# Standard Library
import logging

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect

# AA Ledger
# Ledger
from ledger.helpers.core import add_info_to_context

logger = logging.getLogger(__name__)


@login_required
@permission_required("ledger.basic_access")
def index(request):
    """Index View"""
    context = {
        "title": "Ledger",
    }
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:character_ledger", request.user.profile.main_character.character_id
    )
