from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from esi.models import Token

from allianceauth.corputils.models import CorpMember, CorpStats
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ledger.managers.corpjournal_manager import CorpWalletManager, CorpWalletManagerBase
from ledger.models import CorporationWalletJournalEntry
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
            ],
        )
        cls.user2, _ = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
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

    def test_annotate_ledger(self):
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1002))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1004))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1003))
        add_character_to_user(self.user, EveCharacter.objects.get(character_id=1006))

        corp_stats = CorpStats.objects.create(
            token=Token.objects.filter(user=self.user).first(),
            corp=self.corp,
        )
        CorpMember.objects.create(
            character_id=9999, character_name="Test9999", corpstats=corp_stats
        )

        self.client.force_login(self.user)
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([2001])

        expected_result = [
            {
                "main_character_id": 1001,
                "main_character_name": "Gneuten",
                "alts": [],
                "total_bounty": Decimal("400000.00"),
                "total_ess": Decimal("400000.00"),
            }
        ]

        self.assertEqual(list(result), expected_result)

    def test_annotate_ledger_with_attribute_error(self):
        auth_character = EveCharacter.objects.get(character_id=1019)
        user = AuthUtils.create_user(auth_character.character_name.replace(" ", "_"))
        _ = add_character_to_user(user, auth_character, is_main=False, scopes=None)

        self.client.force_login(user)

        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([2001])

        expected_result = [
            {
                "main_character_id": 1001,
                "main_character_name": "Gneuten",
                "alts": [],
                "total_bounty": Decimal("400000.00"),
                "total_ess": Decimal("400000.00"),
            }
        ]

        self.assertEqual(list(result), expected_result)

    def test_annotate_ledger_no_data(self):
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([9999])

        self.assertEqual(list(result), [])

    def test_annotate_ledger_no_data_no_corporations(self):
        result = CorporationWalletJournalEntry.objects.all().annotate_ledger([])

        self.assertEqual(list(result), [])
