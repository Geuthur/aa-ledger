# Standard Library
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import MagicMock

# Third Party
from aiopenapi3 import RequestError

# Django
from django.utils import timezone

# Alliance Auth
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Ledger
from ledger.app_settings import LEDGER_STALE_TYPES
from ledger.models.characteraudit import CharacterUpdateStatus
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    UpdateManager,
    UpdateSectionResult,
)
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CharacterUpdateStatusFactory,
)


class TestUpdateManager(LedgerTestCase):
    """Unit tests for UpdateManager and update status behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CharacterOwnerFactory(user=cls.user)
        cls.manager = cls.owner.update_manager

    def test_need_update_should_return_false_when_has_token_error(self):
        # Test Data
        status = CharacterUpdateStatusFactory(
            owner=self.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            has_token_error=True,
            last_run_finished_at=timezone.now() - timedelta(hours=5),
        )

        # Test Action
        needs_update = status.need_update()

        # Expected Result
        self.assertFalse(needs_update)

    def test_need_update_should_return_true_when_never_run(self):
        # Test Data
        status = CharacterUpdateStatusFactory(
            owner=self.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            has_token_error=False,
            last_run_finished_at=None,
        )

        # Test Action
        needs_update = status.need_update()

        # Expected Result
        self.assertTrue(needs_update)

    def test_need_update_should_return_false_when_within_cache_duration(self):
        # Test Data: Wallet journal cache is 60 minutes, run 10 minutes ago
        status = CharacterUpdateStatusFactory(
            owner=self.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            has_token_error=False,
            last_run_finished_at=timezone.now() - timedelta(minutes=10),
        )

        # Test Action
        needs_update = status.need_update()

        # Expected Result
        self.assertFalse(needs_update)

    def test_need_update_should_return_true_when_beyond_cache_duration(self):
        # Test Data: Planetary cache is 10 minutes, run 15 minutes ago
        status = CharacterUpdateStatusFactory(
            owner=self.owner,
            section=CharacterUpdateSection.PLANETS,
            has_token_error=False,
            last_run_finished_at=timezone.now() - timedelta(minutes=15),
        )

        # Test Action
        needs_update = status.need_update()

        # Expected Result
        self.assertTrue(needs_update)

    def test_update_section_if_changed_should_handle_http_304_not_modified(self):
        # Test Data
        def mock_fetch(owner, force_refresh):
            raise HTTPNotModified(HTTPStatus.NOT_MODIFIED, {})

        # Test Action
        result = self.manager.update_section_if_changed(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            fetch_func=mock_fetch,
            force_refresh=False,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertEqual(result.error_message, "")

    def test_update_section_if_changed_should_set_token_error_on_http_403(self):
        # Test Data
        def mock_fetch(owner, force_refresh):
            raise HTTPClientError(HTTPStatus.FORBIDDEN, {}, b"Forbidden")

        # Test Action
        result = self.manager.update_section_if_changed(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            fetch_func=mock_fetch,
            force_refresh=False,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertTrue(result.has_token_error)
        self.assertIn("HTTPClientError (403)", result.error_message)

    def test_update_section_if_changed_should_not_set_token_error_on_http_400(self):
        # Test Data
        def mock_fetch(owner, force_refresh):
            raise HTTPClientError(HTTPStatus.BAD_REQUEST, {}, b"Bad Request")

        # Test Action
        result = self.manager.update_section_if_changed(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            fetch_func=mock_fetch,
            force_refresh=False,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertIn("HTTPClientError (400)", result.error_message)

    def test_perform_update_status_should_catch_token_error_without_raising(self):
        # Test Data
        mock_method = MagicMock(side_effect=TokenError("Token expired"))

        # Test Action
        result = self.manager.perform_update_status(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            method=mock_method,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertTrue(result.has_token_error)
        self.assertIn("TokenError: Token expired", result.error_message)

    def test_perform_update_status_should_catch_server_error_without_token_error(self):
        # Test Data
        mock_method = MagicMock(
            side_effect=HTTPServerError(HTTPStatus.BAD_GATEWAY, {}, b"Bad Gateway")
        )

        # Test Action
        result = self.manager.perform_update_status(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            method=mock_method,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertIn("502", result.error_message)

    def test_perform_update_status_should_catch_http_504_gateway_timeout(self):
        # Test Data
        mock_method = MagicMock(
            side_effect=HTTPServerError(
                HTTPStatus.GATEWAY_TIMEOUT, {}, b"Timeout contacting tranquility"
            )
        )

        # Test Action
        result = self.manager.perform_update_status(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            method=mock_method,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertIn("504", result.error_message)

    def test_perform_update_status_should_catch_request_error(self):
        # Test Data
        mock_method = MagicMock(
            side_effect=RequestError(
                operation=None,
                request=None,
                data="Request failed",
                parameters={},
            )
        )

        # Test Action
        result = self.manager.perform_update_status(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            method=mock_method,
        )

        # Expected Result
        self.assertFalse(result.is_changed)
        self.assertFalse(result.is_updated)
        self.assertFalse(result.has_token_error)
        self.assertIn("RequestError", result.error_message)

    def test_update_section_log_should_record_success_on_http_304(self):
        # Test Data
        result_304 = UpdateSectionResult(
            is_changed=False,
            is_updated=False,
            has_token_error=False,
            error_message="",
        )

        # Test Action
        self.manager.update_section_log(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            result=result_304,
        )

        # Expected Result
        status = CharacterUpdateStatus.objects.get(
            owner=self.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
        )
        self.assertTrue(status.is_success)
        self.assertFalse(status.has_token_error)
        self.assertEqual(status.error_message, "")
        self.assertIsNotNone(status.last_run_finished_at)

    def test_get_sections_to_update_force_refresh_should_return_all(self):
        """Test that force_refresh=True resets token errors and returns all sections."""
        # Test Data
        CharacterUpdateStatusFactory(
            owner=self.owner,
            section=CharacterUpdateSection.WALLET_JOURNAL,
            has_token_error=True,
        )

        # Test Action
        sections = self.manager.get_sections_to_update(force_refresh=True)

        # Expected Result
        self.assertEqual(sections, CharacterUpdateSection.get_sections())
        status = CharacterUpdateStatus.objects.get(
            owner=self.owner, section=CharacterUpdateSection.WALLET_JOURNAL
        )
        self.assertFalse(status.has_token_error)

    def test_get_sections_to_update_when_needed_should_return_stale_sections(self):
        """Test that get_sections_to_update returns sections needing update."""
        # Test Data
        CharacterUpdateStatus.objects.filter(owner=self.owner).delete()

        # Test Action
        sections = self.manager.get_sections_to_update(force_refresh=False)

        # Expected Result
        self.assertEqual(len(sections), len(CharacterUpdateSection.get_sections()))

    def test_execute_section_should_call_owner_method_and_log_success(self):
        """Test that execute_section runs owner method and records update status."""
        # Test Data
        expected_result = UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            has_token_error=False,
            error_message="",
            data={"test": "data"},
        )
        self.owner.update_wallet_journal = MagicMock(return_value=expected_result)

        # Test Action
        result = self.manager.execute_section(
            CharacterUpdateSection.WALLET_JOURNAL, force_refresh=True
        )

        # Expected Result
        self.assertEqual(result, expected_result)
        self.owner.update_wallet_journal.assert_called_once()
        status = CharacterUpdateStatus.objects.get(
            owner=self.owner, section=CharacterUpdateSection.WALLET_JOURNAL
        )
        self.assertTrue(status.is_success)
        self.assertFalse(status.has_token_error)

    def test_mixin_provides_update_manager_and_shortcuts(self):
        """Test that UpdateManagerMixin provides update_manager and shortcut methods."""
        # Test Data & Action & Expected Result
        self.assertIsNotNone(self.owner.update_manager)
        self.assertEqual(self.owner.update_manager.owner, self.owner)
        sections = self.owner.get_sections_to_update(force_refresh=True)
        self.assertEqual(sections, CharacterUpdateSection.get_sections())
