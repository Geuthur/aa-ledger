"""
Character Audit Model
"""

# Standard Library
from collections.abc import Callable

# Third Party
from aiopenapi3.errors import ContentTypeError
from bravado.exception import HTTPInternalServerError

# Django
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.exceptions import HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveMarketPrice, EveSolarSystem, EveType

# AA Ledger
from ledger import __title__
from ledger.app_settings import (
    LEDGER_CACHE_KEY,
    LEDGER_USE_COMPRESSED,
)
from ledger.errors import HTTPGatewayTimeoutError, TokenDoesNotExist
from ledger.managers.character_audit_manager import (
    CharacterAuditManager,
)
from ledger.managers.character_journal_manager import CharWalletManager
from ledger.managers.character_mining_manager import CharacterMiningLedgerEntryManager
from ledger.models.general import (
    AuditBase,
    EveEntity,
    UpdateSectionResult,
    UpdateStatus,
    _NeedsUpdate,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharacterAudit(AuditBase):
    """A model to store character information."""

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
        TOKEN_ERROR = "token_error", _("token error")
        ERROR = "error", _("error")
        OK = "ok", _("ok")
        INCOMPLETE = "incomplete", _("incomplete")
        IN_PROGRESS = "in_progress", _("in progress")

        def bootstrap_icon(self) -> str:
            """Return bootstrap corresponding icon class."""
            update_map = {
                status: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>"
                )
                for status in [
                    self.DISABLED,
                    self.TOKEN_ERROR,
                    self.ERROR,
                    self.INCOMPLETE,
                    self.IN_PROGRESS,
                    self.OK,
                ]
            }
            return update_map.get(self, "")

        def bootstrap_text_style_class(self) -> str:
            """Return bootstrap corresponding bootstrap text style class."""
            update_map = {
                self.DISABLED: "text-muted",
                self.TOKEN_ERROR: "text-warning",
                self.INCOMPLETE: "text-warning",
                self.IN_PROGRESS: "text-info",
                self.ERROR: "text-danger",
                self.OK: "text-success",
            }
            return update_map.get(self, "")

        def description(self) -> str:
            """Return description for an enum object."""
            update_map = {
                self.DISABLED: _("Update is disabled"),
                self.TOKEN_ERROR: _("One section has a token error during update"),
                self.INCOMPLETE: _("One or more sections have not been updated"),
                self.IN_PROGRESS: _("Update is in progress"),
                self.ERROR: _("An error occurred during update"),
                self.OK: _("Updates completed successfully"),
            }
            return update_map.get(self, "")

    id = models.AutoField(primary_key=True)

    character_name = models.CharField(max_length=100, null=True, default=None)

    eve_character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="ledger_character"
    )

    active = models.BooleanField(default=True)

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    objects = CharacterAuditManager()

    def __str__(self) -> str:
        try:
            return f"{self.eve_character.character_name} ({self.id})"
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
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = CharacterAudit.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

    @property
    def alts(self) -> models.QuerySet[EveCharacter]:
        """Get all alts for this character."""
        alts = EveCharacter.objects.filter(
            character_ownership__user=self.eve_character.character_ownership.user
        ).select_related(
            "character_ownership",
        )
        return alts

    @property
    def mining_ledger(self):
        """Get the mining ledger for this character."""
        return self.ledger_character_mining

    @property
    def wallet_journal(self):
        """Get the wallet journal for this character."""
        return self.ledger_character_journal

    def get_token(self, scopes=None) -> Token:
        """Get the token for this character."""
        token = (
            Token.objects.filter(character_id=self.eve_character.character_id)
            .require_scopes(scopes if scopes else self.get_esi_scopes())
            .require_valid()
            .first()
        )
        if not token:
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

    def calc_update_needed(self) -> _NeedsUpdate:
        """Calculate if an update is needed."""
        sections_needs_update = {
            section: True for section in self.UpdateSection.get_sections()
        }
        existing_sections: models.QuerySet[CharacterUpdateStatus] = (
            self.ledger_update_status.all()
        )
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)

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
        update_status = self.get_status
        if update_status == self.UpdateStatus.TOKEN_ERROR:
            self.ledger_update_status.filter(
                has_token_error=True,
            ).update(
                has_token_error=False,
            )
            return True
        return False

    def update_section_if_changed(
        self,
        section: UpdateSection,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            data = fetch_func(character=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPInternalServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPNotModified as exc:
            logger.debug("%s: Update has not changed, section: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPGatewayTimeoutError as exc:
            logger.debug(
                "%s: Update has a gateway timeout error, section: %s: %s",
                self,
                section.label,
                exc,
            )
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except (OSError, ContentTypeError) as exc:
            logger.info(
                "%s Update has a %s error, section: %s: %s",
                self,
                type(exc).__name__,
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
            obj.last_update_finished_at = timezone.now()
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

    price_per_unit = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    @staticmethod
    def create_primary_key(character_id, mining_record):
        print("DEBUG mining_record:", mining_record, type(mining_record.date))
        return f"{mining_record.date.strftime('%Y%m%d')}-{mining_record.type_id}-{character_id}-{mining_record.solar_system_id}"

    @staticmethod
    def update_evemarket_price():  # Dont want to make a task only for this
        """Update Prices for the EveMarketPrice."""
        updated = 0
        cached_update = cache.get(f"{LEDGER_CACHE_KEY}-eve-market-price", False)
        if cached_update is False:
            updated = EveMarketPrice.objects.update_from_esi()
            cache.set(
                f"{LEDGER_CACHE_KEY}-eve-market-price", None, (60 * 60 * 24)
            )  # Cache for 24 hours
            logger.debug(f"Updated {updated} for entries EveMarketPrice")
        return updated

    def get_npc_price(self):
        """Get the NPC price for the type."""
        try:
            if LEDGER_USE_COMPRESSED:
                type_name = f"Compressed {self.type.name}"
                price = EveType.objects.get(name=type_name).market_price.average_price
            else:
                price = self.type.market_price.average_price
        except (EveMarketPrice.DoesNotExist, EveType.DoesNotExist):
            price = None
        return price

    objects = CharacterMiningLedgerEntryManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character} {self.id}"


class CharacterUpdateStatus(UpdateStatus):
    """A Model to track the status of the last update."""

    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_update_status"
    )
    section = models.CharField(
        max_length=32, choices=CharacterAudit.UpdateSection.choices, db_index=True
    )

    def __str__(self) -> str:
        return f"{self.character} - {self.section} - {self.is_success}"
