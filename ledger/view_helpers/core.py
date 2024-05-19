"""
Core View Helper
"""

from datetime import datetime
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q

from ledger.app_settings import STORAGE_BASE_KEY
from ledger.decorators import custom_cache_timeout
from ledger.hooks import get_extension_logger
from ledger.models import Events

logger = get_extension_logger(__name__)

filter_market = {"ref_type": "market_transaction"}
filter_market_cost = {
    "ref_type__in": ["transaction_tax", "market_provider_tax", "brokers_fee"]
}
filter_production = {"ref_type__in": ["industry_job_tax", "manufacturing"]}
filter_contracts = {"ref_type__in": ["contract_price_payment_corp", "contract_reward"]}
filter_donations = {"ref_type": "player_donation"}
filter_ess = {"ref_type": "ess_escrow_transfer"}
filter_bounty = {"ref_type": "bounty_prizes"}


def calculate_days_year():
    current_date = datetime.now()
    # Initialisiere die Gesamtanzahl der Tage
    total_days = 365

    # Iteriere durch die Monate rückwärts vom Vormonat
    for month in range(current_date.month, 0, -1):
        # Berechne den Vormonat unter Berücksichtigung von Sonderfällen
        prev_month = month if month != 1 else 12

        # Bestimme die Anzahl der Tage im aktuellen Monat
        days_in_month = (
            current_date.replace(month=month, day=1)
            - current_date.replace(month=prev_month, day=1)
        ).days

        # Addiere die Anzahl der Tage zum Gesamttage
        total_days += days_in_month

    # Berücksichtige die Tage im aktuellen Monat
    total_days += current_date.day

    return total_days


def calculate_ess_stolen(total_amount, ess_amount):
    total_ess_stolen = 0
    total_ess_gain = 0

    try:
        total_ess_gain = ess_amount / total_amount
    except Exception:  # pylint: disable=broad-exception-caught
        return total_ess_stolen, total_ess_gain
    total_ess_gain = total_ess_gain * 100
    total_ess_gain_diff = Decimal(66.667) - total_ess_gain

    if (
        abs(total_ess_gain_diff) < Decimal("0.9") or total_ess_gain_diff < 0
    ):  # Hier können Sie den Schwellenwert nach Bedarf anpassen
        total_ess_gain = Decimal("0")
    else:
        result = total_ess_gain_diff
        total_ess_stolen = int(ess_amount * (result / 100))

        total_ess_gain = format(result, ".2f")

    return total_ess_stolen, total_ess_gain


def _storage_key(identifier: str) -> str:
    return STORAGE_BASE_KEY + str(identifier)


def get_cache_stale(key_name):
    data = cache.get(key=_storage_key(key_name))
    if not data:
        return False
    return data


def set_cache(data, key_name: str, time: int):
    cache.set(
        key=_storage_key(key_name),
        value=data,
        timeout=custom_cache_timeout(hours=time),
    )


def delete_cache(key_name: str):
    cache.delete(_storage_key(key_name))


def events_filter(entries):
    """
    Filter out all Entries that are in the time of the Event
    """
    # Events to Filter out
    events = Events.objects.all()

    q_objects = []

    # Durchlaufen Sie jedes Event und erstellen Sie das entsprechende Q-Objekt für den Datumsbereich
    for event in events:
        if not event.char_ledger:
            continue
        q_objects.append(Q(date__range=(event.date_start, event.date_end)))

    # Kombinieren Sie alle Q-Objekte mit einer ODER-Verknüpfung
    if q_objects:
        combined_q_object = q_objects[0]
        for q_object in q_objects[1:]:
            combined_q_object |= q_object

        entries = entries.exclude(combined_q_object)
    return entries
