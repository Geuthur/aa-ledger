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
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_bounty(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_bounty", qs.query.annotations)

    def test_annotate_ess(self):
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_ess(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_ess", qs.query.annotations)

    def test_annotate_mission(self):
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_mission(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_mission", qs.query.annotations)

    def test_annotate_daily_goal(self):
        character_ids = [1, 2, 3]

        qs = CorporationWalletJournalEntry.objects.annotate_daily_goal(character_ids)
        self.assertIsNotNone(qs)
        self.assertIn("total_daily_goal", qs.query.annotations)

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
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([2001])

        expected_result = [
            {
                "main_character_id": 1001,
                "main_character_name": "Gneuten",
                "alts": [1001],
                "total_bounty": Decimal("400000.00"),
                "total_ess": Decimal("400000.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1010,
                "main_character_name": "Test1",
                "alts": [1010],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1011,
                "main_character_name": "Test2",
                "alts": [1011],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1012,
                "main_character_name": "Test3",
                "alts": [1012],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1013,
                "main_character_name": "Test4",
                "alts": [1013],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1014,
                "main_character_name": "Test5",
                "alts": [1014],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1015,
                "main_character_name": "Test6",
                "alts": [1015],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1016,
                "main_character_name": "Test7",
                "alts": [1016],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1017,
                "main_character_name": "Test8",
                "alts": [1017],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1018,
                "main_character_name": "Test9",
                "alts": [1018],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1019,
                "main_character_name": "Test10",
                "alts": [1019],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1020,
                "main_character_name": "Test11",
                "alts": [1020],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
            {
                "main_character_id": 1021,
                "main_character_name": "Test12",
                "alts": [1021],
                "total_bounty": Decimal("100000.00"),
                "total_ess": Decimal("0.00"),
                "total_miscellaneous": Decimal("0.00"),
            },
        ]

        self.assertEqual(list(result), expected_result)

        # With Attribute Error

        auth_character = EveCharacter.objects.get(character_id=1019)
        user = AuthUtils.create_user(auth_character.character_name.replace(" ", "_"))
        _ = add_character_to_user(user, auth_character, is_main=False, scopes=None)

        self.client.force_login(user)

        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([2001])

        self.assertEqual(list(result), expected_result)

    def test_annotate_ledger_no_data(self):
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([99999])

        self.assertEqual(list(result), [])

    def test_annotate_ledger_no_data_no_corporations(self):
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([])

        self.assertEqual(list(result), [])
