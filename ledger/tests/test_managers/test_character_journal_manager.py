# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import TestCase, override_settings
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub
from ledger.tests.testdata.utils import (
    create_owner_from_user,
    create_wallet_journal_entry,
)

MODULE_PATH = "ledger.managers.character_journal_manager"

LEDGER_CHARACTER_WALLET_JOURNAL_ENDPOINTS = [
    EsiEndpoint("Wallet", "GetCharactersCharacterIdWalletJournal", "character_id"),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch("ledger.models.general.EveEntity")
class TestCharacterJournalManager(LedgerTestCase):
    """Test Character Journal Manager for Character."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)
        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="character",
            character=cls.audit,
            context_id=1,
            entry_id=10,
            amount=1000,
            balance=2000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_wallet_journal(self, mock_eveentity, mock_esi):
        """
        Test updating the wallet journal for a character.

        This test mocks the ESI client and EveEntity model to simulate
        fetching wallet journal entries from ESI and updating the local
        database accordingly.

        ### Results:
            - Wallet Journal Entries (entry_id: 10, 13, 16) are created with correct data.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CHARACTER_WALLET_JOURNAL_ENDPOINTS
        )
        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9999, name="Test Character 1", category="character"
        )

        # Test Action
        self.audit.update_wallet_journal(force_refresh=False)

        # Expected Results
        self.assertSetEqual(
            set(self.audit.ledger_character_journal.values_list("entry_id", flat=True)),
            {10, 13, 16},
        )
        obj = self.audit.ledger_character_journal.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.eve_id, 1001)
        self.assertEqual(obj.second_party.eve_id, 1002)

        obj = self.audit.ledger_character_journal.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.audit.ledger_character_journal.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)


class TestCharacterJournalManagerAnnotations(LedgerTestCase):
    """Test annotation methods in CharacterJournalManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="character",
            character=cls.audit,
            context_id=1,
            entry_id=10,
            amount=1000,
            balance=2000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )

    def test_annotate_bounty_income(self):
        """ "Test annotating bounty income."""
        qs = self.audit.ledger_character_journal.all().annotate_bounty_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "bounty_income"),
                "Bounty income annotation should be present",
            )
            self.assertEqual(obj.bounty_income, 0)

    def test_annotate_miscellaneous_income(self):
        """Test annotating miscellaneous income."""
        qs = self.audit.ledger_character_journal.all().annotate_miscellaneous()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous income annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)


class TestCharacterJournalManagerAggregate(LedgerTestCase):
    """Test aggregation methods in CharacterJournalManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="character",
            character=cls.audit,
            context_id=1,
            entry_id=10,
            amount=1000,
            balance=2000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )

    def test_aggregate_bounty(self):
        """Test aggregating bounty income."""
        result = self.audit.ledger_character_journal.all().aggregate_bounty()
        self.assertEqual(result, 0)

    def test_aggregate_costs(self):
        """Test aggregating costs."""
        result = self.audit.ledger_character_journal.all().aggregate_costs()
        self.assertEqual(result, 0)

    def test_aggregate_miscellaneous(self):
        """Test aggregating miscellaneous income."""
        result = self.audit.ledger_character_journal.all().aggregate_miscellaneous()
        self.assertEqual(result, 1000.00)

    def test_aggregate_ref_type(self):
        """Test aggregating by reference type."""
        result = self.audit.ledger_character_journal.all().aggregate_ref_type(
            ref_type=["player_donation"], income=True
        )
        self.assertEqual(result, 1000.00)
