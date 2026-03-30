"""
This module contains the LedgerEntry model, which is used to store character ledger information in the AA Ledger application.
"""

# Django
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.managers.ledger_manager import BillboardEntryManager
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class LedgerEntry(models.Model):
    """A model to store ledger information."""

    class Meta:
        abstract = True
        default_permissions = ()
        permissions = ()

    id = models.AutoField(primary_key=True)

    year = models.PositiveSmallIntegerField(null=True, default=None)

    month = models.PositiveSmallIntegerField(null=True, default=None)

    day = models.PositiveSmallIntegerField(null=True, default=None)

    bounty = models.FloatField(null=True, default=None)

    ess = models.FloatField(null=True, default=None)

    mining = models.FloatField(null=True, default=None)

    miscellaneous = models.FloatField(null=True, default=None)

    costs = models.FloatField(null=True, default=None)

    last_updated = models.DateTimeField(auto_now=True)

    final_data = models.BooleanField(default=False)

    @property
    def is_final(self) -> bool:
        """Return whether this ledger entry is marked as final."""
        return (
            self.final_data
            or self.last_updated >= timezone.now() - timezone.timedelta(hours=1)
        )


class AllianceLedgerEntry(LedgerEntry):
    """A model to store alliance ledger information."""

    class Meta:
        default_permissions = ()
        permissions = ()

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        EveAllianceInfo, on_delete=models.CASCADE, related_name="ledger_alliance_entry"
    )

    corporation_id = models.IntegerField(null=True, default=None)

    def __str__(self) -> str:
        try:
            return f"Ledger Entry: {self.owner.eve_corporation.alliance.alliance_name} ({self.id})"
        except AttributeError:
            return f"Ledger Entry: {self.name} ({self.id})"


class CorporationLedgerEntry(LedgerEntry):
    """A model to store corporation ledger information."""

    class Meta:
        default_permissions = ()
        permissions = ()

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_entry",
    )

    entity_id = models.IntegerField(null=True, default=None)

    def __str__(self) -> str:
        try:
            return f"Ledger Entry: {self.owner.eve_corporation.corporation_name} ({self.id})"
        except AttributeError:
            return f"Ledger Entry: {self.name} ({self.id})"


class CharacterLedgerEntry(LedgerEntry):
    """A model to store character ledger information."""

    class Meta:
        default_permissions = ()
        permissions = ()

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        CharacterOwner, on_delete=models.CASCADE, related_name="ledger_character_entry"
    )

    def __str__(self) -> str:
        try:
            return (
                f"Ledger Entry: {self.owner.eve_character.character_name} ({self.id})"
            )
        except AttributeError:
            return f"Ledger Entry: {self.name} ({self.id})"


class BillboardEntry(models.Model):
    """A model to store billboard information."""

    class Meta:
        abstract = True
        default_permissions = ()
        permissions = ()

    id = models.AutoField(primary_key=True)

    year = models.PositiveSmallIntegerField(null=True, default=None)

    month = models.PositiveSmallIntegerField(null=True, default=None)

    day = models.PositiveSmallIntegerField(null=True, default=None)

    xy_billboard = models.JSONField(null=True, default=None)

    chord_billboard = models.JSONField(null=True, default=None)

    last_updated = models.DateTimeField(auto_now=True)

    final_data = models.BooleanField(default=False)

    @property
    def is_final(self) -> bool:
        """Return whether this ledger entry is marked as final."""
        return (
            self.final_data
            or self.last_updated >= timezone.now() - timezone.timedelta(hours=1)
        )


class CharacterBillboardEntry(BillboardEntry):
    """A model to store character billboard information."""

    objects: BillboardEntryManager = BillboardEntryManager()

    class Meta:
        default_permissions = ()
        permissions = ()

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        CharacterOwner,
        on_delete=models.CASCADE,
        related_name="ledger_char_billboard_entries",
    )

    def __str__(self) -> str:
        try:
            return f"Billboard Entry: {self.owner.eve_character.character_name} ({self.id})"
        except AttributeError:
            return f"Billboard Entry: {self.name} ({self.id})"


class CorporationBillboardEntry(BillboardEntry):
    """A model to store corporation billboard information."""

    objects: BillboardEntryManager = BillboardEntryManager()

    class Meta:
        default_permissions = ()
        permissions = ()

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        CorporationOwner,
        on_delete=models.CASCADE,
        related_name="ledger_corp_billboard_entries",
    )

    def __str__(self) -> str:
        try:
            return f"Billboard Entry: {self.owner.eve_corporation.corporation_name} ({self.id})"
        except AttributeError:
            return f"Billboard Entry: {self.name} ({self.id})"


class AllianceBillboardEntry(BillboardEntry):
    """A model to store alliance billboard information."""

    objects: BillboardEntryManager = BillboardEntryManager()

    class Meta:
        default_permissions = ()
        permissions = ()

    name = models.CharField(max_length=100, null=True, default=None)

    owner = models.ForeignKey(
        EveAllianceInfo,
        on_delete=models.CASCADE,
        related_name="ledger_alliance_billboard_entries",
    )

    def __str__(self) -> str:
        try:
            return (
                f"Billboard Entry: {self.owner.eve_alliance.alliance_name} ({self.id})"
            )
        except AttributeError:
            return f"Billboard Entry: {self.name} ({self.id})"
