"""
Core View Helper
"""

# Django
from django.db.models import Sum

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def add_info_to_context(request, context: dict) -> dict:
    """Add additional information to the context for the view."""
    # pylint: disable=import-outside-toplevel
    # AA Ledger
    from ledger.models.characteraudit import CharacterAudit

    try:
        user = UserProfile.objects.get(id=request.user.id)
        theme = user.theme
    except UserProfile.DoesNotExist:
        theme = None

    total_issues = (
        CharacterAudit.objects.annotate_total_update_status_user(user=request.user)
        .aggregate(total_failed=Sum("num_sections_failed"))
        .get("total_failed", 0)
    )

    new_context = {
        **{
            "theme": theme,
            "issues": total_issues,
        },
        **context,
    }
    return new_context
