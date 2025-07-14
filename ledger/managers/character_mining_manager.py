# Standard Library
from collections import defaultdict
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Ledger
from ledger import __title__
from ledger.decorators import log_timing
from ledger.helpers.etag import etag_results
from ledger.providers import esi

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.characteraudit import (
        CharacterAudit,
    )
    from ledger.models.general import UpdateSectionResult

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharacterMiningLedgerEntryQueryset(models.QuerySet):
    def annotate_pricing(self) -> models.QuerySet:
        """Annotate price and total columns."""
        return self.annotate(price=F("type__market_price__average_price")).annotate(
            total=ExpressionWrapper(
                F("type__market_price__average_price") * F("quantity"),
                output_field=models.DecimalField(),
            ),
        )

    def annotate_mining(self) -> models.QuerySet:
        """Annotate mining columns."""
        return (
            self.annotate_pricing()
            .values(
                "character__character__character_id",
                "character__character__character_name",
            )
            .annotate(
                total_amount=Round(
                    Coalesce(
                        Sum(F("total")),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                    precision=2,
                )
            )
        )

    def aggregate_amounts_information_modal(
        self, amounts: defaultdict, chars_list: list, filter_date: timezone.datetime
    ) -> dict:
        """Generate data template for the ledger character information view."""
        qs = self.filter(Q(character__character__character_id__in=chars_list))
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
        qs = self.filter(Q(character__character__character_id__in=chars_list))
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
        self, character: "CharacterAudit", force_refresh: bool = False
    ) -> None:
        """Fetch mining ledger entries from ESI data."""
        req_scopes = ["esi-industry.read_character_mining.v1"]

        token = character.get_token(scopes=req_scopes)
        mining_obj = esi.client.Industry.get_characters_character_id_mining(
            character_id=character.character.character_id
        )
        mining_items = etag_results(mining_obj, token, force_refresh=force_refresh)
        self._update_or_create_objs(character, mining_items)

    @transaction.atomic()
    def _update_or_create_objs(self, character: "CharacterAudit", objs: list) -> None:
        """Update or Create mining ledger entries from objs data."""
        existings_pks = set(
            self.filter(
                character=character,
                date__gte=timezone.now() - timezone.timedelta(days=30),
            ).values_list("id", flat=True)
        )
        type_ids = set()
        new_events = []
        old_events = []
        for entry in objs:
            type_ids.add(entry.get("type_id"))
            pk = self.model.create_primary_key(character.pk, entry)
            _e = self.model(
                character=character,
                id=pk,
                date=entry.get("date"),
                type_id=entry.get("type_id"),
                system_id=entry.get("solar_system_id"),
                quantity=entry.get("quantity"),
            )
            if pk in existings_pks:
                old_events.append(_e)
            else:
                new_events.append(_e)

        EveType.objects.bulk_get_or_create_esi(ids=list(type_ids))

        if new_events:
            self.bulk_create(new_events, ignore_conflicts=True)

        if old_events:
            self.bulk_update(old_events, fields=["quantity"])


CharacterMiningLedgerEntryManager = CharacterMiningLedgerEntryManagerBase.from_queryset(
    CharacterMiningLedgerEntryQueryset
)
