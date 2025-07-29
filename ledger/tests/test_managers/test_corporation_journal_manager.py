# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporationaudit_from_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.corporation_journal_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
@patch("ledger.models.general.EveEntity")
class TestCharacterJournalManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="corporation",
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
        cls.token = cls.character_ownership.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_wallet_journal(self, mock_eveentity, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()[0]

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9998, name="Test Character 2", category="character"
        )

        self.audit.update_wallet_journal(force_refresh=False)

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


class TestCorporationJournalManagerAnnotations(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="corporation",
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


class TestCorporationJournalManagerAggregate(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="corporation",
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
