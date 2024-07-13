from django.db import models
from django.db.models import ExpressionWrapper, F

from allianceauth.eveonline.models import EveCharacter

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class AuditCharacterQuerySet(models.QuerySet):
    # pylint: disable=duplicate-code
    def visible_to(self, user):
        # superusers get all visible
        if user.is_superuser:
            logger.debug("Returning all characters for superuser %s.", user)
            return self

        if user.has_perm("ledger.char_audit_admin_manager"):
            logger.debug("Returning all characters for %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if user.has_perm("ledger.char_audit_manager"):
                queries.append(models.Q(character__corporation_id=char.corporation_id))

            logger.debug(
                "%s queries for user %s visible chracters.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class AuditCharacterManager(models.Manager):
    def get_queryset(self):
        return AuditCharacterQuerySet(self.model, using=self._db)

    @staticmethod
    def visible_eve_characters(user):
        qs = EveCharacter.objects.get_queryset()
        if user.is_superuser:
            logger.debug("Returning all characters for superuser %s.", user)
            return qs.all()

        if user.has_perm("ledger.char_audit_admin_manager"):
            logger.debug("Returning all characters for %s.", user)
            return qs.all()

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character_ownership__user=user)]

            if user.has_perm("ledger.char_audit_manager"):
                queries.append(models.Q(corporation_id=char.corporation_id))

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


class CharacterMiningLedgerEntryQueryset(models.QuerySet):
    def annotate_pricing(self) -> models.QuerySet:
        """Annotate price and total columns."""
        return (
            self.select_related("type__market_price")
            .annotate(price=F("type__market_price__average_price"))
            .annotate(
                total=ExpressionWrapper(
                    F("type__market_price__average_price") * F("quantity"),
                    output_field=models.FloatField(),
                ),
            )
        )


class CharacterMiningLedgerEntryManagerBase(models.Manager):
    pass


CharacterMiningLedgerEntryManager = CharacterMiningLedgerEntryManagerBase.from_queryset(
    CharacterMiningLedgerEntryQueryset
)
