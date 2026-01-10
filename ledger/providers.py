"""Shared ESI client for Ledger."""

# Standard Library
import logging
import random
from contextlib import contextmanager
from http import HTTPStatus

# Third Party
from celery import Task

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)
from esi.openapi_clients import ESIClientProvider

# AA Ledger
from ledger import (
    __app_name_useragent__,
    __character_operations__,
    __corporation_operations__,
    __esi_compatibility_date__,
    __github_url__,
    __title__,
    __universe_operations__,
    __version__,
)

esi = ESIClientProvider(
    compatibility_date=__esi_compatibility_date__,
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=__corporation_operations__
    + __character_operations__
    + __universe_operations__,
)


class AppLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that adds a prefix to log messages.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken
    """

    def __init__(self, my_logger, prefix):
        """
        Initializes the AppLogger with a logger and a prefix.

        :param my_logger: Logger instance
        :type my_logger: logging.Logger
        :param prefix: Prefix string to add to log messages
        :type prefix: str
        """

        super().__init__(my_logger, {})

        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        Prepares the log message by adding the prefix.

        :param msg: Original log message
        :type msg: str
        :param kwargs: Additional keyword arguments for logging
        :type kwargs: dict
        :return: Tuple of modified message and kwargs
        :rtype: tuple
        """
        return f"[{self.prefix}] {msg}", kwargs


logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


@contextmanager
def retry_task_on_esi_error(task: Task):
    """Retry Task when a ESI error occurs.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken

    Retries on:
    - Error limits reached (ESIErrorLimitException)
    - Rate limit errors (ESIBucketLimitException)
    - HTTPError with status codes 502, 503, 504 (server errors)

    :param task: Celery Task instance
    :return: Context manager that retries the task on ESI errors.

    """

    def retry(exc: Exception, retry_after: float, issue: str):
        backoff_jitter = int(random.uniform(2, 5) ** task.request.retries)
        countdown = retry_after + backoff_jitter
        logger.warning(
            "ESI Error encountered: %s. Retrying after %.2f seconds. Issue: %s",
            str(exc),
            countdown,
            issue,
        )
        raise task.retry(countdown=countdown, exc=exc)

    try:
        yield
    except ESIErrorLimitException as exc:
        retry(exc, exc.reset, "ESI Error Limit Reached")
    except ESIBucketLimitException as exc:
        retry(exc, exc.reset, f"ESI Bucket Limit Reached for {exc.bucket}")
    except HTTPServerError as exc:
        if exc.status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            retry(exc, 60, f"ESI seems to be down (HTTP {exc.status_code})")
        raise exc
