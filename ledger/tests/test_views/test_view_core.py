from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db.models import QuerySet
from django.test import TestCase

from ledger.models.events import Events
from ledger.view_helpers.core import (
    _storage_key,
    add_info_to_context,
    calculate_ess_stolen,
    delete_cache,
    events_filter,
    get_cache_stale,
    ledger_cache_timeout,
    set_cache,
    set_cache_hourly,
)

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpers(TestCase):
    def test_calculate_ess_stolen_key_error(self):
        # Test case where 'bounty' key is missing
        amounts = {"ess": {"total_amount": 1000, "total_amount_day": 500}, "stolen": {}}

        # Call the function and check if it handles the KeyError
        result = calculate_ess_stolen(amounts)

        # Since 'bounty' key is missing, 'stolen' amounts should not be calculated
        self.assertEqual(result["stolen"].get("total_amount"), None)
        self.assertEqual(result["stolen"].get("total_amount_day"), None)

    def test_calculate_ess_stolen_key_error_ess(self):
        # Test case where 'ess' key is missing
        amounts = {
            "bounty": {"total_amount": 1000, "total_amount_day": 500},
            "stolen": {},
        }

        # Call the function and check if it handles the KeyError
        result = calculate_ess_stolen(amounts)

        # Since 'ess' key is missing, 'stolen' amounts should not be calculated
        self.assertEqual(result["stolen"].get("total_amount"), None)
        self.assertEqual(result["stolen"].get("total_amount_day"), None)

    def test_events_filter(self):
        result = events_filter([])
        self.assertEqual(result, [])

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

    def test_set_cache_hourly(self):
        result = set_cache_hourly("test", "test")
        self.assertIsNone(result)

    def test_delete_cache(self):
        result = delete_cache("test")
        self.assertIsNone(result)

    def test_storage_key(self):
        result = _storage_key("test")
        self.assertEqual(result, "ledger_storage_test")


class TestEventsFilter(TestCase):
    def setUp(self):
        self.entries = MagicMock(spec=QuerySet)
        self.excluded_entries = MagicMock(spec=QuerySet)
        self.entries.exclude.return_value = self.excluded_entries

    @patch.object(Events, "objects")
    def test_events_filter_no_char_ledger(self, mock_objects):
        # Erstellen Sie ein Event ohne char_ledger
        event = MagicMock(char_ledger=None)
        mock_objects.all.return_value = [event]

        # when
        result = events_filter(self.entries)

        # then
        self.entries.exclude.assert_not_called()
        self.assertEqual(result, self.entries)

    @patch.object(Events, "objects")
    def test_events_filter_with_q_objects(self, mock_objects):
        # Erstellen Sie ein Event mit char_ledger und einem Datumsbereich
        event = MagicMock(
            char_ledger=True, date_start="2022-01-01", date_end="2022-01-31"
        )
        mock_objects.all.return_value = [event]

        # when
        result = events_filter(self.entries)

        # then
        self.entries.exclude.assert_called_once()
        self.assertEqual(result, self.excluded_entries)

    @patch.object(Events, "objects")
    def test_events_filter_multiple(self, mock_objects):
        # Erstellen Sie mehrere Events, von denen mindestens eines char_ledger und einen gültigen Datumsbereich hat
        event1 = MagicMock(
            char_ledger=True, date_start="2022-01-01", date_end="2022-01-31"
        )
        event2 = MagicMock(
            char_ledger=False, date_start="2022-02-01", date_end="2022-02-28"
        )
        event3 = MagicMock(
            char_ledger=True, date_start="2022-03-01", date_end="2022-03-31"
        )
        mock_objects.all.return_value = [event1, event2, event3]

        # when
        result = events_filter(self.entries)

        # then
        self.entries.exclude.assert_called_once()
        self.assertEqual(result, self.entries.exclude.return_value)


class TestCache(TestCase):
    def test_ledger_cache_timeout(self):
        # when
        result = ledger_cache_timeout()
        # then
        self.assertTrue(result > 0)

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
