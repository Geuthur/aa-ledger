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


class TestEtagPageHandler(NoSocketsTestCase):
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

    def test_handle_page_results_should_be_success_with_page_3(self):
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )
        self.assertEqual(results, [])
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)

    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_should_raise_notmodifiederror(
        self, mock_handle_etag_headers
    ):
        # given
        mock_handle_etag_headers.side_effect = NotModifiedError()
        # when
        with self.assertRaises(NotModifiedError):
            handle_page_results(self.operation, 1, 2, False, False)

    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_should_raise_http_not_modified(
        self, mock_handle_etag_headers
    ):
        # given
        mock_response = Mock()
        mock_response.status_code = 304
        mock_response.headers = {"ETag": "ETAG", "X-Pages": "2"}
        mock_handle_etag_headers.side_effect = HTTPNotModified(mock_response)
        # when
        with self.assertRaises(
            NotModifiedError
        ):  # Raise NotModifiedError after raising HTTPNotModified
            handle_page_results(self.operation, 1, 2, False, False)
