from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db.models import QuerySet
from django.test import TestCase

from ledger.models.events import Events
from ledger.view_helpers.core import (
    _storage_key,
    calculate_ess_stolen,
    delete_cache,
    events_filter,
    get_cache_stale,
    set_cache,
)

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpers(TestCase):
    def test_calculate_ess_stolen(self):
        # ESS Payout is 100%
        result = calculate_ess_stolen(134777, 89851)
        self.assertEqual(result, (0, 0))

    def test_calculate_ess_stolen_is_stolen(self):
        # ESS Payout is 62%, 38% is stolen
        result = calculate_ess_stolen(134777, 40000)
        self.assertEqual(result, (15067, 38))

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
        # given
        event = MagicMock(char_ledger=None)
        mock_objects.all.return_value = [event]
        # when
        result = events_filter(self.entries)
        # then
        self.entries.exclude.assert_not_called()
        self.assertEqual(result, self.entries)

    @patch.object(Events, "objects")
    def test_events_filter_with_q_objects(self, mock_objects):
        # given
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
        # given
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
