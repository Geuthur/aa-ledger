from unittest.mock import PropertyMock, patch

from django.test import RequestFactory, TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

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
        self.assertEqual(str(self.audit), "Gneuten's Character Data")

    def test_is_active_should_true(self):
        self.audit.last_update_wallet = timezone.now()
        self.audit.last_update_mining = timezone.now()
        self.audit.last_update_planetary = timezone.now()
        self.assertTrue(self.audit.is_active())

    def test_is_active_should_false(self):
        self.audit.last_update_wallet = timezone.now() - timezone.timedelta(days=4)
        self.audit.last_update_mining = timezone.now() - timezone.timedelta(days=4)
        self.audit.last_update_planetary = timezone.now() - timezone.timedelta(days=4)
        self.assertFalse(self.audit.is_active())

    def test_is_active_exception(self):
        self.audit.last_update_wallet = None
        self.audit.last_update_mining = None
        self.audit.last_update_planetary = None
        self.assertFalse(self.audit.is_active())

    @patch(MODULE_PATH + ".logger")
    def test_is_active_should_deactive_character(self, mock_logger):
        self.audit.active = True
        self.audit.last_update_wallet = timezone.now()
        self.audit.last_update_mining = timezone.now() - timezone.timedelta(days=4)
        self.audit.last_update_planetary = timezone.now() - timezone.timedelta(days=4)
        self.assertFalse(self.audit.is_active())
        mock_logger.info.assert_called_once_with(
            "Deactivating Character: %s", self.audit.character.character_name
        )

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

    def test_get_status_opacity_should_return_100(self):
        self.audit.active = True
        self.assertEqual(self.audit.get_status_opacity, "opacity-100")

    def test_get_status_opacity_should_return_25(self):
        self.audit.active = False
        self.assertEqual(self.audit.get_status_opacity, "opacity-25")

    def test_get_status_icon_should_return_ok(self):
        self.audit.last_update_mining = timezone.now()
        self.audit.last_update_wallet = timezone.now()
        self.audit.last_update_planetary = timezone.now()
        self.audit.active = True

        self.assertEqual(self.audit.get_status, self.audit.UpdateStatus("ok"))
        self.assertEqual(
            self.audit.get_status.bootstrap_icon(),
            self.audit.UpdateStatus("ok").bootstrap_icon(),
        )

    def test_get_status_icon_should_return_disabled(self):
        self.audit.active = False
        self.assertEqual(
            self.audit.get_status,
            self.audit.UpdateStatus("disabled"),
        )

    def test_get_status_icon_should_return_not_up_to_date(self):
        self.audit.active = True
        self.audit.last_update_mining = timezone.now() - timezone.timedelta(days=4)
        self.audit.last_update_wallet = timezone.now()
        self.audit.last_update_planetary = timezone.now()
        self.assertEqual(
            self.audit.get_status,
            self.audit.UpdateStatus("not_up_to_date"),
        )
