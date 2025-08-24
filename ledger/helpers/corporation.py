"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

# Django
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import DecimalField, Q, Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.app_settings import LEDGER_CACHE_STALE
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

NPC_ENTITIES = [
    1000125,  # Concord Bounties (Bounty Prizes, ESS
    1000132,  # Secure Commerce Commission (Market Fees)
    1000413,  # Air Laboratories (Daily Login Rewards, etc.)
]


class CorporationData(LedgerCore):
    """Class to hold character data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        request: WSGIRequest,
        corporation: CorporationAudit,
        year=None,
        month=None,
        day=None,
    ):
        LedgerCore.__init__(self, year, month, day)
        self.request = request
        self.corporation = corporation
        self.auth_char_ids = self.auth_character_ids

    def setup_ledger(self, entity: LedgerEntity = None):
        """Setup the Ledger Data for the Corporation."""
        if entity is not None:
            if (
                self.request.GET.get("all", False)
                and entity.entity_id == self.corporation.corporation.corporation_id
            ):
                self.journal = CorporationWalletJournalEntry.objects.filter(
                    self.filter_date,
                    division__corporation=self.corporation,
                ).exclude(  # Filter by date and division
                    first_party_id=self.corporation.corporation.corporation_id,
                    second_party_id=self.corporation.corporation.corporation_id,
                )  # exclude Transaction between the corporation itself
            else:
                character_ids = entity.get_alts_ids_or_self()
                self.journal = (
                    CorporationWalletJournalEntry.objects.filter(
                        self.filter_date,
                        division__corporation=self.corporation,
                    )  # Filter by date and division
                    .filter(
                        Q(first_party_id__in=character_ids)
                        | Q(second_party_id__in=character_ids)
                    )  # Filter only needed Character IDs
                    .exclude(
                        first_party_id=self.corporation.corporation.corporation_id,
                        second_party_id=self.corporation.corporation.corporation_id,
                    )  # exclude Transaction between the corporation itself
                )

                if entity.entity_id == self.corporation.corporation.corporation_id:
                    self.journal = self.journal.filter(
                        Q(first_party_id__in=NPC_ENTITIES)
                        | Q(second_party_id__in=NPC_ENTITIES)
                    )

                # If the entity is a corporation or alliance, we need to exclude the accounts Character IDs
                # from the journal to prevent double counting
                if entity.type in ["alliance", "corporation"]:
                    exclude_ids = self.auth_char_ids - set(character_ids)
                    self.journal = self.journal.exclude(
                        Q(first_party_id__in=exclude_ids)
                        | Q(second_party_id__in=exclude_ids)
                    )
            # Get All Entities from the Journal
            self.entities = set(
                self.journal.values_list("second_party_id", flat=True)
            ) | set(self.journal.values_list("first_party_id", flat=True))
        else:
            self.journal = CorporationWalletJournalEntry.objects.filter(
                self.filter_date, division__corporation=self.corporation
            ).exclude(  # Filter by date and division
                first_party_id=self.corporation.corporation.corporation_id,
                second_party_id=self.corporation.corporation.corporation_id,
            )  # exclude Transaction between the corporation itself

            # Evaluate the existing years for the view
            self.existing_years = (
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation=self.corporation
                )
                .exclude(date__year__isnull=True)
                .values_list("date__year", flat=True)
                .order_by("-date__year")
                .distinct()
            )

            # Get All Entities from the Journal
            self.entities = set(
                self.journal.values_list("second_party_id", flat=True)
            ) | set(self.journal.values_list("first_party_id", flat=True))

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

        # Create the chord data for the billboard
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Ratting (Wallet)"),
            value=bounty,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("ESS (Wallet)"),
            value=ess,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Costs (Wallet)"),
            value=abs(costs),
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to=_("Miscellaneous (Wallet)"),
            value=abs(miscellaneous),
        )

        return char_data

    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the corporation."""
        self.setup_ledger()

        journal = self.journal.values(
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

        # Get the journal hash and cache header
        ledger_hash = self._get_ledger_journal_hash(self.journal.values_list("pk"))
        ledger_header = self._get_ledger_header(
            self.corporation.corporation.corporation_id,
            self.year,
            self.month,
            self.day,
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
        cached_ledger = self._get_cached_ledger(
            journal_up_to_date, ledger_key, ledger_hash
        )
        if cached_ledger is not None:
            return cached_ledger

        # Build the entries from the journal
        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

        ledger, finished_entities = self._process_accounts()
        self._process_remaining_entities(ledger, finished_entities)
        self._add_corporation_entity(ledger)

        # Finalize the billboard for the ledger.
        self.create_rattingbar(list(finished_entities))
        self.billboard.chord_handle_overflow()

        context = self._build_context(ledger_hash, ledger)
        cache.set(key=ledger_key, value=context, timeout=LEDGER_CACHE_STALE)
        cache.set(
            key=self._get_ledger_header(
                self.corporation.corporation.corporation_id,
                self.year,
                self.month,
                self.day,
            ),
            value=ledger_hash,
            timeout=None,  # Cache forever until the journal changes
        )
        return context

    def _process_accounts(self):
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
            details_url = self.create_url(
                viewname="corporation_details",
                corporation_id=self.corporation.corporation.corporation_id,
                entity_id=account.main_character.character_id,
            )
            entity_obj = LedgerEntity(
                account.main_character.character_id,
                character_obj=account.main_character,
                details_url=details_url,
            )
            char_data = self.create_entity_data(
                entity=entity_obj,
                alts=alts,
            )
            if char_data is None:
                continue
            ledger.append(char_data)
            finished_entities.update(existing_alts)
        return ledger, finished_entities

    def _process_remaining_entities(self, ledger, finished_entities):
        """Process remaining entities for the ledger."""
        remaining_entities = self.entities - finished_entities
        if not remaining_entities:
            return
        for entity_id in remaining_entities:
            if entity_id in NPC_ENTITIES:
                continue
            if entity_id == self.corporation.corporation.corporation_id:
                continue
            details_url = self.create_url(
                viewname="corporation_details",
                corporation_id=self.corporation.corporation.corporation_id,
                entity_id=entity_id,
            )
            entity_obj = LedgerEntity(
                entity_id,
                details_url=details_url,
            )
            entity_data = self.create_entity_data(
                entity=entity_obj,
            )
            if entity_data is None:
                continue
            ledger.append(entity_data)
            finished_entities.add(entity_id)

    def _add_corporation_entity(self, ledger):
        """Add the corporation entity to the ledger."""
        corporation_entity = LedgerEntity(
            self.corporation.corporation.corporation_id,
            corporation_obj=self.corporation.corporation,
            details_url=self.create_url(
                viewname="corporation_details",
                corporation_id=self.corporation.corporation.corporation_id,
                entity_id=self.corporation.corporation.corporation_id,
            ),
        )
        corporation_data = self.create_entity_data(
            entity=corporation_entity,
        )
        if corporation_data is not None:
            ledger.append(corporation_data)

    def _build_context(self, journal_hash, ledger):
        """Build the context for the ledger view."""
        return {
            "ledger_hash": journal_hash,
            "title": f"Corporation Ledger - {self.corporation.corporation.corporation_name}",
            "corporation_id": self.corporation.corporation.corporation_id,
            "billboard": json.dumps(self.billboard.dict.asdict()),
            "ledger": ledger,
            "years": list(self.existing_years),
            "totals": self._calculate_totals(ledger),
            "view": self.create_view_data(
                viewname="corporation_details",
                corporation_id=self.corporation.corporation.corporation_id,
                entity_id=self.corporation.corporation.corporation_id,
            ),
        }

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
        self.billboard.create_ratting_bar()
