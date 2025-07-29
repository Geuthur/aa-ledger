# Standard Library
import calendar

# Django
from django.template.defaultfilters import register
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, __version__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@register.filter
def range_filter(value):
    return range(1, value + 1)


@register.filter
def month_name(month):
    """Returns the month name for a given month number (1-12), übersetzbar."""
    months = [
        _("January"),
        _("February"),
        _("March"),
        _("April"),
        _("May"),
        _("June"),
        _("July"),
        _("August"),
        _("September"),
        _("October"),
        _("November"),
        _("December"),
    ]
    try:
        if 1 <= month <= 12:
            return months[month - 1]
    except (IndexError, ValueError, TypeError):
        pass
    return ""


@register.simple_tag
def month_days(date_info):
    """Returns the number of days in a given month, fallback to current if missing."""
    # Versuche, year und month aus dem Argument zu holen (dict oder Objekt)
    year = (
        getattr(date_info, "year", None) or date_info.get("year")
        if hasattr(date_info, "get")
        else None
    )
    month = (
        getattr(date_info, "month", None) or date_info.get("month")
        if hasattr(date_info, "get")
        else None
    )

    # Fallback auf aktuelles Datum, falls None
    now = timezone.now()
    year = year or now.year
    month = month or now.month

    try:
        return list(range(1, calendar.monthrange(int(year), int(month))[1] + 1))
    except Exception:  # pylint: disable=broad-except
        return []


@register.filter
def get_item(dictionary, key):
    """Returns the value for a given key in a dictionary, or empty dict if not found."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}
