"""
Core View Helper
"""

# Standard Library
from decimal import Decimal

# Django
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.models.general import EveEntity

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def add_info_to_context(request, context: dict) -> dict:
    """Add additional information to the context for the view."""
    # pylint: disable=import-outside-toplevel
    # AA Ledger
    from ledger.models.characteraudit import CharacterAudit

    total_issues = (
        CharacterAudit.objects.annotate_total_update_status_user(user=request.user)
        .aggregate(total_failed=Sum("num_sections_failed"))
        .get("total_failed", 0)
    )

    new_context = {
        **{
            "issues": total_issues,
        },
        **context,
    }
    return new_context


class DummyEveCharacter:
    """Dummy Eve Character class for fallback when no character is found."""

    def __init__(self, character_id, character_name="Unknown"):
        self.entity_id = character_id
        self.entity_name = character_name
        self.type = "character"


class LedgerEntity:
    """Class to hold character or corporation data for the ledger."""

    def __init__(self, entity_id, character_obj: EveCharacter = None, details_url=None):
        self.type = "character"
        self.entity = None
        self.entity_id = entity_id
        self.entity_name = None
        self.details_url = details_url
        if character_obj and hasattr(character_obj, "character_id"):
            self.entity = character_obj
            self.entity_id = character_obj.character_id
            self.entity_name = character_obj.character_name
        else:
            try:
                entity_obj = EveEntity.objects.get(eve_id=entity_id)
                self.entity = entity_obj
                self.entity_id = entity_obj.eve_id
                self.entity_name = entity_obj.name
                self.type = entity_obj.category
            except EveEntity.DoesNotExist:
                self.entity = DummyEveCharacter(entity_id, "Unknown")
                self.entity_id = entity_id
                self.entity_name = "Unknown"

    def portrait_url(self):
        """Return the portrait URL for the entity."""
        try:
            if hasattr(self.entity, "portrait_url"):
                return self.entity.portrait_url(size=32)
            if self.entity.category == "faction":
                return ""
            return self.entity.icon_url(size=32)
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting portrait URL for {self.entity_id}: {e}")
            return ""

    def add_details_url(self, details_url):
        """Set the details URL for the entity."""
        self.details_url = details_url

    def get_alts_ids_or_self(self):
        """Return the IDs of all alternative characters or the character ID itself."""
        try:
            character = EveCharacter.objects.get(character_id=self.entity_id)
            if hasattr(character, "character_ownership"):
                alt_ids = character.character_ownership.user.character_ownerships.all().values_list(
                    "character__character_id", flat=True
                )
                return list(alt_ids)
        except (
            EveCharacter.DoesNotExist,
            AttributeError,
            CharacterOwnership.DoesNotExist,
        ):
            pass
        return [self.entity_id]

    @property
    def create_button(self):
        """Generate the URL for character details."""
        title = _("View Details")
        button_html = f"<button class='btn btn-primary btn-sm btn-square' data-bs-toggle='modal' data-bs-target='#modalViewCharacterContainer' data-ajax_url='{self.details_url}' title='{title}' data-tooltip-toggle='ledger-tooltip'><span class='fas fa-info'></span></button>"
        return mark_safe(button_html)


class LedgerCore:
    """Core View Helper for Ledger."""

    def __init__(self, year=None, month=None, day=None):
        self.date_info = {"year": year, "month": month, "day": day}
        self.ledger_type = "ledger"

        # If all are None, default to 'month' view
        if year is None and month is None and day is None:
            self.view = "month"
        else:
            self.view = "day" if day else "month" if month else "year"

        self.journal = None
        self.mining = None
        self.billboard = BillboardSystem(self.view)

    @property
    def year(self):
        return self.date_info["year"]

    @property
    def month(self):
        return self.date_info["month"]

    @property
    def day(self):
        return self.date_info["day"]

    @property
    def filter_date(self):
        """
        Generate a date filter for the ledger based on year, month, and day.
        Returns:
            Q: A Django Q object representing the date filter.
        """
        now = timezone.now()
        # If all are None, use current year and month
        if self.year is None and self.month is None and self.day is None:
            filter_date = Q(date__year=now.year) & Q(date__month=now.month)
        else:
            filter_date = (
                Q(date__year=self.year) if self.year else Q(date__year=now.year)
            )
            if self.month:
                filter_date &= Q(date__month=self.month)
            if self.day:
                filter_date &= Q(date__day=self.day)
        return filter_date

    @property
    def get_details_title(self):
        """
        Generate a title for the details view based on the date information.

        Returns:
            str: A formatted string representing the date or a default title.
        """
        if self.year and self.month and self.day:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        if self.year and self.month:
            return f"{self.year:04d}-{self.month:02d}"
        if self.year:
            return f"{self.year:04d}"
        return "Character Ledger Details"

    def _calculate_totals(self, ledger) -> dict:
        """
        Calculate the total amounts for each category in the ledger.

        Args:
            ledger (list or dict): The ledger data to calculate totals from.

        Returns:
            dict: A dictionary containing the totals for each category.
        """
        totals = {
            "bounty": Decimal(0),
            "ess": Decimal(0),
            "costs": Decimal(0),
            "miscellaneous": Decimal(0),
            "total": Decimal(0),
        }

        if not ledger:
            return totals

        if isinstance(ledger, dict):
            ledger = [ledger]

        for total in ledger:

            if total is None:
                continue

            totals["bounty"] += total["ledger"]["bounty"]
            totals["ess"] += total["ledger"]["ess"]
            totals["costs"] += total["ledger"]["costs"]
            totals["miscellaneous"] += total["ledger"]["miscellaneous"]
            totals["total"] += total["ledger"]["total"]
        return totals

    def create_url(self, viewname: str, **kwargs):
        """
        Create a URL for the given view and entity using kwargs.
        Args:
            viewname: The name of the view to create the URL for.
            kwargs: All needed parameters for the URL (e.g. character_id, corporation_id, etc.)
        Returns:
            A URL string for the specified view.
        """
        if self.year and self.month and self.day:
            return reverse(
                f"ledger:{viewname}_year_month_day",
                kwargs={
                    **kwargs,
                    "year": self.year,
                    "month": self.month,
                    "day": self.day,
                },
            )
        if self.year and self.month:
            return reverse(
                f"ledger:{viewname}_year_month",
                kwargs={
                    **kwargs,
                    "year": self.year,
                    "month": self.month,
                },
            )
        if self.year:
            return reverse(
                f"ledger:{viewname}_year",
                kwargs={**kwargs, "year": self.year},
            )
        return reverse(
            f"ledger:{viewname}_year_month",
            kwargs={
                **kwargs,
                "year": timezone.now().year,
                "month": timezone.now().month,
            },
        )

    def create_view_data(self, viewname: str, **kwargs) -> dict:
        """
        Create view data for the ledger using kwargs.
        Args:
            viewname (str): The name of the view to create the URL for.
            kwargs: All needed parameters for the URL (e.g. character_id, corporation_id, etc.)
        Returns:
            dict: A dictionary containing the type, date, and details URL.
        """
        return {
            "type": self.ledger_type,
            "date": {
                "current": {
                    "year": timezone.now().year,
                    "month": timezone.now().month,
                    "day": timezone.now().day,
                },
                "year": self.year,
                "month": self.month,
                "day": self.day,
            },
            "details_url": self.create_url(
                viewname=viewname,
                **kwargs,
            ),
        }

    def _add_average_details(self, request, amounts, day: int = None):
        """Add average details to the amounts dictionary, skipping if no data or total is 0."""
        if amounts is None:
            return None

        avg = day if day else timezone.now().day
        if request.GET.get("all", False):
            avg = 365

        for key in amounts:
            if (
                isinstance(amounts[key], dict)
                and "total_amount" in amounts[key]
                and amounts[key]["total_amount"] not in (None, 0, 0.0, Decimal(0))
            ):
                total = amounts[key]["total_amount"]
                amounts[key]["average_day"] = total / avg
                amounts[key]["average_hour"] = total / avg / 24
                amounts[key]["average_tick"] = total / 20
                amounts[key]["current_day_tick"] = (
                    amounts[key].get("total_amount_day", 0) / 20
                )
                amounts[key]["average_day_tick"] = total / avg / 20
                amounts[key]["average_hour_tick"] = total / avg / 24 / 20
        return amounts
