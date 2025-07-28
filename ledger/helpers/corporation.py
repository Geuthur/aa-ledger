"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import DecimalField, Q, QuerySet, Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.core import LedgerCore, LedgerEntity
from ledger.helpers.ref_type import RefTypeCategories
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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

    def setup_ledger(self, entity: LedgerEntity = None):
        """Setup the Ledger Data for the Corporation."""

        # Get all Auth Accounts with main character
        self.accounts = (
            UserProfile.objects.filter(
                main_character__isnull=False,
            )
            .prefetch_related(
                "user__profile__main_character",
            )
            .order_by(
                "user__profile__main_character__character_name",
            )
        )

        if entity is not None:
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

            # Get All Entities from the Journal
            self.entities = set(
                self.journal.values_list("second_party_id", flat=True)
            ) | set(self.journal.values_list("first_party_id", flat=True))

            # If the entity is a corporation or alliance, we need to exclude the accounts Character IDs
            # from the journal to prevent double counting
            if entity.type in ["alliance", "corporation"]:
                exclude_ids = self.get_all_account_ids(accounts=self.accounts) - set(
                    character_ids
                )
                self.journal = self.journal.exclude(
                    Q(first_party_id__in=exclude_ids)
                    | Q(second_party_id__in=exclude_ids)
                )
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

    def get_all_account_ids(self, accounts: list[QuerySet]) -> set:
        """Get all account Character IDs for the corporation."""
        account_character_ids = set()
        for account in accounts:
            alts = account.user.character_ownerships.all()
            account_character_ids.update(
                alts.values_list("character__character_id", flat=True)
            )
        return account_character_ids

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

        used_pks = set()
        bounty = Decimal(0)
        ess = Decimal(0)
        miscellaneous = Decimal(0)
        costs = Decimal(0)

        for pk, rows in list(self.entries.items()):
            for row in rows:
                if row["first_party_id"] in ids or row["second_party_id"] in ids:
                    # Skip Market Transactions from buyer between the corporation and its members (Only Count Seller)
                    if (
                        row["ref_type"] == "market_transaction"
                        and row["first_party_id"] in ids
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

        misc = miscellaneous
        total = sum([bounty, ess, miscellaneous, costs])

        if total == 0:
            return None

        char_data = {
            "entity": entity,
            "alts": alts_dict,
            "ledger": {
                "bounty": bounty,
                "ess": ess,
                "miscellaneous": misc,
                "costs": costs,
                "total": total,
            },
            "type": entity.type,
        }

        # Create the chord data for the billboard
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="Wallet",
            value=bounty + ess + miscellaneous,
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="Costs",
            value=abs(costs),
        )
        self.billboard.chord_add_data(
            chord_from=entity.entity_name,
            chord_to="Miscellaneous",
            value=abs(miscellaneous),
        )

        return char_data

    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the character and its alts."""
        self.setup_ledger()

        ledger = []
        finished_entities = set()

        journal = self.journal.values(
            "first_party_id", "second_party_id", "pk", "ref_type"
        ).annotate(
            bounty=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.BOUNTY_PRIZES),
                output_field=DecimalField(),
            ),
            ess=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.ESS_TRANSFER),
                output_field=DecimalField(),
            ),
            costs=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.costs(), amount__lt=0),
                output_field=DecimalField(),
            ),
            miscellaneous=Sum(
                "amount",
                filter=Q(ref_type__in=RefTypeCategories.miscellaneous(), amount__gt=0),
                output_field=DecimalField(),
            ),
        )

        self.entries = {}
        for row in journal:
            self.entries.setdefault(row["pk"], []).append(row)

        for account in self.accounts:
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

            # Create the LedgerEntity object for the character
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

        remaining_entities = self.entities - finished_entities
        if remaining_entities:
            for entity_id in remaining_entities:
                # Skip NPC Entities like CONCORD, AIR Laboratories, etc.
                if entity_id in [
                    1000125,  # Concord Bounties (Bounty Prizes, ESS, etc.)
                    1000132,  # Secure Commerce Commission (Market Fees)
                    1000413,  # Air Laboratories (Daily Login Rewards, etc.)
                    self.corporation.corporation.corporation_id,
                ]:
                    continue

                # Create Details URL for the entity
                details_url = self.create_url(
                    viewname="corporation_details",
                    corporation_id=self.corporation.corporation.corporation_id,
                    entity_id=entity_id,
                )

                # Create the LedgerEntity object for the entity
                entity_obj = LedgerEntity(
                    entity_id,
                    details_url=details_url,
                )

                char_data = self.create_entity_data(
                    entity=entity_obj,
                )

                if char_data is None:
                    continue

                ledger.append(char_data)
                finished_entities.add(entity_id)

        # Create the billboard data
        self.create_rattingbar(list(finished_entities), is_char_ledger=False)
        # Prevent overflow in the chord data
        self.billboard.chord_handle_overflow()

        context = {
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
        return context

    def create_rattingbar(
        self, entities_ids: list = None, is_char_ledger: bool = False
    ):
        """Create the ratting bar for the view."""
        if not entities_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(self.journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        self.billboard.create_or_update_results(
            rattingbar, is_char_ledger=is_char_ledger
        )
        self.billboard.create_ratting_bar()

    # pylint: disable=duplicate-code
    def _create_corporation_details(self, entity: LedgerEntity) -> dict:
        """Create the corporation amounts for the Details View."""
        self.setup_ledger(entity=entity)

        amounts = {}

        ref_types_income = RefTypeCategories.get_miscellaneous()
        ref_types_costs = RefTypeCategories.get_costs()

        # Bounty Income
        if not entity.entity_id == 1000125:  # Remove Concord Bountys
            bounty_income = self.journal.aggregate_bounty()
            if bounty_income > 0:
                amounts["bounty_income"] = {"total_amount": bounty_income}

        # ESS Income (nur wenn bounty_income existiert)
        ess_income = self.journal.aggregate_ess()
        if ess_income > 0:
            amounts["ess_income"] = {"total_amount": ess_income}

        # Income Ref Types
        for ref_type, value in ref_types_income.items():
            ref_type_name = ref_type.lower()
            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=True,
            )
            if aggregated_data > 0:
                amounts[f"{ref_type_name}_income"] = {"total_amount": aggregated_data}

        # Cost Ref Types
        for ref_type, value in ref_types_costs.items():
            ref_type_name = ref_type.lower()

            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=False,
            )
            if aggregated_data < 0:
                amounts[f"{ref_type_name}_cost"] = {"total_amount": aggregated_data}

        # Summary
        summary = [
            amount
            for amount in amounts.values()
            if isinstance(amount, dict) and "total_amount" in amount
        ]

        summary = sum(
            amount["total_amount"] for amount in summary if "total_amount" in amount
        )

        if summary == 0:
            return None

        amounts["summary"] = {
            "total_amount": summary,
        }

        # Dynamische Income/Cost-Typen für das Template
        income_types = [("bounty_income", _("Ratting")), ("ess_income", _("ESS"))]
        income_types += [
            (f"{ref_type.lower()}_income", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types_income
        ]
        cost_types = [
            (f"{ref_type.lower()}_cost", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types_costs
        ]
        amounts["income_types"] = income_types
        amounts["cost_types"] = cost_types
        return amounts
