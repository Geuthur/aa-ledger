import math
from datetime import datetime

from django.db.models import F, Q, Sum

from ledger import app_settings
from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def _billboard_char_ledger(models: list, mining_data, monthly, year: int, month: int):
    """
    Billboard System for Char Ledger
    """

    current_date = datetime.now()
    billboard_dict = {"walletcharts": [], "rattingbar": [], "workflowgauge": []}

    # Ratting Amount from Character Journal
    sum_amount = [
        "Ratting",
    ]
    sum_amount_ess = [
        "ESS Payout",
    ]
    sum_amount_misc = [
        "Miscellaneous",
    ]
    sum_amount_mining = [
        "Mining",
    ]
    date_billboard = [
        "x",
    ]

    entries, ess_entries = models

    # total amounts
    total_isk = 0
    total_cost = 0

    # costs
    total_production_cost = 0
    total_market = 0

    # Month, Days
    range_data = 12 if monthly else 31
    # Vorbedingungen festlegen
    day_checks = list(range(1, range_data + 1))

    # Rückwärts durch die Tage iterieren
    for range_ in day_checks:  # pylint: disable=duplicate-code
        try:
            date = current_date

            total_bounty = 0
            total_ess_payout = 0
            total_miscellaneous = 0

            if monthly:
                date = date.replace(day=1)

            filter_date = (
                Q(date__year=year, date__month=range_)
                if monthly
                else Q(date__year=year, date__month=month, date__day=range_)
            )
            my_filter_mining = filter_date

            mining_query = mining_data.filter(my_filter_mining).values("total", "date")
            mining_aggregated = mining_query.aggregate(total_amount=Sum(F("total")))
            total_amount_mining = mining_aggregated["total_amount"] or 0

            # Char Journal
            for w in entries:
                if w.date.year == year and (
                    w.date.month == range_
                    if monthly
                    else w.date.month == month and w.date.day == range_
                ):
                    if w.ref_type == "bounty_prizes" and w.amount > 0:
                        total_bounty += w.amount
                    if (
                        w.ref_type
                        in [
                            "market_escrow",
                            "transaction_tax",
                            "market_provider_tax",
                            "brokers_fee",
                        ]
                        and w.amount < 0
                    ):
                        total_market += w.amount
                    if (
                        w.ref_type in ["industry_job_tax", "manufacturing"]
                        and w.amount < 0
                    ):
                        total_production_cost += w.amount
                    if (
                        w.ref_type
                        in [
                            "market_transaction",
                            "contract_price_payment_corp",
                            "contract_reward",
                            "contract_price",
                        ]
                        and w.amount > 0
                    ):
                        total_miscellaneous += w.amount
                    if w.amount > 0:
                        total_isk += w.amount
                    else:
                        total_cost += w.amount

            # Corp Journal
            for w in ess_entries:
                if w.date.year == year and (
                    w.date.month == range_
                    if monthly
                    else w.date.month == month and w.date.day == range_
                ):
                    if w.ref_type == "ess_escrow_transfer":
                        total_ess_payout += (
                            w.amount / app_settings.LEDGER_CORP_TAX
                        ) * (100 - app_settings.LEDGER_CORP_TAX)

            date_billboard.append(  # pylint disable:duplicate-code
                date.replace(day=range_).strftime("%Y-%m-%d")
                if not monthly
                else date.replace(month=range_).strftime("%Y-%m")
            )

            sum_amount.append(int(total_bounty))
            sum_amount_ess.append(int(total_ess_payout))
            sum_amount_misc.append(int(total_miscellaneous))
            sum_amount_mining.append(int(total_amount_mining))
        except ValueError:
            continue

    # Misc Costs
    misc_cost = abs(total_cost - total_production_cost - total_market)

    # Gesamtbetrag berechnen
    total_sum = sum(
        sum(filter(lambda x: isinstance(x, int), lst))
        for lst in [sum_amount, sum_amount_ess, sum_amount_misc, sum_amount_mining]
    )

    # Prozentuale Anteile berechnen
    percentages = [
        (
            (sum(filter(lambda x: isinstance(x, int), lst)) / total_sum * 100)
            if total_sum > 0
            else 0
        )
        for lst in [sum_amount, sum_amount_ess, sum_amount_misc, sum_amount_mining]
    ]

    rounded_percentages = [math.floor(perc * 10) / 10 for perc in percentages]

    # Daten für die Gauge vorbereiten
    billboard_dict["workflowgauge"] = (
        [
            ["Ratting", rounded_percentages[0]],
            ["ESS Payout", rounded_percentages[1]],
            ["Miscellaneous", rounded_percentages[2]],
            ["Mining", rounded_percentages[3]],
        ]
        if total_sum
        else None
    )
    billboard_dict["rattingbar"] = (
        [date_billboard, sum_amount, sum_amount_ess, sum_amount_misc, sum_amount_mining]
        if total_sum
        else None
    )

    # Daten für die Wallet-Charts vorbereiten
    wallet_chart_data = [
        # Earns
        ["Earns", int(total_isk)],
        # ["Ratting", int(total_sum_ratting)],  ["Mining", int(total_sum_mining)], ["Misc.", int(total_sum_misc)],
        # Costs
        ["Market Cost", int(abs(total_market))],
        ["Production Cost", int(abs(total_production_cost))],
        ["Misc. Costs", int(misc_cost)],
    ]
    billboard_dict["walletcharts"] = (
        wallet_chart_data if any(item[1] != 0 for item in wallet_chart_data) else None
    )

    return billboard_dict
