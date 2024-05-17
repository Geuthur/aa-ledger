import math
from datetime import datetime
from decimal import Decimal

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from ledger import app_settings
from ledger.models.corporationaudit import CorporationWalletJournalEntry

if app_settings.LEDGER_MEMBERAUDIT_USE:
    from memberaudit.models import CharacterMiningLedgerEntry as CharacterMiningLedger
    from memberaudit.models import CharacterWalletJournalEntry
else:
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry,
        CharacterMiningLedger,
    )

from ledger.hooks import get_extension_logger
from ledger.view_helpers.core import events_filter

logger = get_extension_logger(__name__)


# pylint: disable=too-many-instance-attributes, too-many-arguments, too-many-locals, too-many-branches
class JournalProcess:
    def __init__(self, chars, year, month):
        self.year = year
        self.month = month
        self.chars = chars
        self.monthly = month == 0
        self.corporation_dict = {}
        self.character_dict = {}
        self.summary_total = {}
        self.sr_char = (
            "character__eve_character"
            if app_settings.LEDGER_MEMBERAUDIT_USE
            else "character__character"
        )
        self.corporation_journal = CorporationWalletJournalEntry
        self.character_journal = CharacterWalletJournalEntry
        self.mining_journal = CharacterMiningLedger
        self.summary_total["total_amount"] = 0
        self.summary_total["total_amount_ess"] = 0
        self.summary_total["total_amount_all"] = 0
        self.summary_total["total_amount_mining"] = 0
        self.summary_total["total_amount_others"] = 0
        self.output = []

    def process_corporation_chars(self, corporation_journal):
        # Create a Dict for all Mains(including their alts)
        for _, data in self.chars.items():
            main = data["main"]
            alts = data["alts"]

            chars_mains = [alt.character_id for alt in alts] + [main.character_id]

            alts_names = []

            total_bounty = 0
            total_ess = 0

            char_name = main.character_name
            char_id = main.character_id

            for w in corporation_journal:
                if w.second_party_id in chars_mains:
                    if w.ref_type == "bounty_prizes":
                        total_bounty += w.amount
                    if w.ref_type == "ess_escrow_transfer":
                        total_ess += w.amount

            combined_amount = total_bounty + total_ess

            if total_bounty or total_ess:
                self.corporation_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "alt_names": alts_names,
                    "total_amount": total_bounty,
                    "total_amount_ess": total_ess,
                }

            # Summary all
            self.summary_total["total_amount"] += total_bounty
            self.summary_total["total_amount_ess"] += total_ess
            self.summary_total["total_amount_all"] += combined_amount

    # TODO Calcluate Tax via Amount and Tax Field in Model
    def process_character_chars(
        self, corporation_journal, character_journal, mining_journal
    ):
        chars = [char.character_id for char in self.chars]
        for char in self.chars:
            char_id = char.character_id
            char_name = char.character_name

            # Core
            filter_ledger = Q(second_party_id=char_id)

            # Industry
            filter_market = filter_ledger & Q(ref_type="market_transaction")
            filter_contracts = filter_ledger & Q(
                ref_type__in=[
                    "contract_price_payment_corp",
                    "contract_reward",
                    "contract_price",
                ],
                amount__gt=0,
            )
            filter_donations = filter_ledger & Q(ref_type="player_donation")

            # Ratting
            filter_bounty = filter_ledger & Q(ref_type="bounty_prizes")
            filter_ess = filter_ledger & Q(ref_type="ess_escrow_transfer")
            # Mining
            filter_mining = (
                Q(character__eve_character__character_id=char_id)
                if app_settings.LEDGER_MEMBERAUDIT_USE
                else Q(character__character__character_id=char_id)
            )

            amount_bounty = character_journal.filter(filter_bounty).aggregate(
                total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
            )

            amount_ess = corporation_journal.filter(filter_ess).aggregate(
                total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
            )
            amount_ess["total_amount"] = Decimal(
                (amount_ess["total_amount"] / app_settings.LEDGER_CORP_TAX)
                * (100 - app_settings.LEDGER_CORP_TAX)
            )

            amount_contracts = character_journal.filter(filter_contracts).aggregate(
                total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
            )

            amount_transactions = character_journal.filter(filter_market).aggregate(
                total_amount=Coalesce(Sum(F("amount")), 0, output_field=DecimalField())
            )

            amount_donations = (
                character_journal.filter(filter_donations)
                .exclude(first_party_id__in=chars)
                .aggregate(
                    total_amount=Coalesce(
                        Sum(F("amount")), 0, output_field=DecimalField()
                    )
                )
            )

            amount_mining = (
                mining_journal.filter(filter_mining)
                .values("total", "date")
                .aggregate(
                    total_amount=Coalesce(
                        Sum(F("total")), 0, output_field=DecimalField()
                    )
                )
            )

            total_amount_others = (
                amount_contracts["total_amount"]
                + amount_transactions["total_amount"]
                + amount_donations["total_amount"]
            )
            combined_amount = (
                amount_bounty["total_amount"]
                + amount_ess["total_amount"]
                + total_amount_others
            )

            if amount_bounty["total_amount"] > 0 or total_amount_others > 0:
                self.character_dict[char_id] = {
                    "main_id": char_id,
                    "main_name": char_name,
                    "total_amount": amount_bounty["total_amount"],
                    "total_amount_ess": amount_ess["total_amount"],
                    "total_amount_mining": amount_mining["total_amount"],
                    "total_amount_others": total_amount_others,
                }

            # Total Amount
            self.summary_total["total_amount"] += amount_bounty["total_amount"]
            # ESS
            self.summary_total["total_amount_ess"] += amount_ess["total_amount"]
            # Mined
            self.summary_total["total_amount_mining"] += amount_mining["total_amount"]
            # others
            self.summary_total["total_amount_others"] += total_amount_others
            # Combined
            self.summary_total["total_amount_all"] += combined_amount

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

        character_journal = (
            self.character_journal.objects.filter(filters, filter_date)
            .select_related("first_party", "second_party", self.sr_char)
            .order_by("-date")
        )

        corporation_journal = (
            self.corporation_journal.objects.filter(entries_filter, filter_date)
            .select_related("first_party", "second_party")
            .order_by("-date")
        )

        # Exclude Events to avoid wrong stats
        corporation_journal = events_filter(corporation_journal)
        mining_journal = (
            CharacterMiningLedger.objects.filter(filters, filter_date)
            .select_related(self.sr_char)
            .order_by("-date")
        ).annotate_pricing()

        self.process_character_chars(
            corporation_journal, character_journal, mining_journal
        )

        # Use Only Corporation Ledger
        models = corporation_journal, character_journal, mining_journal
        # Create the Ledger
        ledger = BillboardLedger(
            models, self.monthly, self.year, self.month, corp=False
        )
        billboard_dict = ledger.billboard_char_ledger()

        self.output.append(
            {
                "ratting": sorted(
                    list(self.character_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": self.summary_total,
                "billboard": billboard_dict,
            }
        )

        return self.output

    def corporation_ledger(self, corporations, chars_list):
        filters = Q(division__corporation__corporation__corporation_id__in=corporations)
        filters &= Q(second_party_id__in=chars_list)
        filter_date = Q(date__year=self.year)

        if not self.month == 0:
            filter_date &= Q(date__month=self.month)

        corporation_journal = (
            self.corporation_journal.objects.filter(filters, filter_date)
            .prefetch_related(
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
        ledger = BillboardLedger(models, self.monthly, self.year, self.month, corp=True)
        billboard_dict = ledger.billboard_corp_ledger(
            self.corporation_dict, self.summary_total["total_amount"]
        )

        self.output.append(
            {
                "ratting": sorted(
                    list(self.corporation_dict.values()), key=lambda x: x["main_name"]
                ),
                "total": self.summary_total,
                "billboard": billboard_dict,
            }
        )

        return self.output


class BillboardLedger:
    def __init__(self, models, monthly, year, month, corp=False):
        self.is_corp = corp
        self.models = models
        self.monthly = monthly
        self.year = year
        self.month = month
        self.current_date = datetime.now()
        self.billboard_dict = {
            "walletcharts": [],
            "charts": [],
            "rattingbar": [],
            "workflowgauge": [],
        }
        self.sum_amount = ["Ratting"]
        self.sum_amount_ess = ["ESS Payout"]
        self.sum_amount_misc = ["Miscellaneous"]
        self.sum_amount_mining = ["Mining"]
        self.date_billboard = ["x"]
        self.ess_entries, self.entries, self.mining_data = models
        self.total_isk = 0
        self.total_cost = 0
        self.total_production_cost = 0
        self.total_market = 0
        self.range_data = 12 if self.monthly else 31
        self.day_checks = list(range(1, self.range_data + 1))
        self.total_sum = None

    def process_day(self, range_):
        date = datetime.now()
        total_bounty = 0
        total_ess_payout = 0
        total_miscellaneous = 0
        if self.monthly:
            date = date.replace(day=1)
        filter_date = (
            Q(date__year=self.year, date__month=range_)
            if self.monthly
            else Q(date__year=self.year, date__month=self.month, date__day=range_)
        )

        # Filter the entries for the current day/month
        entries_for_day_ess = self.ess_entries.filter(filter_date)

        if not self.is_corp:
            my_filter_mining = filter_date
            mining_query = self.mining_data.filter(my_filter_mining).values(
                "total", "date"
            )
            mining_aggregated = mining_query.aggregate(total_amount=Sum(F("total")))
            total_amount_mining = mining_aggregated["total_amount"] or 0
            entries_for_day = self.entries.filter(filter_date)
            # Calculate the total bounty, ESS payout, and miscellaneous amounts
            for entry in entries_for_day:
                if entry.ref_type == "bounty_prizes" and entry.amount > 0:
                    total_bounty += entry.amount
                if not self.is_corp:
                    # Calculate the total market escrow, transaction tax, market provider tax, and broker's fee
                    if (
                        entry.ref_type
                        in [
                            "market_escrow",
                            "transaction_tax",
                            "market_provider_tax",
                            "brokers_fee",
                        ]
                        and entry.amount < 0
                    ):
                        self.total_market += entry.amount
                    # Calculate the total production cost
                    if (
                        entry.ref_type in ["industry_job_tax", "manufacturing"]
                        and entry.amount < 0
                    ):
                        self.total_production_cost += entry.amount
                    if (
                        entry.ref_type
                        in [
                            "market_transaction",
                            "contract_price_payment_corp",
                            "contract_reward",
                            "contract_price",
                        ]
                        and entry.amount > 0
                    ):
                        total_miscellaneous += entry.amount
                if entry.amount > 0:
                    self.total_isk += entry.amount
                else:
                    self.total_cost += entry.amount

        for entry in entries_for_day_ess:
            if self.is_corp:
                if entry.ref_type == "bounty_prizes" and entry.amount > 0:
                    total_bounty += entry.amount
            if entry.ref_type == "ess_escrow_transfer":
                total_ess_payout += (entry.amount / app_settings.LEDGER_CORP_TAX) * (
                    100 - app_settings.LEDGER_CORP_TAX
                )

        # Add the totals to the respective lists
        self.sum_amount.append(int(total_bounty))
        self.sum_amount_ess.append(int(total_ess_payout))
        if not self.is_corp:
            self.sum_amount_misc.append(int(total_miscellaneous))
            self.sum_amount_mining.append(int(total_amount_mining))
        # Add the date to the date list
        self.date_billboard.append(
            date.replace(day=range_).strftime("%Y-%m-%d")
            if not self.monthly
            else date.replace(month=range_).strftime("%Y-%m")
        )

    def calculate_total_sum(self):
        self.total_sum = sum(
            sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
            for lst in [
                self.sum_amount,
                self.sum_amount_ess,
                self.sum_amount_misc,
                self.sum_amount_mining,
            ]
        )

    def calculate_percentages(self):
        percentages = [
            (
                (
                    sum(filter(lambda x: isinstance(x, (int, Decimal)), lst))
                    / self.total_sum
                    * 100
                )
                if self.total_sum > 0
                else 0
            )
            for lst in [
                self.sum_amount,
                self.sum_amount_ess,
                self.sum_amount_misc,
                self.sum_amount_mining,
            ]
        ]
        return [math.floor(perc * 10) / 10 for perc in percentages]

    def prepare_gauge_data(self, rounded_percentages):
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

    def prepare_wallet_ratting_bar(self):
        self.billboard_dict["rattingbar"] = (
            (
                [
                    self.date_billboard,
                    self.sum_amount,
                    self.sum_amount_ess,
                    self.sum_amount_misc,
                    self.sum_amount_mining,
                ]
            )
            if self.total_sum
            else None
        )

    def prepare_wallet_charts_data(self):
        # Daten für die Wallet-Charts vorbereiten
        misc_cost = abs(
            self.total_cost - self.total_production_cost - self.total_market
        )
        wallet_chart_data = [
            # Earns
            ["Earns", int(self.total_isk)],
            # ["Ratting", int(total_sum_ratting)],  ["Mining", int(total_sum_mining)], ["Misc.", int(total_sum_misc)],
            # Costs
            ["Market Cost", int(abs(self.total_market))],
            ["Production Cost", int(abs(self.total_production_cost))],
            ["Misc. Costs", int(misc_cost)],
        ]
        self.billboard_dict["walletcharts"] = (
            wallet_chart_data
            if any(item[1] != 0 for item in wallet_chart_data)
            else None
        )

    def prepare_wallet_corps_data(self, corporation_dict, summary_dict_all):
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

    def billboard_char_ledger(self):
        for range_ in self.day_checks:
            try:
                self.process_day(range_)
            except ValueError:
                continue

        self.calculate_total_sum()

        rounded_percentages = self.calculate_percentages()
        self.prepare_gauge_data(rounded_percentages)

        self.prepare_wallet_ratting_bar()

        self.prepare_wallet_charts_data()

        return self.billboard_dict

    def billboard_corp_ledger(self, corporation_dict, summary_dict_all):
        for range_ in self.day_checks:
            try:
                self.process_day(range_)
            except ValueError:
                continue

        self.calculate_total_sum()

        self.prepare_wallet_ratting_bar()

        self.prepare_wallet_corps_data(corporation_dict, summary_dict_all)

        return self.billboard_dict
