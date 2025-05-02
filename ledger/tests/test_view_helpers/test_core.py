# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.core.cache import cache
from django.test import TestCase

# AA Ledger
from ledger.view_helpers.core import (
    _storage_key,
    add_info_to_context,
    calculate_ess_stolen,
    calculate_ess_stolen_amount,
    delete_cache,
    events_filter,
    get_cache_stale,
    set_cache,
)

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_info_to_context(self):
        # given
        request = MagicMock()
        request.user = MagicMock()
        request.user.id = 99999999

        context = {"theme": None}
        # when
        result = add_info_to_context(request, context)
        # then
        self.assertEqual(result, context)

    def test_get_cache_stale(self):
        result = get_cache_stale("test")
        self.assertFalse(result)

    @patch.object(cache, "get", return_value="test_value")
    def test_get_cache_stale_with_data(self, mock_cache_get):
        # given
        key_name = "test_key"
        # when
        result = get_cache_stale(key_name)
        # then
        mock_cache_get.assert_called_once_with(key=_storage_key(key_name))
        self.assertEqual(result, "test_value")

    def test_set_cache(self):
        result = set_cache("test", "test", 1)
        self.assertIsNone(result)

    def test_delete_cache(self):
        result = delete_cache("test")
        self.assertIsNone(result)

    def test_storage_key(self):
        result = _storage_key("test")
        self.assertEqual(result, "ledger_storage_test")

    def test_calculate_ess_stolen_amount(self):
        result = calculate_ess_stolen_amount(1000, 1000)
        self.assertEqual(result, 0)

    def test_calculate_ess_stolen_amount_ess_different(self):
        result = calculate_ess_stolen_amount(1000, 200)
        self.assertEqual(result, 93)

    def test_calculate_ess_stolen_amount_with_exception(self):
        result = calculate_ess_stolen_amount("test", "test")
        self.assertEqual(result, 0)

    def test_calculate_ess_stolen(self):
        result = calculate_ess_stolen(
            {
                "bounty": {"total_amount": 1000},
                "ess": {"total_amount": 1000},
                "stolen": {},
            }
        )

        excepted_result = {
            "bounty": {"total_amount": 1000},
            "ess": {"total_amount": 1000},
            "stolen": {"total_amount": 0},
        }

        self.assertEqual(result, excepted_result)

    def test_calculate_ess_stolen_with_exception(self):
        result = calculate_ess_stolen({"bounty": {"total_amount": 1000}})
        self.assertEqual(result, {"bounty": {"total_amount": 1000}})
