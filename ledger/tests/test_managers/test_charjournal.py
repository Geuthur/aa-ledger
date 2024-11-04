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

    def test_filter_ess(self):
        character_ids = [1, 2, 3]

        qs = self.manager.filter_ess(
            character_ids, filter_date=Q(date__gte="2023-01-01")
        )
        self.assertIsNotNone(qs)
        self.assertIn("total_ess", qs.query.annotations)

        qs_no_filter = self.manager.filter_ess(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_ess", qs_no_filter.query.annotations)

    def test_filter_daily_goal(self):
        character_ids = [1, 2, 3]

        qs = self.manager.filter_daily_goal(
            character_ids, filter_date=Q(date__gte="2023-01-01")
        )
        self.assertIsNotNone(qs)
        self.assertIn("total_daily_goal", qs.query.annotations)

        qs_no_filter = self.manager.filter_daily_goal(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_daily_goal", qs_no_filter.query.annotations)

    def test_filter_mining(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_mining(
            character_ids, filter_date=Q(date__gte="2023-01-01")
        )
        self.assertIsNotNone(qs)

        qs_no_filter = self.manager.annotate_mining(character_ids)
        self.assertIsNotNone(qs_no_filter)

    def test_annotate_mission(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_mission(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_mission", qs.query.annotations)

    def test_annotate_contract_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_contract_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_contract_cost", qs.query.annotations)

    def test_annotate_market_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_market_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_market_cost", qs.query.annotations)

    def test_annotate_assets_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_assets_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_assets_cost", qs.query.annotations)

    def test_annotate_traveling_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_traveling_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_traveling_cost", qs.query.annotations)

    def test_annotate_production_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_production_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_production_cost", qs.query.annotations)

    def test_annotate_skill_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_skill_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_skill_cost", qs.query.annotations)

    def test_annotate_insurance_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_insurance_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_insurance_cost", qs.query.annotations)

    def test_annotate_planetary_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_planetary_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_planetary_cost", qs.query.annotations)

    def test_annotate_lp_cost(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_lp_cost(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_lp", qs.query.annotations)

    def test_annotate_market_income(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_market_income(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_market_income", qs.query.annotations)

    def test_annotate_contract_income(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_contract_income(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_contract_income", qs.query.annotations)

    def test_annotate_donation_income(self):
        character_ids = [1, 2, 3]
        exclude = [4, 5]

        qs = self.manager.annotate_donation_income(character_ids, exclude)
        self.assertIsNotNone(qs)
        self.assertIn("total_donation_income", qs.query.annotations)

        qs_no_filter = self.manager.annotate_donation_income(character_ids)
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("total_donation_income", qs_no_filter.query.annotations)

    def test_annotate_insurance_income(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_insurance_income(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_insurance_income", qs.query.annotations)

    def test_annotate_corporation_projects_income(self):
        character_ids = [1, 2, 3]

        qs = self.manager.annotate_corporation_projects_income(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_cproject_income", qs.query.annotations)

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
        alts = [4, 5]

        # Test with filter
        qs = self.manager.annotate_billboard(character_ids, alts)
        self.assertIsNotNone(qs)
        self.assertIn("total_bounty", qs.query.annotations)
        self.assertIn("total_miscellaneous", qs.query.annotations)
        self.assertIn("total_cost", qs.query.annotations)
        self.assertIn("total_market_cost", qs.query.annotations)
        self.assertIn("total_production_cost", qs.query.annotations)
