"""
Decorators
"""

# Standard Library
import time
from functools import wraps

# Django
from django.core.cache import cache

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.esi import fetch_esi_status
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.app_settings import IS_TESTING

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Use shared ESI status route rate limit from app_settings
ESI_STATUS_ROUTE_RATE_LIMIT = 5
ESI_STATUS_KEY = "esi-is-available-status"


def get_esi_available_cache() -> bool:
    """Return True if ESI availability cache is present."""
    if cache.get(ESI_STATUS_KEY):
        return True
    return False


def when_esi_is_available(func):
    """
    Make sure the decorated task only runs when esi is available and store the result.
    Complete the task without running it when downtime is detected.
    Automatically disabled during tests.
    """

    @wraps(func)
    def outer(*args, **kwargs):

        # During tests we skip ESI checks
        if IS_TESTING or get_esi_available_cache():
            logger.debug("Skipping ESI check (testing mode or cache present).")
            return func(*args, **kwargs)

        # Check ESI status
        if fetch_esi_status().is_ok:
            logger.debug("ESI is available, proceeding.")
            cache.set(ESI_STATUS_KEY, "1", timeout=ESI_STATUS_ROUTE_RATE_LIMIT)
            return func(*args, **kwargs)
        return None  # function will not run

    return outer


def log_timing(logs):
    """
    Ein Dekorator, der die Ausführungszeit einer Funktion misst und in die Logdatei schreibt.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logs.debug(
                "TIME: %s run for %s seconds with args: %s",
                end_time - start_time,
                func.__name__,
                args,
            )
            return result

        return wrapper

    return decorator
