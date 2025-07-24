"""PvE Views"""

# Standard Library
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.helpers.ref_type import RefTypeCategories
from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharacterData:
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
        self.request = request
        self.character = character
        self.date_info = {"year": year, "month": month, "day": day}
        self.ledger_type = "ledger"
        # If all are None, default to 'month' view
        if year is None and month is None and day is None:
            self.view = "month"
        else:
            self.view = "day" if day else "month" if month else "year"

        self.journal = None
        self.mining = None
        self.billboard = BillboardSystem(self.view)

    @property
    def alts_ids(self):
        return self.character.alts.values_list("character_id", flat=True)

    @property
    def year(self):
        return self.date_info["year"]

    @property
    def month(self):
        return self.date_info["month"]

    @property
    def day(self):
        return self.date_info["day"]

    @property
    def filter_date(self):
        now = timezone.now()
        # If all are None, use current year and month
        if self.year is None and self.month is None and self.day is None:
            filter_date = Q(date__year=now.year) & Q(date__month=now.month)
        else:
            filter_date = (
                Q(date__year=self.year) if self.year else Q(date__year=now.year)
            )
            if self.month:
                filter_date &= Q(date__month=self.month)
            if self.day:
                filter_date &= Q(date__day=self.day)
        return filter_date

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
            "character_id": character.eve_character.character_id,
            "billboard": json.dumps(self.billboard.dict.asdict()),
            "ledger": ledger,
            "years": list(existing_years),
            "totals": totals,
            "view": self.get_view_data(),
        }
        return context

    def update_context(self, context: dict, **kwargs) -> dict:
        """Update the context with additional information."""
        new_context = {
            **context,
            **kwargs,
        }
        return new_context

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

    @property
    def get_details_title(self):
        """Return the title for the details view based on the view type."""
        if self.year and self.month and self.day:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        if self.year and self.month:
            return f"{self.year:04d}-{self.month:02d}"
        if self.year:
            return f"{self.year:04d}"
        return "Character Ledger Details"

    def get_view_data(self):
        """Return a dictionary representation of the view data."""
        return {
            "type": self.ledger_type,
            "date": {
                "current": {
                    "year": timezone.now().year,
                    "month": timezone.now().month,
                    "day": timezone.now().day,
                },
                "year": self.year,
                "month": self.month,
                "day": self.day,
            },
            "details_url": self.create_url(
                self.character.eve_character.character_id, viewname="character_details"
            ),
        }

    def create_url(self, character_id, viewname):
        """Generate the URL for character details based on the view type."""
        if self.year and self.month and self.day:
            return reverse(
                f"ledger:{viewname}_year_month_day",
                kwargs={
                    "character_id": character_id,
                    "year": self.year,
                    "month": self.month,
                    "day": self.day,
                },
            )
        if self.year and self.month:
            return reverse(
                f"ledger:{viewname}_year_month",
                kwargs={
                    "character_id": character_id,
                    "year": self.year,
                    "month": self.month,
                },
            )
        if self.year:
            return reverse(
                f"ledger:{viewname}_year",
                kwargs={"character_id": character_id, "year": self.year},
            )
        return reverse(
            f"ledger:{viewname}_year_month",
            kwargs={
                "character_id": character_id,
                "year": timezone.now().year,
                "month": timezone.now().month,
            },
        )

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
            "bounty": bounty,
            "ess": ess,
            "mining": mining_val,
            "costs": costs,
            "miscellaneous": miscellaneous,
            "total": total,
            "update_states": update_states,
            "single_url": self.create_url(
                character.eve_character.character_id, viewname="character_ledger"
            ),
            "details_url": self.create_url(
                character.eve_character.character_id, viewname="character_details"
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

    def _calculate_totals(self, ledger) -> dict:
        totals = {
            "bounty": Decimal(0),
            "ess": Decimal(0),
            "mining": Decimal(0),
            "costs": Decimal(0),
            "miscellaneous": Decimal(0),
            "total": Decimal(0),
        }

        if not ledger:
            return totals

        if isinstance(ledger, dict):
            ledger = [ledger]

        for total in ledger:
            if total is None:
                continue
            totals["bounty"] += total["bounty"]
            totals["ess"] += total["ess"]
            totals["mining"] += total["mining"]
            totals["costs"] += total["costs"]
            totals["miscellaneous"] += total["miscellaneous"]
            totals["total"] += total["total"]
        return totals

    def _create_character_details(self) -> dict:
        self.setup_ledger(self.character)

        amounts = defaultdict(lambda: defaultdict(Decimal))

        ref_types_income = RefTypeCategories.get_miscellaneous()
        ref_types_costs = RefTypeCategories.get_costs()
        amounts["bounty_income"] = {}
        amounts["mining_income"] = {}
        amounts["ess_income"] = {}

        amounts["bounty_income"]["total_amount"] = self.journal.aggregate_bounty()
        amounts["mining_income"]["total_amount"] = self.mining.aggregate_mining()
        amounts["ess_income"]["total_amount"] = (
            amounts["bounty_income"]["total_amount"] * Decimal(0.667)
            if amounts["bounty_income"]["total_amount"]
            else 0
        )

        for ref_type, value in ref_types_income.items():
            ref_type_name = ref_type.lower()
            amounts[f"{ref_type_name}_income"] = {}

            # Check if the ref_type is a donation and handle it accordingly
            if ref_type_name == "donation":
                aggregated_data = self.journal.aggregate_ref_type(
                    ref_type=value,
                    income=True,
                    exclude=self.alts_ids,
                )
                if aggregated_data <= 0:
                    continue
                amounts[f"{ref_type_name}_income"]["total_amount"] = aggregated_data
                continue

            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=True,
            )
            # If the aggregated data is less than or equal to 0, skip it
            if aggregated_data <= 0:
                continue
            amounts[f"{ref_type_name}_income"]["total_amount"] = aggregated_data

        for ref_type, value in ref_types_costs.items():
            ref_type_name = ref_type.lower()
            amounts[f"{ref_type_name}_cost"] = {}

            # Check if the ref_type is a donation and handle it accordingly
            if ref_type_name == "donation":
                aggregated_data = self.journal.aggregate_ref_type(
                    ref_type=value,
                    income=False,
                    exclude=self.alts_ids,
                )
                if aggregated_data <= 0:
                    continue
                amounts[f"{ref_type_name}_cost"]["total_amount"] = aggregated_data
                continue

            amounts[f"{ref_type_name}_cost"] = {}
            aggregated_data = self.journal.aggregate_ref_type(
                ref_type=value,
                income=False,
            )
            # If the aggregated data is less than or equal to 0, skip it
            if aggregated_data >= 0:
                continue

            amounts[f"{ref_type_name}_cost"]["total_amount"] = aggregated_data
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
        return amounts

    def _add_average_details(self, amounts: dict, day: int = None):
        """Add average details to the amounts dictionary, skipping if no data or total is 0."""
        avg = day if day else datetime.now().day
        if self.request.GET.get("all", False):
            avg = 365

        for key in amounts:
            if (
                isinstance(amounts[key], dict)
                and "total_amount" in amounts[key]
                and amounts[key]["total_amount"] not in (None, 0, 0.0, Decimal(0))
            ):
                total = amounts[key]["total_amount"]
                amounts[key]["average_day"] = total / avg
                amounts[key]["average_hour"] = total / avg / 24
                amounts[key]["average_tick"] = total / 20
                amounts[key]["current_day_tick"] = (
                    amounts[key].get("total_amount_day", 0) / 20
                )
                amounts[key]["average_day_tick"] = total / avg / 20
                amounts[key]["average_hour_tick"] = total / avg / 24 / 20
        return amounts
