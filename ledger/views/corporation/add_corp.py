"""
Corporation Audit
"""

# Standard Library
import logging

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as trans

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.decorators import token_required

# AA Ledger
from ledger import tasks
from ledger.models.corporationaudit import CorporationAudit

logger = logging.getLogger(__name__)


@login_required
@token_required(scopes=CorporationAudit.get_esi_scopes())
@permission_required(["ledger.admin_access"])
def add_corp(request, token) -> HttpResponse:
    char = get_object_or_404(EveCharacter, character_id=token.character_id)
    corp, _ = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )

    CorporationAudit.objects.update_or_create(
        corporation=corp,
        defaults={
            "corporation_name": corp.corporation_name,
        },
    )

    tasks.update_corp.apply_async(
        args=[char.corporation_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = trans("{corporation_name} successfully added/updated to Ledger").format(
        corporation_name=corp.corporation_name,
    )
    messages.info(request, msg)
    return redirect("ledger:corporation_ledger", corporation_id=corp.corporation_id)
