# Standard Library
from hashlib import md5

# Django
from django.core.cache import cache

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger.app_settings import (
    LEDGER_CACHE_ENABLED,
    LEDGER_CACHE_KEY,
    LEDGER_CACHE_STALE,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), "Ledger")


class CacheManager:
    """
    Cache Manager for Ledger Data.
    """

    @staticmethod
    def create_ledger_hash(ids: list[int]) -> str:
        """
        Create a hash from a list of IDs.

        Args:
            ids (list[int]): List of IDs to hash.

        Returns:
            str: The resulting hash string.
        """
        hash_object = md5()

        # Handle empty ID list
        if not ids:
            return hash_object.hexdigest()

        # Ensure consistent ordering
        for _id in sorted(set(ids)):
            hash_object.update(f"{_id},".encode())
        return hash_object.hexdigest()

    @staticmethod
    def build_ledger_cache_key(header_key: str) -> str:
        """Build a cache key for ledger data."""
        logger.debug(f"Building Ledger Cache Key for Header Key: {header_key}")
        return f"{LEDGER_CACHE_KEY}-{header_key}"

    def get_cache_key(self, ledger_hash: str, key: str) -> str:
        """
        Get the cache for ledger data.

        This function retrieves the cache for ledger data using a key for identification.

        Args:
            ledger_hash (str): The ledger hash to identify the cache.
            key (str): The specific key for the cache data.
        Returns:
            (str | bool): The cached ledger data or False if not found.
        """
        cache_header = cache.get(ledger_hash, False)

        logger.debug(f"Cache Header: {cache_header}, Journal Hash: {ledger_hash}")

        journal_is_up_to_date = cache_header == ledger_hash
        hash_key = self.build_ledger_cache_key(ledger_hash)

        if journal_is_up_to_date and LEDGER_CACHE_ENABLED:
            logger.debug(f"Ledger Cache Hit: {hash_key} for Key: {key}")
            cached_ledger = cache.get(f"{hash_key}-{key}", False)
            return cached_ledger
        return False

    def set_cache_key(self, key: str, ledger_hash: str, ledger_data) -> None:
        """
        Set the cache for ledger data.

        This function sets the cache for ledger data using a key for identification.

        Args:
            key: (str): The specific key for the cache data.
            ledger_hash (str): The ledger hash to identify the cache.
            ledger_data (LedgerResponse): The ledger data to cache.
        Returns:
            None
        """
        hash_key = self.build_ledger_cache_key(ledger_hash)

        if LEDGER_CACHE_ENABLED is False:
            logger.debug("Caching is Disabled")
            return False

        logger.debug(f"Setting Cache: {hash_key} for Key: {key}")
        # Set the data in the cache
        cache.set(
            key=f"{hash_key}-{key}", value=ledger_data, timeout=LEDGER_CACHE_STALE
        )
        # Set the cache header to indicate the cache is up-to-date
        cache.set(key=ledger_hash, value=ledger_hash, timeout=None)
        return True
