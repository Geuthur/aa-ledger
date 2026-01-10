# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# Alliance Auth (External Libs)
from eveuniverse.models import EveSolarSystem, EveType

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub
from ledger.tests.testdata.utils import (
    create_owner_from_user,
)

MODULE_PATH = "ledger.managers.character_mining_manager"
CHARACTEROWNER_PATH = "ledger.models.characteraudit.CharacterMiningLedger"
LEDGER_CHARACTER_MINING_LEDGER_ENDPOINTS = [
    EsiEndpoint(
        "Industry",
        "GetCharactersCharacterIdMining",
        "character_id",
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi")
@patch(CHARACTEROWNER_PATH + ".update_evemarket_price")
class TestCharacterMiningManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)

        cls.eve_type = EveType.objects.get(id=17425)
        cls.eve_system = EveSolarSystem.objects.get(id=30004783)

        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_mining_ledger(self, _, __, mock_esi):
        """
        Test updating the character mining ledger.

        This test verifies that the mining ledger entries are correctly updated
        from ESI data. It checks that the entries have the expected quantity, system_id,
        and type_id.

        ### Expected Result
        - Mining ledger entries are updated correctly.
        - Entries have correct quantity, system_id, and type_id.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CHARACTER_MINING_LEDGER_ENDPOINTS,
        )

        # Test Action
        self.audit.update_mining_ledger(force_refresh=False)

        # Excepted Results
        obj = self.audit.ledger_character_mining.filter(
            date__contains="2014-10-29"
        ).first()
        self.assertEqual(obj.quantity, 5000)
        self.assertEqual(obj.system_id, 30004783)
        self.assertEqual(obj.type_id, 17425)
