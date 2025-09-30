"""PvE Views"""

# Standard Library
import json
from decimal import Decimal
from typing import Any

# Django
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import DecimalField, Q, QuerySet, Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.app_settings import LEDGER_CACHE_ENABLED, LEDGER_CACHE_STALE
from ledger.constants import NPC_ENTITIES
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationData(LedgerCore):
    """Class to hold character data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        corporation: CorporationAudit,
        division_id: int = None,
        request: WSGIRequest = None,
        year: int = None,
        month: int = None,
        day: int = None,
    ):
        LedgerCore.__init__(self, year, month, day)
        self.request = request
        self.corporation = corporation
        self.division_id = division_id
        self.auth_char_ids = self.auth_character_ids
        self.billboard = BillboardSystem()

    def setup_ledger(self, entity: LedgerEntity = None):
        """Setup the Ledger Data for the Corporation."""
        corporation_id = self.corporation.corporation.corporation_id

        # Base queryset filtered by date and corporation division
        base_qs = self._base_journal_queryset()

        if entity is None:
            # No entity specified: show all entries for the corporation (except self-transfers)
            self.journal = base_qs.exclude(
                first_party_id=corporation_id, second_party_id=corporation_id
            )
            # Prepare auxiliary data used by the view
            self.existing_years = self._compute_existing_years()
            self.entities = self._compute_entities()
            return

        # If the entity is the corporation itself and "all" is set, show all entries
        if (
            self.request is not None
            and self.request.GET.get("all", False)
            and entity.entity_id == corporation_id
        ):
            self.journal = base_qs.exclude(
                first_party_id=corporation_id, second_party_id=corporation_id
            )
            self.entities = self._compute_entities()
            return

        # Regular entity filtering: include any rows where the entity is a first or second party
        character_ids = entity.get_alts_ids_or_self()
        qs = base_qs.filter(
            Q(first_party_id__in=character_ids) | Q(second_party_id__in=character_ids)
        )
        qs = qs.exclude(first_party_id=corporation_id, second_party_id=corporation_id)

        # If the entity is the corporation itself, include NPC transactions too
        if entity.entity_id == corporation_id:
            qs = qs.filter(
                Q(first_party_id__in=NPC_ENTITIES) | Q(second_party_id__in=NPC_ENTITIES)
            )

        # If entity represents a corporation or alliance, exclude auth account character IDs
        # that are not part of the current entity to avoid double counting
        if entity.type in ["alliance", "corporation"]:
            exclude_ids = self.auth_char_ids - set(character_ids)
            qs = qs.exclude(
                Q(first_party_id__in=exclude_ids) | Q(second_party_id__in=exclude_ids)
            )

        self.journal = qs
        self.entities = self._compute_entities()

    def _base_journal_queryset(self):
        """Return the base queryset filtered by the current date range and corporation division."""
        if self.division_id is not None:
            return CorporationWalletJournalEntry.objects.filter(
                self.filter_date,
                division__corporation=self.corporation,
                division=self.division_id,
            )
        return CorporationWalletJournalEntry.objects.filter(
            self.filter_date, division__corporation=self.corporation
        )

    def _compute_entities(self):
        """Return a set of all entity IDs (first and second parties) present in the current journal."""
        return set(self.journal.values_list("second_party_id", flat=True)) | set(
            self.journal.values_list("first_party_id", flat=True)
        )

    def _compute_existing_years(self):
        """Return the available years for journal entries for this corporation."""
        return (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation=self.corporation
            )
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

    # pylint: disable=duplicate-code
    def _compute_journal_values(self) -> QuerySet[dict[str, Any]]:
        """Return the journal values for the current journal."""
        return self.journal.values(
            "first_party_id", "second_party_id", "pk", "ref_type"
        ).annotate(
            bounty=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.BOUNTY_PRIZES),
                output_field=DecimalField(),
            ),
            ess=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.ESS_TRANSFER),
                output_field=DecimalField(),
            ),
            costs=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__lt=0),
                output_field=DecimalField(),
            ),
            miscellaneous=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__gt=0),
                output_field=DecimalField(),
            ),
        )

    def create_entity_data(
        self,
        entity: LedgerEntity,
        alts: EveCharacter = None,
    ) -> dict:
        """Create the URL for entity details based on the view type."""
        ids = (
            list(alts.values_list("character__character_id", flat=True))
            if alts is not None
            else [entity.entity_id]
        )

        # Create Alts Dictionary
        alts_dict = {}
        if alts is not None:
            for alt in alts:
                alts_dict[alt.character.character_id] = alt.character.character_name

            # Remove the main character from the alts dictionary only one entry
            if len(alts_dict) == 1:
                alts_dict.pop(entity.entity_id, None)

        used_pks = set()
        bounty = Decimal(0)
        ess = Decimal(0)
        miscellaneous = Decimal(0)
        costs = Decimal(0)

        for pk, rows in list(self.entries.items()):
            for row in rows:
                if row["first_party_id"] in ids or row["second_party_id"] in ids:
                    if RefTypeManager.special_cases(
                        row, ids=ids, account_char_ids=self.auth_char_ids
                    ):
                        continue
                    bounty += row.get("bounty") or Decimal(0)
                    ess += row.get("ess") or Decimal(0)
                    miscellaneous += row.get("miscellaneous") or Decimal(0)
                    costs += row.get("costs") or Decimal(0)
                    used_pks.add(pk)

        # Remove Used Pks from Entries
        # This is to prevent the entries from being used in the future
        for pk in used_pks:
            self.entries.pop(pk, None)

        total = sum([bounty, ess, miscellaneous, costs])

        if total == 0:
            return None

        char_data = {
            "entity": entity,
            "alts": alts_dict,
            "ledger": {
                "bounty": bounty,
                "ess": ess,
                "miscellaneous": miscellaneous,
                "costs": costs,
                "total": total,
            },
            "type": entity.type,
        }

        return char_data

    def generate_ledger_data(self) -> dict:
        """
        Generate the ledger data for the corporation.

        This method processes the journal entries, builds the ledger data,
        and prepares the context for rendering the corporation ledger view.
        """
        ledger = False
        finished_entities = False

        # Prepare Queryset and auxiliary data
        self.setup_ledger()
        # Compute journal values
        journal = self._compute_journal_values()

        # Get the journal hash and cache header
        ledger_hash = self._get_ledger_journal_hash(journal.values_list("pk"))
        ledger_header = self._get_ledger_header(
            ledger_args=f"{self.corporation.corporation.corporation_id}_{self.division_id}",
            year=self.year,
            month=self.month,
            day=self.day,
        )
        cache_header = cache.get(
            ledger_header,
            False,
        )
        logger.debug(
            f"Ledger Header: {ledger_header}, Cache Header: {cache_header}, Journal Hash: {ledger_hash}"
        )

        # Check if the journal is up to date
        journal_up_to_date = cache_header == ledger_hash
        ledger_key = self._build_ledger_cache_key(ledger_header)

        # Check if we have newest cached version of the ledger
        if journal_up_to_date and LEDGER_CACHE_ENABLED:
            ledger = cache.get(f"{ledger_key}-data", False)
            finished_entities = cache.get(f"{ledger_key}-finished_entities", False)

        if finished_entities is False or ledger is False:
            # Build the entries from the journal
            self.entries = {}
            for row in journal:
                self.entries.setdefault(row["pk"], []).append(row)

            # Process Auth Accounts first
            ledger, finished_entities = self._process_auth_accounts()
            # Process remaining entities
            self._process_remaining_entities(ledger, finished_entities)
            # Process corporation entity last to ensure it's always included
            self._handle_entity(
                ledger=ledger,
                entity_id=self.corporation.corporation.corporation_id,
                corporation_obj=self.corporation.corporation,
            )
        # Finalize the billboard for the ledger.
        self.create_rattingbar(list(finished_entities))
        self.create_chord(ledger)

        context = self._build_context(ledger=ledger)

        # Create Cache
        cache.set(key=f"{ledger_key}-data", value=ledger, timeout=LEDGER_CACHE_STALE)
        cache.set(
            key=f"{ledger_key}-finished_entities",
            value=finished_entities,
            timeout=LEDGER_CACHE_STALE,
        )
        cache.set(
            key=self._get_ledger_header(
                ledger_args=f"{self.corporation.corporation.corporation_id}_{self.division_id}",
                year=self.year,
                month=self.month,
                day=self.day,
            ),
            value=ledger_hash,
            timeout=None,  # Cache forever until the journal changes
        )
        return context

    def generate_data_export(self) -> dict:
        """Generate the data export for the corporation."""
        self.setup_ledger()
        journal = self._compute_journal_values()

        # Build the entries from the journal
        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

        # Process Auth Accounts first
        ledger, finished_entities = self._process_auth_accounts()
        # Process remaining entities
        self._process_remaining_entities(ledger, finished_entities)
        # Process corporation entity last to ensure it's always included
        self._handle_entity(
            ledger=ledger,
            entity_id=self.corporation.corporation.corporation_id,
            corporation_obj=self.corporation.corporation,
        )
        return ledger

    def _build_view_data(self, entity_id: int):
        details_kwargs = {
            "viewname": "corporation_details",
            "corporation_id": self.corporation.corporation.corporation_id,
            "entity_id": entity_id,
        }
        if self.division_id is not None:
            details_kwargs["division_id"] = self.division_id
        return details_kwargs

    def _build_view_url(self, entity_id: int):
        """Return the full URL for a corporation view for the given entity id.

        This wraps create_url(**self._build_view_data(...)) so callers can
        request the URL in a single, readable call without losing ordering.
        """
        return self.create_url(**self._build_view_data(entity_id=entity_id))

    # pylint: disable=too-many-arguments
    def _handle_entity(
        self,
        ledger: list,
        entity_id: int,
        character_obj=None,
        corporation_obj=None,
        alts=None,
        add_finished: bool = True,
        finished_ids=None,
    ) -> set:
        """Create entity object, add to ledger if it has data and return IDs to mark finished.

        - ledger: list to append to
        - entity_id: numeric id
        - character_obj / corporation_obj: optional objects to attach to LedgerEntity
        - alts: optional alts queryset passed to create_entity_data
        - add_finished: whether to return ids that should be added to finished_entities
        - finished_ids: explicit IDs (set or iterable) to mark finished (used for accounts)
        """
        details_url = self._build_view_url(entity_id)
        entity_obj = LedgerEntity(
            entity_id,
            character_obj=character_obj,
            corporation_obj=corporation_obj,
            details_url=details_url,
        )

        # Create the character data for the ledger
        char_data = self.create_entity_data(entity=entity_obj, alts=alts)

        # Only add to ledger if there is data
        if char_data is None:
            return set()

        ledger.append(char_data)

        if not add_finished:
            return set()

        if finished_ids is not None:
            return set(finished_ids)

        return {entity_id}

    def _process_auth_accounts(self):
        """Process Auth Account information for the ledger."""
        ledger = []
        finished_entities = set()
        for account in self.auth_accounts:
            alts = account.user.character_ownerships.all()
            existing_alts = set(
                alts.values_list("character__character_id", flat=True)
            ).intersection(self.entities)
            alts = alts.filter(character__character_id__in=existing_alts)
            if not existing_alts:
                continue
            finished_entities.update(
                self._handle_entity(
                    ledger,
                    account.main_character.character_id,
                    character_obj=account.main_character,
                    alts=alts,
                    finished_ids=existing_alts,
                )
            )
        return ledger, finished_entities

    def _process_remaining_entities(self, ledger, finished_entities: set):
        """Process remaining entities for the ledger."""
        remaining_entities = self.entities - finished_entities
        if not remaining_entities:
            return
        for entity_id in remaining_entities:
            if entity_id in NPC_ENTITIES:
                continue
            if entity_id == self.corporation.corporation.corporation_id:
                continue
            finished_entities.update(self._handle_entity(ledger, entity_id))

    def _build_context(self, ledger):
        """Build the context for the ledger view."""
        view = self._build_view_data(
            entity_id=self.corporation.corporation.corporation_id
        )

        context = {
            "title": f"Corporation Ledger - {self.corporation.corporation.corporation_name}",
            "corporation_id": self.corporation.corporation.corporation_id,
            "division_id": self.division_id,
            "billboard": json.dumps(self.billboard.dict.asdict()),
            "ledger": ledger,
            "divisions": CorporationWalletDivision.objects.filter(
                corporation=self.corporation
            ).order_by("division_id"),
            "years": list(self.existing_years),
            "totals": self._calculate_totals(ledger),
            "view": self.create_view_data(**view),
        }
        return context

    def create_rattingbar(self, entities_ids: list = None):
        """Create the ratting bar for the view."""
        if not entities_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(self.journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        self.billboard.create_or_update_results(rattingbar)
        series, categories = self.billboard.generate_xy_series()
        self.billboard.create_xy_chart(
            title=_("Ratting Bar"), categories=categories, series=series
        )

    def create_chord(self, ledger_data: list[dict]):
        """Create the chord chart for the view."""
        if not ledger_data:
            return

        for entry in ledger_data:
            entity_name = entry["entity"].entity_name
            ledger = entry["ledger"]
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Bounty (Wallet)"),
                value=ledger.get("bounty", 0),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("ESS (Wallet)"),
                value=ledger.get("ess", 0),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Costs (Wallet)"),
                value=abs(ledger.get("costs", 0)),
            )
            self.billboard.chord_add_data(
                chord_from=entity_name,
                chord_to=_("Miscellaneous (Wallet)"),
                value=abs(ledger.get("miscellaneous", 0)),
            )
        self.billboard.chord_handle_overflow()
