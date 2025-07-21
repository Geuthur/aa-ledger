# Django
from django.db import models

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationAuditQuerySet(models.QuerySet):
    def visible_to(self, user):
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
                queries.append(models.Q(corporation__corporation_id__in=corp_ids))

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

    def manage_to(self, user):
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
                queries.append(models.Q(corporation__corporation_id__in=corp_ids))

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


class CorporationAuditManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


CorporationAuditManager = CorporationAuditManagerBase.from_queryset(
    CorporationAuditQuerySet
)
