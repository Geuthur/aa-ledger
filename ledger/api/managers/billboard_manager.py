import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from ledger import app_settings
from ledger.api.managers.core_manager import LedgerData, LedgerDate, LedgerModels


@dataclass
class LedgerSum:
    sum_amount: list = field(default_factory=lambda: ["Ratting"])
    sum_amount_ess: list = field(default_factory=lambda: ["ESS Payout"])
    sum_amount_misc: list = field(default_factory=lambda: ["Miscellaneous"])
    sum_amount_mining: list = field(default_factory=lambda: ["Mining"])
    total_sum: int = None


class BillboardLedger:
    def __init__(self, date_data: LedgerDate, models: LedgerModels, corp=False):
        self.is_corp = corp
        self.data = LedgerData()
        self.models = models
        self.date = date_data
        self.sum = LedgerSum()
        self.billboard_dict = {
            "walletcharts": [],
            "charts": [],
            "rattingbar": [],
            "workflowgauge": [],
        }
        self.date_billboard = ["x"]

    def aggregate_corp(self, journal, range_):
        """Aggregate the journal entries for the corporation."""
        total_bounty = 0
        total_ess_payout = 0
        for entry in journal:
            if (self.date.month == 0 and entry["date"].month == range_) or (
                self.date.month != 0 and entry["date"].day == range_
            ):
                if self.is_corp:
                    if entry["ref_type"] == "bounty_prizes":
                        total_bounty += entry["amount"]
                if entry["ref_type"] == "ess_escrow_transfer":
                    if self.is_corp:
                        total_ess_payout += entry["amount"]
                    else:
                        total_ess_payout += (
                            entry["amount"] / app_settings.LEDGER_CORP_TAX
                        ) * (100 - app_settings.LEDGER_CORP_TAX)
        return total_bounty, total_ess_payout

    def aggregate_char(self, journal, range_):
        """Aggregate the journal entries for the character."""
        total_bounty = 0
        total_miscellaneous = 0
        total_isk = 0
        total_cost = 0
        total_market_cost = 0
        total_production_cost = 0

        for entry in journal:
            if (self.date.month == 0 and entry["date"].month == range_) or (
                self.date.month != 0 and entry["date"].day == range_
            ):
                # Bounty Filter
                if entry["ref_type"] == "bounty_prizes":
                    total_bounty += entry["amount"]
                # Misc Filter
                if (
                    entry["ref_type"]
                    in [
                        "market_transaction",
                        "contract_price_payment_corp",
                        "contract_reward",
                        "contract_price",
                    ]
                    and entry["amount"] > 0
                ):
                    total_miscellaneous += entry["amount"]
                # Donation Filter
                if (entry["ref_type"] == "player_donation") and entry["amount"] > 0:
                    if entry["first_party_id"] not in self.chars:
                        total_miscellaneous += entry["amount"]
                # Total ISK
                if entry["amount"] > 0:
                    total_isk += entry["amount"]
                else:
                    total_cost += entry["amount"]
                # Total Market
                if entry["ref_type"] in [
                    "market_escrow",
                    "transaction_tax",
                    "market_provider_tax",
                    "brokers_fee",
                ]:
                    if entry["amount"] < 0:
                        total_market_cost += entry["amount"]
                # Production Cost
                if entry["ref_type"] in ["industry_job_tax", "manufacturing"]:
                    total_production_cost += entry["amount"]
        return (
            total_bounty,
            total_miscellaneous,
            total_isk,
            total_cost,
            total_market_cost,
            total_production_cost,
        )

    def aggregate_mining(self, journal, range_):
        """Aggregate the journal entries for the mining."""
        total_mining = 0
        for entry in journal:
            if (self.date.month == 0 and entry["date"].month == range_) or (
                self.date.month != 0 and entry["date"].day == range_
            ):
                total_mining += entry["total"] if entry["total"] else 0
        return total_mining

    # pylint: disable=too-many-branches
    def process_day(
        self, range_, corp_journal=None, char_journal=None, mining_journal=None
    ):
        """Process the day for the journal entries."""
        date = datetime.now()

        if self.date.monthly:
            date = date.replace(day=1)

        if corp_journal:
            total_bounty, total_ess = self.aggregate_corp(corp_journal, range_)
            self.data.total_bounty = total_bounty
            self.data.total_ess_payout = total_ess
        if char_journal:
            (
                total_bounty,
                total_miscellaneous,
                total_isk,
                total_cost,
                total_market_cost,
                total_production_cost,
            ) = self.aggregate_char(char_journal, range_)

            self.data.total_bounty = total_bounty
            self.data.total_miscellaneous = total_miscellaneous
            # Wallet Charts
            self.data.total_isk += total_isk
            self.data.total_cost += total_cost
            self.data.total_market_cost += total_market_cost
            self.data.total_production_cost += total_production_cost

        if mining_journal:
            total_mining = self.aggregate_mining(mining_journal, range_)
            self.data.total_mining = total_mining

        # Add the totals to the respective lists
        self.sum.sum_amount.append(int(self.data.total_bounty))
        self.sum.sum_amount_ess.append(int(self.data.total_ess_payout))
        if not self.is_corp:
            self.sum.sum_amount_misc.append(int(self.data.total_miscellaneous))
            self.sum.sum_amount_mining.append(int(self.data.total_mining))
        # Add the date to the date list
        try:
            self.date_billboard.append(
                date.replace(day=range_).strftime("%Y-%m-%d")
                if not self.date.monthly
                else date.replace(month=range_).strftime("%Y-%m")
            )
        except ValueError:
            pass

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
            - self.data.total_market_cost
        )
        wallet_chart_data = [
            # Earns
            ["Income", int(self.data.total_isk)],
            # ["Ratting", int(total_sum_ratting)],  ["Mining", int(total_sum_mining)], ["Misc.", int(total_sum_misc)],
            # Costs
            ["Market Cost", int(abs(self.data.total_market_cost))],
            ["Production Cost", int(abs(self.data.total_production_cost))],
            ["Misc. Cost", int(misc_cost)],
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
    def billboard_char_ledger(self, chars: list):
        self.chars = chars
        corp_journal_values = self.models.corp_journal.values(
            "amount", "ref_type", "first_party_id", "second_party_id", "date"
        )
        char_journal_values = self.models.char_journal.values(
            "amount", "ref_type", "first_party_id", "second_party_id", "date"
        )
        mining_journal_values = self.models.mining_journal.values("total", "date")
        for day in self.date.day_checks:
            self.process_day(
                day, corp_journal_values, char_journal_values, mining_journal_values
            )

        self.calculate_total_sum()

        rounded_percentages = self.calculate_percentages()
        self.generate_gauge_data(rounded_percentages)

        self.generate_wallet_ratting_bar()

        self.generate_wallet_charts_data()

        return self.billboard_dict

    # Create the Billboard Corp Ledger
    def billboard_corp_ledger(self, corporation_dict, summary_dict_all):
        corp_journal_values = self.models.corp_journal.values(
            "amount", "ref_type", "first_party_id", "second_party_id", "date"
        )
        for day in self.date.day_checks:
            self.process_day(day, corp_journal_values)

        self.calculate_total_sum()

        self.generate_wallet_ratting_bar()

        self.generate_wallet_corps_data(corporation_dict, summary_dict_all)

        return self.billboard_dict
