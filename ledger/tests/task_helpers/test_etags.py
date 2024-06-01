from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from ledger.task_helpers.etag_helpers import (
    MAX_ETAG_LIFE,
    HTTPNotModified,
    NotModifiedError,
    del_etag_header,
    etag_results,
    get_etag_header,
    get_etag_key,
    handle_page_results,
    inject_etag_header,
    rem_etag_header,
    set_etag_header,
    stringify_params,
)

MODULE_PATH = "ledger.task_helpers.etag_helpers"


class TestEtagHelpers(TestCase):
    def setUp(self):
        self.mock_operation = Mock()
        self.mock_operation._cache_key.return_value = "cache_key"
        self.mock_operation.operation.operation_id = "operation_id"
        self.mock_operation.future.request.headers = {}
        self.mock_operation.future.request.params = {
            "param1": "value1",
            "param2": "value2",
        }

    def test_get_etag_key(self):
        result = get_etag_key(self.mock_operation)
        self.assertEqual(result, "etag-cache_key")

    @patch(MODULE_PATH + ".cache.get")
    def test_get_etag_header(self, mock_cache_get):
        mock_cache_get.return_value = "etag"
        result = get_etag_header(self.mock_operation)
        self.assertEqual(result, "etag")

    @patch(MODULE_PATH + ".cache.delete")
    def test_del_etag_header(self, mock_cache_delete):
        del_etag_header(self.mock_operation)
        mock_cache_delete.assert_called_once_with("etag-cache_key", False)

    @patch(MODULE_PATH + ".get_etag_header")
    @patch(MODULE_PATH + ".logger")
    def test_inject_etag_header(self, mock_logger, mock_get_etag_header):
        mock_get_etag_header.return_value = "etag"
        inject_etag_header(self.mock_operation)
        self.assertEqual(
            self.mock_operation.future.request.headers["If-None-Match"], "etag"
        )

    @patch(MODULE_PATH + ".logger")
    def test_rem_etag_header(self, mock_logger):
        self.mock_operation.future.request.headers["If-None-Match"] = "etag"
        rem_etag_header(self.mock_operation)
        self.assertNotIn("If-None-Match", self.mock_operation.future.request.headers)

    @patch(MODULE_PATH + ".get_etag_key")
    @patch(MODULE_PATH + ".cache.set")
    @patch(MODULE_PATH + ".logger")
    def test_set_etag_header(self, mock_logger, mock_cache_set, mock_get_etag_key):
        mock_get_etag_key.return_value = "etag_key"
        headers = Mock()
        headers.headers.get.return_value = "etag"
        set_etag_header(self.mock_operation, headers)
        mock_cache_set.assert_called_once_with("etag_key", "etag", MAX_ETAG_LIFE)

    def test_stringify_params(self):
        result = stringify_params(self.mock_operation)
        self.assertEqual(result, "param1: value1, param2: value2")


class TestEtagReults(TestCase):
    def setUp(self):
        self.operation = MagicMock()
        self.headers = MagicMock()  # Use MagicMock instead of Mock
        self.headers.headers = {"ETag": "ABCD", "X-Pages": "2"}

        self.mock_operation = MagicMock()
        self.mock_operation._cache_key.return_value = "cache_key"
        self.mock_operation.operation.operation_id = "operation_id"
        self.mock_operation.future.request.headers = {}
        self.mock_operation.future.request.params = {
            "param1": "value1",
            "param2": "value2",
        }

    @patch("django_redis.cache.RedisCache.set")
    @patch(MODULE_PATH + ".rem_etag_header")
    def test_handle_page_results(self, mock_rem_etag, mock_set):
        self.operation.result.return_value = ([], self.headers)
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )
        self.assertEqual(results, [])
        self.assertEqual(total_pages, 2)

    @patch(MODULE_PATH + ".rem_etag_header")
    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_http_not_modified(
        self, mock_handle_etag_headers, mock_rem_etag
    ):
        self.operation.result.return_value = ([], self.headers)
        mock_handle_etag_headers.side_effect = HTTPNotModified(self.headers)
        # when
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )
        # then
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)

    @patch(MODULE_PATH + ".rem_etag_header")
    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_http_not_modified_etags_incomplete(
        self, mock_handle_etag_headers, mock_rem_etag
    ):
        self.operation.result.return_value = ([], self.headers)
        mock_handle_etag_headers.side_effect = HTTPNotModified(self.headers)

        # when
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, True, False
        )

        # then
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)
        self.assertEqual(results, [])

    @patch(MODULE_PATH + ".handle_page_results")
    @patch(MODULE_PATH + ".inject_etag_header")
    @patch(MODULE_PATH + ".set_etag_header")
    @patch(MODULE_PATH + ".handle_etag_headers")
    @patch(MODULE_PATH + ".logger")
    def test_etag_results(
        self,
        mock_logger,
        mock_handle_etag_headers,
        mock_set_etag_header,
        mock_inject_etag_header,
        mock_handle_page_results,
    ):
        # given
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = "valid_token"

        mock_results = ["result1", "result2"]
        mock_headers = MagicMock()

        self.mock_operation.result.return_value = (mock_results, mock_headers)

        # when
        results = etag_results(self.mock_operation, mock_token)

        # then
        self.assertEqual(results, mock_results)
        mock_token.valid_access_token.assert_called_once()

    @patch(MODULE_PATH + ".handle_page_results")
    @patch(MODULE_PATH + ".set_etag_header")
    def test_etag_results_HTTPNotModified(
        self, mock_set_etag_header, mock_handle_page_results
    ):
        # given
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = "valid_token"

        mock_results = ["result1", "result2"]

        mock_response = MagicMock()

        self.mock_operation.result.side_effect = HTTPNotModified(mock_response)
        self.mock_operation.operation.params = {}
        mock_handle_page_results.return_value = (mock_results, 1, 1)

        # when
        with self.assertRaises(NotModifiedError):
            etag_results(self.mock_operation, mock_token)

        # then
        mock_token.valid_access_token.assert_called_once()
        mock_handle_page_results.assert_not_called()
        mock_set_etag_header.assert_called_once()

    @patch(MODULE_PATH + ".handle_page_results")
    def test_etag_results_with_page(self, mock_handle_page_results):
        # given
        mock_token = MagicMock()
        mock_token.valid_access_token.return_value = "valid_token"

        mock_results = ["result1", "result2"]
        mock_response = MagicMock()

        self.mock_operation.result.side_effect = HTTPNotModified(mock_response)
        self.mock_operation.operation.params = {"page": 1}
        mock_handle_page_results.return_value = (mock_results, 1, 1)
        # when
        results = etag_results(self.mock_operation, mock_token)

        # then
        mock_token.valid_access_token.assert_called_once()
        mock_handle_page_results.assert_called_once_with(
            self.mock_operation, 1, 1, False, False
        )
        self.assertEqual(results, mock_results)
