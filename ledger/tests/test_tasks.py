"""Tests for the providers module."""

# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, PropertyMock, patch

# Third Party
import pook
from aiopenapi3 import RequestError
from celery.exceptions import Retry

# Django
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)

# Alliance Auth (External Libs)
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# AA Ledger
from ledger import tasks
from ledger.errors import DownTimeError
from ledger.models import CharacterOwner
from ledger.models.characteraudit import CharacterUpdateStatus
from ledger.models.corporationaudit import CorporationUpdateStatus
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    CorporationUpdateSection,
    UpdateSectionResult,
    UpdateStatus,
)
from ledger.providers import DOWNTIME_TIMER
from ledger.tasks import (
    _update_character_section,
    _update_corporation_section,
    check_planetary_alarms,
    update_all_characters,
    update_all_corporations,
    update_character,
    update_corporation,
    update_subset_characters,
    update_user_characters,
)
from ledger.tests import AuthTestCase
from ledger.tests.testdata.esi import (
    clear_esi_limits,
    markets_prices_url,
    wallet_journal_url,
)
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterPlanetDetailsFactory,
    CharacterUpdateStatusFactory,
    CorporationOwnerFactory,
    CorporationUpdateStatusFactory,
    UserMainFactory,
)

TASKS_PATH = "ledger.tasks"
MANAGERS_PATH = "ledger.managers"
MODELS_PATH = "ledger.models"


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    DISABLE_DAILY_DOWNTIME_CHECK=True,
)
class TestTasks(AuthTestCase):
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
        CorporationUpdateStatus.objects.filter(
            owner=owner, section="wallet_journal"
        ).first()

        mock_corp_owner_get.return_value = owner
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager
        mock_update_manager.execute_section.return_value = dummy_result

        # Test Action
        res = _update_corporation_section(
            task=MagicMock(),
            eve_id=owner.eve_id,
            section="wallet_journal",
            force_refresh=False,
        )

        # Expected Results
        self.assertEqual(res, dummy_result)
        mock_update_manager.execute_section.assert_called_once_with(
            CorporationUpdateSection.WALLET_JOURNAL, force_refresh=False
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
        CharacterUpdateStatus.objects.filter(owner=owner, section="").first()

        mock_owner_get.return_value = owner
        mock_update_manager = MagicMock()
        mock_update_manager_property.return_value = mock_update_manager
        mock_update_manager.execute_section.return_value = dummy_result

        # Test Action
        res = _update_character_section(
            task=MagicMock(),
            eve_id=owner.eve_id,
            section="wallet_journal",
            force_refresh=False,
        )

        # Expected Results
        self.assertEqual(res, dummy_result)
        mock_update_manager.execute_section.assert_called_once_with(
            CharacterUpdateSection.WALLET_JOURNAL, force_refresh=False
        )

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

    @patch(TASKS_PATH + ".send_user_notification", spec=True)
    def test_check_planetary_alarms_should_notify_with_plain_message(
        self, mock_send: MagicMock
    ):
        """Test that expired planets are sent as one plain text message."""
        # Test Data
        user = UserMainFactory()
        owner = CharacterOwnerFactory(user=user)
        details = CharacterPlanetDetailsFactory(
            character=owner, planet__character=owner, notification=True
        )

        # Test Action
        check_planetary_alarms()

        # Expected Result
        mock_send.delay.assert_called_once()
        kwargs = mock_send.delay.call_args.kwargs
        self.assertEqual(kwargs["user_id"], user.id)
        self.assertIn(details.planet.eve_planet.name, kwargs["message"])
        details.refresh_from_db()
        self.assertTrue(details.notification_sent)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    DISABLE_DAILY_DOWNTIME_CHECK=True,
)
@patch(TASKS_PATH + ".CharacterUpdateSection.get_sections", lambda: ["wallet_journal"])
@patch.object(tasks.update_character, "retry", side_effect=Retry)
class TestUpdateCharacterEsiRetry(AuthTestCase):
    """ESI errors of a section retry `update_character` through the UpdateManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CharacterOwnerFactory(user=cls.user)

    def setUp(self):
        super().setUp()
        clear_esi_limits(self.owner)
        self.addCleanup(clear_esi_limits, self.owner)

    def _assert_retried(self, mock_retry, exc_type, countdown_min: float):
        mock_retry.assert_called_once()
        kwargs = mock_retry.call_args.kwargs
        self.assertIsInstance(kwargs["exc"], exc_type)
        self.assertGreaterEqual(kwargs["countdown"], countdown_min)
        status = CharacterUpdateStatus.objects.get(
            owner=self.owner, section=CharacterUpdateSection.WALLET_JOURNAL
        )
        self.assertFalse(status.is_success)
        self.assertTrue(status.error_message.startswith(exc_type.__name__))

    def test_should_retry_on_esi_server_errors(self, mock_retry):
        for status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                mock_retry.reset_mock()
                pook.get(
                    wallet_journal_url(self.owner),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                with self.assertRaises(Retry):
                    tasks.update_character(self.owner.eve_id)

                # Expected Result
                self._assert_retried(mock_retry, HTTPServerError, DOWNTIME_TIMER)

    @pook.on
    def test_should_retry_on_the_esi_error_limit(self, mock_retry):
        # Test Data
        pook.get(
            wallet_journal_url(self.owner),
            reply=420,
            response_json={"error": "Error limited"},
            response_headers={"X-RateLimit-Reset": "30"},
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, ESIErrorLimitException, 30)

    @pook.on
    def test_should_retry_on_the_esi_bucket_limit(self, mock_retry):
        # Test Data: the wallet bucket of the character is used up
        cache.set(f"esi:bucket:char-wallet:{self.owner.eve_id}", 0, timeout=900)

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, ESIBucketLimitException, 1)

    @pook.on
    @patch("esi.app_settings.ESI_SERVER_ERROR_MAX_RETRIES", 1)
    def test_should_retry_on_request_errors(self, mock_retry):
        # Test Data
        pook.get(wallet_journal_url(self.owner)).error(
            ConnectionError("Connection reset")
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, RequestError, DOWNTIME_TIMER)

    @patch(TASKS_PATH + ".CharacterOwner.update_wallet_journal", autospec=True)
    def test_should_retry_on_downtime_errors_of_a_section(
        self, mock_update_wallet_journal, mock_retry
    ):
        # Test Data
        mock_update_wallet_journal.side_effect = DownTimeError(
            "ESI is in daily downtime"
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.owner.eve_id)

        # Expected Result
        self._assert_retried(mock_retry, DownTimeError, DOWNTIME_TIMER)

    def test_should_record_other_esi_errors_without_retry(self, mock_retry):
        for status_code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.NOT_FOUND]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                pook.get(
                    wallet_journal_url(self.owner),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                result = tasks.update_character(self.owner.eve_id)

                # Expected Result
                self.assertTrue(result)
                mock_retry.assert_not_called()
                status = CharacterUpdateStatus.objects.get(
                    owner=self.owner, section=CharacterUpdateSection.WALLET_JOURNAL
                )
                self.assertFalse(status.is_success)
                self.assertIn(str(status_code.value), status.error_message)
                self.assertEqual(self.owner.get_status, UpdateStatus.ERROR)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    DISABLE_DAILY_DOWNTIME_CHECK=True,
)
@patch(
    TASKS_PATH + ".CorporationUpdateSection.get_sections",
    lambda: ["wallet_division_names"],
)
@patch.object(tasks.update_corporation, "retry", side_effect=Retry)
class TestUpdateCorporationEsiRetry(AuthTestCase):
    """ESI errors of a section retry `update_corporation` through the UpdateManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CorporationOwnerFactory(user=cls.user)

    @patch(TASKS_PATH + ".CorporationOwner.update_wallet_division_names", autospec=True)
    def test_should_retry_on_retryable_esi_errors(self, mock_update, mock_retry):
        for exc in [
            HTTPServerError(HTTPStatus.SERVICE_UNAVAILABLE, {}, b"Unavailable"),
            DownTimeError("ESI is in daily downtime"),
        ]:
            with self.subTest(exc=type(exc).__name__):
                # Test Data
                mock_retry.reset_mock()
                mock_update.side_effect = exc

                # Test Action
                with self.assertRaises(Retry):
                    tasks.update_corporation(self.owner.eve_id, force_refresh=True)

                # Expected Result
                mock_retry.assert_called_once()
                self.assertIs(mock_retry.call_args.kwargs["exc"], exc)
                status = CorporationUpdateStatus.objects.get(
                    owner=self.owner,
                    section=CorporationUpdateSection.WALLET_DIVISION_NAMES,
                )
                self.assertFalse(status.is_success)

    @patch(TASKS_PATH + ".CorporationOwner.update_wallet_division_names", autospec=True)
    def test_should_record_other_errors_without_retry(self, mock_update, mock_retry):
        # Test Data
        mock_update.side_effect = HTTPServerError(
            HTTPStatus.INTERNAL_SERVER_ERROR, {}, b"Internal Server Error"
        )

        # Test Action
        result = tasks.update_corporation(self.owner.eve_id, force_refresh=True)

        # Expected Result
        self.assertTrue(result)
        mock_retry.assert_not_called()
        status = CorporationUpdateStatus.objects.get(
            owner=self.owner, section=CorporationUpdateSection.WALLET_DIVISION_NAMES
        )
        self.assertFalse(status.is_success)
        self.assertIn("500", status.error_message)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    DISABLE_DAILY_DOWNTIME_CHECK=True,
)
class TestUpdateMarketPricesEsiRetry(AuthTestCase):
    """ESI errors of the market prices retry the character queue tasks."""

    def setUp(self):
        super().setUp()
        cache.delete("esi_error_limit_reset")

    @patch(TASKS_PATH + ".update_character", spec=True)
    def test_should_retry_on_esi_server_errors(self, mock_update_character):
        for task in [tasks.update_all_characters, tasks.update_subset_characters]:
            with (
                self.subTest(task=task.name),
                pook.use(),
                patch.object(task, "retry", side_effect=Retry) as mock_retry,
            ):
                # Test Data
                pook.get(
                    markets_prices_url(),
                    reply=HTTPStatus.SERVICE_UNAVAILABLE,
                    response_json={"error": "Service Unavailable"},
                )

                # Test Action
                with self.assertRaises(Retry):
                    task()

                # Expected Result
                mock_retry.assert_called_once()
                self.assertIsInstance(
                    mock_retry.call_args.kwargs["exc"], HTTPServerError
                )
                mock_update_character.apply_async.assert_not_called()
