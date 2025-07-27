"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.core import LedgerCore
from ledger.helpers.ref_type import RefTypeCategories
from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharacterData(LedgerCore):
    """Class to hold character data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        request: WSGIRequest,
        character: CharacterAudit,
        year=None,
        month=None,
        day=None,
    ):
        LedgerCore.__init__(self, year, month, day)
        self.request = request
        self.character = character

    @property
    def alts_ids(self):
        return self.character.alts.values_list("character_id", flat=True)

    def setup_ledger(self, character: CharacterAudit):
        """Set up the ledger based on the view type."""
        if self.request.GET.get("single", False):
            self.ledger_type = "single"

        if self.request.GET.get("all", False):
            self.journal = CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.character.alts.values_list(
                    "character_id", flat=True
                ),
            )
            self.mining = CharacterMiningLedger.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.character.alts.values_list(
                    "character_id", flat=True
                ),
            )
        else:
            self.journal = character.ledger_character_journal.filter(self.filter_date)
            self.mining = character.ledger_character_mining.filter(self.filter_date)

    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the character and its alts."""
        if self.request.GET.get("single", False):
            characters = CharacterAudit.objects.filter(
                eve_character__character_id=self.character.eve_character.character_id
            )
            character = characters.first()
            character_data = self._create_character_data(character=character)
            ledger = character_data
        else:
            ledger = []
            characters = CharacterAudit.objects.filter(
                eve_character__character_id__in=self.alts_ids
            ).select_related("eve_character")
            for character in characters:
                character_data = self._create_character_data(character=character)
                if character_data:
                    ledger.append(character_data)

        totals = self._calculate_totals(ledger)

        # Evaluate the existing years for the view
        existing_years = (
            CharacterWalletJournalEntry.objects.filter(character__in=characters)
            .exclude(date__year__isnull=True)
            .values_list("date__year", flat=True)
            .order_by("-date__year")
            .distinct()
        )

        # Create the ratting bar for the view
        self.create_rattingbar(
            is_char_ledger=True,
            character_ids=characters.values_list(
                "eve_character__character_id", flat=True
            ),
        )

        context = {
            "title": f"Character Ledger - {self.character.eve_character.character_name}",
            "character_id": self.character.eve_character.character_id,
            "billboard": json.dumps(self.billboard.dict.asdict()),
            "ledger": ledger,
            "years": list(existing_years),
            "totals": totals,
            "view": self.create_view_data(
                viewname="character_details",
                character_id=self.character.eve_character.character_id,
            ),
        }
        return context

    def _create_character_data(
        self,
        character: CharacterAudit,
    ):
        """Create a dictionary with character data and update billboard/ledger."""
        self.setup_ledger(character)

        if not self.journal.exists() and not self.mining.exists():
            return None

        journal_sum = self.journal.aggregate(total=Sum("amount"))["total"] or 0
        mining_sum = self.mining.aggregate(total=Sum("quantity"))["total"] or 0

        if journal_sum == 0 and mining_sum == 0:
            return None

        bounty = self.journal.aggregate_bounty()
        ess = bounty * Decimal(0.667)
        mining_val = self.mining.aggregate_mining()
        costs = self.journal.aggregate_costs(second_party=self.alts_ids)
        miscellaneous = self.journal.aggregate_miscellaneous(first_party=self.alts_ids)
        total = bounty + ess + mining_val + miscellaneous + costs

        update_states = {}

        for status in character.ledger_update_status.all():
            update_states[status.section] = {
                "is_success": status.is_success,
                "last_update_finished_at": status.last_update_finished_at,
                "last_run_finished_at": status.last_run_finished_at,
            }

        char_data = {
            "character": character,
            "ledger": {
                "bounty": bounty,
                "ess": ess,
                "mining": mining_val,
                "costs": costs,
                "miscellaneous": miscellaneous,
                "total": total,
            },
            "update_states": update_states,
            "single_url": self.create_url(
                viewname="character_ledger",
                character_id=character.eve_character.character_id,
            ),
            "details_url": self.create_url(
                viewname="character_details",
                character_id=character.eve_character.character_id,
            ),
        }

        # Create the chord data for the billboard
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to="Wallet",
            value=bounty + ess + mining_val + miscellaneous,
        )
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to="Costs",
            value=abs(costs),
        )

        return char_data

    def create_rattingbar(
        self, character_ids: list = None, is_char_ledger: bool = False
    ):
        """Create the ratting bar for the view."""
        if not character_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(
            CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=character_ids,
            )
        )
        rattingbar = rattingbar_timeline.annotate_bounty_income().annotate_miscellaneous_with_exclude(
            exclude=self.alts_ids
        )
        self.billboard.create_or_update_results(
            rattingbar, is_char_ledger=is_char_ledger
        )
        self.billboard.create_ratting_bar()

    def _create_character_details(self) -> dict:
        self.setup_ledger(self.character)

        amounts = {}

        ref_types_income = RefTypeCategories.get_miscellaneous()
        ref_types_costs = RefTypeCategories.get_costs()

        # Bounty Income
        bounty_income = self.journal.aggregate_bounty()
        if bounty_income > 0:
            amounts["bounty_income"] = {"total_amount": bounty_income}

        # Mining Income
        mining_income = self.mining.aggregate_mining()
        if mining_income > 0:
            amounts["mining_income"] = {"total_amount": mining_income}

        # ESS Income (nur wenn bounty_income existiert)
        if bounty_income > 0:
            ess_income = bounty_income * Decimal(0.667)
            if ess_income > 0:
                amounts["ess_income"] = {"total_amount": ess_income}

        # Income Ref Types
        for ref_type, value in ref_types_income.items():
            ref_type_name = ref_type.lower()

            # Check if the ref_type is a donation and handle it accordingly
            if ref_type_name == "donation":
                aggregated_data = self.journal.aggregate_ref_type(
                    ref_type=value,
                    income=True,
                    exclude=self.alts_ids,
                )
                if aggregated_data > 0:
                    amounts[f"{ref_type_name}_income"] = {
                        "total_amount": aggregated_data
                    }
                continue

            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=True,
            )
            if aggregated_data > 0:
                amounts[f"{ref_type_name}_income"] = {"total_amount": aggregated_data}

        # Cost Ref Types
        for ref_type, value in ref_types_costs.items():
            ref_type_name = ref_type.lower()

            # Check if the ref_type is a donation and handle it accordingly
            if ref_type_name == "donation":
                aggregated_data = self.journal.aggregate_ref_type(
                    ref_type=value,
                    income=False,
                    exclude=self.alts_ids,
                )
                if aggregated_data < 0:
                    amounts[f"{ref_type_name}_cost"] = {"total_amount": aggregated_data}
                continue

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
