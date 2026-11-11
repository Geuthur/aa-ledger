"""Helpers for ESI tests with pook."""

# Django
from django.core.cache import cache

ESI_BASE_URL = "https://esi.evetech.net"


def wallet_journal_url(owner) -> str:
    """Return the ESI URL of the wallet journal of a character owner."""
    return f"{ESI_BASE_URL}/characters/{owner.eve_id}/wallet/journal"


def markets_prices_url() -> str:
    """Return the ESI URL of the market prices."""
    return f"{ESI_BASE_URL}/markets/prices"


def clear_esi_limits(owner) -> None:
    """Remove the ESI error limit and the wallet bucket of an owner from the cache."""
    cache.delete("esi_error_limit_reset")
    cache.delete(f"esi:bucket:char-wallet:{owner.eve_id}")
