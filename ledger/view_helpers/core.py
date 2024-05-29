"""
Core View Helper
"""

from decimal import Decimal
from typing import Tuple

from django.core.cache import cache
from django.db.models import Q

from ledger.app_settings import STORAGE_BASE_KEY
from ledger.decorators import custom_cache_timeout
from ledger.hooks import get_extension_logger
from ledger.models.events import Events

logger = get_extension_logger(__name__)


def calculate_ess_stolen(total_amount: int, ess_amount: int) -> Tuple[int, int]:
    total_ess_stolen = 0
    total_ess_gain = 0

    total_ess_gain = ess_amount / total_amount
    total_ess_gain = total_ess_gain * 100

    total_ess_gain_diff = Decimal(66.667) - int(total_ess_gain)
    if (
        abs(total_ess_gain_diff) < Decimal("0.9") or total_ess_gain_diff < 0
    ):  # Hier können Sie den Schwellenwert nach Bedarf anpassen
        total_ess_gain = 0
    else:
        total_ess_stolen = ess_amount * (total_ess_gain_diff / 100)
        total_ess_gain = total_ess_gain_diff

    return round(total_ess_stolen), round(total_ess_gain)


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
