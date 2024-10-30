from django.db.models import Q

from ledger.api.helpers import convert_ess_payout, get_alts_queryset
from ledger.api.managers.billboard_manager import BillboardData, BillboardLedger
from ledger.api.managers.core_manager import LedgerDate, LedgerModels, LedgerTotal
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import CorporationWalletJournalEntry

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

    def process_character_chars(self, journal):
        """Process the characters for the Journal"""
        character_dict = {}
        character_totals = LedgerTotal()

        # Step 1: Annotated the Journal Entries
        def process_char(char):
            char_name = char.character_name
            char_id = char.character_id

            # Call annotate_ledger and store the result
            result = journal.generate_ledger(
                [char_id], self.filter_date, self.chars_list
            )

            amounts = result["amounts"]
            amounts_others = result["amounts_others"]
            amounts_costs = result["amounts_costs"]

            # Convert the ESS Payout for Character
            amounts["ess"] = convert_ess_payout(amounts["ess"])

            # Summing amounts
            total_amounts = sum(amounts.values())

            # Summing amounts_others
            total_amount_others = sum(amounts_others.values())

            # Summing amounts_costs
            total_costs_amount = sum(amounts_costs.values())

            # Calculate the summary amount
            total_summary_amount = sum([total_amounts, total_amount_others])
            total_summary_amount -= abs(total_costs_amount)

            if total_summary_amount or total_costs_amount:
                character_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "total_amount": amounts["bounty"],
                    "total_amount_ess": amounts["ess"],
                    "total_amount_mining": amounts["mining"],
                    "total_amount_others": total_amount_others,
                    "total_amount_costs": total_costs_amount,
                }

            totals = {
                "total_amount": amounts["bounty"],
                "total_amount_ess": amounts["ess"],
                "total_amount_mining": amounts["mining"],
                "total_amount_others": total_amount_others,
                "total_amount_costs": total_costs_amount,
                "total_amount_all": total_summary_amount,
            }
            # Summary all
            character_totals.get_summary(totals)

        for char in self.chars:
            process_char(char)

        return character_dict, character_totals.to_dict()

    def generate_ledger(self):
        # Get the Character IDs
        if self.alts:
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        self.filter_date = Q(date__year=self.year)
        if not self.month == 0:
            self.filter_date &= Q(date__month=self.month)

        # Filter for the Character Journal
        journal = CharacterWalletJournalEntry.objects.filter(
            self.filter_date
        ).select_related("first_party", "second_party")

        # Create the Dicts for each Character
        character_dict, character_totals = self.process_character_chars(journal)

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

    def generate_billboard(self):
        # Get the Character IDs
        if self.alts:
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        # Filter for the Character Journal
        journal = CharacterWalletJournalEntry.objects.filter(
            Q(first_party_id__in=self.chars_list)
            | Q(second_party_id__in=self.chars_list),
            filter_date,
        )

        corporation_journal = CorporationWalletJournalEntry.objects.filter(
            Q(second_party_id__in=self.chars_list), filter_date
        )

        mining_journal = CharacterMiningLedger.objects.filter(
            Q(character__character__character_id__in=self.chars_list), filter_date
        ).annotate_pricing()

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        data = BillboardData()
        models = LedgerModels(
            character_journal=journal,
            corporation_journal=corporation_journal,
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
