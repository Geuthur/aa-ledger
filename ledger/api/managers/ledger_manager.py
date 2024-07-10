from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger.api.helpers import convert_ess_payout, get_models_and_string
from ledger.api.managers.billboard_manager import BillboardLedger
from ledger.api.managers.core_manager import (
    LedgerDate,
    LedgerFilter,
    LedgerModels,
    LedgerTotal,
)
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)

CharacterMiningLedger, CharacterWalletJournalEntry = get_models_and_string()


class JournalProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(self, chars, year, month):
        self.year = year
        self.month = month
        self.chars = chars
        self.corporation_dict = {}
        self.character_dict = {}
        self.summary_total = LedgerTotal()

    def calc_summary_total(self, totals):
        self.summary_total.total_amount += totals.get("total_amount", 0)
        self.summary_total.total_amount_ess += totals.get("total_amount_ess", 0)
        self.summary_total.total_amount_all += totals.get("total_amount_all", 0)
        self.summary_total.total_amount_mining += totals.get("total_amount_mining", 0)
        self.summary_total.total_amount_others += totals.get("total_amount_others", 0)
        self.summary_total.total_amount_costs += totals.get("total_amount_costs", 0)

    def aggregate_journal(self, journal):
        result = journal.aggregate(
            total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
        )
        return result["total_amount"]

    def aggregate_journal_flat(self, journal):
        total_amount = 0
        for entry in journal:
            total_amount += entry
        return total_amount

    def process_corporation_chars(self, corporation_journal):
        # Create a Dict for all Mains(including their alts)
        for _, data in self.chars.items():
            main = data["main"]
            alts = data["alts"]

            chars_mains = [alt.character_id for alt in alts] + [main.character_id]

            total_bounty = 0
            total_ess = 0

            char_name = main.character_name
            char_id = main.character_id

            # Get the Filter Settings
            filters = LedgerFilter(chars_mains)

            total_bounty = self.aggregate_journal_flat(
                corporation_journal.filter(filters.filter_bounty).values_list(
                    "amount", flat=True
                )
            )
            total_ess = self.aggregate_journal_flat(
                corporation_journal.filter(filters.filter_ess).values_list(
                    "amount", flat=True
                )
            )

            summary_amount = total_bounty + total_ess

            if total_bounty or total_ess:
                self.corporation_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "alt_names": [],
                    "total_amount": total_bounty,
                    "total_amount_ess": total_ess,
                }

            totals = {
                "total_amount": total_bounty,
                "total_amount_ess": total_ess,
                "total_amount_all": summary_amount,
            }
            # Summary all
            self.calc_summary_total(totals)

    def process_character_chars(
        self, corporation_journal, character_journal, mining_journal
    ):
        """Process the characters for the Journal"""
        chars = [char.character_id for char in self.chars]
        for char in self.chars:
            char_id = char.character_id
            char_name = char.character_name

            # Get the Filter Settings
            filters = LedgerFilter([char_id])

            amounts = {
                "bounty": self.aggregate_journal(
                    character_journal.filter(filters.filter_bounty)
                ),
                "ess": self.aggregate_journal(
                    corporation_journal.filter(filters.filter_ess)
                ),
                "contracts": self.aggregate_journal(
                    character_journal.filter(filters.filter_contract)
                ),
                "transactions": self.aggregate_journal(
                    character_journal.filter(filters.filter_market)
                ),
                "donations": self.aggregate_journal(
                    character_journal.filter(filters.filter_donation).exclude(
                        first_party_id__in=chars
                    )
                ),
                "market_cost": self.aggregate_journal(
                    character_journal.filter(filters.filter_market_cost)
                ),
                "production_cost": self.aggregate_journal(
                    character_journal.filter(filters.filter_production)
                ),
                "mining": mining_journal.filter(filters.filter_mining)
                .values("total", "date")
                .aggregate(
                    total_amount=Coalesce(
                        Sum(F("total")), 0, output_field=DecimalField()
                    )
                ),
            }

            # Convert the ESS Payout for Character
            amounts["ess"] = convert_ess_payout(amounts["ess"])

            total_amount_others = (
                amounts["contracts"] + amounts["transactions"] + amounts["donations"]
            )
            costs_amount = amounts["market_cost"] + amounts["production_cost"]
            summary_amount = (
                amounts["bounty"]
                + amounts["ess"]
                + amounts["mining"]["total_amount"]
                + total_amount_others
            )
            summary_amount -= abs(costs_amount)

            if summary_amount > 0:
                self.character_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "total_amount": amounts["bounty"],
                    "total_amount_ess": amounts["ess"],
                    "total_amount_mining": amounts["mining"]["total_amount"],
                    "total_amount_others": total_amount_others,
                    "total_amount_costs": costs_amount,
                }

            totals = {
                "total_amount": amounts["bounty"],
                "total_amount_ess": amounts["ess"],
                "total_amount_all": summary_amount,
                "total_amount_mining": amounts["mining"]["total_amount"],
                "total_amount_others": total_amount_others,
                "total_amount_costs": costs_amount,
            }
            # Summary all
            self.calc_summary_total(totals)

    def character_ledger(self):
        # Get the Character IDs
        chars = [char.character_id for char in self.chars]

        # Get the Filter Settings
        filters = LedgerFilter(chars)

        # Filter the entries for the Year/Month
        filter_date = Q(date__year=self.year)
        if self.month != 0:
            filter_date &= Q(date__month=self.month)

        # Get the Corporation Journal
        corporation_journal = CorporationWalletJournalEntry.objects.filter(
            filters.filter_second_party, filter_date
        ).select_related(
            "first_party",
            "second_party",
        )
        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)

        # Get the Mining Journal
        mining_journal = (
            CharacterMiningLedger.objects.filter(filters.filter_mining, filter_date)
        ).annotate_pricing()

        # Filter for the Character Journal
        character_journal = CharacterWalletJournalEntry.objects.filter(
            filters.filter_partys, filter_date
        ).select_related("first_party", "second_party")

        # Create the Dicts for each Character
        self.process_character_chars(
            corporation_journal, character_journal, mining_journal
        )

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        models = LedgerModels(
            character_journal=character_journal,
            corporation_journal=corporation_journal,
            mining_journal=mining_journal,
        )

        # Create the Billboard for the Characters
        ledger = BillboardLedger(date_data, models, corp=False)
        billboard_dict = ledger.billboard_char_ledger(chars)

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(self.character_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": self.summary_total.to_dict(),
                "billboard": billboard_dict,
            }
        )

        return output

    def corporation_ledger(self, chars_list: list):
        # Get the Filter Settings
        filters = LedgerFilter(chars_list)

        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        corporation_journal = CorporationWalletJournalEntry.objects.filter(
            filters.filter_second_party, filter_date
        ).select_related(
            "first_party",
            "second_party",
        )

        # Create the Dicts for each Character
        self.process_corporation_chars(corporation_journal)

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        models = LedgerModels(corporation_journal=corporation_journal)

        # Create the Billboard for the Corporation
        ledger = BillboardLedger(date_data, models, corp=True)

        billboard_dict = ledger.billboard_corp_ledger(
            self.corporation_dict, self.summary_total.total_amount, self.chars
        )

        output = []
        output.append(
            {
                "ratting": sorted(
                    list(self.corporation_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": self.summary_total.to_dict(),
                "billboard": billboard_dict,
            }
        )

        return output
