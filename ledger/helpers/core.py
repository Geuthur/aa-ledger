"""
Core View Helper
"""

# Django
from django.db.models import Q, QuerySet

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.models.events import Events

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def add_info_to_context(request, context: dict) -> dict:
    """Add additional information to the context for the view."""
    # pylint: disable=import-outside-toplevel
    # AA Ledger
    from ledger.models.characteraudit import CharacterAudit

    theme = None
    try:
        user = UserProfile.objects.get(id=request.user.id)
        theme = user.theme
    except UserProfile.DoesNotExist:
        pass

    issues = CharacterAudit.objects.get_update_status_issues(user=request.user)

    new_context = {
        **{
            "theme": theme,
            "issues": issues,
        },
        **context,
    }
    return new_context


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
