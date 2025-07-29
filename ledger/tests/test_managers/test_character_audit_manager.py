# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterAudit, CharacterUpdateStatus
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_update_status,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.character_audit_manager"


class TestCharacterAuditManager(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )
        cls.audit = add_characteraudit_character_to_user(cls.user, 1001)

        cls.character_ownership.delete()

    def test_disable_characters_with_no_ownership_should_disable(self):
        # given
        scetions = CharacterAudit.UpdateSection.get_sections()
        for section in scetions:
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

        # then
        self.assertEqual(CharacterAudit.objects.disable_characters_with_no_owner(), 1)


class TestCharacterAnnotateTotalUpdateStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )

    def test_should_be_ok(self):
        # given
        character = add_characteraudit_character_to_user(self.user, 1001)
        sections = CharacterAudit.UpdateSection.get_sections()
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

        # when
        update_status = CharacterAudit.objects.annotate_total_update_status()
        obj = update_status.first()

        # then
        self.assertEqual(obj.total_update_status, CharacterAudit.UpdateStatus.OK)

    def test_should_be_incomplete(self):
        # given
        character = add_characteraudit_character_to_user(self.user, 1001)
        sections = CharacterAudit.UpdateSection.get_sections()
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

        # when
        update_status = CharacterAudit.objects.annotate_total_update_status()
        obj = update_status.first()

        # then
        self.assertEqual(
            obj.total_update_status, CharacterAudit.UpdateStatus.INCOMPLETE
        )

    def test_should_be_token_error(self):
        # given
        character = add_characteraudit_character_to_user(self.user, 1001)
        sections = CharacterAudit.UpdateSection.get_sections()
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
            section=CharacterAudit.UpdateSection.WALLET_JOURNAL,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # when
        update_status = CharacterAudit.objects.annotate_total_update_status()
        obj = update_status.first()

        # then
        self.assertEqual(
            obj.total_update_status, CharacterAudit.UpdateStatus.TOKEN_ERROR
        )

    def test_should_be_disabled(self):
        # given
        character = add_characteraudit_character_to_user(self.user, 1001)
        sections = CharacterAudit.UpdateSection.get_sections()
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

        # when
        update_status = CharacterAudit.objects.annotate_total_update_status()
        obj = update_status.first()

        # then
        self.assertEqual(obj.total_update_status, CharacterAudit.UpdateStatus.DISABLED)

    def test_should_be_error(self):
        # given
        character = add_characteraudit_character_to_user(self.user, 1001)
        sections = CharacterAudit.UpdateSection.get_sections()
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

        # when
        update_status = CharacterAudit.objects.annotate_total_update_status()
        obj = update_status.first()

        # then
        self.assertEqual(obj.total_update_status, CharacterAudit.UpdateStatus.ERROR)
