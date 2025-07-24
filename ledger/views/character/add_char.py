"""
Character Audit
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as trans

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, tasks
from ledger.models.characteraudit import CharacterAudit

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@token_required(scopes=CharacterAudit.get_esi_scopes())
@permission_required("ledger.basic_access")
def add_char(request, token):
    char, _ = CharacterAudit.objects.update_or_create(
        eve_character=EveCharacter.objects.get_character_by_id(token.character_id),
        defaults={
            "active": True,
            "character_name": token.character_name,
        },
    )
    tasks.update_character.apply_async(
        args=[char.pk], kwargs={"force_refresh": True}, priority=6
    )

    msg = trans("{character_name} successfully added/updated to Ledger").format(
        character_name=char.eve_character.character_name,
    )
    messages.info(request, msg)
    return redirect(
        "ledger:character_ledger", character_id=char.eve_character.character_id
    )
