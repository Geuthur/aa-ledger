from django.db.models import Q, Sum

from ledger.api.api_helper.billboard_helper import BillboardData, BillboardLedger
from ledger.api.api_helper.core_manager import (
    LedgerCharacterDict,
    LedgerDate,
    LedgerModels,
    LedgerTotal,
)
from ledger.api.helpers import convert_corp_tax, get_alts_queryset
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterWalletJournalEntry

logger = get_extension_logger(__name__)


class CharacterProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, chars, year, month, corporations=None):
        self.year = year
        self.month = month
        self.chars = chars
        self.alts = self.get_alts(chars)
        self.chars_list = []
        self.corp = corporations if corporations else []
        self.summary_total = LedgerTotal()

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

        # Process Ledger Models
        char_journal, mining_journal, corp_journal = (
            CharacterWalletJournalEntry.objects.filter(
                self.filter_date,
            )
            .select_related("first_party", "second_party")
            .generate_ledger(
                characters=self.chars,
                filter_date=self.filter_date,
                exclude=self.chars_list,
            )
        )

        # Annotate Mining for Characters
        mining_char_journal = (
            mining_journal.annotate_pricing()
            .values("character__character__character_id")
            .annotate(total_amount=Sum("total"))
            .values(
                "character__character__character_id",
                "character__character__character_name",
                "total_amount",
            )
        )

        # Annotate Corp Journal for Characters
        corp_character_journal = (
            corp_journal.annotate_daily_goal()
            .annotate_ess()
            .values("second_party__eve_id", "second_party__name", "ess", "daily_goal")
        )

        for mining_char in mining_char_journal:
            char_id = mining_char["character__character__character_id"]
            char_name = mining_char["character__character__character_name"]
            total_amount_mining = mining_char["total_amount"]

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

        for char in char_journal:
            char_name = char.get("char_name", "Unknown")
            char_id = char.get("char_id", 0)

            total_bounty = char.get("bounty", 0)
            total_others = char.get("miscellanous", 0)
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

        for char in corp_character_journal:
            char_name = char.get("second_party__name", "Unknown")
            char_id = char.get("second_party__eve_id", 0)

            total_ess = convert_corp_tax(char.get("ess", 0))
            total_daily_goal = convert_corp_tax(char.get("daily_goal", 0))

            if total_daily_goal:
                character_dict.add_amount_to_character(
                    char_id,
                    total_daily_goal,
                    "total_amount_others",
                )

            if total_ess:
                character_dict.add_amount_to_character(
                    char_id,
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
        # Get the All Alt Characters from Main
        if self.alts:
            self.chars = self.alts
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        self.filter_date = Q(date__year=self.year)
        if not self.month == 0:
            self.filter_date &= Q(date__month=self.month)

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
        # Get the Character IDs
        if self.alts:
            self.chars = self.alts
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        # Process Ledger Models
        char_journal, mining_journal, corp_journal = (
            CharacterWalletJournalEntry.objects.filter(
                filter_date,
            )
            .select_related("first_party", "second_party")
            .generate_ledger(
                characters=self.chars, filter_date=filter_date, exclude=self.chars_list
            )
        )
        mining_journal = mining_journal.annotate_pricing()

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        data = BillboardData()
        models = LedgerModels(
            character_journal=char_journal,
            corporation_journal=corp_journal,
            mining_journal=mining_journal,
        )

        # Create the Billboard for the Characters
        ledger = BillboardLedger(date_data, models, data, corp=False)
        billboard_dict = ledger.billboard_char_ledger(self.chars, self.chars_list)

        output = []
        output.append(
            {
                "billboard": billboard_dict,
            }
        )

        return output
