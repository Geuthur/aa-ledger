# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterOwner
from ledger.models.helpers.update_manager import CharacterUpdateSection, UpdateStatus
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    create_owner_from_user,
    create_update_status,
)

MODULE_PATH = "ledger.managers.character_audit_manager"


class TestCharacterAuditManager(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user)

        cls.user_character.delete()

    def test_disable_characters_with_no_ownership_should_disable(self):
        """
        Test that characters without ownership are disabled.

        This test creates a character audit entry without any associated ownership
        and then calls the disable_characters_with_no_owner method. It verifies that
        the character is correctly disabled.

        ### Results:
        - Characters without ownership are disabled.
        - The method returns the correct count of disabled characters.
        """
        # Test Data
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                self.audit,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )
        # Expected Result
        self.assertEqual(CharacterOwner.objects.disable_characters_with_no_owner(), 1)
        self.assertFalse(CharacterOwner.objects.get(pk=self.audit.pk).active)


class TestCharacterAnnotateTotalUpdateStatus(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_be_ok(self):
        """
        Test that a character with all successful updates is marked as OK.

        This test creates a character audit entry with successful update statuses
        for all sections and verifies that the total update status is annotated as OK.

        ### Results:
        - Characters with all successful updates are marked as OK.
        - The method correctly annotates the total update status.
        """
        # Test Data
        character = create_owner_from_user(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # Test Action
        update_status = CharacterOwner.objects.annotate_total_update_status()
        obj = update_status.first()

        # Expected Result
        self.assertEqual(obj.total_update_status, UpdateStatus.OK)

    def test_should_be_incomplete(self):
        """
        Test that a character with incomplete updates is marked as INCOMPLETE.

        This test creates a character audit entry with successful update statuses
        for some sections and verifies that the total update status is annotated as INCOMPLETE.

         ### Results:
        - Characters with incomplete updates are marked as INCOMPLETE.
        - The method correctly annotates the total update status."""
        # Test Data
        character = create_owner_from_user(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections[:2]:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # Test Action
        update_status = CharacterOwner.objects.annotate_total_update_status()
        obj = update_status.first()

        # Expected Result
        self.assertEqual(obj.total_update_status, UpdateStatus.INCOMPLETE)

    def test_should_be_token_error(self):
        """
        Test that a character with token errors is marked as TOKEN_ERROR.

        This test creates a character audit entry with at least one section having
        a token error and verifies that the total update status is annotated as TOKEN_ERROR.

        ### Results:
        - Characters with token errors are marked as TOKEN_ERROR.
        - The method correctly annotates the total update status.
        """
        # Test Data
        character = create_owner_from_user(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        create_update_status(
            character,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_status = CharacterOwner.objects.annotate_total_update_status()
        obj = update_status.first()

        # Expected Result
        self.assertEqual(obj.total_update_status, UpdateStatus.TOKEN_ERROR)

    def test_should_be_disabled(self):
        """
        Test that a disabled character is marked as DISABLED.

        This test creates a character audit entry, marks it as inactive,
        and verifies that the total update status is annotated as DISABLED.

        ### Results:
        - Disabled characters are marked as DISABLED.
        - The method correctly annotates the total update status.
        """
        # Test Data
        character = create_owner_from_user(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        character.active = False
        character.save()

        # Test Action
        update_status = CharacterOwner.objects.annotate_total_update_status()
        obj = update_status.first()

        # Expected Result
        self.assertEqual(obj.total_update_status, UpdateStatus.DISABLED)

    def test_should_be_error(self):
        """
        Test that a character with errors is marked as ERROR.

        This test creates a character audit entry with failed update statuses
        for all sections and verifies that the total update status is annotated as ERROR.

        ### Results:
        - Characters with errors are marked as ERROR.
        - The method correctly annotates the total update status.
        """
        # Test Data
        character = create_owner_from_user(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            create_update_status(
                character,
                section=section,
                is_success=False,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # Test Action
        update_status = CharacterOwner.objects.annotate_total_update_status()
        obj = update_status.first()

        # Expected Result
        self.assertEqual(obj.total_update_status, UpdateStatus.ERROR)
