from unittest.mock import patch

from django.test import TestCase

from app_utils.esi import EsiDailyDowntime

from ledger.decorators import custom_cache_timeout, when_esi_is_available


class TestDecorators(TestCase):
    @patch("ledger.decorators.fetch_esi_status")
    @patch("ledger.decorators.IS_TESTING", new=False)
    def test_when_esi_is_available(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_called_once()
        self.assertEqual(result, "Esi is Available")

    @patch("ledger.decorators.fetch_esi_status", side_effect=EsiDailyDowntime)
    @patch("ledger.decorators.IS_TESTING", new=False)
    def test_when_esi_is_available_downtime(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        self.assertIsNone(result)

    @patch("ledger.decorators.fetch_esi_status")
    @patch("ledger.decorators.IS_TESTING", new=True)
    def test_when_esi_is_available_is_test(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        self.assertEqual(result, "Esi is Available")

    def test_custom_cache_timeout_still_active(self):
        # given
        minutes = 120
        # when
        result = custom_cache_timeout(minutes=minutes)
        # then
        self.assertTrue(result > 0)

    def test_custom_cache_timeout_expired(self):
        # given
        minutes = -5
        # when
        result = custom_cache_timeout(minutes=minutes)
        # then
        self.assertTrue(result == 0)
