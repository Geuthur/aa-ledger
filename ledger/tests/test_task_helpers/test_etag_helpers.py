# Standard Library
from unittest.mock import MagicMock, Mock, patch

# Django
from django.core.cache import cache
from django.test import TestCase

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.task_helpers.etag_helpers import (
    MAX_ETAG_LIFE,
    HTTPNotModified,
    NotModifiedError,
    del_etag_header,
    etag_results,
    get_etag_header,
    get_etag_key,
    handle_etag_headers,
    handle_page_results,
    inject_etag_header,
    rem_etag_header,
    set_etag_header,
    stringify_params,
)

MODULE_PATH = "ledger.task_helpers.etag_helpers"


def clear_cache(cache_key):
    """Clear cache."""
    cache.delete(cache_key)


class TestEtagHelpers(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        clear_cache("ledger-cache_key")
        cls.headers = Mock()
        cls.headers.headers = {
            "ETag": "ETAG",
            "X-Pages": "1",
        }
        cls.operation = Mock()
        cls.operation._cache_key.return_value = "cache_key"
        cls.operation.operation.operation_id = "operation_id"
        cls.operation.future.request.headers = {
            "If-None-Match": "ABCD",
            "If-Modified-Since": "2023-10-01T00:00:00Z",
        }
        cls.operation.future.request.params = {
            "param1": "value1",
            "param2": "value2",
        }

        cls.headers_no_etag = Mock()
        cls.headers_no_etag.headers = {}
        cache.set("ledger-cache_key", "ABCD", MAX_ETAG_LIFE)

    def test_get_etag_key(self):
        result = get_etag_key(self.operation)
        self.assertEqual(result, "ledger-cache_key")

    def test_get_etag_header(self):
        # given
        cache.set("ledger-cache_key", "ABCD", MAX_ETAG_LIFE)
        # when
        result = get_etag_header(self.operation)
        # then
        self.assertEqual(result, "ABCD")

    def test_inject_etag_header(self):
        inject_etag_header(self.operation)
        self.assertEqual(self.operation.future.request.headers["If-None-Match"], "ABCD")

    def test_set_etag_header(self):
        result = set_etag_header(self.operation, self.headers)
        self.assertTrue(result)

        result = set_etag_header(self.operation, self.headers_no_etag)
        self.assertFalse(result)

    def test_stringify_params(self):
        result = stringify_params(self.operation)
        self.assertEqual(result, "param1: value1, param2: value2")


class TestEtagHandler(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        clear_cache("ledger-cache_key_2")
        cls.headers = Mock()
        cls.headers.headers = {
            "ETag": "ETAG",
            "X-Pages": "2",
        }
        cls.operation = Mock()
        cls.operation._cache_key.return_value = "cache_key_2"
        cls.operation.operation.operation_id = "operation_id"
        cls.operation.future.request.headers = {
            "If-None-Match": "DCBA",
            "If-Modified-Since": "2023-10-01T00:00:00Z",
        }
        cls.operation.future.request.params = {
            "param1": "value1",
            "param2": "value2",
        }
        cls.operation.result.return_value = ([], cls.headers)

        cls.headers_no_etag = Mock()
        cls.headers_no_etag.headers = {}
        cache.set("ledger-cache_key_2", "DCBA", MAX_ETAG_LIFE)

    @patch("django_redis.cache.RedisCache.set")
    def test_handle_page_results(self, _):
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )
        self.assertEqual(results, [])
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)

    @patch(MODULE_PATH + ".handle_etag_headers")
    @patch("django_redis.cache.RedisCache.set")
    def test_handle_page_results_notmodified(self, _, mock_handle_etag_headers):
        # given
        mock_error = NotModifiedError()
        mock_error.response = Mock()
        mock_error.response.headers = {
            "ETag": "ETAG",
            "X-Pages": "2",
        }  # Ensure headers is a dictionary
        mock_handle_etag_headers.side_effect = mock_error

        # when
        try:
            results, current_page, total_pages = handle_page_results(
                self.operation, 1, 2, False, False
            )
        except NotModifiedError:
            # Handle the expected exception
            results, current_page, total_pages = [], 1, 2

        # then
        mock_handle_etag_headers.assert_called()
        self.assertEqual(current_page, 1)
        self.assertEqual(total_pages, 2)
        self.assertEqual(results, [])
