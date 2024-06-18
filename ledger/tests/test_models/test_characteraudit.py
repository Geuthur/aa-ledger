import datetime
from unittest.mock import PropertyMock, patch

from django.test import TestCase
from django.utils import timezone
from eveuniverse.models import EveSolarSystem, EveType

from allianceauth.eveonline.models import EveCharacter

from ledger.app_settings import LEDGER_CHAR_MAX_INACTIVE_DAYS
from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all

MODULE_PATH = "ledger.models.general"


class TestCharacterAuditModel(TestCase):
    @classmethod
    def setUp(self):
        load_allianceauth()
        self.audit = CharacterAudit(
            character=EveCharacter.objects.get(character_id=1001)
        )

    def test_str(self):
        self.assertEqual(str(self.audit), "Gneuten's Character Data")

    def test_is_active(self):
        self.assertTrue(self.audit.is_active)

    def test_is_active_false(self):
        # given/when
        self.audit.last_update_wallet = timezone.now() - datetime.timedelta(
            days=LEDGER_CHAR_MAX_INACTIVE_DAYS + 1
        )
        self.audit.last_update_mining = timezone.now() - datetime.timedelta(
            days=LEDGER_CHAR_MAX_INACTIVE_DAYS + 1
        )
        self.audit.save()
        # then
        self.assertFalse(self.audit.is_active())

    def test_is_active_updates_active_field(self):
        # given/when
        self.audit.last_update_wallet = timezone.now() - datetime.timedelta(
            days=LEDGER_CHAR_MAX_INACTIVE_DAYS + 1
        )
        self.audit.last_update_mining = timezone.now() - datetime.timedelta(
            days=LEDGER_CHAR_MAX_INACTIVE_DAYS + 1
        )
        self.audit.active = True
        self.audit.save()
        # then
        self.assertFalse(self.audit.is_active())

        self.audit.refresh_from_db()
        self.assertFalse(self.audit.active)

    def test_is_active_exception(self):
        with patch.object(
            self.audit.__class__, "last_update_wallet", new_callable=PropertyMock
        ) as mock_wallet:
            with patch.object(
                self.audit.__class__, "last_update_mining", new_callable=PropertyMock
            ) as mock_mining:
                # Make the mocks raise an exception when accessed
                mock_wallet.side_effect = Exception
                mock_mining.side_effect = Exception

                self.assertFalse(self.audit.is_active())

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.audit.get_esi_scopes(),
            [
                # Mining Ledger
                "esi-industry.read_character_mining.v1",
                # Wallet / Market /  Contracts
                "esi-wallet.read_character_wallet.v1",
                "esi-contracts.read_character_contracts.v1",
            ],
        )


class TestCharacterWalletJournal(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.journal = CharacterWalletJournalEntry.objects.get(entry_id=1)

    def test_str(self):
        self.assertEqual(
            str(self.journal),
            "Character Wallet Journal: CONCORD 'bounty_prizes' Gneuten: 100000.00 isk",
        )


class TestCharacterMiningLedger(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        cls.mining = CharacterMiningLedger.objects.get(
            id="20240316-17425-1001-30004783"
        )

    def test_str(self):
        self.assertEqual(
            str(self.mining), "Gneuten's Character Data 20240316-17425-1001-30004783"
        )
