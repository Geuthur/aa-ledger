# Standard Library
from unittest.mock import PropertyMock, patch

# Django
from django.test import RequestFactory, TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterAudit, CharacterUpdateStatus
from ledger.models.general import _NeedsUpdate
from ledger.tests.testdata.generate_characteraudit import (
    add_charactermaudit_character_to_user,
    create_update_status,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterWalletJournalModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )
        cls.audit = add_charactermaudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        cls.update_status = create_update_status(
            cls.audit,
            section="wallet_journal",
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

    def test_str(self):
        excepted_str = CharacterAudit.objects.get(id=self.audit.id)
        self.assertEqual(self.audit, excepted_str)

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

    def test_get_status_states(self):
        update_status = self.update_status
        audit = self.audit

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.OK,
        )

        audit.active = False
        audit.save()

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.DISABLED,
        )

        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = True
        update_status.save()

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.ERROR,
        )

        update_status.delete()

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.DISABLED,
        )

    def test_reset_has_token_error(self):
        audit = self.audit

        self.assertEqual(
            audit.reset_has_token_error(),
            False,
        )

    def test_reset_update_status(self):
        # given
        audit = self.audit
        # when
        update_status = audit.reset_update_status("mining_ledger")
        # then
        self.assertEqual(
            update_status,
            CharacterUpdateStatus.objects.get(
                character=audit,
                section="mining_ledger",
            ),
        )
