"""Shared ESI client for Ledger."""

# Alliance Auth
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
