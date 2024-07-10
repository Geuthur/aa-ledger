"""
Decorators
"""

import logging
import time
from functools import wraps

from app_utils.esi import EsiDailyDowntime, fetch_esi_status

from ledger.app_settings import IS_TESTING
from ledger.hooks import get_extension_logger

# Konfigurieren des Loggings
logging.basicConfig(filename="log/timings.log", level=logging.INFO)

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


def log_timing(func):
    """
    Ein Dekorator, der die Ausführungszeit einer Funktion misst und in die Logdatei schreibt.
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(
            "%s wurde aufgerufen. Ausführungszeit: %s Sekunden",
            func.__name__,
            end_time - start_time,
        )
        return result

    return wrapper
