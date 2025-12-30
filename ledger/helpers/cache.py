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

    @staticmethod
    def build_billboard_cache_key(billboard_key: str) -> str:
        """Build a cache key for billboard data."""
        logger.debug(f"Building Billboard Cache Key for Bill Key: {billboard_key}")
        return f"{LEDGER_CACHE_KEY}-billboard-{billboard_key}"

    def get_cache_ledger(self, ledger_hash: str) -> str:
        """
        Get the cache for ledger data.

        This function retrieves the cached ledger data using a unique ledger hash as the key.

        Args:
            ledger_hash (str): The ledger hash to identify the cache.

        Returns:
            (str | bool): The cached ledger data or False if not found.
        """
        cache_header = cache.get(ledger_hash, False)

        logger.debug(f"Cache Header: {cache_header}, Journal Hash: {ledger_hash}")

        journal_is_up_to_date = cache_header == ledger_hash
        ledger_key = self.build_ledger_cache_key(ledger_hash)

        if journal_is_up_to_date and LEDGER_CACHE_ENABLED:
            logger.debug(f"Ledger Cache Hit: {ledger_key}")
            cached_ledger = cache.get(f"{ledger_key}-data", False)
            return cached_ledger
        return False

    def get_cache_billboard(self, billboard_hash: str):
        """
        Get the cache for billboard data.

        This function retrieves the cached billboard data using a unique billboard key.

        Args:
            bill_key (str): The billboard key to identify the cache.

        Returns:
            (BillboardSchema | bool): The cached billboard data or False if not found.
        """
        cache_header = cache.get(billboard_hash, False)

        logger.debug(
            f"Billboard Cache Header: {cache_header}, Billboard Hash: {billboard_hash}"
        )

        journal_is_up_to_date = cache_header == billboard_hash
        billboard_key = self.build_billboard_cache_key(billboard_hash)
        if journal_is_up_to_date and LEDGER_CACHE_ENABLED:
            logger.debug(f"Billboard Cache Hit: {billboard_key}")
            cached_billboard = cache.get(billboard_key, False)
            return cached_billboard
        return False

    def set_cache_billboard(self, billboard_hash: str, billboard_data) -> None:
        """
        Set the cache for billboard data.

        This function sets the cache for billboard data using a unique billboard key as the key.

        Args:
            bill_key (str): The billboard key to identify the cache.
            billboard_data (BillboardSchema): The billboard data to cache.
        Returns:
            None
        """
        billboard_key = self.build_billboard_cache_key(billboard_hash)

        logger.debug(f"Setting Billboard Cache: {billboard_key}")

        cache.set(key=billboard_key, value=billboard_data, timeout=LEDGER_CACHE_STALE)
        cache.set(key=billboard_hash, value=billboard_hash, timeout=None)
        return True

    def set_cache_ledger(self, ledger_hash: str, ledger_data) -> None:
        """
        Set the cache for ledger data.

        This function sets the cache for ledger data using a unique ledger hash as the key.

        Args:
            ledger_hash (str): The ledger hash to identify the cache.
            ledger_data (LedgerResponse): The ledger data to cache.

        Returns:
            None
        """
        ledger_key = self.build_ledger_cache_key(ledger_hash)

        logger.debug(f"Setting Ledger Cache: {ledger_key}")

        cache.set(
            key=f"{ledger_key}-data", value=ledger_data, timeout=LEDGER_CACHE_STALE
        )
        cache.set(key=ledger_hash, value=ledger_hash, timeout=None)
        return True
