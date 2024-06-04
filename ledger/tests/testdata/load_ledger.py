"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from pathlib import Path

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ledger.models.characteraudit import CharacterAudit, CharacterMiningLedger
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


def load_char_mining():
    CharacterMiningLedger.objects.all().delete()
    CharacterMiningLedger(
        character=CharacterAudit.objects.get(id=1),
        id="20240316-17425-1001-30004783",
        date="2024-03-16",
        type_id=17425,
        system_id=30004783,
        quantity=1000,
    )
    CharacterMiningLedger(
        character=CharacterAudit.objects.get(id=1),
        id="20240316-17423-1001-30004785",
        date="2024-03-16",
        type_id=17423,
        system_id=30004785,
        quantity=1000,
    )
