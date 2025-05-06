# Standard Library
from unittest.mock import PropertyMock, patch

# Django
from django.test import RequestFactory, TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter

# AA Ledger
from ledger.app_settings import LEDGER_CHAR_MAX_INACTIVE_DAYS
from ledger.models.characteraudit import (
    CharacterAudit,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterWalletJournalModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = CharacterAudit(
            character=EveCharacter.objects.get(character_id=1001)
        )

    def test_str(self):
        self.assertEqual(str(self.audit), "Gneuten (None)")

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.audit.get_esi_scopes(),
            [
                # Mining Ledger
                "esi-industry.read_character_mining.v1",
                # Wallet / Market /  Contracts
                "esi-wallet.read_character_wallet.v1",
                "esi-contracts.read_character_contracts.v1",
                # Planetary Interaction
                "esi-planets.manage_planets.v1",
            ],
        )
