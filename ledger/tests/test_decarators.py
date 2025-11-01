# Standard Library
from unittest.mock import patch

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger import __title__
from ledger.decorators import (
    log_timing,
    when_esi_is_available,
)

DECORATOR_PATH = "ledger.decorators."


@patch(DECORATOR_PATH + "ESI_STATUS_ROUTE_RATE_LIMIT", new=1)
class TestDecorators(NoSocketsTestCase):
    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "IS_TESTING", new=True)
    def test_when_esi_is_available_is_test(self, mock_fetch_esi_status):
        """Test when ESI is available in testing mode."""

        @when_esi_is_available
        def trigger_esi_deco():
            return "Testing Mode."

        # when
        result = trigger_esi_deco()
        # then
        self.assertEqual(result, "Testing Mode.")

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_ok(self, mock_fetch_esi_status):
        """Test when ESI is available in non-testing mode."""

        # ensure the fetch_esi_status call reports ESI as up
        mock_fetch_esi_status.return_value.is_ok = True

        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_called_once()
        self.assertEqual(result, "Esi is Available")

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_not_ok(self, mock_fetch_esi_status):
        """Test when ESI is not available in non-testing mode."""
        # ensure the fetch_esi_status call reports ESI as down
        mock_fetch_esi_status.return_value.is_ok = False

        @when_esi_is_available
        def trigger_esi_deco():
            return None

        # when
        result = trigger_esi_deco()
        # then
        self.assertIsNone(result)

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_ok_and_cached(self, mock_fetch_esi_status):
        """Test when ESI is available in non-testing mode and cached."""
        # Make a Exception to ensure fetch_esi_status is not called
        mock_fetch_esi_status.side_effect = Exception("Should not be called")

        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_not_called()
        self.assertEqual(result, "Esi is Available")

    def test_log_timing(self):
        # given
        logger = LoggerAddTag(get_extension_logger(__name__), __title__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # when
        result = trigger_log_timing()
        # then
        self.assertEqual(result, "Log Timing")
