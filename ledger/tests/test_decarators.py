# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.decorators import (
    acquire_lock_or_wait_for_cache,
    log_timing,
    when_esi_is_available,
)

DECORATOR_PATH = "ledger.decorators."


@patch(DECORATOR_PATH + "ESI_STATUS_ROUTE_RATE_LIMIT", new=1)
class TestDecorators(TestCase):
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
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_ok(self, mock_get_redis_client, mock_fetch_esi_status):
        """Test when ESI is available in non-testing mode."""
        # make the redis client behave as if no cache is set and we can acquire the lock
        redis_client = MagicMock()
        redis_client.get.return_value = None
        # simulate that we acquired the lock so the live check runs
        redis_client.set.return_value = True
        redis_client.setex.return_value = None
        mock_get_redis_client.return_value = redis_client

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
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_not_ok(self, mock_get_redis_client, mock_fetch_esi_status):
        """Test when ESI is not available in non-testing mode."""
        # make the redis client behave as if no cache is set and we can acquire the lock
        redis_client = MagicMock()
        redis_client.get.return_value = None
        redis_client.set.return_value = True
        redis_client.setex.return_value = None
        mock_get_redis_client.return_value = redis_client

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
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_ok_and_cached(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test when ESI is available in non-testing mode and cached."""
        redis_client = MagicMock()
        redis_client.get.return_value = "1"
        mock_get_redis_client.return_value = redis_client

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

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_when_esi_is_ok_and_not_acquired(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test when ESI is available in non-testing mode and not acquired."""
        redis_client = MagicMock()
        redis_client.get.return_value = None
        # simulate that we did not acquire the lock so the wait runs
        redis_client.set.return_value = False
        redis_client.setex.return_value = None
        mock_get_redis_client.return_value = redis_client
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
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_wait_for_lock_or_cache_when_cache_available(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test wait_for_lock_or_cache when cache is available."""
        # make the redis client behave as if cache is set
        redis_client = MagicMock()
        redis_client.get.return_value = "1"
        mock_get_redis_client.return_value = redis_client

        result, cache_available = acquire_lock_or_wait_for_cache(redis_client)
        # then
        self.assertFalse(result)
        self.assertTrue(cache_available)

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_wait_for_lock_or_cache_when_lock_acquired(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test wait_for_lock_or_cache when lock is acquired."""
        # make the redis client behave as if no cache is set and we can acquire the lock
        redis_client = MagicMock()
        redis_client.get.return_value = None
        redis_client.set.return_value = True
        redis_client.setex.return_value = None
        mock_get_redis_client.return_value = redis_client

        result, cache_available = acquire_lock_or_wait_for_cache(redis_client)
        # then
        self.assertTrue(result)
        self.assertFalse(cache_available)

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_wait_for_lock_or_cache_redis_lock_not_acquired(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test wait_for_lock_or_cache when lock is not acquired ."""
        # make the redis client behave as if no cache is set and we can acquire the lock
        redis_client = MagicMock()
        redis_client.get.return_value = None
        redis_client.set.return_value = False
        redis_client.setex.return_value = None
        mock_get_redis_client.return_value = redis_client

        result, cache_available = acquire_lock_or_wait_for_cache(redis_client)
        # then
        self.assertFalse(result)
        self.assertFalse(cache_available)

    @patch(DECORATOR_PATH + "fetch_esi_status")
    @patch(DECORATOR_PATH + "get_redis_client")
    @patch(DECORATOR_PATH + "IS_TESTING", new=False)
    def test_wait_for_lock_or_cache_when_redis_get_raises_exception(
        self, mock_get_redis_client, mock_fetch_esi_status
    ):
        """Test wait_for_lock_or_cache when redis_client.get raises exceptions."""
        redis_client = MagicMock()
        # Make get() raise an exception to hit the except branch inside the poll loop
        redis_client.get.side_effect = Exception("Simulated Redis GET Error")
        # ensure set() doesn't unexpectedly break the flow if called
        redis_client.set.return_value = False
        mock_get_redis_client.return_value = redis_client

        result, cache_available = acquire_lock_or_wait_for_cache(redis_client)

        self.assertFalse(result)
        self.assertFalse(cache_available)

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
