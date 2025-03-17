from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

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

        cls.char_1 = EveCharacter.objects.get(character_id=1001)
        cls.char_2 = EveCharacter.objects.get(character_id=1002)

        cls.alt_1 = EveCharacter.objects.get(character_id=1003)
        cls.alt_2 = EveCharacter.objects.get(character_id=1004)

    def test_annotate_bounty(self):
        qs = self.manager.annotate_bounty_income()
        self.assertIsNotNone(qs)
        self.assertIn("bounty_income", qs.query.annotations)

    def test_annotate_mission_income(self):
        qs = self.manager.annotate_mission_income()
        self.assertIsNotNone(qs)
        self.assertIn("mission_income", qs.query.annotations)

    def test_annotate_incursion_income(self):
        qs = self.manager.annotate_incursion_income()
        self.assertIsNotNone(qs)
        self.assertIn("incursion_income", qs.query.annotations)

    def test_annotate_market_income(self):
        qs = self.manager.annotate_market_income()
        self.assertIsNotNone(qs)
        self.assertIn("market_income", qs.query.annotations)

    def test_annotate_contract_income(self):
        qs = self.manager.annotate_contract_income()
        self.assertIsNotNone(qs)
        self.assertIn("contract_income", qs.query.annotations)

    def test_annotate_donation_income(self):
        exclude = [4, 5]
        qs = self.manager.annotate_donation_income(exclude)
        self.assertIsNotNone(qs)
        self.assertIn("donation_income", qs.query.annotations)

        qs_no_filter = self.manager.annotate_donation_income()
        self.assertIsNotNone(qs_no_filter)
        self.assertIn("donation_income", qs_no_filter.query.annotations)

    def test_annotate_insurance_income(self):
        qs = self.manager.annotate_insurance_income()
        self.assertIsNotNone(qs)
        self.assertIn("insurance_income", qs.query.annotations)

    def test_annotate_milestone_income(self):
        qs = self.manager.annotate_milestone_income()
        self.assertIsNotNone(qs)
        self.assertIn("milestone_income", qs.query.annotations)

    def test_annotate_contract_cost(self):
        qs = self.manager.annotate_contract_cost()
        self.assertIsNotNone(qs)
        self.assertIn("contract_cost", qs.query.annotations)

    def test_annotate_market_cost(self):
        qs = self.manager.annotate_market_cost()
        self.assertIsNotNone(qs)
        self.assertIn("market_cost", qs.query.annotations)

    def test_annotate_assets_cost(self):
        qs = self.manager.annotate_asset_cost()
        self.assertIsNotNone(qs)
        self.assertIn("asset_cost", qs.query.annotations)

    def test_annotate_traveling_cost(self):
        qs = self.manager.annotate_traveling_cost()
        self.assertIsNotNone(qs)
        self.assertIn("traveling_cost", qs.query.annotations)

    def test_annotate_production_cost(self):
        qs = self.manager.annotate_production_cost()
        self.assertIsNotNone(qs)
        self.assertIn("production_cost", qs.query.annotations)

    def test_annotate_skill_cost(self):
        qs = self.manager.annotate_skill_cost()
        self.assertIsNotNone(qs)
        self.assertIn("skill_cost", qs.query.annotations)

    def test_annotate_insurance_cost(self):
        qs = self.manager.annotate_insurance_cost()
        self.assertIsNotNone(qs)
        self.assertIn("insurance_cost", qs.query.annotations)

    def test_annotate_planetary_cost(self):
        qs = self.manager.annotate_planetary_cost()
        self.assertIsNotNone(qs)
        self.assertIn("planetary_cost", qs.query.annotations)

    def test_annotate_lp_cost(self):
        qs = self.manager.annotate_lp_cost()
        self.assertIsNotNone(qs)
        self.assertIn("lp_cost", qs.query.annotations)

    def test_annotate_costs(self):
        qs = self.manager.annotate_costs()
        self.assertIsNotNone(qs)
        self.assertIn("costs", qs.query.annotations)

    def test_annotate_miscellaneous(self):
        qs = self.manager.annotate_miscellaneous()
        self.assertIsNotNone(qs)
        self.assertIn("miscellaneous", qs.query.annotations)

    def test_annotate_miscellaneous_with_exclude(self):
        qs = self.manager.annotate_miscellaneous_with_exclude()
        self.assertIsNotNone(qs)
        self.assertIn("miscellaneous", qs.query.annotations)

    def test_generate_ledger(self):

        character_ids = [self.char_1, self.char_2]
        filter_date = Q(date__gte=timezone.make_aware(timezone.datetime(2023, 1, 1)))
        exclude = [4, 5]

        # Test with filter
        result_with_filter = self.manager.generate_ledger(
            character_ids, filter_date, exclude
        )
        self.assertIsNotNone(result_with_filter)

    def test_generate_billboard(self):

        character_ids = [1, 2, 3]
        alts = [4, 5]

        # Test with filter
        qs = self.manager.annotate_billboard(character_ids, alts)
        self.assertIsNotNone(qs)
        self.assertIn("bounty_income", qs.query.annotations)
        self.assertIn("miscellaneous", qs.query.annotations)
        self.assertIn("costs", qs.query.annotations)
        self.assertIn("market_cost", qs.query.annotations)
        self.assertIn("production_cost", qs.query.annotations)

    def test_generate_ledger_with_attribute_error(self):
        character_ids = [self.char_1, self.char_2, "a"]
        filter_date = Q(date__gte=timezone.make_aware(timezone.datetime(2023, 1, 1)))
        exclude = [4, 5]

        result_with_filter = self.manager.generate_ledger(
            character_ids, filter_date, exclude
        )
        self.assertIsNotNone(result_with_filter)
