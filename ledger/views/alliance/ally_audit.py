"""
Corporation Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as trans
from esi.decorators import token_required

from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter
from allianceauth.eveonline.providers import ObjectNotFound, provider


@login_required
@token_required(scopes=["publicData"])
@permission_required(["ledger.admin_access"])
def add_ally(request, token) -> HttpResponse:
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    ally = EveAllianceInfo.objects.filter(alliance_id=char.alliance_id).first()

    if not ally:
        try:
            ally_data = provider.get_alliance(char.alliance_id)
            ally, _ = EveAllianceInfo.objects.get_or_create(
                alliance_id=ally_data.id,
                defaults={
                    "alliance_name": ally_data.name,
                    "alliance_ticker": ally_data.ticker,
                    "executor_corp_id": ally_data.executor_corp_id,
                },
            )
            # Add/Update All Corporations to eveuniverse model
            ally.populate_alliance()
            msg = trans("{alliance_name} successfully added to Ledger").format(
                alliance_name=ally.alliance_name,
            )
            messages.success(request, msg)
        except ObjectNotFound:
            msg = trans("Failed to fetch Alliance data for {alliance_name}").format(
                alliance_name=char.alliance_name,
            )
            messages.warning(request, msg)
    else:
        msg = trans("{alliance_name} is already in the Ledger System").format(
            alliance_name=ally.alliance_name,
        )
        messages.info(request, msg)

    return redirect("ledger:alliance_ledger", alliance_pk=0)
