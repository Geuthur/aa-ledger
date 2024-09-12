"""
Character Audit
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as trans
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
    char, _ = CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id)
    )
    update_character.apply_async(
        args=[token.character_id], kwargs={"force_refresh": True}, priority=6
    )

    msg = trans("{character_name} successfully added/updated to Ledger").format(
        character_name=char.character.character_name,
    )
    messages.info(request, msg)
    return redirect("ledger:character_ledger", character_pk=0)
