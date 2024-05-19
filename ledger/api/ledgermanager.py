import math
from datetime import datetime
from decimal import Decimal

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger import app_settings
from ledger.api.helpers import get_models_and_string
from ledger.hooks import get_extension_logger
from ledger.models.corporationaudit import CorporationWalletJournalEntry
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)

CharacterMiningLedger, CharacterWalletJournalEntry, SR_CHAR = get_models_and_string()


class LedgerDataCore:
    """LedgerDataCore class to store the core data."""

    def __init__(self, models):
        self.ess_entries, self.entries, self.mining_data = models
        self.total_bounty = 0
        self.total_ess_payout = 0
        self.total_miscellaneous = 0
        self.total_isk = 0


class LedgerData(LedgerDataCore):
    """LedgerData class to store the data."""

    def __init__(self, models):
        super().__init__(models)
        self.total_cost = 0
        self.total_production_cost = 0
        self.total_market = 0


class LedgerDate:
    """LedgerDate class to store the date data."""

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.monthly = month == 0
        self.current_date = datetime.now()
        self.range_data = 12 if self.monthly else 31
        self.day_checks = list(range(1, self.range_data + 1))


class LedgerSum:
    """LedgerSum class to store the sum amounts."""

    def __init__(self):
        self.sum_amount = ["Ratting"]
        self.sum_amount_ess = ["ESS Payout"]
        self.sum_amount_misc = ["Miscellaneous"]
        self.sum_amount_mining = ["Mining"]
        self.total_sum = None


class LedgerTotal:
    """LedgerTotal class to store the total amounts."""

    def __init__(self):
        self.total_amount = 0
        self.total_amount_ess = 0
        self.total_amount_all = 0
        self.total_amount_mining = 0
        self.total_amount_others = 0

    def to_dict(self):
        """Return the SummaryTotal as a dictionary."""
        return {
            "total_amount": self.total_amount,
            "total_amount_ess": self.total_amount_ess,
            "total_amount_all": self.total_amount_all,
            "total_amount_mining": self.total_amount_mining,
            "total_amount_others": self.total_amount_others,
        }


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

    def aggregate_journal(self, journal):
        result = journal.aggregate(
            total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
        )
        return result["total_amount"]

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

            filter_ledger = Q(second_party_id__in=chars_mains)
            filter_bounty = filter_ledger & Q(ref_type="bounty_prizes")
            filter_ess = filter_ledger & Q(ref_type="ess_escrow_transfer")

            total_bounty = self.aggregate_journal(
                corporation_journal.filter(filter_bounty)
            )
            total_ess = self.aggregate_journal(corporation_journal.filter(filter_ess))

            combined_amount = total_bounty + total_ess

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
                "total_amount_all": combined_amount,
            }
            # Summary all
            self.calc_summary_total(totals)

    def process_character_chars(
        self, corporation_journal, character_journal, mining_journal
    ):
        chars = [char.character_id for char in self.chars]
        for char in self.chars:
            char_id = char.character_id
            char_name = char.character_name

            # Core Filters
            filters = {
                "ledger": Q(second_party_id=char_id),
                "market": Q(second_party_id=char_id, ref_type="market_transaction"),
                "contracts": Q(
                    second_party_id=char_id,
                    ref_type__in=[
                        "contract_price_payment_corp",
                        "contract_reward",
                        "contract_price",
                    ],
                    amount__gt=0,
                ),
                "donations": Q(second_party_id=char_id, ref_type="player_donation"),
                "bounty": Q(second_party_id=char_id, ref_type="bounty_prizes"),
                "ess": Q(second_party_id=char_id, ref_type="ess_escrow_transfer"),
                "mining": (
                    Q(character__eve_character__character_id=char_id)
                    if app_settings.LEDGER_MEMBERAUDIT_USE
                    else Q(character__character__character_id=char_id)
                ),
            }

            amounts = {
                "bounty": self.aggregate_journal(
                    character_journal.filter(filters["bounty"])
                ),
                "ess": self.aggregate_journal(
                    corporation_journal.filter(filters["ess"])
                ),
                "contracts": self.aggregate_journal(
                    character_journal.filter(filters["contracts"])
                ),
                "transactions": self.aggregate_journal(
                    character_journal.filter(filters["market"])
                ),
                "donations": self.aggregate_journal(
                    character_journal.filter(filters["donations"]).exclude(
                        first_party_id__in=chars
                    )
                ),
                "mining": mining_journal.filter(filters["mining"])
                .values("total", "date")
                .aggregate(
                    total_amount=Coalesce(
                        Sum(F("total")), 0, output_field=DecimalField()
                    )
                ),
            }

            amounts["ess"] = Decimal(
                (amounts["ess"] / app_settings.LEDGER_CORP_TAX)
                * (100 - app_settings.LEDGER_CORP_TAX)
            )

            total_amount_others = (
                amounts["contracts"] + amounts["transactions"] + amounts["donations"]
            )
            combined_amount = amounts["bounty"] + amounts["ess"] + total_amount_others

            if amounts["bounty"] > 0 or total_amount_others > 0:
                self.character_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "total_amount": amounts["bounty"],
                    "total_amount_ess": amounts["ess"],
                    "total_amount_mining": amounts["mining"]["total_amount"],
                    "total_amount_others": total_amount_others,
                }

            totals = {
                "total_amount": amounts["bounty"],
                "total_amount_ess": amounts["ess"],
                "total_amount_all": combined_amount,
                "total_amount_mining": amounts["mining"]["total_amount"],
                "total_amount_others": total_amount_others,
            }
            # Summary all
            self.calc_summary_total(totals)

    def character_ledger(self):
        filters = (
            Q(character__eve_character__in=self.chars)
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else Q(character__character__in=self.chars)
        )
        filter_date = Q(date__year=self.year)
        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        chars = [char.character_id for char in self.chars]

        entries_filter = Q(second_party_id__in=chars) | Q(first_party_id__in=chars)

        # Filter the entries for the current day/month
        character_journal = (
            CharacterWalletJournalEntry.objects.filter(filters, filter_date)
            .select_related("first_party", "second_party", SR_CHAR)
            .order_by("-date")
        )

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(entries_filter, filter_date)
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)
        mining_journal = (
            CharacterMiningLedger.objects.filter(filters, filter_date)
            .select_related(SR_CHAR)
            .order_by("-date")
        ).annotate_pricing()

        self.process_character_chars(
            corporation_journal, character_journal, mining_journal
        )

        # Use Only Corporation Ledger
        models = corporation_journal, character_journal, mining_journal
        # Create the Ledger
        date_data = LedgerDate(self.year, self.month)
        ledger = BillboardLedger(models, date_data, corp=False)
        billboard_dict = ledger.billboard_char_ledger()

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

    def corporation_ledger(self, corporations, chars_list):
        filters = Q(division__corporation__corporation__corporation_id__in=corporations)
        filters &= Q(second_party_id__in=chars_list)
        filter_date = Q(date__year=self.year)

        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        corporation_journal = (
            CorporationWalletJournalEntry.objects.filter(filters, filter_date)
            .select_related(
                "division",
                "division__corporation",
                "division__corporation__corporation",
                "first_party",
                "second_party",
            )
            .order_by("-date")
        )
        self.process_corporation_chars(corporation_journal)

        # Use Only Corporation Ledger
        models = corporation_journal, None, None
        # Create the Ledger
        date_data = LedgerDate(self.year, self.month)
        ledger = BillboardLedger(models, date_data, corp=True)
        billboard_dict = ledger.billboard_corp_ledger(
            self.corporation_dict, self.summary_total.total_amount
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


class BillboardLedger:
    def __init__(self, models, date_data, corp=False):
        self.is_corp = corp
        self.models = models
        self.data = LedgerData(models)
        self.date = date_data
        self.sum = LedgerSum()
        self.billboard_dict = {
            "walletcharts": [],
            "charts": [],
            "rattingbar": [],
            "workflowgauge": [],
        }
        self.date_billboard = ["x"]

    def set_filters(self, filter_date):
        if self.is_corp:
            return Q(date__year=self.date.year, date__month=filter_date)
        return Q(
            date__year=self.date.year,
            date__month=self.date.month,
            date__day=filter_date,
        )

    def aggregate_journal(self, journal):
        result = journal.aggregate(
            total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
        )
        return result["total_amount"]

    def process_day(self, range_):
        date = datetime.now()
        if self.date.monthly:
            date = date.replace(day=1)
            # Core
        filters = {
            "date": (
                Q(date__year=self.date.year, date__month=range_)
                if self.date.monthly
                else Q(
                    date__year=self.date.year,
                    date__month=self.date.month,
                    date__day=range_,
                )
            ),
            "miscellaneous": Q(
                ref_type__in=[
                    "market_transaction",
                    "contract_price_payment_corp",
                    "contract_reward",
                    "contract_price",
                ],
                amount__gt=0,
            ),
            "market_cost": Q(
                ref_type__in=[
                    "market_escrow",
                    "transaction_tax",
                    "market_provider_tax",
                    "brokers_fee",
                ],
                amount__lt=0,
            ),
            "production_cost": Q(
                ref_type__in=["industry_job_tax", "manufacturing"], amount__lt=0
            ),
            "bounty": Q(ref_type="bounty_prizes"),
            "ess": Q(ref_type="ess_escrow_transfer"),
        }
        # Calculate the totals for Character Billboard
        if not self.is_corp:
            mining_query = self.data.mining_data.filter(filters["date"]).values(
                "total", "date"
            )
            mining_aggregated = mining_query.aggregate(total_amount=Sum(F("total")))
            total_amount_mining = mining_aggregated["total_amount"] or 0
            # Calculate the total bounty, ESS payout, and miscellaneous amounts
            self.data.total_bounty = self.aggregate_journal(
                self.data.entries.filter(filters["bounty"], filters["date"])
            )
            # Calculate the total market escrow, transaction tax, market provider tax, and broker's fee
            self.data.total_market = self.aggregate_journal(
                self.data.entries.filter(filters["market_cost"], filters["date"])
            )
            # Calculate the total production cost
            self.data.total_production_cost = self.aggregate_journal(
                self.data.entries.filter(filters["production_cost"], filters["date"])
            )
            # Calculate the total miscellaneous
            self.data.total_miscellaneous = self.aggregate_journal(
                self.data.entries.filter(filters["miscellaneous"], filters["date"])
            )
            self.data.total_isk = self.aggregate_journal(
                self.data.entries.filter(Q(amount__gt=0))
            )
            self.data.total_cost = self.aggregate_journal(
                self.data.entries.filter(Q(amount__lt=0))
            )
        # Calculate the totals for Corporation Billboard
        if self.is_corp:
            self.data.total_ess_payout = (
                self.aggregate_journal(
                    self.data.ess_entries.filter(filters["ess"], filters["date"])
                )
                / app_settings.LEDGER_CORP_TAX
            ) * (100 - app_settings.LEDGER_CORP_TAX)
            self.data.total_bounty = self.aggregate_journal(
                self.data.ess_entries.filter(filters["bounty"], filters["date"])
            )

        # Add the totals to the respective lists
        self.sum.sum_amount.append(int(self.data.total_bounty))
        self.sum.sum_amount_ess.append(int(self.data.total_ess_payout))
        if not self.is_corp:
            self.sum.sum_amount_misc.append(int(self.data.total_miscellaneous))
            self.sum.sum_amount_mining.append(int(total_amount_mining))
        # Add the date to the date list
        self.date_billboard.append(
            date.replace(day=range_).strftime("%Y-%m-%d")
            if not self.date.monthly
            else date.replace(month=range_).strftime("%Y-%m")
        )

    def calculate_total_sum(self):
        self.sum.total_sum = sum(
            sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
            for lst in [
                self.sum.sum_amount,
                self.sum.sum_amount_ess,
                self.sum.sum_amount_misc,
                self.sum.sum_amount_mining,
            ]
        )

    def calculate_percentages(self):
        percentages = [
            (
                (
                    sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
                    / self.sum.total_sum
                    * 100
                )
                if self.sum.total_sum > 0
                else 0
            )
            for lst in [
                self.sum.sum_amount,
                self.sum.sum_amount_ess,
                self.sum.sum_amount_misc,
                self.sum.sum_amount_mining,
            ]
        ]
        return [math.floor(perc * 10) / 10 for perc in percentages]

    def generate_gauge_data(self, rounded_percentages):
        self.billboard_dict["workflowgauge"] = (
            [
                ["Ratting", rounded_percentages[0]],
                ["ESS Payout", rounded_percentages[1]],
                ["Miscellaneous", rounded_percentages[2]],
                ["Mining", rounded_percentages[3]],
            ]
            if sum(rounded_percentages)
            else None
        )

    def generate_wallet_ratting_bar(self):
        self.billboard_dict["rattingbar"] = (
            (
                [
                    self.date_billboard,
                    self.sum.sum_amount,
                    self.sum.sum_amount_ess,
                    self.sum.sum_amount_misc,
                    self.sum.sum_amount_mining,
                ]
            )
            if self.sum.total_sum
            else None
        )

    def generate_wallet_charts_data(self):
        # Daten für die Wallet-Charts vorbereiten
        misc_cost = abs(
            self.data.total_cost
            - self.data.total_production_cost
            - self.data.total_market
        )
        wallet_chart_data = [
            # Earns
            ["Earns", int(self.data.total_isk)],
            # ["Ratting", int(total_sum_ratting)],  ["Mining", int(total_sum_mining)], ["Misc.", int(total_sum_misc)],
            # Costs
            ["Market Cost", int(abs(self.data.total_market))],
            ["Production Cost", int(abs(self.data.total_production_cost))],
            ["Misc. Costs", int(misc_cost)],
        ]
        self.billboard_dict["walletcharts"] = (
            wallet_chart_data
            if any(item[1] != 0 for item in wallet_chart_data)
            else None
        )

    # Generate Charts Billboard for Corporation Wallets
    def generate_wallet_corps_data(self, corporation_dict, summary_dict_all):
        for entry in corporation_dict.values():
            total_amount_entry = entry["total_amount"]
            percentage = (total_amount_entry / summary_dict_all) * 100
            name = entry["main_name"]
            self.billboard_dict["charts"].append([name, percentage])

        self.billboard_dict["charts"] = (
            sorted(self.billboard_dict["charts"], key=lambda x: x[0])
            if self.billboard_dict["charts"]
            else None
        )

    # Create the Billboard Char Ledger
    def billboard_char_ledger(self):
        for range_ in self.date.day_checks:
            try:
                self.process_day(range_)
            except ValueError:
                continue

        self.calculate_total_sum()

        rounded_percentages = self.calculate_percentages()
        self.generate_gauge_data(rounded_percentages)

        self.generate_wallet_ratting_bar()

        self.generate_wallet_charts_data()

        return self.billboard_dict

    # Create the Billboard Corp Ledger
    def billboard_corp_ledger(self, corporation_dict, summary_dict_all):
        for range_ in self.date.day_checks:
            try:
                self.process_day(range_)
            except ValueError:
                continue

        self.calculate_total_sum()

        self.generate_wallet_ratting_bar()

        self.generate_wallet_corps_data(corporation_dict, summary_dict_all)

        return self.billboard_dict
