"""
Decorators
"""

import sys
from datetime import datetime, timedelta
from functools import wraps

from app_utils.esi import EsiDailyDowntime, fetch_esi_status

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)

IS_TESTING = sys.argv[1:2] == ["test"]


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


def custom_cache_timeout(minutes=0, hours=0, seconds=0):
    now = datetime.now()
    delta = timedelta(minutes=minutes, hours=hours, seconds=seconds)
    next_time = (now + delta).replace(minute=0, second=0, microsecond=0)
    timeout = next_time - now
    if timeout < timedelta(seconds=0):
        return 0
    return timeout.total_seconds()
