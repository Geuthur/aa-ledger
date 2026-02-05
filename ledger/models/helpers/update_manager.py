# Standard Library
from typing import TYPE_CHECKING, Union

# Django
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Ledger
from ledger import __title__
from ledger.models.general import (
    UpdateSectionResult,
    _NeedsUpdate,
)

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.characteraudit import CharacterOwner, CharacterUpdateStatus
    from ledger.models.corporationaudit import CorporationOwner, CorporationUpdateStatus

# AA Ledger
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class UpdateStatus(models.TextChoices):
    DISABLED = "disabled", _("Disabled")
    TOKEN_ERROR = "token_error", _("Token Error")
    ERROR = "error", _("Error")
    OK = "ok", _("OK")
    INCOMPLETE = "incomplete", _("Incomplete")
    IN_PROGRESS = "in_progress", _("In Progress")

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


class CharacterUpdateSection(models.TextChoices):
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


class CorporationUpdateSection(models.TextChoices):
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


class UpdateManager:
    """Manager class to handle update operations for CharacterOwner and CorporationOwner.
    This class provides methods to manage and track update statuses for both character and corporation owners.

    Args:
        owner (CorporationOwner | CharacterOwner): The owner model (corporation or character)
        update_section (CorporationUpdateSection | CharacterUpdateSection): The update section class (CorporationUpdateSection or CharacterUpdateSection)
        update_status (CorporationUpdateStatus | CharacterUpdateStatus): The update status class (CorporationUpdateStatus or CharacterUpdateStatus)
    """

    def __init__(
        self,
        owner: Union["CorporationOwner", "CharacterOwner"],
        update_section: CorporationUpdateSection | CharacterUpdateSection,
        update_status: Union["CorporationUpdateStatus", "CharacterUpdateStatus"],
    ):
        self.owner = owner
        self.update_section = update_section
        self.update_status = update_status

    # Shared methods
    def calc_update_needed(self) -> _NeedsUpdate:
        """
        Calculate which sections need an update and save the results in a _NeedsUpdate object.

        Returns:
            _NeedsUpdate: An object containing a mapping of sections to their update needs.
        """
        sections_needs_update = {
            section: True for section in self.update_section.get_sections()
        }
        existing_sections = self.update_status.objects.filter(owner=self.owner)
        needs_update = {
            obj.section: obj.need_update()
            for obj in existing_sections
            if obj.section in sections_needs_update
        }
        sections_needs_update.update(needs_update)
        return _NeedsUpdate(section_map=sections_needs_update)

    def reset_update_status(self, section: models.TextChoices):
        """
        Create or Reset the update status for a specific section.

        Args:
            section (models.TextChoices): The section to reset.
        Returns:
            UpdateStatus (Object): The reset update status object for the Owner Model.
        """
        update_status_obj = self.update_status.objects.get_or_create(
            owner=self.owner,
            section=section,
        )[0]
        update_status_obj.reset()
        return update_status_obj

    def reset_has_token_error(self) -> None:
        """
        Reset has_token_error for all sections.

        Returns:
            None
        """
        self.update_status.objects.filter(
            has_token_error=True,
        ).update(
            has_token_error=False,
        )

    def update_section_if_changed(
        self, section: models.TextChoices, fetch_func, force_refresh: bool = False
    ):
        """
        Handle updating a specific section if there are changes.

        Args:
            section (models.TextChoices): The section to update.
            fetch_func (Callable): The function to fetch the data for the section.
            force_refresh (bool): Whether to force a refresh of the data.
        Returns:
            UpdateSectionResult: The result of the update operation.
        Raises:
            HTTPClientError: If there is a client error during the fetch.
            HTTPServerError: If there is a server error during the fetch.
            HTTPNotModified: If the data has not been modified.
        """
        section = self.update_section(section)
        try:
            data = fetch_func(owner=self.owner, force_refresh=force_refresh)
            logger.debug(
                "%s: Update has changed, section: %s", self.owner, section.label
            )
        except HTTPNotModified:
            logger.debug(
                "%s: Update has not changed, section: %s", self.owner, section.label
            )
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error(
                "%s: %s: Update has Client Error: %s %s",
                self.owner,
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
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    def update_section_log(
        self, section: models.TextChoices, result: UpdateSectionResult
    ) -> None:
        """
        Update the status of a specific section.
        Args:
            section (models.TextChoices): The section to update.
            result (UpdateSectionResult): The result of the update operation.
        Returns:
            None
        """
        error_message = result.error_message if result.error_message else ""
        is_success = not result.has_token_error
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": result.has_token_error,
            "last_run_finished_at": timezone.now(),
        }
        obj = self.update_status.objects.update_or_create(
            owner=self.owner,
            section=section,
            defaults=defaults,
        )[0]
        if result.is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self.owner, section.label, status)

    def perform_update_status(
        self, section: models.TextChoices, method, *args, **kwargs
    ):
        """
        Perform update status.
        Args:
            section (models.TextChoices): The section to update.
            method (Callable): The method to perform the update.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.
        Returns:
            Any: The result of the method call.
        Raises:
            Exception: Reraises any exception encountered during the method call.
        """
        try:
            result = method(*args, **kwargs)
        except HTTPServerError as exc:
            raise exc
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error(
                "%s: %s: Error during update status: %s",
                self.owner,
                section.label,
                error_message,
            )
            self.update_status.objects.update_or_create(
                owner=self.owner,
                section=section,
                defaults={
                    "is_success": False,
                    "error_message": error_message,
                    "has_token_error": False,
                    "last_update_at": timezone.now(),
                },
            )
            raise exc
        return result
