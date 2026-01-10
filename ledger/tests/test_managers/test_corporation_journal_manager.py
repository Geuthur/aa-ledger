# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub
from ledger.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
    create_wallet_journal_entry,
)

MODULE_PATH = "ledger.managers.corporation_journal_manager"

LEDGER_CORPORATION_JOURNAL_ENDPOINTS = [
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWalletsDivisionJournal",
        "corporation_id",
        "division",
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch("ledger.models.general.EveEntity")
class TestCharacterJournalManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
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
        Test updating the wallet journal for a corporation.

        This test verifies that the wallet journal entries for a corporation division
        are correctly updated from ESI data.

        ### Expected Result
        - Wallet journal entries are updated correctly.
        - Entries have correct amounts and parties.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CORPORATION_JOURNAL_ENDPOINTS
        )

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9998, name="Test Character 2", category="character"
        )

        # Test Action
        self.audit.update_wallet_journal(force_refresh=False)

        # Expected Results
        self.assertSetEqual(
            set(
                self.division.ledger_corporation_journal.values_list(
                    "entry_id", flat=True
                )
            ),
            {10, 13, 16},
        )
        obj = self.division.ledger_corporation_journal.get(entry_id=10)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.context_id, 1)
        self.assertEqual(obj.first_party.eve_id, 2001)
        self.assertEqual(obj.second_party.eve_id, 1001)

        obj = self.division.ledger_corporation_journal.get(entry_id=13)
        self.assertEqual(obj.amount, 5000)

        obj = self.division.ledger_corporation_journal.get(entry_id=16)
        self.assertEqual(obj.amount, 10000)


class TestCorporationJournalManagerAnnotations(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
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
        qs = self.division.ledger_corporation_journal.annotate_bounty_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "bounty_income"),
                "Bounty income annotation should be present",
            )
            self.assertEqual(obj.bounty_income, 0)

    def test_annotate_ess_income(self):
        qs = self.division.ledger_corporation_journal.annotate_ess_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "ess_income"),
                "ESS income annotation should be present",
            )
            self.assertEqual(obj.ess_income, 0)

    def test_annotate_miscellaneous(self):
        qs = self.division.ledger_corporation_journal.annotate_miscellaneous()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)

    def test_annotate_costs(self):
        qs = self.division.ledger_corporation_journal.annotate_costs()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "costs"),
                "Costs annotation should be present",
            )
            self.assertEqual(obj.costs, 0)


class TestCorporationJournalManagerAggregate(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
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
        result = self.division.ledger_corporation_journal.aggregate_bounty()
        self.assertEqual(result, 0)

    def test_aggregate_costs(self):
        result = self.division.ledger_corporation_journal.aggregate_costs()
        self.assertEqual(result, 0)

    def test_aggregate_miscellaneous(self):
        result = self.division.ledger_corporation_journal.aggregate_miscellaneous()
        self.assertEqual(result, 1000.00)

    def test_aggregate_ref_type(self):
        result = self.division.ledger_corporation_journal.aggregate_ref_type(
            ref_type=["player_donation"], income=True
        )
        self.assertEqual(result, 1000.00)
