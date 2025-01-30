from datetime import datetime

from django.db.models import Q

from ledger.api.api_helper.billboard_helper import BillboardData, BillboardLedger
from ledger.api.api_helper.core_manager import (
    LedgerCharacterDict,
    LedgerModels,
    LedgerTotal,
)
from ledger.api.helpers import get_alts_queryset
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterWalletJournalEntry

logger = get_extension_logger(__name__)


class CharacterProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, chars, date: datetime, view=None):
        self.date = date
        self.chars = chars
        self.view = view
        self.alts = self.get_alts(chars)
        self.chars_list = []
        self.summary_total = LedgerTotal()
        self.create_queryset()

    def create_queryset(self):
        """Create the Queryset for the Model"""
        # Get the All Alt Characters from Main
        if self.alts:
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        # pylint: disable=duplicate-code
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)

        # Process Ledger Models
        self.char_journal, self.mining_journal, self.corp_journal = (
            CharacterWalletJournalEntry.objects.filter(
                filter_date,
            )
            .select_related("first_party", "second_party")
            .generate_ledger(
                characters=self.chars,
                filter_date=filter_date,
                exclude=self.chars_list,
            )
        )

    def get_alts(self, main):
        """Get the Alts for the Main Character"""
        alts = None
        if len(main) == 1:
            # pylint: disable=broad-exception-caught
            try:
                alts = get_alts_queryset(main[0])
            except Exception:
                pass
        return alts

    # pylint: disable=too-many-locals
    def process_character_chars(self):
        """Process the characters for the Journal"""
        # Initialize character_dict with default values
        character_dict = LedgerCharacterDict()
        character_totals = LedgerTotal()

        # Annotate Mining for Characters
        mining_char_journal = self.mining_journal.annotate_mining()

        # Annotate Corp Journal for Characters
        corp_character_journal = (
            self.corp_journal.values("second_party__eve_id", "second_party__name")
            .annotate_daily_goal_income(is_character_ledger=True)
            .annotate_ess_income(is_character_ledger=True)
        )

        character_journal = self.char_journal

        for mining_char in mining_char_journal:
            char_name = mining_char.get(
                "character__character__character_name", "Unknown"
            )
            char_id = mining_char.get("character__character__character_id", 0)
            total_amount_mining = mining_char.get("total_amount", 0)

            character_dict.add_or_update_character(
                char_id,
                char_name,
                total_amount_mining=total_amount_mining,
            )

            totals = {
                "total_amount_mining": total_amount_mining,
            }
            # Summary all
            character_totals.get_summary(totals)

        for char in character_journal:
            char_name = char.get("char_name", "Unknown")
            char_id = char.get("char_id", 0)

            total_bounty = char.get("bounty_income", 0)
            total_others = char.get("miscellaneous", 0)
            total_costs = char.get("costs", 0)

            if total_bounty or total_others or total_costs:
                character_dict.add_or_update_character(
                    char_id,
                    char_name,
                    total_amount=total_bounty,
                    total_amount_others=total_others,
                    total_amount_costs=total_costs,
                )

            totals = {
                "total_amount": total_bounty,
                "total_amount_others": total_others,
                "total_amount_costs": total_costs,
            }
            # Summary all
            character_totals.get_summary(totals)

        for corp_char in corp_character_journal:
            char_name = corp_char.get("second_party__name", "Unknown")
            char_id = corp_char.get("second_party__eve_id", 0)

            total_ess = corp_char.get("ess_income", 0)
            total_daily_goal = corp_char.get("daily_goal_income", 0)

            if total_daily_goal:
                character_dict.add_amount_to_character(
                    char_id,
                    char_name,
                    total_daily_goal,
                    "total_amount_others",
                )

            if total_ess:
                character_dict.add_amount_to_character(
                    char_id,
                    char_name,
                    total_ess,
                    "total_amount_ess",
                )

            totals = {
                "total_amount_ess": total_ess,
                "total_amount_others": total_daily_goal,
            }
            # Summary all
            character_totals.get_summary(totals)

        # Generate the total sum
        character_totals.calculate_total_sum(character_dict.to_dict())

        return character_dict.to_dict(), character_totals.to_dict()

    def generate_ledger(self):
        # Create the Dicts for each Character
        character_dict, character_totals = self.process_character_chars()

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(character_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": character_totals,
            }
        )

        return output

    # pylint: disable=unused-argument
    def generate_billboard(self, corporations=None):
        mining_journal = self.mining_journal.annotate_pricing()

        # Create Data for Billboard
        data = BillboardData()
        models = LedgerModels(
            character_journal=self.char_journal,
            corporation_journal=self.corp_journal,
            mining_journal=mining_journal,
        )

        # Create the Billboard for the Characters
        ledger = BillboardLedger(view=self.view, models=models, data=data, corp=False)
        billboard_dict = ledger.billboard_ledger(self.chars_list, self.chars_list)

        output = []
        output.append(
            {
                "billboard": billboard_dict,
            }
        )

        return output
