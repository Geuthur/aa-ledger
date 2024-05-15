"""
Corporation Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from esi.decorators import token_required

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ledger.models.corporationaudit import CorporationAudit
from ledger.tasks import update_corp


@login_required
@token_required(scopes=CorporationAudit.get_esi_scopes())
@permission_required(["ledger.admin_access", "ledger.char_audit_admin_access"])
def add_corp(request, token):
    char = EveCharacter.objects.get_character_by_id(token.character_id)
    corp, _ = EveCorporationInfo.objects.get_or_create(
        corporation_id=char.corporation_id,
        defaults={
            "member_count": 0,
            "corporation_ticker": char.corporation_ticker,
            "corporation_name": char.corporation_name,
        },
    )

    CorporationAudit.objects.update_or_create(corporation=corp)
    update_corp.apply_async(
        args=[char.corporation_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = f"{char.corporation_name} successfully added/updated to Ledger"
    messages.info(request, msg)
    return render(request, "ledger/ledger/index.html")
