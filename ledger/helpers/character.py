"""PvE Views"""

# Standard Library
import json
from decimal import Decimal

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.core import LedgerCore
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
        self.alts_ids = self.get_alt_ids

    @property
    def get_alt_ids(self):
        return self.character.alts.values_list("character_id", flat=True)

    @property
    def is_old_ess(self):
        """
        Compatibility check for old ESS income calculation.
        Since Swagger ESI has added ESS Ref Type to the Character Journal Endpoint
        """
        try:
            if self.month is None and self.year is None:
                return False
            if self.year >= 2025 and self.month >= 6:
                return False
        except TypeError:
            return True
        return True

    def setup_ledger(self, character: CharacterAudit):
        """Setup the Ledger Data for the Character."""

        # Show Card Template for Character Ledger
        if self.request.GET.get("single", False):
            self.ledger_type = "single"

        # Get All Journal Entries for the Character and its Alts for Details View
        if self.request.GET.get("all", False):
            self.journal = CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.alts_ids,
            )
            self.mining = CharacterMiningLedger.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.alts_ids,
            )
        else:
            # Get Journal Entries for the Character and its Alts
            self.journal = character.ledger_character_journal.filter(self.filter_date)
            self.mining = character.ledger_character_mining.filter(self.filter_date)

    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the character and its alts."""
        # Only show the character if 'single' is set in the request
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

        # Generate the totals for the ledger
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
            is_old_ess=self.is_old_ess,
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
            "is_old_ess": self.is_old_ess,
        }
        return context

    def _create_character_data(
        self,
        character: CharacterAudit,
    ):
        """Create a dictionary with character data and update billboard/ledger."""
        self.setup_ledger(character)

        # If no journal or mining data exists, return None
        if not self.journal.exists() and not self.mining.exists():
            return None

        bounty = self.journal.aggregate_bounty()
        ess = (
            self.journal.aggregate_bounty() * Decimal(0.667)
            if self.is_old_ess
            else self.journal.aggregate_ess()
        )
        mining_val = self.mining.aggregate_mining()
        costs = self.journal.aggregate_costs(second_party=self.alts_ids)
        miscellaneous = self.journal.aggregate_miscellaneous(first_party=self.alts_ids)
        total = sum(
            [
                bounty,
                ess,
                costs,
                miscellaneous,
            ]
        )

        # If total is 0, we do not need to create a character data entry
        if int(total) == 0:
            return None

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
            chord_to=_("Bounty"),
            value=bounty,
        )
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to=_("ESS"),
            value=ess,
        )
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to=_("Mining"),
            value=mining_val,
        )
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to=_("Miscellaneous"),
            value=miscellaneous,
        )
        self.billboard.chord_add_data(
            chord_from=character.eve_character.character_name,
            chord_to=_("Costs"),
            value=abs(costs),
        )

        return char_data

    def create_rattingbar(self, character_ids: list = None, is_old_ess: bool = False):
        """Create the ratting bar for the view."""
        if not character_ids:
            return

        rattingbar_timeline = self.billboard.create_timeline(
            CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=character_ids,
            )
        )
        rattingbar_mining_timeline = self.billboard.create_timeline(
            CharacterMiningLedger.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=character_ids,
            )
        )

        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous_with_exclude(exclude=self.alts_ids)
        )
        rattingbar_mining = rattingbar_mining_timeline.annotate_mining(with_period=True)
        self.billboard.create_or_update_results(rattingbar, is_old_ess=is_old_ess)
        self.billboard.add_category(rattingbar_mining, category="mining")
        self._build_xy_chart(title=_("Ratting Bar"))
