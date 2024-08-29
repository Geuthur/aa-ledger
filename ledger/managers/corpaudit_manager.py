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
            queries = [models.Q(corporation__corporation_id=char.corporation_id)]

            if user.has_perm("ledger.corp_audit_manager"):
                queries.append(
                    models.Q(corporation__corporation_id=char.corporation_id)
                )

            logger.debug(
                "%s queries for user %s visible corporations.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class CorpAuditManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


CorpAuditManager = CorpAuditManagerBase.from_queryset(CorpAuditQuerySet)
