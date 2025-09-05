# Standard Library
from types import SimpleNamespace
from unittest.mock import patch

# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveMarketPrice, EveSolarSystem, EveType

# AA Ledger
from ledger.models.characteraudit import CharacterMiningLedger
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_miningledger import create_miningledger
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterMiningLedgerModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )
        cls.audit = add_characteraudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        cls.eve_type = EveType.objects.get(id=17425)
        cls.eve_system = EveSolarSystem.objects.get(id=30004783)

        cls.eve_type2 = EveType.objects.get(id=16268)
        cls.eve_type_price = EveType.objects.get(id=28437)

        cls.miningentry = create_miningledger(
            character=cls.audit,
            id=1,
            date=timezone.now(),
            type=cls.eve_type,
            system=cls.eve_system,
            quantity=100,
        )
        cls.miningentry2 = create_miningledger(
            character=cls.audit,
            id=2,
            date=timezone.now(),
            type=cls.eve_type2,
            system=cls.eve_system,
            quantity=100,
        )
        cls.miningrecord = SimpleNamespace(
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            type_id=1,
            solar_system_id=1,
        )
        cls.eve_market_price = EveMarketPrice.objects.create(
            eve_type=cls.eve_type_price,
            average_price=100,
        )

    def test_str(self):
        self.assertEqual(str(self.miningentry), f"{self.audit} 1")

    def test_create_primary_key(self):
        # when
        primary_key = CharacterMiningLedger.create_primary_key(
            self.audit.eve_character.character_id, self.miningrecord
        )
        # then
        self.assertEqual(primary_key, "20240101-1-1001-1")

    def test_get_npc_price(self):
        # when
        npc_price = self.miningentry2.get_npc_price()
        # then
        self.assertIsNotNone(npc_price)
        self.assertEqual(npc_price, 100)

    @patch(MODULE_PATH + ".cache.get", return_value=False)
    @patch(MODULE_PATH + ".EveMarketPrice.objects.update_from_esi")
    def test_update_evemarket_price(self, mock_market_price, mock_cache_get):
        # given
        mock_market_price.return_value = 1337
        # when
        updated = self.miningentry.update_evemarket_price()
        # then
        self.assertTrue(mock_market_price.called)
        self.assertEqual(updated, 1337)
