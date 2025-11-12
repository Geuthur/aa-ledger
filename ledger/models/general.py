"""
General Model
"""

# Standard Library
import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NamedTuple

# Third Party
from aiopenapi3.errors import ContentTypeError, HTTPClientError, HTTPServerError

# Django
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.exceptions import HTTPNotModified

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


class AuditBase(models.Model):
    """A base model for audit models."""

    class Meta:
        abstract = True

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

    def update_section_if_changed(
        self,
        section: models.TextChoices,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            data = fetch_func(audit=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            # TODO ADD DISCORD/AUTH NOTIFICATION?
            logger.error(
                "%s: %s: Update has Client Error: %s %s",
                self,
                section.label,
                error_message,
                exc.status_code,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=True,
                error_message=error_message,
            )
        except HTTPNotModified:
            logger.debug("%s: Update has not changed, section: %s", self, section.label)
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

    def reset_has_token_error(self) -> None:
        """Reset the has_token_error flag for this character."""
        if self.get_status == self.UpdateStatus.TOKEN_ERROR:
            self.update_status.filter(
                has_token_error=True,
            ).update(
                has_token_error=False,
            )
            return True
        return False

    def reset_update_status(self, section):
        """Reset the status of a given update section and return it."""
        update_status_obj = self.update_status.get_or_create(
            section=section,
        )[0]
        update_status_obj.reset()
        return update_status_obj

    def perform_update_status(
        self, section, method: Callable, *args, **kwargs
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

            # Update the status using the related manager name
            self.update_status.update_or_create(
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

    def update_section_log(
        self,
        section: models.TextChoices,
        result: UpdateSectionResult,
    ) -> None:
        """Update the status of a specific section."""
        error_message = result.error_message if result.error_message else ""
        is_success = not result.has_token_error
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": result.has_token_error,
            "last_run_finished_at": timezone.now(),
        }
        obj: UpdateStatus = self.update_status.update_or_create(
            section=section,
            defaults=defaults,
        )[0]
        if result.is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    def calc_update_needed(self) -> _NeedsUpdate:
        """Calculate if an update is needed."""
        sections_needs_update = {
            section: True for section in self.UpdateSection.get_sections()
        }
        existing_sections: models.QuerySet[UpdateStatus] = self.update_status.all()
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)


class UpdateStatus(models.Model):
    """A Model to track the status of the last update."""

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

    class Meta:
        abstract = True
        default_permissions = ()

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
