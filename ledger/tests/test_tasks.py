"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, PropertyMock, patch

# Django
from django.test import override_settings
from django.utils import timezone

# AA Ledger
from ledger.models.characteraudit import CharacterUpdateStatus
from ledger.models.corporationaudit import CorporationUpdateStatus
from ledger.models.general import UpdateSectionResult
from ledger.tasks import (
    _update_character_section,
    _update_corporation_section,
    update_all_characters,
    update_all_corporations,
    update_character,
    update_corporation,
)
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import create_owner_from_user, create_update_status

TASKS_PATH = "ledger.tasks"
MANAGERS_PATH = "ledger.managers"
MODELS_PATH = "ledger.models"


class TestTasks(LedgerTestCase):
    """
    Tests for ledger tasks.
    """

    @patch(TASKS_PATH + ".update_corporation", spec=True)
    @patch(TASKS_PATH + ".update_character", spec=True)
    def test_update_all_ledger(
        self,
        mock_update_character: MagicMock,
        mock_update_corporation: MagicMock,
    ):
        """
        Test 'update_all_ledger' task.

        # Test Scenarios:
            1. Task queues update tasks for all active corporation and character owners.
        """
        # Test Data
        create_owner_from_user(user=self.user)
        create_owner_from_user(user=self.user, owner_type="corporation")

        # Test Action
        update_all_corporations(force_refresh=False)
        update_all_characters(force_refresh=False)

        # Expected Result
        self.assertTrue(mock_update_character.apply_async.called)
        self.assertTrue(mock_update_corporation.apply_async.called)

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(TASKS_PATH + ".logger")
    @patch(TASKS_PATH + ".update_corp_wallet_journal")
    @patch(
        TASKS_PATH + ".CorporationUpdateSection.get_sections",
        lambda: ["wallet_journal"],
    )
    def test_update_corporation(
        self, mock_update_corp_wallet: MagicMock, mock_logger: MagicMock
    ):
        """
        Test 'update_corporation' task.

        # Test Scenarios:
            1. Task updates corporation owner data (only wallet).
            2. Task no need update when data is fresh.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, owner_type="corporation")

        # Test Action
        update_corporation(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.corporation_name
        )

        # Setup for Scenario 2: No update needed
        mock_update_corp_wallet.reset_mock()
        create_update_status(
            owner=owner,
            section="wallet_journal",
            is_success=True,
            owner_type="corporation",
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_corporation(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with(
            "No updates needed for %s", owner.corporation_name
        )
        mock_update_corp_wallet.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".CorporationOwner.update_manager", new_callable=PropertyMock)
    @patch(MODELS_PATH + ".CorporationOwner.objects.get")
    def test_update_corp_section(
        self, mock_corp_owner_get, mock_update_manager_property
    ):
        """
        Test update of a corporation section.

        Results:
            - CorporationUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, owner_type="corporation")
        dummy_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data="Dummy Data",
        )
        update_status = CorporationUpdateStatus.objects.filter(
            owner=owner, section="wallet_journal"
        ).first()

        mock_corp_owner_get.return_value = owner
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager
        mock_update_manager.perform_update_status.return_value = dummy_result

        def _mock_update_section_log(section, result):
            create_update_status(
                owner=owner,
                owner_type="corporation",
                section=section,
                has_token_error=result.has_token_error,
                is_success=not result.has_token_error,
                error_message=result.error_message,
            )

        mock_update_manager.update_section_log.side_effect = _mock_update_section_log

        # Test Action
        _update_corporation_section(
            task=MagicMock(),
            eve_id=owner.eve_id,
            section="wallet_journal",
            force_refresh=False,
        )

        # Expected Results
        new_update_status = CorporationUpdateStatus.objects.get(
            owner=owner, section="wallet_journal"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(TASKS_PATH + ".logger")
    @patch(TASKS_PATH + ".update_char_wallet_journal")
    @patch(
        TASKS_PATH + ".CharacterUpdateSection.get_sections", lambda: ["wallet_journal"]
    )
    def test_update_character(
        self, mock_update_wallet_journal: MagicMock, mock_logger: MagicMock
    ):
        """
        Test 'update_character' task.

        # Test Scenarios:
            1. Task updates character owner data (only wallet).
            2. Task no need update when data is fresh.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, owner_type="character")

        # Test Action
        update_character(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.character_name
        )

        # Setup for Scenario 2: No update needed
        mock_update_wallet_journal.reset_mock()
        create_update_status(
            owner=owner,
            owner_type="character",
            section="wallet_journal",
            is_success=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        update_character(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.info.assert_called_with(
            "No updates needed for %s", owner.character_name
        )
        mock_update_wallet_journal.assert_not_called()
        # Ensure update manager reports no update needed
        self.assertFalse(owner.update_manager.calc_update_needed())

    @patch(MODELS_PATH + ".CharacterOwner.update_manager", new_callable=PropertyMock)
    @patch(MODELS_PATH + ".CharacterOwner.objects.get")
    def test_update_character_section(
        self, mock_owner_get, mock_update_manager_property
    ):
        """
        Test update of a character section.

        Results:
            - CharacterUpdateStatus is created/updated correctly.
        """
        # Test Data
        owner = create_owner_from_user(user=self.user, owner_type="character")
        token = self.user.token_set.first()
        owner.get_token = MagicMock(return_value=token)
        dummy_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data="Dummy Data",
        )
        update_status = CharacterUpdateStatus.objects.filter(
            owner=owner, section=""
        ).first()

        mock_owner_get.return_value = owner
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager
        mock_update_manager.perform_update_status.return_value = dummy_result

        def _mock_update_section_log(section, result):
            create_update_status(
                owner=owner,
                owner_type="character",
                section=section,
                has_token_error=result.has_token_error,
                is_success=not result.has_token_error,
                error_message=result.error_message,
            )

        mock_update_manager.update_section_log.side_effect = _mock_update_section_log

        # Test Action
        _update_character_section(
            task=MagicMock(),
            eve_id=owner.eve_id,
            section="wallet_journal",
            force_refresh=False,
        )

        # Expected Results
        new_update_status = CharacterUpdateStatus.objects.get(
            owner=owner, section="wallet_journal"
        )
        self.assertEqual(update_status, None)
        self.assertEqual(new_update_status.has_token_error, False)
        self.assertEqual(new_update_status.is_success, True)
