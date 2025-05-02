# Standard Library
import logging
from collections import defaultdict

# Django
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

logger = logging.getLogger(__name__)


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
        return self.annotate(price=F("type__market_price__average_price")).annotate(
            total=ExpressionWrapper(
                F("type__market_price__average_price") * F("quantity"),
                output_field=models.DecimalField(),
            ),
        )

    def annotate_mining(self) -> models.QuerySet:
        """Annotate mining columns."""
        return (
            self.annotate_pricing()
            .values(
                "character__character__character_id",
                "character__character__character_name",
            )
            .annotate(
                total_amount=Round(
                    Coalesce(
                        Sum(F("total")),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                    precision=2,
                )
            )
        )

    def aggregate_amounts_information_modal(
        self, amounts: defaultdict, chars_list: list, filter_date: timezone.datetime
    ) -> dict:
        """Generate data template for the ledger character information view."""
        qs = self.filter(Q(character__character__character_id__in=chars_list))
        qs = qs.annotate_pricing()
        qs = qs.aggregate(
            total_amount=Round(
                Coalesce(
                    Sum(F("total"), filter=Q(date__year=filter_date.year)),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            ),
            total_amount_day=Round(
                Coalesce(
                    Sum(F("total"), filter=Q(date__day=filter_date.day)),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            ),
        )

        amounts["mining"]["total_amount"] = qs["total_amount"]
        amounts["mining"]["total_amount_day"] = qs["total_amount_day"]

        return amounts

    def annotate_billboard(self, chars_list: list) -> models.QuerySet:
        """Annotate billboard columns."""
        qs = self.filter(Q(character__character__character_id__in=chars_list))
        return qs.annotate(
            total_amount=Round(
                Coalesce(
                    Sum(F("total")),
                    Value(0),
                    output_field=DecimalField(),
                ),
                precision=2,
            )
        )


class CharacterMiningLedgerEntryManagerBase(models.Manager):
    pass


CharacterMiningLedgerEntryManager = CharacterMiningLedgerEntryManagerBase.from_queryset(
    CharacterMiningLedgerEntryQueryset
)
