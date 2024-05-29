from unittest.mock import patch

from django.test import TestCase

from app_utils.esi import EsiDailyDowntime

from ledger.decorators import custom_cache_timeout, when_esi_is_available


class TestDecorators(TestCase):
    @patch("ledger.decorators.fetch_esi_status")
    @patch("ledger.decorators.IS_TESTING", new=False)
    def test_when_esi_is_available(self, mock_fetch_esi_status):
        # Arrange
        @when_esi_is_available
        def test_func():
            return "Function ran"

        # Act
        result = test_func()

        # Assert
        mock_fetch_esi_status.assert_called_once()
        self.assertEqual(result, "Function ran")

    @patch("ledger.decorators.fetch_esi_status", side_effect=EsiDailyDowntime)
    @patch("ledger.decorators.IS_TESTING", new=False)
    def test_when_esi_is_available_downtime(self, mock_fetch_esi_status):
        # Set up your test here
        @when_esi_is_available
        def triggeR_esi_deco():
            return "Esi is Available"

        # Call your function here. It should raise EsiDailyDowntime.
        result = triggeR_esi_deco()

        # Assert that the function returned None
        self.assertIsNone(result)

        # Assert that fetch_esi_status was called
        mock_fetch_esi_status.assert_called_once()

    def test_custom_cache_timeout_still_active(self):
        # Arrange
        minutes = 120

        # Act
        result = custom_cache_timeout(minutes=minutes)

        # Assert
        self.assertTrue(result > 0)

    def test_custom_cache_timeout_expired(self):
        # Arrange
        minutes = -5

        # Act
        result = custom_cache_timeout(minutes=minutes)
        print(result)

        # Assert
        self.assertTrue(result == 0)
