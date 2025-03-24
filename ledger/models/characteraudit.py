"""
Character Audit Model
"""

import datetime
import logging

from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EveSolarSystem, EveType

from allianceauth.eveonline.models import EveCharacter

from ledger import app_settings
from ledger.managers.characterjournal_manager import CharWalletManager
from ledger.managers.charaudit_manager import (
    AuditCharacterManager,
    CharacterMiningLedgerEntryManager,
)
from ledger.models.general import EveEntity

logger = logging.getLogger(__name__)


class CharacterAudit(models.Model):
    class UpdateStatus(models.TextChoices):
        DISABLED = "disabled", _("disabled")
        NOT_UP_TO_DATE = "not_up_to_date", _("not up to date")
        ERROR = "error", _("error")
        OK = "ok", _("ok")

        def bootstrap_icon(self) -> str:
            """Return bootstrap corresponding icon class."""
            update_map = {
                self.DISABLED: f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>",
                self.NOT_UP_TO_DATE: f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>",
                self.ERROR: f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>",
                self.OK: f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='ledger-tooltip' title='{self.description()}'>⬤</span>",
            }
            return update_map.get(self, "")

        def bootstrap_text_style_class(self) -> str:
            """Return bootstrap corresponding bootstrap text style class."""
            update_map = {
                self.DISABLED: "text-danger",
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

    active = models.BooleanField(default=False)

    last_update_wallet = models.DateTimeField(null=True, default=None, blank=True)

    last_update_mining = models.DateTimeField(null=True, default=None, blank=True)

    last_update_planetary = models.DateTimeField(null=True, default=None, blank=True)

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    objects = AuditCharacterManager()

    def __str__(self):
        return f"{self.character.character_name}'s Character Data"

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

    def _get_is_active(self):
        time_ref = timezone.now() - datetime.timedelta(
            days=app_settings.LEDGER_CHAR_MAX_INACTIVE_DAYS
        )
        try:
            is_active = True

            is_active = is_active and self.last_update_wallet > time_ref
            is_active = is_active and self.last_update_mining > time_ref
            is_active = is_active and self.last_update_planetary > time_ref
            return is_active
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def is_active(self):
        is_active = self._get_is_active()
        if self.active != is_active:
            self.active = is_active
            if is_active is False:
                logger.info("Deactivating Character: %s", self.character.character_name)
            self.save()
        return is_active

    # TODO Create a Update Status Model to handle all update section separately
    @property
    def get_status_icon(self):
        if self.active is False:
            return mark_safe(self.UpdateStatus("disabled").bootstrap_icon())

        is_active = self._get_is_active()

        # Check if one of the updates are not up to date
        if is_active is False:
            return mark_safe(self.UpdateStatus("not_up_to_date").bootstrap_icon())
        return mark_safe(self.UpdateStatus("ok").bootstrap_icon())

    @property
    def get_status_opacity(self):
        if self.active:
            return "opacity-100"
        return "opacity-25"


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
    character = models.ForeignKey(CharacterAudit, on_delete=models.CASCADE)

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
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_character"
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
