"""
Decorators
"""

from functools import wraps

from app_utils.esi import EsiDailyDowntime, fetch_esi_status

from ledger.app_settings import IS_TESTING
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def when_esi_is_available(func):
    """Make sure the decorated task only runs when esi is available.

    Raise exception when ESI is offline.
    Complete the task without running it when downtime is detected.

    Automatically disabled during tests.
    """

    @wraps(func)
    def outer(*args, **kwargs):
        if IS_TESTING is not True:
            try:
                fetch_esi_status().raise_for_status()
            except EsiDailyDowntime:
                logger.info("Daily Downtime detected. Aborting.")
                return None  # function will not run

        return func(*args, **kwargs)

    return outer
