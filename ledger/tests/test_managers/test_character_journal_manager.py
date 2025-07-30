# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase, override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
)
from ledger.tests.testdata.generate_walletjournal import create_wallet_journal_entry
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.character_journal_manager"


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
        cls.audit = create_characteraudit_from_evecharacter(1001)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="character",
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

    def test_update_wallet_journal(self, mock_eveentity, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        mock_eveentity.objects.create_bulk_from_esi.return_value = True

        EveEntity.objects.create(
            eve_id=9999, name="Test Character 1", category="character"
        )

        self.audit.update_wallet_journal(force_refresh=False)

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


class TestCharacterJournalManagerAnnotations(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_from_evecharacter(1001)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="character",
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
        qs = self.audit.ledger_character_journal.all().annotate_bounty_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "bounty_income"),
                "Bounty income annotation should be present",
            )
            self.assertEqual(obj.bounty_income, 0)

    def test_annotate_mission_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_mission_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "mission_income"),
                "Mission income annotation should be present",
            )
            self.assertEqual(obj.mission_income, 0)

    def test_annotate_market_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_market_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "market_income"),
                "Market income annotation should be present",
            )
            self.assertEqual(obj.market_income, 0)

    def test_annotate_incursion_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_incursion_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "incursion_income"),
                "Incursion income annotation should be present",
            )
            self.assertEqual(obj.incursion_income, 0)

    def test_annotate_contract_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_contract_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "contract_income"),
                "Contract income annotation should be present",
            )
            self.assertEqual(obj.contract_income, 0)

    def test_annotate_donation_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_donation_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "donation_income"),
                "Donation income annotation should be present",
            )
            self.assertEqual(obj.donation_income, 1000.00)

    def test_annotate_insurance_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_insurance_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "insurance_income"),
                "Insurance income annotation should be present",
            )
            self.assertEqual(obj.insurance_income, 0)

    def test_annotate_milestone_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_milestone_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "milestone_income"),
                "Milestone income annotation should be present",
            )
            self.assertEqual(obj.milestone_income, 0)

    def test_annotate_daily_goal_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_daily_goal_income()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "daily_goal_income"),
                "Daily goal income annotation should be present",
            )
            self.assertEqual(obj.daily_goal_income, 0)

    def test_annotate_miscellaneous_income(self):
        qs = self.audit.ledger_character_journal.all().annotate_miscellaneous()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous income annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)

    def test_annotate_miscellaneous_with_exclude(self):
        qs = (
            self.audit.ledger_character_journal.all().annotate_miscellaneous_with_exclude()
        )
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "miscellaneous"),
                "Miscellaneous with exclude annotation should be present",
            )
            self.assertEqual(obj.miscellaneous, 1000.00)

    def test_annotate_contract_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_contract_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "contract_cost"),
                "Contract costs annotation should be present",
            )
            self.assertEqual(obj.contract_cost, 0)

    def test_annotate_market_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_market_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "market_cost"),
                "Market costs annotation should be present",
            )
            self.assertEqual(obj.market_cost, 0)

    def test_annotate_asset_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_asset_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "asset_cost"),
                "Asset costs annotation should be present",
            )
            self.assertEqual(obj.asset_cost, 0)

    def test_annotate_traveling_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_traveling_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "traveling_cost"),
                "Traveling costs annotation should be present",
            )
            self.assertEqual(obj.traveling_cost, 0)

    def test_annotate_production_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_production_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "production_cost"),
                "Production costs annotation should be present",
            )
            self.assertEqual(obj.production_cost, 0)

    def test_annotate_skill_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_skill_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "skill_cost"),
                "Skill costs annotation should be present",
            )
            self.assertEqual(obj.skill_cost, 0)

    def test_annotate_insurance_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_insurance_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "insurance_cost"),
                "Insurance costs annotation should be present",
            )
            self.assertEqual(obj.insurance_cost, 0)

    def test_annotate_planetary_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_planetary_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "planetary_cost"),
                "Planetary costs annotation should be present",
            )
            self.assertEqual(obj.planetary_cost, 0)

    def test_annotate_lp_cost(self):
        qs = self.audit.ledger_character_journal.all().annotate_lp_cost()
        for obj in qs:
            self.assertTrue(
                hasattr(obj, "lp_cost"),
                "LP costs annotation should be present",
            )
            self.assertEqual(obj.lp_cost, 0)


class TestCharacterJournalManagerAggregate(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_from_evecharacter(1001)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="character",
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
        result = self.audit.ledger_character_journal.all().aggregate_bounty()
        self.assertEqual(result, 0)

    def test_aggregate_costs(self):
        result = self.audit.ledger_character_journal.all().aggregate_costs()
        self.assertEqual(result, 0)

    def test_aggregate_miscellaneous(self):
        result = self.audit.ledger_character_journal.all().aggregate_miscellaneous()
        self.assertEqual(result, 1000.00)

    def test_aggregate_ref_type(self):
        result = self.audit.ledger_character_journal.all().aggregate_ref_type(
            ref_type=["player_donation"], income=True
        )
        self.assertEqual(result, 1000.00)
