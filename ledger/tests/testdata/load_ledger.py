"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from datetime import date, datetime
from pathlib import Path

from eveuniverse.models import EveMarketPrice, EveSolarSystem, EveType

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


def load_ledger_all():
    load_eveentity()
    load_eveuniverse()
    load_char_audit()
    load_corp_audit()
    load_char_mining()
    load_char_journal()
    load_corp_journal()


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
        id=1, character=EveCharacter.objects.get(character_id=1001)
    )
    CharacterAudit.objects.update_or_create(
        id=2, character=EveCharacter.objects.get(character_id=1002)
    )
    CharacterAudit.objects.update_or_create(
        id=3, character=EveCharacter.objects.get(character_id=1003)
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
    EveMarketPrice.objects.all().delete()
    EveMarketPrice.objects.create(
        eve_type=EveType.objects.get(id=17425),
        adjusted_price=1000,
        average_price=1000,
        updated_at=datetime.now(),
    )
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        id="20240316-17425-1001-30004783",
        date=date(2024, 3, 16),
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30004783),
        quantity=100,
    )
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        id="20240316-17423-1001-30004785",
        date=date(2024, 3, 16),
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30002063),
        quantity=100,
    )
    CharacterMiningLedger.objects.create(
        character=CharacterAudit.objects.get(id=2),
        id="20240316-17423-1002-30004785",
        date=date(2024, 3, 16),
        type=EveType.objects.get(id=17425),
        system=EveSolarSystem.objects.get(id=30002063),
        quantity=100,
    )


def load_char_journal():
    CharacterWalletJournalEntry.objects.all().delete()
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=30004783,
        context_id_type="system_id",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=1,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=30004783,
        context_id_type="system_id",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=2,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=30004783,
        context_id_type="system_id",
        date="2024-01-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=3,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=20,
        context_id_type="system_id",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=20,
        reason="",
        ref_type="contract_reward",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    # Player Donation
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=30,
        context_id_type="system_id",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=30,
        reason="Test Transfer",
        ref_type="player_donation",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=-100_000,
        balance=0,
        context_id=31,
        context_id_type="system_id",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1001),
        entry_id=31,
        reason="Test Transfer",
        ref_type="player_donation",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=100_000,
        balance=0,
        context_id=31,
        context_id_type="system_id",
        date="2024-03-19T14:00:01Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1001),
        entry_id=31,
        reason="Test Transfer",
        ref_type="player_donation",
        second_party=EveEntity.objects.get(eve_id=1006),
        tax=0,
        tax_receiver_id=0,
    )

    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=-100_000,
        balance=0,
        context_id=40,
        context_id_type="system_id",
        date="2024-03-19T14:00:03Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=40,
        reason="Test Transfer",
        ref_type="transaction_tax",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=-100_000,
        balance=0,
        context_id=50,
        context_id_type="system_id",
        date="2024-03-19T14:00:07Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=50,
        reason="Test Transfer",
        ref_type="industry_job_tax",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    # Market Escrow
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=-100_000,
        balance=0,
        context_id=60,
        context_id_type="system_id",
        date="2024-03-19T14:00:10Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=60,
        reason="Test Transfer",
        ref_type="market_escrow",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    # Market Escrow
    CharacterWalletJournalEntry.objects.create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        amount=-100_000,
        balance=0,
        context_id=60,
        context_id_type="system_id",
        date="2024-03-19T14:00:10Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=60,
        reason="Test Transfer",
        ref_type="insurance",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )


def load_corp_journal():
    CorporationWalletJournalEntry.objects.all().delete()
    CorporationWalletDivision.objects.all().delete()
    CorporationWalletDivision.objects.update_or_create(
        id=1,
        corporation=CorporationAudit.objects.get(id=1),
        balance=100_000,
        division=1,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=1,
        reason="",
        ref_type="ess_escrow_transfer",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=2,
        reason="",
        ref_type="ess_escrow_transfer",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=3,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=4,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    # Year 2023
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2023-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=101,
        reason="",
        ref_type="ess_escrow_transfer",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2023-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=102,
        reason="",
        ref_type="ess_escrow_transfer",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2023-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=201,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2023-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=202,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1001),
        tax=0,
        tax_receiver_id=0,
    )

    # Many Test Entries
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=203,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1002),
        tax=0,
        tax_receiver_id=0,
    )

    # Many Test Entries
    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=204,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1010),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=205,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1011),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=206,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1012),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=207,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1013),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=208,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1014),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=209,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1015),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=210,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1016),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=211,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1017),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=212,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1018),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=213,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1019),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=214,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1020),
        tax=0,
        tax_receiver_id=0,
    )

    CorporationWalletJournalEntry.objects.create(
        division=CorporationWalletDivision.objects.get(id=1),
        amount=100_000,
        balance=100_000_000,
        context_id=0,
        context_id_type="division",
        date="2024-03-19T14:00:00Z",
        description="Test",
        first_party=EveEntity.objects.get(eve_id=1000125),
        entry_id=215,
        reason="",
        ref_type="bounty_prizes",
        second_party=EveEntity.objects.get(eve_id=1021),
        tax=0,
        tax_receiver_id=0,
    )
