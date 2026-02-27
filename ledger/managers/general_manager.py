# Standard Library
from typing import TYPE_CHECKING, Any

# Django
from django.db import models
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.providers import ObjectNotFound
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eve_sde.models import ItemType

# AA Ledger
from ledger import __title__
from ledger.app_settings import LEDGER_BULK_BATCH_SIZE
from ledger.providers import AppLogger, esi

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import MarketsPricesGetItem

    # AA Ledger
    from ledger.models.general import EveEntity as EveEntityContext
    from ledger.models.general import EveMarketPrice as EveMarketPriceContext


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
            raise ObjectNotFound(eve_id, "unknown_type")
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
        _current_market_prices = EveMarketPrice.objects.filter(
            eve_type_id__in=_esi_market_type_ids
        ).values_list("eve_type_id", flat=True)

        for obj in objs:
            eve_market_type = EveMarketPrice(
                eve_type=ItemType.objects.get(
                    id=obj.type_id
                ),  # TODO: optimize get? to avoid that much queries
                average_price=obj.average_price,
                adjusted_price=obj.adjusted_price,
                updated_at=timezone.now(),
            )

            if obj.type_id in _current_market_prices:
                _update_price.append(eve_market_type)
            else:
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
