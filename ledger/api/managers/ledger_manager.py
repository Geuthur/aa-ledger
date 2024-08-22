from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger.api.helpers import (
    convert_ess_payout,
    get_alts_queryset,
    get_models_and_string,
)
from ledger.api.managers.billboard_manager import BillboardData, BillboardLedger
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
        self.alts = self.get_alts(chars)
        self.chars_list = []
        self.corporation_dict = {}
        self.character_dict = {}
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

    # pylint: disable=too-many-locals
    def process_corporation_chars(self, corporation_journal):
        # Create IDs for the second_party_ids
        second_party_ids = corporation_journal.values_list("second_party_id", flat=True)

        # Get the Filter Settings for all characters
        all_chars_mains = [
            alt.character_id for data in self.chars.values() for alt in data["alts"]
        ]
        filters = LedgerFilter(all_chars_mains)

        # Aggregate the data in a single query for all characters
        aggregated_data = (
            corporation_journal.filter(Q(filters.filter_bounty) | Q(filters.filter_ess))
            .values("second_party_id")
            .annotate(
                total_bounty=Coalesce(
                    Sum("amount", filter=filters.filter_bounty),
                    0,
                    output_field=DecimalField(),
                ),
                total_ess=Coalesce(
                    Sum("amount", filter=filters.filter_ess),
                    0,
                    output_field=DecimalField(),
                ),
            )
        )

        # Convert aggregated data to a dictionary for quick lookup
        aggregated_dict = {item["second_party_id"]: item for item in aggregated_data}

        for _, data in self.chars.items():
            main = data["main"]
            alts = data["alts"]

            # Assuming journal is a list of objects with a second_party_id attribute
            alts_names = [
                alt.character_id for alt in alts if alt.character_id in second_party_ids
            ]

            for alt in alts:
                self.chars_list.append(alt.character_id)

            # Calculate total amounts for the current main and its alts
            total_bounty = sum(
                aggregated_dict.get(alt.character_id, {}).get("total_bounty", 0)
                for alt in alts
            )
            total_ess = sum(
                aggregated_dict.get(alt.character_id, {}).get("total_ess", 0)
                for alt in alts
            )

            summary_amount = total_bounty + total_ess

            if summary_amount > 0:
                self.corporation_dict[main.character_id] = {
                    "main_id": main.character_id,
                    "main_name": main.character_name,
                    "alt_names": alts_names,
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

    # pylint: disable=too-many-locals
    def process_character_chars(
        self, corporation_journal, character_journal, mining_journal
    ):
        """Process the characters for the Journal"""
        for char in self.chars:
            char_id = char.character_id
            char_name = char.character_name

            # Get the Filter Settings
            filters = LedgerFilter([char_id])
            all_costs_filters = filters.get_all_costs_filters()
            all_misc_filters = filters.get_all_misc_filters(self.chars_list)

            amounts = {
                "bounty": self.aggregate_journal(
                    character_journal.filter(filters.filter_bounty)
                ),
                "ess": self.aggregate_journal(
                    corporation_journal.filter(filters.filter_ess)
                ),
                "mining": mining_journal.filter(filters.filter_mining)
                .values("total", "date")
                .aggregate(
                    total_amount=Coalesce(
                        Sum(F("total")), 0, output_field=DecimalField()
                    )
                ),
            }

            amounts_others = {
                filter_name: self.aggregate_journal(
                    character_journal.filter(filter_query)
                )
                for filter_name, filter_query in all_misc_filters.items()
            }

            amounts_costs = {
                filter_name: self.aggregate_journal(
                    character_journal.filter(filter_query)
                )
                for filter_name, filter_query in all_costs_filters.items()
            }

            # Convert the ESS Payout for Character
            amounts["ess"] = convert_ess_payout(amounts["ess"])

            # Summing amounts_others
            total_amount_others = sum(amounts_others.values())

            # Summing amounts_costs
            costs_amount = sum(amounts_costs.values())

            summary_amount = (
                amounts["bounty"]
                + amounts["ess"]
                + amounts["mining"]["total_amount"]
                + total_amount_others
            )

            summary_amount -= abs(costs_amount)

            if summary_amount:
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
        # Exclude Alts
        if self.alts:
            self.chars_list = [char.character_id for char in self.alts]
        else:
            self.chars_list = [char.character_id for char in self.chars]

        # Get the Filter Settings
        filters = LedgerFilter(self.chars_list)

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
        data = BillboardData()
        models = LedgerModels(
            character_journal=character_journal,
            corporation_journal=corporation_journal,
            mining_journal=mining_journal,
        )

        # Create the Billboard for the Characters
        ledger = BillboardLedger(date_data, models, data, corp=False)
        billboard_dict = ledger.billboard_char_ledger(self.chars, self.chars_list)

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
        data = BillboardData(
            corporation_dict=self.corporation_dict,
            total_amount=self.summary_total.total_amount,
        )
        models = LedgerModels(corporation_journal=corporation_journal)

        # Create the Billboard for the Corporation
        ledger = BillboardLedger(date_data, models, data, corp=True)

        billboard_dict = ledger.billboard_corp_ledger(self.chars_list)

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

    def corporation_billboard(self, chars_list: list):
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

        # Create Data for Billboard
        date_data = LedgerDate(self.year, self.month)
        data = BillboardData(
            corporation_dict=self.corporation_dict,
            total_amount=self.summary_total.total_amount,
        )
        models = LedgerModels(corporation_journal=corporation_journal)

        # Create the Billboard for the Corporation
        ledger = BillboardLedger(date_data, models, data, corp=True)

        billboard_dict = ledger.billboard_corp_ledger(self.chars_list)

        output = []
        output.append(
            {
                "billboard": billboard_dict,
            }
        )

        return output
