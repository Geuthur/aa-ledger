"""
Core View Helper
"""

# Standard Library
import logging
from decimal import Decimal
from typing import Any, NamedTuple

# Django
from django.core.cache import cache
from django.db.models import Q, QuerySet

# Alliance Auth
from allianceauth.authentication.models import UserProfile

# AA Ledger
from ledger.app_settings import STORAGE_BASE_KEY
from ledger.models.events import Events

logger = logging.getLogger(__name__)


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


def delete_cache(key_name: str):
    cache.delete(_storage_key(key_name))


def events_filter(qs: QuerySet) -> QuerySet:
    """Remove Entries that are in the Event Time"""
    # Events to Filter out
    events = Events.objects.all()

    q_objects = []

    # Durchlaufen Sie jedes Event und erstellen Sie das entsprechende Q-Objekt für den Datumsbereich
    for event in events:
        if not event.char_ledger:
            continue
        q_objects.append(Q(date__range=(event.date_start, event.date_end)))

    # Combine all Q-Objects
    if q_objects:
        combined_q_object = q_objects[0]
        for q_object in q_objects[1:]:
            combined_q_object |= q_object
        # Exclude all Entries that are in the Event Time
        qs = qs.exclude(combined_q_object & Q(ref_type="ess_escrow_transfer"))
    return qs


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
    data: Any = None
