"""
Corporation Audit
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter
from allianceauth.eveonline.providers import ObjectNotFound, provider
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.models.general import EveEntity

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@token_required(scopes=["publicData"])
@permission_required(["ledger.manage_access"])
def add_ally(request, token) -> HttpResponse:
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    try:
        ally = EveAllianceInfo.objects.get(alliance_id=char.alliance_id)

        msg = _("{alliance_name} is already in the Ledger System").format(
            alliance_name=ally.alliance_name,
        )
        messages.info(request, msg)
    except EveAllianceInfo.DoesNotExist:
        try:
            ally_data = provider.get_alliance(char.alliance_id)
            ally, __ = EveAllianceInfo.objects.get_or_create(
                alliance_id=ally_data.id,
                defaults={
                    "alliance_name": ally_data.name,
                    "alliance_ticker": ally_data.ticker,
                    "executor_corp_id": ally_data.executor_corp_id,
                },
            )
            # Add/Update All Corporations to eveuniverse model
            ally.populate_alliance()

            # Add the alliance to the EveEntity model
            EveEntity.objects.get_or_create(
                eve_id=ally.alliance_id,
                defaults={
                    "name": ally.alliance_name,
                    "category": "alliance",
                },
            )
            msg = _("{alliance_name} successfully added to Ledger").format(
                alliance_name=ally.alliance_name,
            )
            messages.success(request, msg)
        except ObjectNotFound:
            msg = _("Failed to fetch Alliance data for {alliance_name}").format(
                alliance_name=char.alliance_name,
            )
            messages.warning(request, msg)
            return redirect("ledger:alliance_ledger", alliance_id=char.alliance_id)
    return redirect("ledger:alliance_ledger", alliance_id=ally.alliance_id)
