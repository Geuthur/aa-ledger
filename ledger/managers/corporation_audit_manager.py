# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models import Case, Count, Q, Value, When

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.models.helpers.update_manager import CorporationUpdateSection, UpdateStatus
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.corporationaudit import CorporationOwner


class CorporationAuditQuerySet(models.QuerySet["CorporationOwner"]):
    def visible_to(self, user: User):
        """Returns a queryset of all corps visible to the user."""
        if user.is_superuser:
            logger.debug(
                "Returning all corps for superuser %s.",
                user,
            )
            return self

        if user.has_perm("ledger.corp_audit_admin_manager"):
            logger.debug("Returning all corps for Corp Audit Admin %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = []

            if user.has_perm("ledger.advanced_access"):
                # If the user has advanced access, return all corps from their characters
                corp_ids = char.character_ownership.user.character_ownerships.all().values_list(
                    "character__corporation_id", flat=True
                )
                queries.append(models.Q(eve_corporation__corporation_id__in=corp_ids))

            logger.debug("%s queries for User %s.", len(queries), user)

            if len(queries) == 0:
                return self.none()

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user: User):
        """Return all corps that the user can manage."""
        if user.is_superuser:
            logger.debug(
                "Returning all corps for superuser %s.",
                user,
            )
            return self

        if user.has_perm("ledger.corp_audit_admin_manager"):
            logger.debug("Returning all corps for Corp Audit Admin %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = []

            if user.has_perm("ledger.corp_audit_manager"):
                # If the user has corp management access, return all corps from their characters
                corp_ids = char.character_ownership.user.character_ownerships.all().values_list(
                    "character__corporation_id", flat=True
                )
                queries.append(models.Q(eve_corporation__corporation_id__in=corp_ids))

            logger.debug("%s queries for User %s.", len(queries), user)

            if len(queries) == 0:
                return self.none()

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def annotate_total_update_status_user(self, user: User):
        """Get the total update status for the given user."""
        # TODO: implement this method if needed
        return user

    def annotate_total_update_status(self):
        """Get the total update status."""
        sections = CorporationUpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ledger_corporation_update_status",
                    filter=Q(ledger_corporation_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ledger_corporation_update_status",
                    filter=Q(
                        ledger_corporation_update_status__section__in=sections,
                        ledger_corporation_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ledger_corporation_update_status",
                    filter=Q(
                        ledger_corporation_update_status__section__in=sections,
                        ledger_corporation_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ledger_corporation_update_status",
                    filter=Q(
                        ledger_corporation_update_status__section__in=sections,
                        ledger_corporation_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class CorporationAuditManager(models.Manager["CorporationOwner"]):
    def get_queryset(self) -> CorporationAuditQuerySet:
        return CorporationAuditQuerySet(self.model, using=self._db)

    def annotate_total_update_status_user(self, user: User):
        return self.get_queryset().annotate_total_update_status_user(user)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)
