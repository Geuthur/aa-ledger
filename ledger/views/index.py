"""PvE Views"""

# Standard Library
import logging

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

# AA Ledger
# Ledger
from ledger.helpers.core import add_info_to_context
from ledger.tasks import clear_all_etags, update_all_characters, update_all_corps

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


@login_required
@permission_required("ledger.admin_access")
def admin(request):
    if request.method == "POST":
        if request.POST.get("run_char_updates"):
            messages.info(request, _("Queued Update All Characters"))
            update_all_characters.apply_async(priority=7)
        if request.POST.get("run_corp_updates"):
            messages.info(request, _("Queued Update All Corporations"))
            update_all_corps.apply_async(priority=7)
        if request.POST.get("run_clear_etag"):
            messages.info(request, _("Queued Clear All ETags"))
            clear_all_etags.apply_async(priority=1)
    return render(request, "ledger/admin.html")
