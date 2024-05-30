"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from pathlib import Path

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import CorporationAudit


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


def load_corp_audit():
    CorporationAudit.objects.all().delete()
    CorporationAudit.objects.update_or_create(
        corporation=EveCorporationInfo.objects.get(corporation_id=2001)
    )
    CorporationAudit.objects.update_or_create(
        corporation=EveCorporationInfo.objects.get(corporation_id=2002)
    )
    CorporationAudit.objects.update_or_create(
        corporation=EveCorporationInfo.objects.get(corporation_id=2003)
    )
