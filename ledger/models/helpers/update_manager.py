# Standard Library
import inspect
from collections.abc import Callable
from http import HTTPStatus
from typing import Any

# Third Party
from aiopenapi3 import RequestError

# Django
from django.apps import apps
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Ledger
from ledger import __title__
from ledger.models.general import (
    UpdateSectionResult,
    _NeedsUpdate,
)
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
        owner: Any = None,
        update_section: Any = None,
        update_status: Any = None,
        **kwargs: Any,
    ):
        if owner is None and "character" in kwargs:
            owner = kwargs["character"]
        self.owner = owner
        self.update_section = update_section
        self.update_status = update_status

    @property
    def character(self) -> Any:
        """Backward-compatible property referencing self.owner."""
        return self.owner

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
            owner=self.owner,
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
        """
        section = self.update_section(section)
        sig = inspect.signature(fetch_func)
        fetch_kwargs: dict[str, Any] = {}
        if "force_refresh" in sig.parameters:
            fetch_kwargs["force_refresh"] = force_refresh

        try:
            if "owner" in sig.parameters:
                fetch_kwargs["owner"] = self.owner
                data = fetch_func(**fetch_kwargs)
            elif "character" in sig.parameters:
                fetch_kwargs["character"] = self.owner
                data = fetch_func(**fetch_kwargs)
            else:
                data = fetch_func(self.owner, **fetch_kwargs)

            logger.debug(
                "%s: Update has changed, section: %s", self.owner, section.label
            )
            return UpdateSectionResult(
                is_changed=True,
                is_updated=True,
                data=data,
            )
        except HTTPNotModified:
            logger.debug(
                "%s: Update has not changed (HTTP 304), section: %s",
                self.owner,
                section.label,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message="",
            )
        except (HTTPServerError, RequestError) as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.debug(
                "%s: %s: ESI server error / timeout: %s",
                self.owner,
                section.label,
                error_message,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message=error_message,
            )
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__} ({exc.status_code}): {str(exc)}"
            is_token_problem = exc.status_code in [
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
                HTTPStatus.NOT_FOUND,
            ]
            if is_token_problem:
                logger.warning(
                    "%s: %s: Update has Token Error: %s %s",
                    self.owner,
                    section.label,
                    error_message,
                    exc.status_code,
                )
            else:
                logger.debug(
                    "%s: %s: Update has Client Error: %s %s",
                    self.owner,
                    section.label,
                    error_message,
                    exc.status_code,
                )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=is_token_problem,
                error_message=error_message,
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
        is_success = not result.has_token_error and not bool(error_message)
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
    ) -> UpdateSectionResult:
        """
        Perform update status.
        Args:
            section (models.TextChoices): The section to update.
            method (Callable): The method to perform the update.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.
        Returns:
            UpdateSectionResult: The result of the method call.
        """
        try:
            result = method(*args, **kwargs)
        except (HTTPServerError, RequestError) as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.debug(
                "%s: %s: ESI server error / timeout: %s",
                self.owner,
                section.label,
                error_message,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=False,
                error_message=error_message,
            )
        except TokenError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.warning(
                "%s: %s: Update has Token Error: %s",
                self.owner,
                section.label,
                error_message,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=True,
                error_message=error_message,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_message = f"{type(exc).__name__}: {str(exc)}"
            # pylint: disable=no-member
            is_token_problem = isinstance(exc, HTTPClientError) and exc.status_code in [
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.FORBIDDEN,
                HTTPStatus.NOT_FOUND,
            ]
            if is_token_problem:
                logger.warning(
                    "%s: %s: Update has Token Error: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            else:
                logger.error(
                    "%s: %s: Error during update status: %s",
                    self.owner,
                    section.label,
                    error_message,
                )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=is_token_problem,
                error_message=error_message,
            )
        return result

    def get_sections_to_update(self, force_refresh: bool = False) -> list[str]:
        """
        Determine which sections need to be updated.

        Args:
            force_refresh (bool): If True, reset token errors and return all sections.

        Returns:
            list[str]: The list of section values to update.
        """
        if force_refresh:
            self.reset_has_token_error()
            return list(self.update_section.get_sections())

        needs_update = self.calc_update_needed()
        if not needs_update:
            return []

        return [
            sec
            for sec in self.update_section.get_sections()
            if needs_update.for_section(sec)
        ]

    # pylint: disable=keyword-arg-before-vararg
    def execute_section(
        self,
        section: Any,
        force_refresh: bool = False,
        *args,
        **kwargs,
    ) -> UpdateSectionResult:
        """
        Execute an update for a specific section end-to-end.

        This method:
        1. Resets the status for the section.
        2. Resolves the corresponding update method on self.owner.
        3. Inspects the method's parameters and injects force_refresh if accepted.
        4. Calls perform_update_status with full ESI exception handling.
        5. Updates and logs the section status log.

        Args:
            section (Any): The section to update (enum or string value).
            force_refresh (bool): Whether to force a refresh.
            *args: Additional positional arguments for the update method.
            **kwargs: Additional keyword arguments for the update method.

        Returns:
            UpdateSectionResult: The result of the update operation.
        """
        section_enum = (
            self.update_section(section)
            if not isinstance(section, self.update_section)
            else section
        )

        self.reset_update_status(section_enum)

        method: Callable = getattr(self.owner, section_enum.method_name)
        method_signature = inspect.signature(method)

        if (
            "force_refresh" in method_signature.parameters
            and "force_refresh" not in kwargs
        ):
            kwargs["force_refresh"] = force_refresh

        result = self.perform_update_status(section_enum, method, *args, **kwargs)
        self.update_section_log(section_enum, result)
        return result


class UpdateManagerMixin:
    """
    Mixin for Django models that support section-based updates via UpdateManager.

    Subclasses must define:
        update_section_class: The TextChoices enum class defining update sections.
        update_status_model: The Model class tracking section update statuses.
    """

    update_section_class: Any = None
    update_status_model: Any = None

    @property
    def update_manager(self) -> UpdateManager:
        """Return the initialized UpdateManager instance for this owner."""
        if not hasattr(self, "_update_manager"):
            status_model = self.update_status_model
            if isinstance(status_model, str):
                status_model = apps.get_model(self._meta.app_label, status_model)

            if self.update_section_class is None or status_model is None:
                raise AttributeError(
                    f"{self.__class__.__name__} must define 'update_section_class' "
                    "and 'update_status_model' to use UpdateManagerMixin."
                )
            self._update_manager = UpdateManager(
                owner=self,
                update_section=self.update_section_class,
                update_status=status_model,
            )
        return self._update_manager

    # pylint: disable=keyword-arg-before-vararg
    def execute_section(
        self,
        section: Any,
        force_refresh: bool = False,
        *args,
        **kwargs,
    ) -> UpdateSectionResult:
        """Shortcut to execute a section update via the update_manager."""
        return self.update_manager.execute_section(
            section, force_refresh=force_refresh, *args, **kwargs
        )

    def get_sections_to_update(self, force_refresh: bool = False) -> list[str]:
        """Shortcut to get sections needing update via the update_manager."""
        return self.update_manager.get_sections_to_update(force_refresh=force_refresh)
