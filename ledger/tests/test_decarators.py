# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.decorators import (
    log_timing,
)
from ledger.providers import AppLogger
from ledger.tests import LedgerTestCase

DECORATOR_PATH = "ledger.decorators."


class TestDecorators(LedgerTestCase):
    def test_log_timing(self):
        """
        Test log_timing decorator functionality.

        This test defines a simple function decorated with log_timing and
        verifies that it returns the expected result.
        """
        # Test Data
        logger = AppLogger(get_extension_logger(__name__), __title__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # Test Action
        result = trigger_log_timing()

        # Expected Result
        self.assertEqual(result, "Log Timing")
