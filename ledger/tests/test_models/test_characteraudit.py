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
from ledger.tests.testdata.generate_characteraudit import (
    add_characterowner_character_to_user,
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
        cls.owner = add_characterowner_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                owner=cls.owner,
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
        update_status = self.update_status_wallet
        audit = self.owner

        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.OK,
        )

        audit.active = False
        audit.save()

        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.DISABLED,
        )

        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = True
        update_status.save()

        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.TOKEN_ERROR,
        )

        audit.active = True
        audit.save()
        update_status.is_success = False
        update_status.has_token_error = False
        update_status.save()

        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.ERROR,
        )

        update_status.delete()

        self.assertEqual(
            self.owner.get_status,
            UpdateStatus.INCOMPLETE,
        )
