from django.db import models

from allianceauth.eveonline.models import EveCorporationInfo

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
            logger.debug("Returning all corps for Corp Audit Admin %s.", user)
            return self

        if user.has_perm("ledger.admin_access"):
            logger.debug("Returning all corps for Admin Access %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            if user.has_perm("ledger.corp_audit_manager"):
                query = models.Q(corporation__corporation_id=char.corporation_id)
            else:
                logger.debug("User %s has no permission. Nothing visible.", user)
                return self.none()
            logger.debug(
                "Returning own corp for Corp Audit Manager %s.",
                user,
            )
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class CorpAuditManager(models.Manager):
    def get_queryset(self):
        return CorpAuditQuerySet(self.model, using=self._db)

    @staticmethod
    def visible_eve_corporations(user):
        qs = EveCorporationInfo.objects.get_queryset()
        if user.is_superuser:
            logger.debug("Returning all corporations for superuser %s.", user)
            return qs.all()

        if user.has_perm("ledger.corp_audit_admin_access"):
            logger.debug("Returning all corporations for %s.", user)
            return qs.all()

        if user.has_perm("ledger.admin_access"):
            logger.debug("Returning all corporations for %s.", user)
            return qs.all()

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(corporation__corporation_id=char.corporation_id)]

            if user.has_perm("ledger.corp_audit_manager"):
                queries.append = models.Q(
                    corporation__corporation_id=char.corporation_id
                )

            logger.debug(
                "%s queries for user %s visible chracters.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return qs.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return qs.none()

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)
