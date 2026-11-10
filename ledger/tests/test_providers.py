"""Tests for the providers module."""

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
from aiopenapi3 import RequestError

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPClientError,
    HTTPServerError,
)

# AA Ledger
from ledger.errors import DownTimeError
from ledger.providers import esi, retry_task_on_esi_error
from ledger.tests import NoSocketsTestCase

MODULE_PATH = "ledger.providers"


class TestEsiClient(NoSocketsTestCase):
    @override_settings(DEBUG=False)
    def test_client_loads_with_debug_disabled(self):
        # when
        client = esi.client
        # then
        self.assertTrue(hasattr(client.Market, "GetMarketsPrices"))


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRetryTaskOnESIError(NoSocketsTestCase):
    """Tests for retry_task_on_esi_error context manager."""

    def setUp(self):
        super().setUp()
        self.task = MagicMock()
        self.task.request.retries = 1
        self.task.retry = MagicMock(side_effect=Exception("Retry called"))

    def _assert_retried(self, exc, countdown):
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], countdown)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_esi_error_limit_exception(self, mock_random):
        # Test Data
        mock_random.return_value = 3.0
        exc = ESIErrorLimitException(60.0)

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self._assert_retried(exc, 63)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_esi_bucket_limit_exception(self, mock_random):
        # Test Data
        mock_random.return_value = 4.0
        exc = ESIBucketLimitException(bucket="test_bucket", reset=30.0)

        # Test Action
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self._assert_retried(exc, 34)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_http_server_errors(self, mock_random):
        for status_code in (502, 503, 504):
            with self.subTest(status_code=status_code):
                # Test Data
                mock_random.return_value = 2.5
                self.task.retry.reset_mock()
                exc = HTTPServerError(status_code, {}, b"Server Error")

                # Test Action
                with self.assertRaises(Exception):
                    with retry_task_on_esi_error(self.task):
                        raise exc

                # Expected Result
                self._assert_retried(exc, 602)

    def test_should_not_retry_on_other_http_server_errors(self):
        # Test Data
        exc = HTTPServerError(500, {}, b"Internal Server Error")

        # Test Action
        with self.assertRaises(HTTPServerError):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.task.retry.assert_not_called()

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_request_error(self, mock_random):
        # Test Data
        mock_random.return_value = 2.0
        exc = RequestError(operation=None, request=None, data="Test", parameters={})

        # Test Action
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self._assert_retried(exc, 602)

    def test_should_not_retry_on_http_client_errors(self):
        for status_code in (400, 404):
            with self.subTest(status_code=status_code):
                # Test Data
                exc = HTTPClientError(status_code, {}, b"Client Error")

                # Test Action
                with self.assertRaises(HTTPClientError) as context:
                    with retry_task_on_esi_error(self.task):
                        raise exc

                # Expected Result
                self.task.retry.assert_not_called()
                self.assertEqual(context.exception.status_code, status_code)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_apply_backoff_jitter_on_retries(self, mock_random):
        # Test Data
        mock_random.return_value = 4.0
        self.task.request.retries = 2
        exc = ESIErrorLimitException(60.0)

        # Test Action
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self._assert_retried(exc, 76)

    def test_should_pass_through_on_success(self):
        # Test Action
        with retry_task_on_esi_error(self.task):
            result = "success"

        # Expected Result
        self.assertEqual(result, "success")
        self.task.retry.assert_not_called()

    def test_should_pass_through_unhandled_exceptions(self):
        # Test Data
        exc = ValueError("Some other error")

        # Test Action
        with self.assertRaises(ValueError):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.task.retry.assert_not_called()

    @override_settings(DISABLE_DAILY_DOWNTIME_CHECK=False)
    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_daily_downtime(self, mock_random):
        # Test Data
        mock_random.return_value = 3.0
        with patch(MODULE_PATH + ".timezone.now") as mock_now:
            mock_now.return_value = timezone.datetime.strptime("11:05", "%H:%M")

            # Test Action
            with self.assertRaises(Exception) as context:
                with retry_task_on_esi_error(self.task):
                    raise ValueError("never reached")

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        call_kwargs = self.task.retry.call_args[1]
        self.assertIsInstance(call_kwargs["exc"], DownTimeError)
        self.assertEqual(call_kwargs["countdown"], 603)

    @override_settings(DISABLE_DAILY_DOWNTIME_CHECK=True)
    def test_should_skip_the_downtime_check_when_disabled(self):
        # Test Data
        with patch(MODULE_PATH + ".timezone.now") as mock_now:
            mock_now.return_value = timezone.datetime.strptime("11:05", "%H:%M")

            # Test Action
            with retry_task_on_esi_error(self.task):
                result = "success"

        # Expected Result
        self.assertEqual(result, "success")
        self.task.retry.assert_not_called()
