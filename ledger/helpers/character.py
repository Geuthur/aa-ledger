"""PvE Views"""

# Standard Library
from decimal import Decimal

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.billboard import BillboardSystem
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
        section=None,
    ):
        super().__init__(year, month, day)
        self.request = request
        self.character = character
        self.alts_ids = self.get_alt_ids
        self.characters = CharacterAudit.objects.filter(
            eve_character__character_id__in=self.alts_ids
        ).select_related("eve_character")
        self.section = section
        self.billboard = BillboardSystem()
        self.queryset = character.ledger_character_journal.filter(self.filter_date)
        self.mining = character.ledger_character_mining.filter(self.filter_date)

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

    def filter_character_journal(
        self, character: CharacterAudit
    ) -> tuple[QuerySet[CharacterWalletJournalEntry], QuerySet[CharacterMiningLedger]]:
        """Filter the journal entries for the character and its alts."""
        if self.section == "summary":
            journal = CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.alts_ids,
            )
            mining = CharacterMiningLedger.objects.filter(
                self.filter_date,
                character__eve_character__character_id__in=self.alts_ids,
            )
            return journal, mining
        # Get Journal Entries for the Character
        journal = character.ledger_character_journal.filter(self.filter_date)
        mining = character.ledger_character_mining.filter(self.filter_date)
        return journal, mining

    def generate_ledger_data(self) -> dict:
        """Generate the ledger data for the character and its alts."""
        # Only show the character if 'single' is set in the request
        if self.section == "single":
            self.ledger_type = "single"
            characters = CharacterAudit.objects.filter(
                eve_character=self.character.eve_character
            ).select_related("eve_character")
            character_data = self._create_character_data(character=self.character)
            ledger = character_data
        else:
            ledger = []
            characters = self.characters
            for character in self.characters:
                character_data = self._create_character_data(character=character)
                if character_data:
                    ledger.append(character_data)

        # Billboard
        self.billboard.change_view(self.get_view_mode())
        # Create the ratting bar for the view
        self.create_rattingbar(
            is_old_ess=self.is_old_ess,
            character_ids=characters.values_list(
                "eve_character__character_id", flat=True
            ),
        )
        return ledger

    def _create_character_data(
        self,
        character: CharacterAudit,
    ):
        """Create a dictionary with character data and update billboard/ledger."""
        journal, mining = self.filter_character_journal(character)

        # If no journal or mining data exists, return None
        if not journal.exists() and not mining.exists():
            return None

        bounty = journal.aggregate_bounty()
        ess = (
            journal.aggregate_bounty() * Decimal(0.667)
            if self.is_old_ess
            else journal.aggregate_ess()
        )
        mining_val = mining.aggregate_mining()
        costs = journal.aggregate_costs(second_party=self.alts_ids)
        miscellaneous = journal.aggregate_miscellaneous(first_party=self.alts_ids)

        total = sum(
            [
                bounty,
                ess,
                costs,
                miscellaneous,
            ]
        )

        # If total is 0, we do not need to create a character data entry
        if int(total) + int(mining_val) == 0:
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
                section="single",
            ),
            "details_url": self.create_url(
                viewname="character_details",
                character_id=character.eve_character.character_id,
                section="single",
            ),
        }
        self.billboard.change_view(self.get_view_mode())
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

        # Create the timeline for the ratting bar
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
        # Annotate the timeline with the relevant data
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous_exclude_donations(exclude=self.alts_ids)
        )
        rattingbar_mining = rattingbar_mining_timeline.annotate_mining(with_period=True)

        # Generate the XY series for the ratting bar
        self.billboard.create_or_update_results(rattingbar, is_old_ess=is_old_ess)
        self.billboard.add_category(rattingbar_mining, category="mining")
        series, categories = self.billboard.generate_xy_series()
        if series and categories:
            # Create the ratting bar chart
            self.billboard.create_xy_chart(
                title=_("Ratting Bar"), categories=categories, series=series
            )
