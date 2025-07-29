"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__

# Ledger
from ledger.helpers.core import add_info_to_context
from ledger.tasks import clear_all_etags, update_all_characters, update_all_corporations

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.basic_access")
def index(request):
    """Index View"""
    context = {
        "title": "Ledger",
    }
    context = add_info_to_context(request, context)
    return redirect(
        "ledger:character_ledger",
        character_id=request.user.profile.main_character.character_id,
    )


@login_required
@permission_required("ledger.basic_access")
def admin(request):
    if not request.user.is_superuser:
        messages.error(request, _("You do not have permission to access this page."))
        return redirect("ledger:index")

    if request.method == "POST":
        force_refresh = False
        if request.POST.get("force_refresh", False):
            force_refresh = True
        if request.POST.get("run_clear_etag"):
            messages.info(request, _("Queued Clear All ETags"))
            clear_all_etags.apply_async(priority=1)
        if request.POST.get("run_char_updates"):
            messages.info(request, _("Queued Update All Characters"))
            update_all_characters.apply_async(
                kwargs={"force_refresh": force_refresh}, priority=7
            )
        if request.POST.get("run_corp_updates"):
            messages.info(request, _("Queued Update All Corporations"))
            update_all_corporations.apply_async(
                kwargs={"force_refresh": force_refresh}, priority=7
            )
    return render(request, "ledger/admin.html")
