# Django
from django.utils import timezone

# AA Ledger
from ledger.models.events import Events


def create_event(char_ledger: bool, **kwargs) -> Events:
    """Create a Event for a Corporation"""
    params = {
        "char_ledger": char_ledger,
    }
    params.update(kwargs)
    events = Events(**params)
    events.save()
    return events


def create_event_1_day(
    char_ledger: bool, date_start: timezone.datetime, **kwargs
) -> Events:
    """Create a Event for a Corporation"""
    params = {
        "char_ledger": char_ledger,
        "date_start": date_start,
        "date_end": date_start + timezone.timedelta(days=1),
    }
    params.update(kwargs)
    events = Events(**params)
    events.save()
    return events
