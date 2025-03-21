"""PvE Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect

from ledger.hooks import get_extension_logger

# Ledger
from ledger.view_helpers.core import add_info_to_context

logger = get_extension_logger(__name__)


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
