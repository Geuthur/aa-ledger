# Standard Library
from collections import defaultdict
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveSolarSystem, EveType

# AA Ledger
from ledger import __title__
from ledger.app_settings import LEDGER_PRICE_PERCENTAGE
from ledger.decorators import log_timing
from ledger.providers import esi

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import CharactersCharacterIdMiningGetItem

    # AA Ledger
    from ledger.models.characteraudit import (
        CharacterAudit,
    )
    from ledger.models.general import UpdateSectionResult

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def require_valid_price_percentage(func):
    def wrapper(*args, **kwargs):
        if not isinstance(LEDGER_PRICE_PERCENTAGE, (int, float)):
            raise ValueError("LEDGER_PRICE_PERCENTAGE must be a number")
        if LEDGER_PRICE_PERCENTAGE <= 0:
            raise ValueError("LEDGER_PRICE_PERCENTAGE must be positive")
        return func(*args, **kwargs)

    return wrapper


class CharacterMiningLedgerEntryQueryset(models.QuerySet):
    @require_valid_price_percentage
    def annotate_pricing(self) -> models.QuerySet:
        """Annotate price and total columns."""
        return self.annotate(price=F("price_per_unit")).annotate(
            total=ExpressionWrapper(
                (F("price_per_unit") * F("quantity")) * LEDGER_PRICE_PERCENTAGE,
                output_field=models.DecimalField(),
            ),
        )

    def annotate_mining(self, with_period: bool = False) -> models.QuerySet:
        """Annotate mining columns."""
        qs = self.annotate_pricing()
        values_fields = [
            "character__eve_character__character_id",
            "character__eve_character__character_name",
        ]
        if with_period:
            values_fields.append("period")

        return qs.values(*values_fields).annotate(
            mining_income=Round(
                Coalesce(
                    Sum(F("total")),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            )
        )

    def aggregate_mining(self):
        """Aggregate mining amounts."""
        qs = self.annotate_pricing()
        return qs.aggregate(
            total_amount=Round(
                Coalesce(
                    Sum(F("total")),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            )
        )["total_amount"]

    def aggregate_amounts_information_modal(
        self, amounts: defaultdict, chars_list: list, filter_date: timezone.datetime
    ) -> dict:
        """Generate data template for the ledger character information view."""
        qs = self.filter(Q(character__eve_character__character_id__in=chars_list))
        qs = qs.annotate_pricing()
        qs = qs.aggregate(
            total_amount=Round(
                Coalesce(
                    Sum(F("total"), filter=Q(date__year=filter_date.year)),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            ),
            total_amount_day=Round(
                Coalesce(
                    Sum(F("total"), filter=Q(date__day=filter_date.day)),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            ),
        )

        amounts["mining"]["total_amount"] = qs["total_amount"]
        amounts["mining"]["total_amount_day"] = qs["total_amount_day"]

        return amounts

    def annotate_billboard(self, chars_list: list) -> models.QuerySet:
        """Annotate billboard columns."""
        qs = self.filter(Q(character__eve_character__character_id__in=chars_list))
        return qs.annotate(
            total_amount=Round(
                Coalesce(
                    Sum(F("total")),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            )
        )


class CharacterMiningLedgerEntryManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a mining ledger entry from ESI data."""
        return character.update_section_if_changed(
            section=character.UpdateSection.MINING_LEDGER,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, audit: "CharacterAudit", force_refresh: bool = False
    ) -> None:
        """Fetch mining ledger entries from ESI data."""
        req_scopes = ["esi-industry.read_character_mining.v1"]
        token = audit.get_token(scopes=req_scopes)

        # Make the ESI request
        operation = esi.client.Industry.GetCharactersCharacterIdMining(
            character_id=audit.eve_character.character_id,
            token=token,
        )

        mining_items = operation.results(force_refresh=force_refresh)

        # Process and update or create mining ledger entries
        self._update_or_create_objs(audit, mining_items)

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        character: "CharacterAudit",
        objs: list["CharactersCharacterIdMiningGetItem"],
    ) -> None:
        """Update or Create mining ledger entries from objs data."""
        existings_pks = set(
            self.filter(
                character=character,
                date__gte=timezone.now() - timezone.timedelta(days=30),
            ).values_list("id", flat=True)
        )
        type_ids = set()
        system_ids = set()
        new_events = []
        old_events = []

        for entry in objs:
            type_ids.add(entry.type_id)
            system_ids.add(entry.solar_system_id)
            pk = self.model.create_primary_key(character.pk, entry)
            _e = self.model(
                character=character,
                id=pk,
                date=entry.date,
                type_id=entry.type_id,
                system_id=entry.solar_system_id,
                quantity=entry.quantity,
            )
            if pk in existings_pks:
                old_events.append(_e)
            else:
                new_events.append(_e)

        # Ensure both EveType and EveSolarSystem objects exist before creating mining entries
        EveType.objects.bulk_get_or_create_esi(ids=list(type_ids))
        EveSolarSystem.objects.bulk_get_or_create_esi(ids=list(system_ids))

        if new_events:
            self.bulk_create(new_events, ignore_conflicts=True)

        if old_events:
            self.bulk_update(old_events, fields=["quantity"])

        self._update_mining_price(character)

    def _update_mining_price(self, character: "CharacterAudit") -> None:
        """Update prices for mining ledger entries."""
        # Update EveMarketPrice on a Daily basis
        self.model.update_evemarket_price()

        mining_ledger = character.mining_ledger.filter(price_per_unit__isnull=True)
        logger.debug(
            f"Checking {mining_ledger.count()} mining ledger entries for missing prices."
        )

        updated_entries = []
        for entry in mining_ledger:
            npc_price = entry.get_npc_price()
            if npc_price is not None:
                entry.price_per_unit = npc_price
                updated_entries.append(entry)

        if updated_entries:
            self.bulk_update(updated_entries, fields=["price_per_unit"])

        logger.debug(
            f"Updated prices for {len(updated_entries)}({character.character_name}) mining ledger entries."
        )


CharacterMiningLedgerEntryManager = CharacterMiningLedgerEntryManagerBase.from_queryset(
    CharacterMiningLedgerEntryQueryset
)
