"""
Character Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from esi.decorators import token_required

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit
from ledger.tasks import update_character

logger = get_extension_logger(__name__)


@login_required
@token_required(scopes=CharacterAudit.get_esi_scopes())
@permission_required("ledger.basic_access")
def add_char(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id)
    )
    update_character.apply_async(
        args=[token.character_id], kwargs={"force_refresh": True}, priority=6
    )
    msg = "Char successfully added/updated to Ledger"
    messages.info(request, msg)
    return redirect("ledger:ledger_index")
