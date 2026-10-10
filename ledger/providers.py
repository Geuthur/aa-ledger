"""Shared ESI client for Ledger."""

# Standard Library
import logging
from pathlib import Path

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.openapi_clients import ESIClientProvider

# AA Ledger
from ledger import (
    __app_name_useragent__,
    __esi_compatibility_date__,
    __github_url__,
    __operations__,
    __title__,
    __version__,
)

spec_file = Path(__file__).parent / f"openapi_{__esi_compatibility_date__}.json"
esi = ESIClientProvider(
    compatibility_date=__esi_compatibility_date__,
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=__operations__,
    spec_file=spec_file,
)

DOWNTIME_TIMER = 60 * 10  # 10 minutes


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
