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
from ledger import __title__
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
            ("admin_access", "Has access to all Administration tools"),
        )


# EvE Entity Model - Store all Chars, Corps, Allys
class EveEntity(models.Model):
    """An Eve entity like a corporation or a character"""

    CATEGORY_ALLIANCE = "alliance"
    CATEGORY_CHARACTER = "character"
    CATEGORY_CORPORATION = "corporation"

    CATEGORY_CHOICES = (
        (CATEGORY_ALLIANCE, "Alliance"),
        (CATEGORY_CORPORATION, "Corporation"),
        (CATEGORY_CHARACTER, "Character"),
    )

    eve_id = models.IntegerField(
        primary_key=True, validators=[MinValueValidator(0)], verbose_name=_("id")
    )
    category = models.CharField(
        max_length=32, choices=CATEGORY_CHOICES, verbose_name=_("category")
    )
    name = models.CharField(max_length=254, verbose_name=_("name"))

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

    objects = EveEntityManager()

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

    class Meta:
        default_permissions = ()


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
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
