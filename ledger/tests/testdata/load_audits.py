"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from pathlib import Path

from allianceauth.eveonline.models import EveCharacter

from ledger.models.characteraudit import CharacterAudit


def load_char_audit():
    CharacterAudit.objects.all().delete()
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(1001)
    )
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(1002)
    )
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(1003)
    )
