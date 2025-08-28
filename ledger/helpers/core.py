"""
Core View Helper
"""

# Standard Library
from decimal import Decimal
from hashlib import md5

# Django
from django.db.models import Q, QuerySet, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership, UserProfile
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.app_settings import LEDGER_CACHE_KEY
from ledger.helpers.ref_type import RefTypeManager
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


class DummyEveEntity:
    """Dummy Eve Entity class for fallback when no entity is found."""

    def __init__(self, entity_id, entity_name="Unknown"):
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.type = "character"


class LedgerEntity:
    """Class to hold character or corporation data for the ledger."""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        entity_id,
        character_obj: EveCharacter = None,
        corporation_obj: EveCorporationInfo = None,
        alliance_obj: EveAllianceInfo = None,
        details_url=None,
    ):
        self.type = "character"
        self.entity = None
        self.entity_id = entity_id
        self.entity_name = None
        self.details_url = details_url
        if character_obj and hasattr(character_obj, "character_id"):
            self.entity = character_obj
            self.entity_id = character_obj.character_id
            self.entity_name = character_obj.character_name
        elif corporation_obj and hasattr(corporation_obj, "corporation_id"):
            self.entity = corporation_obj
            self.entity_id = corporation_obj.corporation_id
            self.entity_name = corporation_obj.corporation_name
            self.type = "corporation"
        elif alliance_obj and hasattr(alliance_obj, "alliance_id"):
            self.entity = alliance_obj
            self.entity_id = alliance_obj.alliance_id
            self.entity_name = alliance_obj.alliance_name
            self.type = "alliance"
        else:
            try:
                entity_obj = EveEntity.objects.get(eve_id=entity_id)
                self.entity = entity_obj
                self.entity_id = entity_obj.eve_id
                self.entity_name = entity_obj.name
                self.type = entity_obj.category
            except EveEntity.DoesNotExist:
                self.entity = DummyEveEntity(entity_id, "Unknown")
                self.entity_id = entity_id
                self.entity_name = "Unknown"

    @property
    def is_eve_character(self):
        """Check if the entity is an Eve Character."""
        return isinstance(self.entity, EveCharacter)

    @property
    def is_eve_corporation(self):
        """Check if the entity is an Eve Corporation."""
        return isinstance(self.entity, EveCorporationInfo)

    @property
    def is_eve_entity(self):
        """Check if the entity is an Eve Entity."""
        return isinstance(self.entity, EveEntity)

    @property
    def alts(self) -> QuerySet[EveCharacter]:
        """Get all alts for this character."""
        if not isinstance(self.entity, EveCharacter):
            raise ValueError("Entity is not an EveCharacter.")
        alts = EveCharacter.objects.filter(
            character_ownership__user=self.entity.character_ownership.user
        ).select_related(
            "character_ownership",
        )
        return alts

    def portrait_url(self):
        """Return the portrait URL for the entity."""
        try:
            if isinstance(self.entity, EveCorporationInfo):
                return self.entity.logo_url_32

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

    @property
    def auth_accounts(self):
        """Get all user accounts with a main character."""
        return (
            UserProfile.objects.filter(
                main_character__isnull=False,
            )
            .prefetch_related(
                "user__profile__main_character",
            )
            .order_by(
                "user__profile__main_character__character_name",
            )
        )

    @property
    def auth_character_ids(self) -> set:
        """Get all account Character IDs from Alliance Auth."""
        account_character_ids = set()
        for account in self.auth_accounts:
            alts = account.user.character_ownerships.all()
            account_character_ids.update(
                alts.values_list("character__character_id", flat=True)
            )
        return account_character_ids

    def _get_ledger_journal_hash(self, journal: list[str]) -> str:
        """Generate a hash for the ledger journal."""
        return md5(",".join(str(x) for x in sorted(journal)).encode()).hexdigest()

    def _get_ledger_hash(self, header_key: str) -> str:
        """Generate a hash for the ledger journal."""
        return md5(header_key.encode()).hexdigest()

    def _get_ledger_header(
        self, entity_id: int, year: int, month: int, day: int
    ) -> str:
        """Generate a header string for the ledger."""
        return f"{entity_id}_{year}_{month}_{day}"

    def _build_ledger_cache_key(self, header_key: str) -> str:
        """Build a cache key for the ledger."""
        return f"{LEDGER_CACHE_KEY}-{self._get_ledger_hash(header_key)}"

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
            "mining": Decimal(0),
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

            totals["bounty"] += total["ledger"].get("bounty", 0)
            totals["ess"] += total["ledger"].get("ess", 0)
            totals["costs"] += total["ledger"].get("costs", 0)
            totals["mining"] += total["ledger"].get("mining", 0)
            totals["miscellaneous"] += total["ledger"].get("miscellaneous", 0)
            totals["total"] += total["ledger"].get("total", 0)
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

    # pylint: disable=too-many-locals
    def _generate_amounts(
        self,
        income_types: list,
        entity: LedgerEntity,
        is_old_ess: bool = False,
        char_ids: list = None,
    ) -> dict:
        """Generate amounts for the entity based on income types and reference types."""
        amounts = {}

        ref_types = RefTypeManager.get_all_categories()

        # Bounty Income
        if not entity.entity_id == 1000125:  # Remove Concord Bountys
            bounty_income = self.journal.aggregate_bounty()
            if bounty_income > 0:
                amounts["bounty_income"] = {
                    "total_amount": bounty_income,
                    "ref_types": ["bounty_prizes"],
                }

        if isinstance(entity.entity, EveCharacter):
            # Mining Income
            mining_income = self.mining.aggregate_mining()
            if mining_income > 0:
                amounts["mining_income"] = {
                    "total_amount": mining_income,
                    "ref_types": ["mining"],
                }

        # ESS Income (nur wenn bounty_income existiert)
        ess_income = (
            bounty_income * Decimal(0.667)
            if is_old_ess and bounty_income
            else self.journal.aggregate_ess()
        )
        if ess_income > 0:
            amounts["ess_income"] = {
                "total_amount": ess_income,
                "ref_types": ["ess_escrow_transfer"],
            }

        # Income/Cost Ref Types (DRY)
        for ref_type, value in ref_types.items():
            ref_type_name = ref_type.lower()
            for kind, income_flag in (("income", True), ("cost", False)):
                kwargs = {"ref_type": value, "income": income_flag}
                kwargs = RefTypeManager.special_cases_details(
                    value, entity, kwargs, journal_type=entity.type, char_ids=char_ids
                )
                agg = self.journal.aggregate_ref_type(**kwargs)
                if (income_flag and agg > 0) or (not income_flag and agg < 0):
                    amounts[f"{ref_type_name}_{kind}"] = {
                        "total_amount": agg,
                        "ref_types": value,
                    }

        # Summary (exclude mining_income)
        summary = sum(
            amount["total_amount"]
            for key, amount in amounts.items()
            if key != "mining_income"
            and isinstance(amount, dict)
            and "total_amount" in amount
        )

        if summary == 0:
            return None

        amounts["summary"] = {
            "total_amount": summary,
        }

        # Dynamische Income/Cost-Typen für das Template
        income_types += [
            (f"{ref_type.lower()}_income", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types
        ]
        cost_types = [
            (f"{ref_type.lower()}_cost", _(ref_type.replace("_", " ").title()))
            for ref_type in ref_types
        ]
        amounts["income_types"] = income_types
        amounts["cost_types"] = cost_types
        return amounts

    def _create_corporation_details(self, entity: LedgerEntity) -> dict:
        """Create the corporation amounts for the Information View."""
        # NOTE (can only used if setup_ledger is defined in the subclass)
        self.setup_ledger(entity=entity)  # pylint: disable=no-member

        income_types = [
            ("bounty_income", _("Bounty")),
            ("ess_income", _("Encounter Surveillance System")),
        ]
        amounts = self._generate_amounts(income_types=income_types, entity=entity)
        return amounts

    # pylint: disable=no-member
    def _create_character_details(self) -> dict:
        """
        Create the character amounts for the Information View.
        Only work with CharacterData Class
        """
        if not self.character:
            raise ValueError("No Character Data found.")

        # NOTE (can only used if setup_ledger is defined in the subclass)
        self.setup_ledger(self.character)

        entity = LedgerEntity(
            entity_id=self.character.eve_character.character_id,
            character_obj=self.character.eve_character,
        )

        income_types = [
            ("bounty_income", _("Bounty")),
            ("ess_income", _("Encounter Surveillance System")),
            ("mining_income", _("Mining")),
        ]
        amounts = self._generate_amounts(
            income_types=income_types,
            entity=entity,
            is_old_ess=self.is_old_ess,
            char_ids=self.alts_ids,
        )
        return amounts

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

    def _build_xy_chart(self, title: str):
        """Build the XY chart for the billboard."""
        if not self.billboard.results:
            return

        xy_data, categories = self.billboard.generate_xy_series()
        self.billboard.create_xy_chart(
            title=title,
            categories=categories,
            series=xy_data,
        )
