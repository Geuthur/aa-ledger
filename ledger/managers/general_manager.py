# Standard Library
from typing import TYPE_CHECKING, Any, Literal

# Django
from django.db import models
from django.utils import timezone

# Alliance Auth (External Libs)
from eve_sde.models import ItemType

# AA Ledger
from ledger.app_settings import LEDGER_BULK_BATCH_SIZE
from ledger.providers import esi, logger

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import MarketsPricesGetItem

    # AA Ledger
    from ledger.models.general import EveEntity as EveEntityContext
    from ledger.models.general import EveMarketPrice as EveMarketPriceContext


class GeneralManager(models.Manager):
    """App rules that Django cannot check itself.

    General is unmanaged, so this manager never queries the database.
    """

    def has_basic_access(self, user) -> bool:
        """True if the user may use the app."""
        return user.has_perm("ledger.basic_access")

    def has_advanced_access(self, user) -> bool:
        """True if the user may access Corporation and Alliance Ledger."""
        return user.has_perm("ledger.advanced_access")

    def has_manage_access(self, user) -> bool:
        """True if the user holds the general manage permission."""
        return user.has_perm("ledger.manage_access")

    def has_char_audit_access(self, user) -> bool:
        """True if the user may see and manage characters of the own corporation."""
        return user.has_perm("ledger.char_audit_manager")

    def has_char_audit_admin_access(self, user) -> bool:
        """True if the user may see and manage all characters."""
        return user.has_perm("ledger.char_audit_admin_manager")

    def has_corp_audit_access(self, user) -> bool:
        """True if the user may manage the own corporations."""
        return user.has_perm("ledger.corp_audit_manager")

    def has_corp_audit_admin_access(self, user) -> bool:
        """True if the user may see and manage all corporations."""
        return user.has_perm("ledger.corp_audit_admin_manager")

    def has_management_access(self, user) -> bool:
        """True if the user holds any management permission."""
        return any(
            user.has_perm(perm)
            for perm in (
                "ledger.manage_access",
                "ledger.char_audit_manager",
                "ledger.char_audit_admin_manager",
                "ledger.corp_audit_manager",
                "ledger.corp_audit_admin_manager",
            )
        )

    def has_admin_management_access(self, user) -> bool:
        """True if the user holds a system-wide audit admin permission."""
        return any(
            user.has_perm(perm)
            for perm in (
                "ledger.char_audit_admin_manager",
                "ledger.corp_audit_admin_manager",
            )
        )

    def has_delete_access(
        self, owner_type: Literal["character", "corporation"], user
    ) -> bool:
        """True if the user may delete owners of the given type."""
        if not getattr(user, "is_authenticated", False):
            return False
        if owner_type == "character":
            return self.has_char_audit_admin_access(user)
        if owner_type == "corporation":
            return self.has_corp_audit_admin_access(user)
        return False


class EveEntityManager(models.Manager["EveEntityContext"]):
    def get_or_create_esi(self, *, eve_id: int) -> tuple[Any, bool]:
        """gets or creates entity object with data fetched from ESI"""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models import EveEntity

        try:
            entity = self.get(eve_id=eve_id)
            return entity, False
        except EveEntity.DoesNotExist:
            return self.update_or_create_esi(eve_id=eve_id)

    def create_bulk_from_esi(self, eve_ids):
        """gets bulk names with ESI"""
        if len(eve_ids) > 0:
            # pylint: disable=import-outside-toplevel
            # AA Ledger
            from ledger.models.general import EveEntity

            chunk_size = 500
            id_chunks = [
                eve_ids[i : i + chunk_size] for i in range(0, len(eve_ids), chunk_size)
            ]
            for chunk in id_chunks:
                response = esi.client.Universe.PostUniverseNames(body=chunk).results()
                new_names = []
                logger.debug(
                    "Eve Entity Manager EveName: count in %s count out %s",
                    len(chunk),
                    len(response),
                )
                for entity in response:
                    new_names.append(
                        EveEntity(
                            eve_id=entity.id,
                            name=entity.name,
                            category=entity.category,
                        )
                    )
                EveEntity.objects.bulk_create(
                    new_names, batch_size=LEDGER_BULK_BATCH_SIZE, ignore_conflicts=True
                )
            return True
        return True

    def update_or_create_esi(self, *, eve_id: int) -> tuple[Any, bool]:
        """updates or creates entity object with data fetched from ESI"""
        response = esi.client.Universe.PostUniverseNames(body=[eve_id]).results()
        if len(response) != 1:
            raise ValueError(f"Unknown Type with ID {eve_id} not found.")
        entity_data = response[0]
        return self.update_or_create(
            eve_id=entity_data.id,
            defaults={
                "name": entity_data.name,
                "category": entity_data.category,
            },
        )


class EveMarketPriceManager(models.Manager["EveMarketPriceContext"]):
    def update_from_esi(self) -> int:
        """Update or create EveMarketPrice from ESI data."""

        prices = self.fetch_data_from_esi()
        if not prices:
            logger.debug("No market price data fetched from ESI.")
            return 0

        updated_prices = self.update_objs_from_esi(prices)
        return updated_prices

    def fetch_data_from_esi(self) -> list["MarketsPricesGetItem"]:
        """Fetch market price data from ESI."""
        response = esi.client.Market.GetMarketsPrices().results(use_etag=False)
        return response

    def update_objs_from_esi(self, objs: list["MarketsPricesGetItem"]) -> int:
        """Update or create EveMarketPrice objects from ESI data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.general import EveMarketPrice

        _update_price = []
        _new_price = []
        _esi_market_type_ids = {obj.type_id for obj in objs}
        _current_market_prices = {
            market_price.eve_type_id: market_price
            for market_price in EveMarketPrice.objects.filter(
                eve_type_id__in=_esi_market_type_ids
            )
        }
        _now = timezone.now()

        for obj in objs:
            if obj.type_id in _current_market_prices:
                eve_market_type = _current_market_prices[obj.type_id]
                eve_market_type.average_price = obj.average_price
                eve_market_type.adjusted_price = obj.adjusted_price
                eve_market_type.updated_at = _now
                _update_price.append(eve_market_type)
            else:
                eve_market_type = EveMarketPrice(
                    eve_type=ItemType.objects.get(
                        id=obj.type_id
                    ),  # TODO: optimize get? to avoid that much queries
                    average_price=obj.average_price,
                    adjusted_price=obj.adjusted_price,
                    updated_at=_now,
                )
                _new_price.append(eve_market_type)

        if _update_price:
            self.bulk_update(
                _update_price,
                fields=["average_price", "adjusted_price", "updated_at"],
                batch_size=LEDGER_BULK_BATCH_SIZE,
            )
        if _new_price:
            self.bulk_create(
                _new_price, batch_size=LEDGER_BULK_BATCH_SIZE, ignore_conflicts=True
            )
        return len(objs)
