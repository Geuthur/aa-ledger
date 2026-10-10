"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, PropertyMock, patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# AA Ledger
from ledger.models import CharacterOwner
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
    update_subset_characters,
    update_user_characters,
)
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterUpdateStatusFactory,
    CorporationOwnerFactory,
    CorporationUpdateStatusFactory,
    UserMainFactory,
)

TASKS_PATH = "ledger.tasks"
MANAGERS_PATH = "ledger.managers"
MODELS_PATH = "ledger.models"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestTasks(LedgerTestCase):
    """
    Tests for ledger tasks.
    """

    @patch(TASKS_PATH + ".update_corporation", spec=True)
    @patch(TASKS_PATH + ".update_character", spec=True)
    @patch(TASKS_PATH + ".CharacterMiningLedger.update_evemarket_price", spec=True)
    def test_update_all_ledger(
        self,
        mock_update_evemarket_price: MagicMock,
        mock_update_character: MagicMock,
        mock_update_corporation: MagicMock,
    ):
        """
        Test 'update_all_ledger' task.

        # Test Scenarios:
            1. Task queues update tasks for all active corporation and character owners.
        """
        # Test Data
        CharacterOwnerFactory(user=self.user)
        CorporationOwnerFactory(user=self.user)

        # Test Action
        update_all_corporations(force_refresh=False)
        update_all_characters(force_refresh=False)

        # Expected Result
        self.assertTrue(mock_update_character.apply_async.called)
        self.assertTrue(mock_update_corporation.apply_async.called)

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
        owner = CorporationOwnerFactory(user=self.user)

        # Test Action
        update_corporation(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.corporation_name
        )

        # Setup for Scenario 2: No update needed
        mock_update_corp_wallet.reset_mock()
        CorporationUpdateStatusFactory(
            owner=owner,
            section="wallet_journal",
            is_success=True,
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
        owner = CorporationOwnerFactory(user=self.user)
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
            CorporationUpdateStatusFactory(
                owner=owner,
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
        owner = CharacterOwnerFactory(user=self.user)

        # Test Action
        update_character(eve_id=owner.eve_id, force_refresh=False)

        # Expected Result
        mock_logger.debug.assert_called_with(
            "Queued %s Audit Updates for %s", 1, owner.character_name
        )

        # Setup for Scenario 2: No update needed
        mock_update_wallet_journal.reset_mock()
        CharacterUpdateStatusFactory(
            owner=owner,
            section="wallet_journal",
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
        owner = CharacterOwnerFactory(user=self.user)
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
            CharacterUpdateStatusFactory(
                owner=owner,
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

    @patch(TASKS_PATH + ".update_character")
    @patch(TASKS_PATH + ".CharacterMiningLedger.update_evemarket_price")
    def test_update_subset_characters_should_group_by_user(
        self, mock_price: MagicMock, mock_update_character: MagicMock
    ):
        """Test that update_subset_characters groups characters by user and queues all alts together."""
        # Test Data
        user_1 = UserMainFactory()
        main_1 = CharacterOwnerFactory(user=user_1)
        alt_1_char = EveCharacterFactory()
        add_character_to_user(
            user=user_1,
            character=alt_1_char,
            is_main=False,
            scopes=CharacterOwner.get_esi_scopes(),
        )
        alt_1 = CharacterOwnerFactory(
            eve_character=alt_1_char,
            character_name=alt_1_char.character_name,
        )

        user_2 = UserMainFactory()
        main_2 = CharacterOwnerFactory(user=user_2)

        # Test Action
        update_subset_characters(subset=1, min_runs=1, max_runs=10, force_refresh=True)

        # Expected Result
        queued_ids = [
            call.kwargs["args"][0]
            for call in mock_update_character.apply_async.call_args_list
        ]
        self.assertIn(main_1.eve_id, queued_ids)
        self.assertIn(alt_1.eve_id, queued_ids)
        self.assertIn(main_2.eve_id, queued_ids)

    @patch(TASKS_PATH + ".update_character")
    def test_update_user_characters_should_queue_all_active_characters(
        self, mock_update_character: MagicMock
    ):
        """Test that update_user_characters queues all active characters for a specific user."""
        # Test Data
        user = UserMainFactory()
        main = CharacterOwnerFactory(user=user)
        alt_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=alt_char,
            is_main=False,
            scopes=CharacterOwner.get_esi_scopes(),
        )
        alt = CharacterOwnerFactory(
            eve_character=alt_char,
            character_name=alt_char.character_name,
            active=True,
        )
        inactive_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=inactive_char,
            is_main=False,
            scopes=CharacterOwner.get_esi_scopes(),
        )
        CharacterOwnerFactory(
            eve_character=inactive_char,
            character_name=inactive_char.character_name,
            active=False,
        )

        # Test Action
        update_user_characters(user_id=user.id, force_refresh=True)

        # Expected Result
        queued_ids = [
            call.kwargs["args"][0]
            for call in mock_update_character.apply_async.call_args_list
        ]
        self.assertIn(main.eve_id, queued_ids)
        self.assertIn(alt.eve_id, queued_ids)
        self.assertEqual(len(queued_ids), 2)

    @patch(TASKS_PATH + ".update_char_wallet_journal")
    @patch(TASKS_PATH + ".update_character.apply_async")
    @patch(
        TASKS_PATH + ".CharacterUpdateSection.get_sections",
        lambda: ["wallet_journal"],
    )
    def test_update_character_with_update_alts_should_queue_alts(
        self, mock_apply_async: MagicMock, mock_update_wallet_journal: MagicMock
    ):
        """Test that update_character queues active alts when update_alts=True."""
        # Test Data
        user = UserMainFactory()
        main = CharacterOwnerFactory(user=user)
        alt_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=alt_char,
            is_main=False,
            scopes=CharacterOwner.get_esi_scopes(),
        )
        alt = CharacterOwnerFactory(
            eve_character=alt_char,
            character_name=alt_char.character_name,
            active=True,
        )

        # Test Action
        update_character(eve_id=main.eve_id, force_refresh=True, update_alts=True)

        # Expected Result
        mock_apply_async.assert_called_once_with(
            args=[alt.eve_id],
            kwargs={"force_refresh": True, "update_alts": False},
            priority=7,
        )
