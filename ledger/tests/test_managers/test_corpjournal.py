from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from esi.models import Token

from allianceauth.corputils.models import CorpMember, CorpStats
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.managers.corpjournal_manager import CorpWalletManager
from ledger.models import CorporationWalletDivision, CorporationWalletJournalEntry
from ledger.models.general import EveEntity
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.managers.corpjournal_manager"


class CharManagerQuerySetTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.manager = CorpWalletManager()
        cls.corp = EveCorporationInfo.objects.get(corporation_id=2001)

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
            ],
        )

    def test_annotate_bounty(self):
        qs = CorporationWalletJournalEntry.objects.annotate_bounty_income()
        self.assertIsNotNone(qs)
        self.assertIn("bounty_income", qs.query.annotations)

    def test_annotate_ess(self):
        qs = CorporationWalletJournalEntry.objects.annotate_ess_income()
        self.assertIsNotNone(qs)
        self.assertIn("ess_income", qs.query.annotations)

    def test_annotate_mission(self):
        qs = CorporationWalletJournalEntry.objects.annotate_mission_income()
        self.assertIsNotNone(qs)
        self.assertIn("mission_income", qs.query.annotations)

    def test_annotate_daily_goal(self):
        qs = CorporationWalletJournalEntry.objects.annotate_daily_goal_income()
        self.assertIsNotNone(qs)
        self.assertIn("daily_goal_income", qs.query.annotations)

    def test_annotate_ledger(self):
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1002))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1004))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1003))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1006))

        test9999 = EveEntity.objects.create(
            eve_id=9999,
            category=EveEntity.CATEGORY_CHARACTER,
            name="Test9999",
        )

        test9998 = EveEntity.objects.create(
            eve_id=9998,
            category=EveEntity.CATEGORY_CHARACTER,
            name="Test9999",
        )

        # Create CorporationWalletJournalEntry objects
        CorporationWalletJournalEntry.objects.create(
            division=CorporationWalletDivision.objects.get(id=1),
            amount=100_000,
            balance=100_000_000,
            context_id=0,
            context_id_type="division",
            date="2024-03-19T14:00:00Z",
            description="Test",
            first_party=EveEntity.objects.get(eve_id=1000125),
            entry_id=298,
            reason="",
            ref_type="bounty_prizes",
            second_party=test9998,
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
            entry_id=299,
            reason="",
            ref_type="bounty_prizes",
            second_party=test9999,
            tax=0,
            tax_receiver_id=0,
        )

        self.client.force_login(self.user)
        result = CorporationWalletJournalEntry.objects.all().generate_ledger([2001])

        expected_result = [
            {
                "main_entity_id": 1001,
                "alts": [1001, 1002],
                "bounty": Decimal("400000.00"),
                "ess": Decimal("400000.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1010,
                "alts": [1010],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1011,
                "alts": [1011],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1012,
                "alts": [1012],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1013,
                "alts": [1013],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1014,
                "alts": [1014],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1015,
                "alts": [1015],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1016,
                "alts": [1016],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1017,
                "alts": [1017],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1018,
                "alts": [1018],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1019,
                "alts": [1019],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1020,
                "alts": [1020],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 1021,
                "alts": [1021],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 9998,
                "alts": [9998],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
            {
                "main_entity_id": 9999,
                "alts": [9999],
                "bounty": Decimal("100000.00"),
                "ess": Decimal("0.00"),
                "mission": Decimal("0.00"),
                "incursion": Decimal("0.00"),
                "daily_goal": Decimal("0.00"),
                "citadel": Decimal("0.00"),
                "miscellaneous": Decimal("0.00"),
            },
        ]

        sorted_result = sorted(list(result), key=lambda x: x["main_entity_id"])
        sorted_expected_result = sorted(
            expected_result, key=lambda x: x["main_entity_id"]
        )

        self.assertEqual(sorted_result, sorted_expected_result)

    def test_annotate_ledger_no_data(self):
        result = CorporationWalletJournalEntry.objects.all().generate_ledger([99999])

        self.assertEqual(list(result), [])

    def test_annotate_ledger_no_data_no_corporations(self):
        result = CorporationWalletJournalEntry.objects.all().generate_ledger([])

        self.assertEqual(list(result), [])
