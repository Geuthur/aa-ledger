from datetime import datetime

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def _billboard_corp_ledger(
    wallet_journal, summary_dict, summary_dict_all, monthly, year: int, month: int
):  # pylint: disable=too-many-arguments
    """
    Billboard System for Corp Ledger
    """

    current_date = datetime.now()

    current_date = current_date.replace(year=year)
    if not month == 0:
        current_date = current_date.replace(month=month)

    billboard_dict = {"charts": [], "rattingbar": []}

    for entry in summary_dict.values():
        total_amount_entry = entry["total_amount"]
        percentage = (total_amount_entry / summary_dict_all) * 100
        name = entry["main_name"]
        billboard_dict["charts"].append([name, percentage])

    sum_amount = []
    sum_amount.append("Ratting")

    sum_amount_ess = []
    sum_amount_ess.append("ESS Payout")

    date_billboard = []
    date_billboard.append("x")

    # Month, Days
    range_data = 12 if monthly else 31
    # Vorbedingungen festlegen
    day_checks = list(range(1, range_data + 1))

    # Iteration über die Tage
    # pylint: disable=duplicate-code
    for range_ in day_checks:
        try:
            date = current_date

            if monthly:
                date = date.replace(day=1)

            total_bounty = 0
            total_ess = 0

            for w in wallet_journal:
                if w.date.year == year and (
                    w.date.month == range_
                    if monthly
                    else w.date.month == month and w.date.day == range_
                ):
                    if w.ref_type == "bounty_prizes":
                        total_bounty += w.amount
                    if w.ref_type == "ess_escrow_transfer":
                        total_ess += w.amount

            # Hinzufügen des Datums zum date_billboard
            date_billboard.append(
                date.replace(day=range_).strftime("%Y-%m-%d")
                if not monthly
                else date.replace(month=range_).strftime("%Y-%m")
            )

            # Hinzufügen der Summen zu den Summenlisten
            sum_amount.append(int(total_bounty))
            sum_amount_ess.append(int(total_ess))
        except ValueError:
            continue

    total_sum = sum(
        sum(filter(lambda x: isinstance(x, int), lst))
        for lst in [sum_amount, sum_amount_ess]
    )

    billboard_dict["charts"] = (
        sorted(billboard_dict["charts"], key=lambda x: x[0])
        if billboard_dict["charts"]
        else None
    )
    billboard_dict["rattingbar"] = (
        [date_billboard, sum_amount, sum_amount_ess] if total_sum else None
    )

    return billboard_dict
