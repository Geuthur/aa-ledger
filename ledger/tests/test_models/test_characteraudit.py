# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import (
    CharacterOwner,
    CharacterUpdateSection,
    CharacterUpdateStatus,
)
from ledger.models.helpers.update_manager import UpdateStatus
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_owner_to_user,
    create_update_status,
)

MODULE_PATH = "ledger.models.characteraudit"


class TestCharacterWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.owner = add_owner_to_user(
            cls.user, cls.user_character.character.character_id
        )
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                owner=cls.owner,
                section=section,
                error_message="",
                is_success=True,
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )
        cls.update_status_wallet = CharacterUpdateStatus.objects.get(
            owner=cls.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
        )
        cls.update_status_mining_ledger = CharacterUpdateStatus.objects.get(
            owner=cls.owner,
            section=CharacterUpdateSection.MINING_LEDGER,
        )

    def test_str(self):
        excepted_str = CharacterOwner.objects.get(id=self.owner.id)
        self.assertEqual(self.owner, excepted_str)

    def test_get_esi_scopes(self):
        """
        Test retrieval of ESI scopes for CharacterOwner.

        ### Expected Result
        - Correct list of ESI scopes is returned.
        """
        self.assertEqual(
            self.owner.get_esi_scopes(),
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
        """
        Test various states of get_status property.

        ### Expected Results:
        - OK
        - DISABLED
        - TOKEN_ERROR
        - ERROR
        - INCOMPLETE
        """
        # Test Data - OK
        update_status = self.update_status_wallet
        audit = self.owner

        # Expected Result
        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.OK,
        )

        # Test Data - DISABLED
        audit.active = False
        audit.save()

        # Expected Result
        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.DISABLED,
        )

        # Test Data - TOKEN_ERROR
        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = True
        update_status.save()

        # Expected Result
        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.TOKEN_ERROR,
        )

        # Test Data - ERROR
        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = False
        update_status.save()

        # Expected Result
        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.ERROR,
        )
        update_status.delete()

        # Test Data - INCOMPLETE
        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.INCOMPLETE,
        )
