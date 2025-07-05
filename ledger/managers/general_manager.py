# Standard Library
from typing import Any

# Django
from django.db import models

# Alliance Auth
from allianceauth.eveonline.providers import ObjectNotFound
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveEntityManager(models.Manager):
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
                response = esi.client.Universe.post_universe_names(ids=chunk).results()
                new_names = []
                logger.debug(
                    "Eve Entity Manager EveName: count in %s count out %s",
                    len(chunk),
                    len(response),
                )
                for entity in response:
                    new_names.append(
                        EveEntity(
                            eve_id=entity["id"],
                            name=entity["name"],
                            category=entity["category"],
                        )
                    )
                EveEntity.objects.bulk_create(new_names, ignore_conflicts=True)
            return True
        return True

    def update_or_create_esi(self, *, eve_id: int) -> tuple[Any, bool]:
        """updates or creates entity object with data fetched from ESI"""
        response = esi.client.Universe.post_universe_names(ids=[eve_id]).results()
        if len(response) != 1:
            raise ObjectNotFound(eve_id, "unknown_type")
        entity_data = response[0]
        return self.update_or_create(
            eve_id=entity_data["id"],
            defaults={
                "name": entity_data["name"],
                "category": entity_data["category"],
            },
        )
