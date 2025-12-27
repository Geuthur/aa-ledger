"""
General Model
"""

# Standard Library
import datetime
from dataclasses import dataclass
from typing import Any, NamedTuple

# Django
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, app_settings
from ledger.managers.general_manager import EveEntityManager

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Permission Manager


class General(models.Model):
    """A model defining commonly used properties and methods for Ledger."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app, Ledger."),
            ("advanced_access", "Can access Corporation and Alliance Ledger."),
            ("manage_access", "Can manage Ledger."),
        )


# EvE Entity Model - Store all Chars, Corps, Allys
class EveEntity(models.Model):
    """An Eve entity like a corporation or a character"""

    objects: EveEntityManager = EveEntityManager()

    class Meta:
        default_permissions = ()

    CATEGORY_ALLIANCE = "alliance"
    CATEGORY_CHARACTER = "character"
    CATEGORY_CORPORATION = "corporation"

    CATEGORY_CHOICES = (
        (CATEGORY_ALLIANCE, "Alliance"),
        (CATEGORY_CORPORATION, "Corporation"),
        (CATEGORY_CHARACTER, "Character"),
    )

    eve_id = models.IntegerField(
        primary_key=True, validators=[MinValueValidator(0)], verbose_name=_("ID")
    )
    category = models.CharField(
        max_length=32, choices=CATEGORY_CHOICES, verbose_name=_("Category")
    )
    name = models.CharField(max_length=254, verbose_name=_("Name"))

    # optionals for character/corp
    corporation = models.ForeignKey(
        "EveEntity",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="corp",
    )
    alliance = models.ForeignKey(
        "EveEntity",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="alli",
    )
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.eve_id}, category='{self.category}', "
            f"name='{self.name}')"
        )

    @property
    def is_alliance(self) -> bool:
        """Return True if entity is an alliance, else False."""
        return self.category == self.CATEGORY_ALLIANCE

    @property
    def is_corporation(self) -> bool:
        """Return True if entity is an corporation, else False."""
        return self.category == self.CATEGORY_CORPORATION

    @property
    def is_character(self) -> bool:
        """Return True if entity is a character, else False."""
        return self.category == self.CATEGORY_CHARACTER

    def icon_url(self, size=128) -> str:
        """Url to an icon image for this organization."""
        if self.category == self.CATEGORY_ALLIANCE:
            return EveAllianceInfo.generic_logo_url(self.eve_id, size=size)

        if self.category == self.CATEGORY_CORPORATION:
            return EveCorporationInfo.generic_logo_url(self.eve_id, size=size)

        if self.category == self.CATEGORY_CHARACTER:
            return EveCharacter.generic_portrait_url(self.eve_id, size=size)

        raise NotImplementedError(
            f"Avatar URL not implemented for category {self.category}"
        )

    def needs_update(self):
        return self.last_update + datetime.timedelta(days=7) < timezone.now()


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
    has_token_error: bool = False
    error_message: str | None = None
    data: Any = None


@dataclass(frozen=True)
class _NeedsUpdate:
    """An Object to track if an update is needed."""

    section_map: dict[str, bool]

    def __bool__(self) -> bool:
        """Check if any section needs an update."""
        return any(self.section_map.values())

    def for_section(self, section: str) -> bool:
        """Check if an update is needed for a specific section."""
        return self.section_map.get(section, False)


class UpdateStatusBaseModel(models.Model):
    """A Model to track the status of the last update."""

    class Meta:
        abstract = True
        default_permissions = ()

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
    last_update_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been successful finished at this time",
    )

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if not self.is_success or not self.last_update_finished_at:
            needs_update = True
        else:
            section_time_stale = app_settings.LEDGER_STALE_TYPES.get(self.section, 60)
            stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)

            try:
                needs_update = self.last_update_finished_at <= stale
            except AttributeError:
                needs_update = True

        if needs_update and self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self,
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
        default_permissions = ()
