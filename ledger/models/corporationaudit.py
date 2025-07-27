"""
Corporation Audit Model
"""

# Standard Library
from collections.abc import Callable

# Third Party
from bravado.exception import HTTPInternalServerError

# Django
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.models import Token

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.errors import HTTPGatewayTimeoutError, NotModifiedError
from ledger.managers.corporation_audit_manager import CorporationAuditManager
from ledger.managers.corporation_journal_manager import (
    CorporationDivisionManager,
    CorporationWalletManager,
)
from ledger.models.characteraudit import WalletJournalEntry
from ledger.models.general import UpdateSectionResult, UpdateStatus, _NeedsUpdate
from ledger.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationAudit(models.Model):

    class UpdateSection(models.TextChoices):
        WALLET_DIVISION_NAMES = "wallet_division_names", _("Divisions Names")
        WALLET_DIVISION = "wallet_division", _("Divisions")
        WALLET_JOURNAL = "wallet_journal", _("Wallet Journal")

        @classmethod
        def get_sections(cls) -> list[str]:
            """Return list of section values."""
            return [choice.value for choice in cls]

        @property
        def method_name(self) -> str:
            """Return method name for this section."""
            return f"update_{self.value}"

    corporation_name = models.CharField(max_length=100, null=True, default=None)

    active = models.BooleanField(default=True)

    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="ledger_corporationaudit",
    )

    objects = CorporationAuditManager()

    def __str__(self) -> str:
        try:
            return f"{self.corporation.corporation_name} ({self.id})"
        except AttributeError:
            return f"{self.corporation} ({self.id})"

    def update_wallet_division_names(self, force_refresh: bool) -> None:
        return self.ledger_corporation_division.update_or_create_esi_names(
            self, force_refresh=force_refresh
        )

    def update_wallet_division(self, force_refresh: bool) -> None:
        return self.ledger_corporation_division.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_wallet_journal(self, force_refresh: bool) -> None:
        return CorporationWalletJournalEntry.objects.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    # pylint: disable=duplicate-code
    def calc_update_needed(self) -> _NeedsUpdate:
        """Calculate if an update is needed."""
        sections_needs_update = {
            section: True for section in self.UpdateSection.get_sections()
        }
        existing_sections: models.QuerySet[CorporationUpdateStatus] = (
            self.ledger_corporation_update_status.all()
        )
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)

    # pylint: disable=duplicate-code
    def reset_update_status(self, section: UpdateSection) -> "CorporationUpdateStatus":
        """Reset the status of a given update section and return it."""
        update_status_obj: CorporationUpdateStatus = (
            self.ledger_corporation_update_status.get_or_create(
                section=section,
            )[0]
        )
        update_status_obj.reset()
        return update_status_obj

    # pylint: disable=duplicate-code
    def reset_has_token_error(self) -> None:
        """Reset the has_token_error flag for this corporation."""
        self.ledger_corporation_update_status.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    # pylint: disable=duplicate-code
    def update_section_if_changed(
        self,
        section: UpdateSection,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            data = fetch_func(corporation=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPInternalServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except NotModifiedError:
            logger.debug("%s: Update has not changed, section: %s", self, section.label)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPGatewayTimeoutError as exc:
            logger.debug(
                "%s: Update has a gateway timeout error, section: %s: %s",
                self,
                section.label,
                exc,
            )
            return UpdateSectionResult(is_changed=False, is_updated=False)
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    # pylint: disable=duplicate-code
    def update_section_log(
        self,
        section: UpdateSection,
        is_success: bool,
        is_updated: bool = False,
        error_message: str = None,
    ) -> None:
        """Update the status of a specific section."""
        error_message = error_message if error_message else ""
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": False,
            "last_run_finished_at": timezone.now(),
        }
        obj: CorporationUpdateStatus = (
            self.ledger_corporation_update_status.update_or_create(
                section=section,
                defaults=defaults,
            )[0]
        )
        if is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    # pylint: disable=duplicate-code
    def perform_update_status(
        self, section: UpdateSection, method: Callable, *args, **kwargs
    ) -> UpdateSectionResult:
        """Perform update status."""
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            # TODO ADD DISCORD NOTIFICATION?
            error_message = f"{type(exc).__name__}: {str(exc)}"
            is_token_error = isinstance(exc, (TokenError))
            logger.error(
                "%s: %s: Error during update status: %s",
                self,
                section.label,
                error_message,
                exc_info=not is_token_error,  # do not log token errors
            )
            self.ledger_corporation_update_status.update_or_create(
                section=section,
                defaults={
                    "is_success": False,
                    "error_message": error_message,
                    "has_token_error": is_token_error,
                    "last_update_at": timezone.now(),
                },
            )
            raise exc
        return result

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            # General
            "esi-search.search_structures.v1",
            "esi-universe.read_structures.v1",
            "esi-characters.read_corporation_roles.v1",
            # Mining
            "esi-industry.read_corporation_mining.v1",
            # wallets
            "esi-wallet.read_corporation_wallets.v1",
            "esi-markets.read_corporation_orders.v1",
            "esi-industry.read_corporation_jobs.v1",
            "esi-corporations.read_divisions.v1",
        ]

    def get_token(self, scopes, req_roles) -> Token:
        """Get the token for this corporation."""
        if "esi-characters.read_corporation_roles.v1" not in scopes:
            scopes.append("esi-characters.read_corporation_roles.v1")

        char_ids = EveCharacter.objects.filter(
            corporation_id=self.corporation.corporation_id
        ).values("character_id")

        tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

        for token in tokens:
            try:
                roles = esi.client.Character.get_characters_character_id_roles(
                    character_id=token.character_id, token=token.valid_access_token()
                ).result()

                has_roles = False
                for role in roles.get("roles", []):
                    if role in req_roles:
                        has_roles = True

                if has_roles:
                    return token
            except TokenError as e:
                logger.error(
                    "Token ID: %s (%s)",
                    token.pk,
                    e,
                )
        return False

    class Meta:
        default_permissions = ()
        permissions = (
            ("corp_audit_manager", "Has Access to own Corporations."),
            ("corp_audit_admin_manager", "Has access to all Corporations."),
        )


class CorporationWalletDivision(models.Model):
    objects = CorporationDivisionManager()

    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_division",
    )
    name = models.CharField(max_length=100, null=True, default=None)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    division_id = models.IntegerField()

    class Meta:
        default_permissions = ()


class CorporationWalletJournalEntry(WalletJournalEntry):
    division = models.ForeignKey(
        CorporationWalletDivision,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_journal",
    )

    objects = CorporationWalletManager()

    def __str__(self):
        return f"Corporation Wallet Journal: RefType: {self.ref_type} - {self.first_party.name} -> {self.second_party.name}: {self.amount} ISK"

    @classmethod
    def get_visible(cls, user):
        corps_vis = CorporationAudit.objects.visible_to(user)
        return cls.objects.filter(division__corporation__in=corps_vis)


class CorporationUpdateStatus(UpdateStatus):
    """A Model to track the status of the last update."""

    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_update_status",
    )
    section = models.CharField(
        max_length=32, choices=CorporationAudit.UpdateSection.choices, db_index=True
    )

    def __str__(self) -> str:
        return f"{self.corporation} - {self.section} - {self.is_success}"
