"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from pathlib import Path

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


def load_char_journal():
    CharacterWalletJournalEntry.objects.all().delete()
    CharacterWalletJournalEntry(
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
        ref_type="player_division",
        second_party_id=1010,
        tax=0,
        tax_receiver_id=0,
    )


def load_corp_journal():
    CorporationWalletJournalEntry.objects.all().delete()
    CorporationWalletDivision(
        corporation=CorporationAudit.objects.get(id=1),
        balance=100_000,
        division=1,
    )
    CorporationWalletJournalEntry(
        division=CorporationWalletDivision.objects.get(id=1),
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
        ref_type="player_division",
        second_party_id=1010,
        tax=0,
        tax_receiver_id=0,
    )
