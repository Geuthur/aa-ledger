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
    handle_etag_headers,
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
        mock_cache_get.return_value = "ABCD"
        result = get_etag_header(self.mock_operation)
        self.assertEqual(result, "ABCD")

    @patch(MODULE_PATH + ".cache.delete")
    def test_del_etag_header(self, mock_cache_delete):
        del_etag_header(self.mock_operation)
        mock_cache_delete.assert_called_once_with("etag-cache_key", False)

    @patch(MODULE_PATH + ".get_etag_header")
    def test_inject_etag_header(self, mock_get_etag_header):
        mock_get_etag_header.return_value = "ABCD"
        inject_etag_header(self.mock_operation)
        self.assertEqual(
            self.mock_operation.future.request.headers["If-None-Match"], "ABCD"
        )

    def test_rem_etag_header(self):
        self.mock_operation.future.request.headers["If-None-Match"] = "ABCD"
        result = rem_etag_header(self.mock_operation)
        self.assertNotIn("If-None-Match", self.mock_operation.future.request.headers)
        self.assertTrue(result)

        self.mock_operation.future.request.headers = {}
        result = rem_etag_header(self.mock_operation)
        self.assertFalse(result)

    @patch(MODULE_PATH + ".get_etag_key")
    @patch(MODULE_PATH + ".cache.set")
    def test_set_etag_header(self, mock_cache_set, mock_get_etag_key):
        mock_get_etag_key.return_value = "etag_key"
        headers = Mock()
        headers.headers.get.return_value = "ABCD"
        result = set_etag_header(self.mock_operation, headers)
        mock_cache_set.assert_called_once_with("etag_key", "ABCD", MAX_ETAG_LIFE)
        self.assertTrue(result)

        mock_get_etag_key.return_value = None
        headers.headers.get.return_value = None
        result = set_etag_header(self.mock_operation, headers)
        self.assertFalse(result)

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
        self.mock_operation.future.request.headers = {"If-None-Match": "ABCD"}
        self.mock_operation.future.request.params = {
            "param1": "value1",
            "param2": "value2",
        }

    @patch("django_redis.cache.RedisCache.set")
    def test_handle_page_results(self, _):
        self.operation.result.return_value = ([], self.headers)
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
        self.operation.result.return_value = ([], self.headers)
        mock_error = NotModifiedError()
        mock_error.response = Mock()
        mock_error.response.headers = self.headers
        mock_handle_etag_headers.side_effect = mock_error

        # when
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )

        # then
        mock_handle_etag_headers.assert_called()
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)
        self.assertEqual(results, [])

    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_http_not_modified(self, mock_handle_etag_headers):
        self.operation.result.return_value = ([], self.headers)
        mock_handle_etag_headers.side_effect = HTTPNotModified(self.headers)
        # when
        results, current_page, total_pages = handle_page_results(
            self.operation, 1, 2, False, False
        )
        # then
        self.assertEqual(current_page, 3)
        self.assertEqual(total_pages, 2)

    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_handle_page_results_http_not_modified_etags_incomplete(
        self, mock_handle_etag_headers
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

    @patch(MODULE_PATH + ".get_etag_header")
    @patch(MODULE_PATH + ".del_etag_header")
    @patch(MODULE_PATH + ".set_etag_header")
    @patch(MODULE_PATH + ".stringify_params")
    def test_handle_etag_headers(
        self,
        mock_stringify_params,
        mock_set_etag_header,
        mock_del_etag_header,
        mock_get_etag_header,
    ):
        # given
        mock_operation = MagicMock()
        mock_operation.operation.operation_id = "test_id"
        mock_headers = MagicMock()
        mock_headers.headers.get.return_value = "test_etag"
        mock_get_etag_header.return_value = "test_etag"
        mock_stringify_params.return_value = "test_params"

        # when
        with self.assertRaises(NotModifiedError):
            handle_etag_headers(mock_operation, mock_headers, False, False)

        # then
        mock_get_etag_header.assert_called_once_with(mock_operation)
        mock_set_etag_header.assert_not_called()
        mock_del_etag_header.assert_not_called()

    @patch(MODULE_PATH + ".handle_etag_headers")
    def test_etag_results(
        self,
        _,
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

    def test_etag_results_notoken(
        self,
    ):
        # given
        mock_token = False

        mock_results = ["result1", "result2"]
        mock_headers = MagicMock()

        self.mock_operation.result.return_value = (mock_results, mock_headers)

        # when
        results = etag_results(self.mock_operation, mock_token, force_refresh=True)

        # then
        self.assertEqual(results, mock_results)

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

        self.mock_operation.return_value = mock_response
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
        self.assertEqual(
            self.mock_operation.future.request.headers["If-None-Match"], "ABCD"
        )

    @patch(MODULE_PATH + ".handle_page_results")
    def test_etag_results_with_page_notmodified(self, mock_handle_page_results):
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
