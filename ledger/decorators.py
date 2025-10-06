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


def when_esi_is_available(func):
    """
    Make sure the decorated task only runs when esi is available and store the result.
    Complete the task without running it when downtime is detected.
    Automatically disabled during tests.
    """

    @wraps(func)
    def outer(*args, **kwargs):
        # During tests we skip ESI checks
        if IS_TESTING is not True:
            cache_key = "esi_status_is_up"
            redis_client = get_redis_client()

            # Prevent hammering ESI status endpoint
            if redis_client.get(cache_key):
                logger.debug("ESI status cached as available.")
                return func(*args, **kwargs)

            # Set a Lock so only one process checks ESI
            acquired = False
            token = str(uuid.uuid4())
            lock_key = "esi_status_lock"
            try:
                acquired = redis_client.set(lock_key, token, nx=True, ex=10)
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "Failed to acquire ESI status lock, will attempt live check."
                )

            # If we didn't get the lock, wait a bit for the result
            if not acquired:
                waited = 0.0
                poll_interval = 0.1
                max_wait = 3.0
                while waited < max_wait:
                    try:
                        if redis_client.get(cache_key):
                            logger.debug(
                                "ESI status became available in cache while waiting."
                            )
                            return func(*args, **kwargs)
                    except Exception:  # pylint: disable=broad-except
                        logger.debug(
                            "Error polling ESI cache while waiting for lock holder."
                        )
                    time.sleep(poll_interval)
                    waited += poll_interval

            # Check ESI status
            if fetch_esi_status().is_ok:
                logger.debug("ESI is available, proceeding.")
                # 5 second TTL
                redis_client.setex(cache_key, 5, "1")
                return func(*args, **kwargs)
            return None  # function will not run
        return func(*args, **kwargs)

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
