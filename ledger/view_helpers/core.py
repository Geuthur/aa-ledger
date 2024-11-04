"""
Core View Helper
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q, QuerySet

from allianceauth.authentication.models import UserProfile

from ledger.app_settings import STORAGE_BASE_KEY
from ledger.hooks import get_extension_logger
from ledger.models.events import Events

logger = get_extension_logger(__name__)


# pylint: disable=unused-argument
def add_info_to_context(request, context: dict) -> dict:
    """Add additional information to the context for the view."""
    theme = None
    try:
        user = UserProfile.objects.get(id=request.user.id)
        theme = user.theme
    except UserProfile.DoesNotExist:
        pass

    new_context = {
        **{"theme": theme},
        **context,
    }
    return new_context


def ledger_cache_timeout():
    """
    Calculate time left to next hour

    Example:
    1 Hour
        10:15 -> 45 minutes left
        10:45 -> 15 minutes left
    """
    now = datetime.now()
    delta = timedelta(minutes=60, hours=0, seconds=0)
    next_time = (now + delta).replace(minute=0, second=0, microsecond=0)
    timeout = next_time - now
    return timeout.total_seconds()


def calculate_ess_stolen_amount(bounty, ess):
    try:
        total_ess_gain = ess / bounty
        total_ess_gain = total_ess_gain * 100

        total_ess_gain_diff = Decimal(66.667) - int(total_ess_gain)

        stolen = ess * (total_ess_gain_diff / 100)
        # If the difference is less than 0.9 or negative, no ESS was stolen
        if abs(total_ess_gain_diff) < Decimal("0.9") or total_ess_gain_diff < 0:
            stolen = 0
    # pylint: disable=broad-except
    except Exception:
        stolen = 0
    return round(stolen)


def calculate_ess_stolen(amounts):
    try:
        amounts["stolen"]["total_amount"] = calculate_ess_stolen_amount(
            amounts["bounty"]["total_amount"], amounts["ess"]["total_amount"]
        )
        amounts["stolen"]["total_amount_day"] = calculate_ess_stolen_amount(
            amounts["bounty"]["total_amount_day"], amounts["ess"]["total_amount_day"]
        )
    except KeyError:
        pass
    return amounts


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
        timeout=time,
    )


def set_cache_hourly(data, key_name: str):
    """Reset hourly"""
    cache.set(
        key=_storage_key(key_name),
        value=data,
        timeout=ledger_cache_timeout(),
    )


def delete_cache(key_name: str):
    cache.delete(_storage_key(key_name))


def events_filter(entries) -> "QuerySet":
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
