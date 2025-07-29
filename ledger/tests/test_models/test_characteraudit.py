# Standard Library
from unittest.mock import PropertyMock, patch

# Django
from django.test import RequestFactory, TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterAudit, CharacterUpdateStatus
from ledger.models.general import _NeedsUpdate
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
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
        cls.audit = add_characteraudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        sections = CharacterAudit.UpdateSection.get_sections()
        for section in sections:
            create_update_status(
                cls.audit,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )
        cls.update_status_wallet = CharacterUpdateStatus.objects.get(
            character=cls.audit,
            section=CharacterAudit.UpdateSection.WALLET_JOURNAL,
        )
        cls.update_status_mining_ledger = CharacterUpdateStatus.objects.get(
            character=cls.audit,
            section=CharacterAudit.UpdateSection.MINING_LEDGER,
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
        update_status = self.update_status_wallet
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
            CharacterAudit.UpdateStatus.TOKEN_ERROR,
        )

        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = False
        update_status.save()

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.ERROR,
        )

        update_status.delete()

        self.assertEqual(
            self.audit.get_status,
            CharacterAudit.UpdateStatus.INCOMPLETE,
        )

    def test_reset_has_token_error(self):
        audit = self.audit

        self.assertEqual(
            audit.reset_has_token_error(),
            False,
        )

        self.update_status_mining_ledger.has_token_error = True
        self.update_status_mining_ledger.save()

        self.assertEqual(
            audit.reset_has_token_error(),
            True,
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
