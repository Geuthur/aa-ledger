"""
Character Audit Model
"""

# Standard Library
import logging
from collections.abc import Callable

# Third Party
from bravado.exception import HTTPInternalServerError

# Django
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, Token
from esi.errors import TokenError

# Alliance Auth (External Libs)
from eveuniverse.models import EveSolarSystem, EveType

# AA Ledger
from ledger import app_settings
from ledger.errors import HTTPGatewayTimeoutError, NotModifiedError, TokenDoesNotExist
from ledger.managers.character_audit_manager import (
    CharacterAuditManager,
)
from ledger.managers.character_journal_manager import CharWalletManager
from ledger.managers.character_mining_manager import CharacterMiningLedgerEntryManager
from ledger.models.general import EveEntity, UpdateSectionResult

logger = logging.getLogger(__name__)


class CharacterAudit(models.Model):

    class UpdateSection(models.TextChoices):
        WALLET_JOURNAL = "wallet_journal", _("Wallet Journal")
        MINING_LEDGER = "mining_ledger", _("Mining Ledger")
        PLANETS = "planets", _("Planets")
        PLANETS_DETAILS = "planets_details", _("Planets Details")

        @classmethod
        def get_sections(cls) -> list[str]:
            """Return list of section values."""
            return [choice.value for choice in cls]

        @property
        def method_name(self) -> str:
            """Return method name for this section."""
            return f"update_{self.value}"

    class UpdateStatus(models.TextChoices):
        DISABLED = "disabled", _("disabled")
        NOT_UP_TO_DATE = "not_up_to_date", _("not up to date")
        ERROR = "error", _("error")
        OK = "ok", _("ok")

        def bootstrap_icon(self) -> str:
            """Return bootstrap corresponding icon class."""
            update_map = {
                self.DISABLED: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>"
                ),
                self.NOT_UP_TO_DATE: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>"
                ),
                self.ERROR: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>"
                ),
                self.OK: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>"
                ),
            }
            return update_map.get(self, "")

        def bootstrap_text_style_class(self) -> str:
            """Return bootstrap corresponding bootstrap text style class."""
            update_map = {
                self.DISABLED: "text-warning",
                self.NOT_UP_TO_DATE: "text-warning",
                self.ERROR: "text-danger",
                self.OK: "text-success",
            }
            return update_map.get(self, "")

        def description(self) -> str:
            """Return description for an enum object."""
            update_map = {
                self.DISABLED: _("Update is disabled"),
                self.NOT_UP_TO_DATE: _(
                    "One of the updates is older than {} day"
                ).format(app_settings.LEDGER_CHAR_MAX_INACTIVE_DAYS),
                self.ERROR: _("An error occurred during update"),
                self.OK: _("Updates completed successfully"),
            }
            return update_map.get(self, "")

    id = models.AutoField(primary_key=True)

    character_name = models.CharField(max_length=100, null=True, default=None)

    character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="ledger_character"
    )

    active = models.BooleanField(default=True)

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    objects = CharacterAuditManager()

    def __str__(self) -> str:
        try:
            return f"{self.character.character_name} ({self.id})"
        except AttributeError:
            return f"{self.character_name} ({self.id})"

    class Meta:
        default_permissions = ()
        permissions = (
            ("char_audit_manager", "Has access to all characters for own Corp"),
            ("char_audit_admin_manager", "Has access to all characters"),
        )

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            # Mining Ledger
            "esi-industry.read_character_mining.v1",
            # Wallet / Market /  Contracts
            "esi-wallet.read_character_wallet.v1",
            "esi-contracts.read_character_contracts.v1",
            # Planetary Interaction
            "esi-planets.manage_planets.v1",
        ]

    @property
    def get_status(self) -> UpdateStatus:
        """Get the status of this character."""
        if not self.active:
            return self.UpdateStatus.DISABLED
        if not self.ledger_update_status.exists():
            return self.UpdateStatus.DISABLED
        if self.ledger_update_status.filter(
            is_success=False, has_token_error=True
        ).exists():
            return self.UpdateStatus.ERROR
        if self.ledger_update_status.filter(
            is_success=False, has_token_error=False
        ).exists():
            return self.UpdateStatus.ERROR
        # if self.calc_update_needed():
        #    return self.UpdateStatus.NOT_UP_TO_DATE
        return self.UpdateStatus.OK

    def get_token(self, scopes=None) -> Token:
        """Get the token for this character."""
        token = (
            Token.objects.filter(character_id=self.character.character_id)
            .require_scopes(scopes if scopes else self.get_esi_scopes())
            .require_valid()
            .first()
        )
        if not token:
            # TODO add Discord Notification?
            raise TokenDoesNotExist(
                f"Token does not exist for {self} with scopes {scopes}"
            )
        return token

    def update_wallet_journal(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_journal.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_mining_ledger(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_mining.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_planets(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_planet.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_planets_details(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_planet_details.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def calc_update_needed(self) -> list[UpdateSection]:
        """Calculate if an update is needed."""
        sections: models.QuerySet[CharacterUpdateStatus] = (
            self.ledger_update_status.all()
        )
        needs_update = []
        for section in sections:
            if section.need_update():
                needs_update.append(section.section)
        return needs_update

    def reset_update_status(self, section: UpdateSection) -> "CharacterUpdateStatus":
        """Reset the status of a given update section and return it."""
        update_status_obj: CharacterUpdateStatus = (
            self.ledger_update_status.get_or_create(
                section=section,
            )[0]
        )
        update_status_obj.reset()
        return update_status_obj

    def reset_has_token_error(self) -> None:
        """Reset the has_token_error flag for this character."""
        self.ledger_update_status.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    def update_section_if_changed(
        self,
        section: UpdateSection,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            logger.debug("%s: Update has changed, section: %s", self, section.label)
            data = fetch_func(character=self, force_refresh=force_refresh)
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
        obj: CharacterUpdateStatus = self.ledger_update_status.update_or_create(
            section=section,
            defaults=defaults,
        )[0]
        if is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    def perform_update_status(
        self, section: UpdateSection, method: Callable, *args, **kwargs
    ) -> UpdateSectionResult:
        """Perform update status."""
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            is_token_error = isinstance(exc, (TokenError))
            logger.error(
                "%s: %s: Error during update status: %s",
                self,
                section.label,
                error_message,
                exc_info=not is_token_error,  # do not log token errors
            )
            self.ledger_update_status.update_or_create(
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


class WalletJournalEntry(models.Model):
    amount = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )
    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )
    context_id = models.BigIntegerField(null=True, default=None)

    class ContextType(models.TextChoices):
        STRUCTURE_ID = "structure_id"
        STATION_ID = "station_id"
        MARKET_TRANSACTION_ID = "market_transaction_id"
        CHARACTER_ID = "character_id"
        CORPORATION_ID = "corporation_id"
        ALLIANCE_ID = "alliance_id"
        EVE_SYSTEM = "eve_system"
        INDUSTRY_JOB_ID = "industry_job_id"
        CONTRACT_ID = "contract_id"
        PLANET_ID = "planet_id"
        SYSTEM_ID = "system_id"
        TYPE_ID = "type_id"

    context_id_type = models.CharField(
        max_length=30, choices=ContextType.choices, null=True, default=None
    )
    date = models.DateTimeField()
    description = models.CharField(max_length=500)
    first_party = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    entry_id = models.BigIntegerField()
    reason = models.CharField(max_length=500, null=True, default=None)
    ref_type = models.CharField(max_length=72)
    second_party = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="+",
    )
    tax = models.DecimalField(max_digits=20, decimal_places=2, null=True, default=None)
    tax_receiver_id = models.IntegerField(null=True, default=None)

    class Meta:
        abstract = True
        indexes = (
            models.Index(fields=["date"]),
            models.Index(fields=["amount"]),
            models.Index(fields=["entry_id"]),
            models.Index(fields=["ref_type"]),
            models.Index(fields=["first_party"]),
            models.Index(fields=["second_party"]),
        )
        default_permissions = ()


class CharacterWalletJournalEntry(WalletJournalEntry):
    character = models.ForeignKey(
        CharacterAudit,
        on_delete=models.CASCADE,
        related_name="ledger_character_journal",
    )

    objects = CharWalletManager()

    def __str__(self):
        return f"Character Wallet Journal: RefType: {self.ref_type} - {self.first_party.name} -> {self.second_party.name}: {self.amount} ISK"

    @classmethod
    def get_visible(cls, user):
        chars_vis = CharacterAudit.objects.visible_to(user)
        return cls.objects.filter(character__in=chars_vis)


# Mining Models


class CharacterMiningLedger(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_character_mining"
    )
    date = models.DateTimeField()
    type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, related_name="ledger_evetype"
    )
    system = models.ForeignKey(
        EveSolarSystem, on_delete=models.CASCADE, related_name="ledger_evesolarsystem"
    )
    quantity = models.IntegerField()

    @staticmethod
    def create_primary_key(character_id, mining_record):
        return f"{mining_record['date'].strftime('%Y%m%d')}-{mining_record['type_id']}-{character_id}-{mining_record['solar_system_id']}"

    objects = CharacterMiningLedgerEntryManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character} {self.id}"


class CharacterUpdateStatus(models.Model):
    """A Model to track the status of the last update."""

    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_update_status"
    )
    section = models.CharField(
        max_length=32, choices=CharacterAudit.UpdateSection.choices, db_index=True
    )
    is_success = models.BooleanField(default=None, null=True, db_index=True)
    error_message = models.TextField()
    has_token_error = models.BooleanField(default=False)

    last_run_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been started at this time",
    )
    last_run_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been successful finished at this time",
    )
    last_update_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been started at this time",
    )
    last_update_finished = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been successful finished at this time",
    )

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character} - {self.section} - {self.is_success}"

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if not self.is_success or not self.last_update_finished:
            needs_update = True
        else:
            section_time_stale = app_settings.LEDGER_STALE_TYPES.get(self.section, 60)
            stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)
            needs_update = self.last_update_finished <= stale

        if needs_update and self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self.character,
                self.section,
            )
            needs_update = False

        return needs_update

    def reset(self) -> None:
        """Reset this update status."""
        self.is_success = None
        self.error_message = ""
        self.has_token_error = False
        self.last_run_at = timezone.now()
        self.last_run_finished_at = None
        self.save()
