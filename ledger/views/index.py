"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, tasks

# Ledger
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


@login_required
@permission_required("ledger.basic_access")
def index(request):
    """Index View"""
    return redirect(
        "ledger:character_ledger",
        character_id=request.user.profile.main_character.character_id,
        year=timezone.now().year,
        month=timezone.now().month,
    )


@login_required
@permission_required("ledger.basic_access")
def admin(request: WSGIRequest):
    # Check Permissions
    if not request.user.is_superuser:
        messages.error(request, _("You do not have permission to access this page."))
        return redirect("ledger:index")

    # Handle Character
    def _handle_character_updates(force_refresh):
        character_id = request.POST.get("character_id")
        if character_id is not None:
            try:
                character = CharacterOwner.objects.get(
                    eve_character__character_id=int(character_id)
                )
                msg = format_lazy(
                    _("Queued Update for Character: {character_name}"),
                    character_name=character.character_name,
                )
                messages.info(request, msg)
                tasks.update_character.apply_async(
                    kwargs={
                        "character_pk": character.pk,
                        "force_refresh": force_refresh,
                    },
                    priority=7,
                )
            except (ValueError, CharacterOwner.DoesNotExist):
                msg = format_lazy(
                    _("Character with ID {character_id} not found"),
                    character_id=character_id,
                )
                messages.error(request, msg)
            return

        tasks.update_all_characters.apply_async(
            kwargs={"force_refresh": force_refresh}, priority=7
        )
        messages.info(request, _("Queued Update All Characters"))
        return

    # Handle Corporation
    def _handle_corporation_updates(force_refresh):
        corporation_id = request.POST.get("corporation_id")
        if corporation_id is not None:
            try:
                corporation = CorporationOwner.objects.get(
                    eve_corporation__corporation_id=int(corporation_id)
                )
                msg = format_lazy(
                    _("Queued Update for Corporation: {corporation_name}"),
                    corporation_name=corporation.corporation_name,
                )
                messages.info(request, msg)
                tasks.update_corporation.apply_async(
                    args=[corporation.pk],
                    kwargs={"force_refresh": force_refresh},
                    priority=7,
                )
            except (ValueError, CorporationOwner.DoesNotExist):
                msg = format_lazy(
                    _("Corporation with ID {corporation_id} not found"),
                    corporation_id=corporation_id,
                )
                messages.error(request, msg)
            return

        tasks.update_all_corporations.apply_async(
            kwargs={"force_refresh": force_refresh}, priority=7
        )
        messages.info(request, _("Queued Update All Corporations"))
        return

    # Handle POST Requests
    if request.method == "POST":
        force_refresh = bool(request.POST.get("force_refresh", False))

        # General Tasks
        if request.POST.get("run_clear_cache"):
            messages.info(request, _("Queued Clear All Cache"))
            tasks.clear_all_cache.apply_async(priority=1)
        # Specific Tasks
        if request.POST.get("run_character_updates"):
            _handle_character_updates(force_refresh)
        if request.POST.get("run_corporation_updates"):
            _handle_corporation_updates(force_refresh)
    return render(request, "ledger/view-administration.html")
