from django.db import models

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class CorpAuditQuerySet(models.QuerySet):
    def visible_to(self, user):
        # superusers get all visible
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
            query = None

            if user.has_perm("ledger.advanced_access"):
                query = models.Q(corporation__corporation_id=char.corporation_id)

            logger.debug("Returning own corps for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class CorpAuditManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


CorpAuditManager = CorpAuditManagerBase.from_queryset(CorpAuditQuerySet)
