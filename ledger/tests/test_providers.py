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
from ledger.providers import DownTimeError, retry_task_on_esi_error
from ledger.tests import NoSocketsTestCase

MODULE_PATH = "ledger.providers"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRetryTaskOnESIError(NoSocketsTestCase):
    """Tests for retry_task_on_esi_error context manager."""

    def setUp(self):
        """
        Set up test case with a mock Celery task.
        """
        super().setUp()
        self.task = MagicMock()
        self.task.request.retries = 1
        self.task.retry = MagicMock(side_effect=Exception("Retry called"))

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_esi_error_limit_exception(self, mock_random):
        """
        Test should retry task when ESI error limit is reached.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 3.0  # Fixed jitter for testing
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 63)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_esi_bucket_limit_exception(self, mock_random):
        """
        Test should retry task when ESI bucket limit is reached.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 4.0  # Fixed jitter for testing
        reset_time = 30.0
        bucket_name = "test_bucket"
        exc = ESIBucketLimitException(bucket=bucket_name, reset=reset_time)

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 34)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_http_502_error(self, mock_random):
        """
        Test should retry task on HTTP 502 Bad Gateway error.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 2.5  # Fixed jitter for testing
        exc = HTTPServerError(502, {}, b"Bad Gateway")

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["exc"], exc)
        self.assertEqual(call_kwargs["countdown"], 602)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_http_503_error(self, mock_random):
        """
        Test should retry task on HTTP 503 Service Unavailable error.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 3.5  # Fixed jitter for testing
        exc = HTTPServerError(503, {}, b"Service Unavailable")

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 603)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_http_504_error(self, mock_random):
        """
        Test should retry task on HTTP 504 Gateway Timeout error.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 2.0  # Fixed jitter for testing
        exc = HTTPServerError(504, {}, b"Gateway Timeout")

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 602)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_request_error(self, mock_random):
        """
        Test should retry task on Request Error.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        # Test Data
        mock_random.return_value = 2.0  # Fixed jitter for testing
        exc = RequestError(
            operation=None,
            request=None,
            data="Test Data",
            parameters={},
        )

        # Test Action
        with self.assertRaises(Exception) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.assertEqual(str(context.exception), "Retry called")
        self.task.retry.assert_called_once()
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 602)

    def test_should_not_retry_on_http_404_error(self):
        """
        Test should not retry task on HTTP 404 error (client error).

        Results:
        - The original HTTPClientError is raised.
        - The task.retry method is not called.
        """
        # Test Data
        exc = HTTPClientError(404, {}, b"Not Found")

        # Test Action
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 404)

    def test_should_not_retry_on_http_400_error(self):
        """
        Test should not retry task on HTTP 400 error (client error).

        Results:
        - The original HTTPClientError is raised.
        - The task.retry method is not called.
        """
        # Test Data
        exc = HTTPClientError(400, {}, b"Bad Request")

        # Test Action
        with self.assertRaises(HTTPClientError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.task.retry.assert_not_called()
        self.assertEqual(context.exception.status_code, 400)

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_apply_backoff_jitter_on_retries(self, mock_random):
        """
        Test should apply exponential backoff jitter based on retry count.

        Results:
        - The countdown for retry should include jitter based on the number of retries.
        """
        # Test Data
        mock_random.return_value = 4.0
        self.task.request.retries = 2  # Third attempt
        reset_time = 60.0
        exc = ESIErrorLimitException(reset_time)

        # Test Action
        with self.assertRaises(Exception):
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        call_kwargs = self.task.retry.call_args[1]
        self.assertEqual(call_kwargs["countdown"], 76)

    def test_should_pass_through_on_success(self):
        """
        Test should pass through when no exception is raised.

        Results:
        - The code inside the context manager executes successfully.
        - The task.retry method is not called.
        """
        # Test Action
        with retry_task_on_esi_error(self.task):
            result = "success"

        # Expected Result
        self.assertEqual(result, "success")
        self.task.retry.assert_not_called()

    def test_should_pass_through_unhandled_exceptions(self):
        """
        Test should pass through exceptions that are not ESI-related.

        Results:
        - The original exception is raised.
        - The task.retry method is not called.
        """
        # Test Data
        exc = ValueError("Some other error")

        # Test Action
        with self.assertRaises(ValueError) as context:
            with retry_task_on_esi_error(self.task):
                raise exc

        # Expected Result
        self.task.retry.assert_not_called()
        self.assertEqual(str(context.exception), "Some other error")

    @patch(MODULE_PATH + ".random.uniform")
    def test_should_retry_on_daily_downtime(self, mock_random):
        """
        Test should retry task when ESI is in daily downtime.

        Results:
        - The task.retry method is called with appropriate countdown.
        """
        mock_random.return_value = 3.0  # Fixed jitter for testing
        # Test Data
        with patch(MODULE_PATH + ".timezone.now") as mock_now:
            mock_now.return_value = timezone.datetime.strptime("11:05", "%H:%M")
            exc = Exception("Downtime Error")

            # Test Action
            with self.assertRaises(Exception) as context:
                with retry_task_on_esi_error(self.task):
                    raise exc

            # Expected Result
            self.assertEqual(str(context.exception), "Retry called")
            self.task.retry.assert_called_once()
            call_kwargs = self.task.retry.call_args[1]
            self.assertEqual(
                str(call_kwargs["exc"]), str(DownTimeError("ESI is in daily downtime"))
            )
            self.assertEqual(call_kwargs["countdown"], 603)
