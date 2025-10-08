"""
Decorators
"""

# Standard Library
import time
from functools import wraps

# Third Party
from redis import Redis

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.allianceauth import get_redis_client
from app_utils.esi import fetch_esi_status
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.app_settings import IS_TESTING

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

ESI_STATUS_ROUTE_RATE_LIMIT = 3
ESI_STATUS_KEY = "esi-is-available-status"
ESI_STATUS_REDIS_LOCK = "esi-is-available-lock"


def get_esi_available_cache(redis_client: Redis) -> bool:
    """Return True if ESI availability cache is present."""
    if redis_client.get(ESI_STATUS_KEY):
        return True
    return False


def acquire_esi_status_lock(redis_client: Redis) -> bool:
    """Try to acquire a short-lived lock in Redis. Returns True on success."""
    return redis_client.set(
        ESI_STATUS_REDIS_LOCK, "1", nx=True, ex=ESI_STATUS_ROUTE_RATE_LIMIT
    )


def acquire_lock_or_wait_for_cache(redis_client: Redis):
    """Wait a short time for either the cache to appear or the lock to become available.

    Returns a tuple (acquired, cache_available).
    """
    waited = 0.0
    poll_interval = 0.1
    max_wait = float(ESI_STATUS_ROUTE_RATE_LIMIT) - 0.1
    while waited < max_wait:
        try:
            # If cache was set while waiting, proceed.
            if get_esi_available_cache(redis_client):
                logger.debug("ESI status became available in cache while waiting.")
                return False, True

            # If the lock expired or was released, try to acquire it.
            if not redis_client.get(ESI_STATUS_REDIS_LOCK):
                logger.debug("ESI status lock expired, trying to acquire.")
                acquired = acquire_esi_status_lock(redis_client)
                if acquired:
                    # We acquired the lock and will perform the check
                    return True, False
        except Exception:  # pylint: disable=broad-except
            logger.debug("Error polling ESI cache while waiting for lock holder.")
        time.sleep(poll_interval)
        waited += poll_interval

    return False, False


def when_esi_is_available(func):
    """
    Make sure the decorated task only runs when esi is available and store the result.
    Complete the task without running it when downtime is detected.
    Automatically disabled during tests.
    """

    @wraps(func)
    def outer(*args, **kwargs):
        redis_client = get_redis_client()

        # During tests we skip ESI checks
        if IS_TESTING or get_esi_available_cache(redis_client):
            logger.debug("Skipping ESI check (testing mode or cache present).")
            return func(*args, **kwargs)

        # Try to acquire a short-lived lock so only one process checks ESI
        acquired = acquire_esi_status_lock(redis_client)
        # If we didn't get the lock, wait a short time for cache or lock
        if not acquired:
            acquired, cache_available = acquire_lock_or_wait_for_cache(redis_client)
            if cache_available:
                return func(*args, **kwargs)

        # Check ESI status
        if fetch_esi_status().is_ok:
            logger.debug("ESI is available, proceeding.")
            try:
                redis_client.setex(ESI_STATUS_KEY, ESI_STATUS_ROUTE_RATE_LIMIT, "1")
            except Exception:  # pylint: disable=broad-except
                logger.debug("Failed to set ESI availability cache.")
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
