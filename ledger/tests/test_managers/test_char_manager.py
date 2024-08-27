from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import TestCase

from app_utils.testing import create_user_from_evecharacter

from ledger.managers.characterjournal_manager import CharWalletManager
from ledger.models.characteraudit import CharacterWalletJournalEntry
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.managers.characterjournal_manager"


class CharManagerQuerySetTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.manager = CharacterWalletJournalEntry.objects.all()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

    def test_annotate_bounty(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_bounty(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_bounty", qs.query.annotations)

        qs_no_filter = self.manager.annotate_bounty(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_bounty", qs_no_filter.query.annotations)

    def test_annotate_ess(self):
        character_ids = [1, 2, 3]

        qs = self.manager.filter_ess(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_ess", qs.query.annotations)

        qs_no_filter = self.manager.filter_ess(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_ess", qs_no_filter.query.annotations)

    def test_annotate_mission(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_mission(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_mission", qs.query.annotations)

        qs_no_filter = self.manager.annotate_mission(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_mission", qs_no_filter.query.annotations)

    def test_annotate_mining(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_mining(character_ids)
        self.assertIsNotNone(qs)

        qs_no_filter = self.manager.annotate_mining(character_ids)
        self.assertIsNotNone(qs_no_filter)

    def test_annotate_contract_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_contract_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_contract_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_contract_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_contract_cost", qs_no_filter.query.annotations)

    def test_annotate_market_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_market_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_market_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_market_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_market_cost", qs_no_filter.query.annotations)

    def test_annotate_assets_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_assets_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_assets_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_assets_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_assets_cost", qs_no_filter.query.annotations)

    def test_annotate_traveling_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_traveling_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_traveling_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_traveling_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_traveling_cost", qs_no_filter.query.annotations)

    def test_annotate_production_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_production_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_production_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_production_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_production_cost", qs_no_filter.query.annotations)

    def test_annotate_skill_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_skill_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_skill_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_skill_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_skill_cost", qs_no_filter.query.annotations)

    def test_annotate_insurance_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_insurance_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_insurance_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_insurance_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_insurance_cost", qs_no_filter.query.annotations)

    def test_annotate_planetary_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_planetary_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_planetary_cost", qs.query.annotations)

        qs_no_filter = self.manager.annotate_planetary_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_planetary_cost", qs_no_filter.query.annotations)

    def test_annotate_lp_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_lp_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_lp", qs.query.annotations)

        qs_no_filter = self.manager.annotate_lp_cost(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_lp", qs_no_filter.query.annotations)

    def test_annotate_market_trade(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_market_trade(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_market_trade", qs.query.annotations)

        qs_no_filter = self.manager.annotate_market_trade(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_market_trade", qs_no_filter.query.annotations)

    def test_annotate_contract_trade(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_contract_trade(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_contract_trade", qs.query.annotations)

        qs_no_filter = self.manager.annotate_contract_trade(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_contract_trade", qs_no_filter.query.annotations)

    def test_annotate_donation_trade(self):
        character_ids = [1, 2, 3]
        exclude = [4, 5]

        qs = self.manager.annotate_donation_trade(character_ids, exclude)
        self.assertIsNotNone(qs)
        self.assertIn("total_donation_trade", qs.query.annotations)

        qs_no_filter = self.manager.annotate_donation_trade(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_donation_trade", qs_no_filter.query.annotations)

    def test_annotate_insurance_trade(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_insurance_trade(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_insurance_trade", qs.query.annotations)

        qs_no_filter = self.manager.annotate_insurance_trade(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_insurance_trade", qs_no_filter.query.annotations)

    def test_generate_ledger(self):

        character_ids = [1, 2, 3]
        filter_date = Q(date__gte="2023-01-01")
        exclude = [4, 5]

        # Test with filter
        result_with_filter = self.manager.generate_ledger(
            character_ids, filter_date, exclude
        )
        self.assertIsNotNone(result_with_filter)
        self.assertIn("amounts", result_with_filter)
        self.assertIn("amounts_others", result_with_filter)
        self.assertIn("amounts_costs", result_with_filter)

        # Test without filter
        result_without_filter = self.manager.generate_ledger(character_ids)
        self.assertIsNotNone(result_without_filter)
        self.assertIn("amounts", result_without_filter)
        self.assertIn("amounts_others", result_without_filter)
        self.assertIn("amounts_costs", result_without_filter)

    def test_generate_billboard(self):

        character_ids = [1, 2, 3]
        filter_date = Q(date__gte="2023-01-01")
        exclude = [4, 5]

        # Test with filter
        qs = self.manager.generate_billboard(character_ids, filter_date, exclude)
        self.assertIsNotNone(qs)
        self.assertIn("total_bounty", qs.query.annotations)

        # Test without filter
        qs_no_filter = self.manager.generate_billboard(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_bounty", qs_no_filter.query.annotations)
