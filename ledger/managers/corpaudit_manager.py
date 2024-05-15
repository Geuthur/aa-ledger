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

        if user.has_perm("ledger.corp_audit_admin_access"):
            logger.debug("Returning all corps for %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = []
            if user.has_perm("ledger.corp_audit_manager"):
                queries.append(
                    models.Q(corporation__corporation_id=char.corporation_id)
                )
            logger.debug(
                "%s queries for user %s visible chracters.",
                len(queries),
                user,
            )
            if len(queries) == 0:
                return self.none()

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class CorpAuditManager(models.Manager):
    def get_queryset(self):
        return CorpAuditQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)
