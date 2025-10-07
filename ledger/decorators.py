"""
Decorators
"""

# Standard Library
import time
import uuid
from functools import wraps

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


def _esi_cache_available(redis_client, cache_key):
    """Return True if ESI availability cache is present. Handles Redis errors."""
    try:
        if redis_client.get(cache_key):
            return True
    except Exception:  # pylint: disable=broad-except
        # If Redis is flaky, fall through to live check
        logger.debug("Error reading ESI cache, will attempt live check.")
    return False


def _acquire_lock(redis_client, lock_key, token, lock_ttl):
    """Try to acquire a short-lived lock in Redis. Returns True on success."""
    try:
        return redis_client.set(lock_key, token, nx=True, ex=lock_ttl)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Failed to acquire ESI status lock, will attempt live check.")
        return False


def _wait_for_lock_or_cache(redis_client, cache_key, lock_key, token, lock_ttl):
    """Wait a short time for either the cache to appear or the lock to become available.

    Returns a tuple (acquired, cache_available).
    """
    waited = 0.0
    poll_interval = 0.1
    max_wait = float(lock_ttl) - 0.1
    while waited < max_wait:
        try:
            # If cache was set while waiting, proceed.
            if _esi_cache_available(redis_client, cache_key):
                logger.debug("ESI status became available in cache while waiting.")
                return False, True

            # If the lock expired or was released, try to acquire it.
            if not redis_client.get(lock_key):
                try:
                    acquired = redis_client.set(lock_key, token, nx=True, ex=lock_ttl)
                    if acquired:
                        # We acquired the lock and will perform the check
                        return True, False
                except Exception:  # pylint: disable=broad-except
                    logger.debug("Failed to re-acquire lock while waiting for holder.")
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
        # During tests we skip ESI checks
        if IS_TESTING:
            return func(*args, **kwargs)

        cache_key = "esi_status_is_up"
        redis_client = get_redis_client()

        # Prevent hammering ESI status endpoint
        if _esi_cache_available(redis_client, cache_key):
            logger.debug("ESI status cached as available.")
            return func(*args, **kwargs)

        # Try to acquire a short-lived lock so only one process checks ESI
        token = str(uuid.uuid4())
        lock_key = "esi_status_lock"
        lock_ttl = 5
        acquired = _acquire_lock(redis_client, lock_key, token, lock_ttl)

        # If we didn't get the lock, wait a short time for cache or lock
        if not acquired:
            acquired, cache_available = _wait_for_lock_or_cache(
                redis_client, cache_key, lock_key, token, lock_ttl
            )
            if cache_available:
                return func(*args, **kwargs)

        # Check ESI status
        if fetch_esi_status().is_ok:
            logger.debug("ESI is available, proceeding.")
            # 5 second TTL
            try:
                redis_client.setex(cache_key, 5, "1")
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
