from django.db.models import ExpressionWrapper, F, FloatField, Q, Sum

from ledger.api.api_helper.billboard_helper import BillboardData, BillboardLedger
from ledger.api.api_helper.core_manager import (
    LedgerCharacterDict,
    LedgerDate,
    LedgerModels,
    LedgerTotal,
)
from ledger.api.helpers import convert_ess_payout, get_alts_queryset
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
        # Initialize character_dict with default values
        character_dict = LedgerCharacterDict()
        character_totals = LedgerTotal()

        # Call annotate_ledger and store the result
        journal = journal.generate_ledger(
            character_ids=self.chars,
            filter_date=self.filter_date,
            exclude=self.chars_list,
        )

        # Call annotate_ledger and store the result
        char_mining_journal = (
            CharacterMiningLedger.objects.filter(
                self.filter_date, character__character__character_id__in=self.chars_list
            )
            .annotate(
                price=F("type__market_price__average_price"),
                total=ExpressionWrapper(
                    F("type__market_price__average_price") * F("quantity"),
                    output_field=FloatField(),
                ),
            )
            .values("character__character__character_id")
            .annotate(total_amount=Sum("total"))
            .values(
                "character__character__character_id",
                "character__character__character_name",
                "total_amount",
            )
        )

        for mining_char in char_mining_journal:
            char_id = mining_char["character__character__character_id"]
            char_name = mining_char["character__character__character_name"]
            total_amount_mining = round(mining_char["total_amount"])

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

        for char in journal:
            char_name = char.get("char_name", "Unknown")
            char_id = char.get("char_id", 0)

            total_bounty = round(char.get("total_bounty", 0))
            total_ess = round(convert_ess_payout(char.get("total_ess", 0)))
            total_others = round(char.get("total_others", 0))
            total_costs = round(char.get("total_costs", 0))

            if total_bounty or total_ess or total_others or total_costs:
                character_dict.add_or_update_character(
                    char_id,
                    char_name,
                    total_amount=total_bounty,
                    total_amount_ess=total_ess,
                    total_amount_others=total_others,
                    total_amount_costs=total_costs,
                )

            totals = {
                "total_amount": total_bounty,
                "total_amount_ess": total_ess,
                "total_amount_others": total_others,
                "total_amount_costs": total_costs,
            }
            # Summary all
            character_totals.get_summary(totals)

        # Generate the total sum
        character_totals.calculate_total_sum(character_dict.to_dict())

        return character_dict.to_dict(), character_totals.to_dict()

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

    # pylint: disable=unused-argument
    def generate_billboard(self, corporations=None):
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
