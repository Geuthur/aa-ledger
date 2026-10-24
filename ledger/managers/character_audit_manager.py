# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models import Case, Count, Q, Value, When

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.models.general import General
from ledger.models.helpers.update_manager import CharacterUpdateSection, UpdateStatus
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.characteraudit import CharacterOwner as CharacterAuditContext


class CharacterAuditQuerySet(models.QuerySet["CharacterAuditContext"]):
    # pylint: disable=duplicate-code
    def visible_to(self, user: User):
        if General.has_perm(user, General.Permission.CHAR_AUDIT_ADMIN_MANAGER):
            logger.debug("Returning all characters for %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(eve_character__character_ownership__user=user)]

            if General.has_perm(user, General.Permission.CHAR_AUDIT_MANAGER):
                queries.append(
                    models.Q(eve_character__corporation_id=char.corporation_id)
                )

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

    def manage_to(self, user: User):
        """Return all characters that the user can manage."""
        if General.has_perm(user, General.Permission.CHAR_AUDIT_ADMIN_MANAGER):
            logger.debug("Returning all characters for Char Audit Admin %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = []

            if General.has_perm(user, General.Permission.CHAR_AUDIT_MANAGER):
                # If the user has char management access, return all chars for own Corp
                queries.append(
                    models.Q(eve_character__corporation_id=char.corporation_id)
                )

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

    def annotate_total_update_status_user(self, user):
        """Get the total update status for the given user."""
        char = user.profile.main_character
        assert char

        query = models.Q(eve_character__character_ownership__user=user)

        return self.filter(query).annotate_total_update_status()

    def annotate_total_update_status(self):
        """Get the total update status."""
        sections = CharacterUpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ledger_update_status",
                    filter=Q(ledger_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ledger_update_status",
                    filter=Q(
                        ledger_update_status__section__in=sections,
                        ledger_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ledger_update_status",
                    filter=Q(
                        ledger_update_status__section__in=sections,
                        ledger_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ledger_update_status",
                    filter=Q(
                        ledger_update_status__section__in=sections,
                        ledger_update_status__has_token_error=True,
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

    def disable_characters_with_no_owner(self) -> int:
        """Disable characters which have no owner. Return count of disabled characters."""
        orphaned_characters = self.filter(
            eve_character__character_ownership__isnull=True, active=True
        )
        if orphaned_characters.exists():
            orphans = list(
                orphaned_characters.values_list(
                    "eve_character__character_name", flat=True
                ).order_by("eve_character__character_name")
            )
            orphaned_characters.update(active=False)
            logger.info(
                "Disabled %d characters which do not belong to a user: %s",
                len(orphans),
                ", ".join(orphans),
            )
            return len(orphans)
        return 0

    def enable_characters_with_owner(self) -> int:
        """Enable disabled characters which have an owner again and a valid token.

        Return count of enabled characters.
        """
        candidates = self.filter(
            eve_character__character_ownership__isnull=False, active=False
        ).select_related("eve_character")
        candidate_ids = {c.eve_character.character_id for c in candidates}
        if not candidate_ids:
            return 0

        valid_ids = set(
            Token.objects.filter(character_id__in=candidate_ids)
            .require_scopes(self.model.get_esi_scopes())
            .require_valid()
            .values_list("character_id", flat=True)
        )
        to_enable = self.filter(eve_character__character_id__in=valid_ids, active=False)
        names = list(
            to_enable.values_list("eve_character__character_name", flat=True).order_by(
                "eve_character__character_name"
            )
        )
        if not names:
            return 0

        to_enable.update(active=True)
        logger.info(
            "Enabled %d characters which have an owner and a valid token again: %s",
            len(names),
            ", ".join(names),
        )
        return len(names)


class CharacterAuditManager(models.Manager["CharacterAuditContext"]):
    def get_queryset(self):
        return CharacterAuditQuerySet(self.model, using=self._db)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()

    def annotate_total_update_status_user(self, user):
        return self.get_queryset().annotate_total_update_status_user(user)

    def disable_characters_with_no_owner(self) -> int:
        return self.get_queryset().disable_characters_with_no_owner()

    def enable_characters_with_owner(self) -> int:
        return self.get_queryset().enable_characters_with_owner()

    @staticmethod
    def visible_eve_characters(user):
        qs = EveCharacter.objects.get_queryset()
        if General.has_perm(user, General.Permission.CHAR_AUDIT_ADMIN_MANAGER):
            logger.debug("Returning all characters for %s.", user)
            return qs.all()

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character_ownership__user=user)]

            if General.has_perm(user, General.Permission.CHAR_AUDIT_MANAGER):
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

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)
