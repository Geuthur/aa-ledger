"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from pathlib import Path

from eveuniverse.models import EveSolarSystem, EveType

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)
from ledger.models.general import EveEntity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse


def _load_eveentity_data():
    with open(Path(__file__).parent / "eveentity.json", encoding="utf-8") as fp:
        return json.load(fp)


_entities_data = _load_eveentity_data()


def load_eveentity():
    EveEntity.objects.all().delete()
    for character_info in _entities_data.get("EveEntity"):
        EveEntity.objects.create(
            eve_id=character_info.get("eve_id"),
            name=character_info.get("name"),
            category=character_info.get("category"),
        )


def load_char_audit():
    CharacterAudit.objects.all().delete()
    CharacterAudit.objects.update_or_create(
        id=1, character=EveCharacter.objects.get_character_by_id(1001)
    )
    CharacterAudit.objects.update_or_create(
        id=2, character=EveCharacter.objects.get_character_by_id(1002)
    )
    CharacterAudit.objects.update_or_create(
        id=3, character=EveCharacter.objects.get_character_by_id(1003)
    )


def load_corp_audit():
    CorporationAudit.objects.all().delete()
    CorporationAudit.objects.update_or_create(
        id=1, corporation=EveCorporationInfo.objects.get(corporation_id=2001)
    )
    CorporationAudit.objects.update_or_create(
        id=2, corporation=EveCorporationInfo.objects.get(corporation_id=2002)
    )
    CorporationAudit.objects.update_or_create(
        id=3, corporation=EveCorporationInfo.objects.get(corporation_id=2003)
    )


def load_char_mining():
    CharacterMiningLedger.objects.all().delete()
    load_eveuniverse()
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(id=1),
        id="20240316-17425-1001-30004783",
        date="2024-03-16",
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30004783),
        quantity=1000,
    )
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(id=1),
        id="20240316-17423-1001-30004785",
        date="2024-03-16",
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30002063),
        quantity=1000,
    )
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(id=2),
        id="20240316-17423-1002-30004785",
        date="2024-03-16",
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30002063),
        quantity=1000,
    )


def load_char_journal():
    CharacterWalletJournalEntry.objects.all().delete()
    load_eveentity()
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(id=1),
        id=1,
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2016-10-29T14:00:00Z",
        description="Test",
        first_party_id=1001,
        entry_id=1,
        reason="Test Transfer",
        ref_type="test",
        second_party_id=1002,
        tax=0,
        tax_receiver_id=0,
    )
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(id=1),
        id=2,
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2016-10-29T14:00:00Z",
        description="Test",
        first_party_id=1001,
        entry_id=2,
        reason="Test Transfer",
        ref_type="test",
        second_party_id=1003,
        tax=0,
        tax_receiver_id=0,
    )


def load_corp_journal():
    CorporationWalletJournalEntry.objects.all().delete()
    load_eveentity()
    CorporationWalletDivision.objects.create(
        corporation=CorporationAudit.objects.get(id=1),
        balance=100_000,
        division=1,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        id=1,
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2016-10-29T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1001),
        entry_id=1,
        reason="Test Transfer",
        ref_type="test",
        second_party=EveEntity.objects.get(eve_id=1002),
        tax=0,
        tax_receiver_id=0,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        id=2,
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2016-10-29T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1001),
        entry_id=2,
        reason="Test Transfer",
        ref_type="test",
        second_party=EveEntity.objects.get(eve_id=1003),
        tax=0,
        tax_receiver_id=0,
    )
