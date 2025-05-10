# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.helpers.core import events_filter
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.models.events import Events
from ledger.models.general import EveEntity
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.generate_events import create_event_1_day
from ledger.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpersEvents(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["ledger.basic_access"]
        )
        cls.audit = add_corporationaudit_corporation_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )
        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)
        create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division,
            entry_id=1,
            amount=1000,
            balance=1000000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="ess_escrow_transfer",
        )
        create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division,
            entry_id=2,
            amount=5000,
            balance=1000000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=2,
                hour=10,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Is Filtered from Events",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="ess_escrow_transfer",
        )
        create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division,
            entry_id=2,
            amount=5000,
            balance=1000000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=5,
                hour=10,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Is Filtered from Events",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="ess_escrow_transfer",
        )

    def test_events_filter_should_filter(self):
        # given
        create_event_1_day(
            char_ledger=True,
            date_start=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=2,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
        )
        journal = CorporationWalletJournalEntry.objects.all()
        # when
        journal_result = events_filter(journal)
        # then
        self.assertEqual(journal_result.count(), 2)
        self.assertEqual(journal_result[0].entry_id, 1)

    def test_events_filter_should_not_filter(self):
        # given
        create_event_1_day(
            char_ledger=False,
            date_start=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=2,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
        )
        journal = CorporationWalletJournalEntry.objects.all()
        # when
        journal_result = events_filter(journal)
        # then
        self.assertEqual(journal_result.count(), 3)

    def test_events_filter_should_filter_all_events(self):
        # given
        create_event_1_day(
            char_ledger=True,
            date_start=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=2,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
        )
        create_event_1_day(
            char_ledger=True,
            date_start=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=5,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
        )
        journal = CorporationWalletJournalEntry.objects.all()
        # when
        journal_result = events_filter(journal)
        # then
        self.assertEqual(journal_result.count(), 1)
