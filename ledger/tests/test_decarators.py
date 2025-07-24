# Standard Library
import logging
from unittest.mock import patch

# Django
from django.test import TestCase

# Alliance Auth (External Libs)
from app_utils.esi import EsiDailyDowntime

# AA Ledger
from ledger.decorators import when_esi_is_available


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
            return "Daily Downtime detected. Aborting."

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
            return "Teesting Mode."

        # when
        result = trigger_esi_deco()
        # then
        self.assertEqual(result, "Teesting Mode.")

    def test_log_timing(self):
        # given
        # Alliance Auth
        from allianceauth.services.hooks import get_extension_logger

        # Alliance Auth (External Libs)
        from app_utils.logging import LoggerAddTag

        # AA Ledger
        from ledger import __title__
        from ledger.decorators import log_timing

        logger = LoggerAddTag(get_extension_logger(__name__), __title__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # when
        result = trigger_log_timing()
        # then
        self.assertEqual(result, "Log Timing")
