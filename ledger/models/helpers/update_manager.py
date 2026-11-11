"""
Update manager: tracks per-section ESI updates of an owner model.

A section is one ESI data set (e.g. the wallet). Every owner has one
`UpdateStatusBaseModel` row per section that records when the section was
last fetched, whether it succeeded and whether the token failed.
`UpdateManager` runs the `update_<section>` methods of the owner, handles the
ESI errors and writes the status rows. Owners get it through
`UpdateManagerMixin`.

ESI errors that `retry_task_on_esi_error` retries (error and bucket limits,
HTTP 502/503/504, request errors, downtime) are not swallowed: they are
recorded in the status row of the section and raised again, so the task
around the update can retry. All other errors end in the status row.
"""

# Standard Library
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, NamedTuple

# Django
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Ledger
from ledger import app_settings
from ledger.providers import is_retryable_esi_error, logger


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


class UpdateStatus(models.TextChoices):
    """Status for ESI data updates.
    Used to indicate the overall status of an Owner.
    """

    DISABLED = "disabled", _("Disabled")
    TOKEN_ERROR = "token_error", _("Token Error")
    ERROR = "error", _("Error")
    OK = "ok", _("OK")
    INCOMPLETE = "incomplete", _("Incomplete")
    IN_PROGRESS = "in_progress", _("In Progress")


class UpdateSection(models.TextChoices):
    """
    Base Class for Update Sections.

    Every value needs an `update_<value>` method on the owner model.
    """

    @classmethod
    def get_sections(cls) -> list[str]:
        """Return list of section values."""
        return [choice.value for choice in cls]

    @property
    def method_name(self) -> str:
        """Return method name for this section."""
        return f"update_{self.value}"


class CharacterUpdateSection(UpdateSection):
    """Sections for character updates."""

    WALLET_JOURNAL = "wallet_journal", _("Wallet Journal")
    MINING_LEDGER = "mining_ledger", _("Mining Ledger")
    PLANETS = "planets", _("Planets")
    PLANETS_DETAILS = "planets_details", _("Planets Details")


class CorporationUpdateSection(UpdateSection):
    """Sections for corporation updates."""

    WALLET_DIVISION_NAMES = "wallet_division_names", _("Divisions Names")
    WALLET_DIVISION = "wallet_division", _("Divisions")
    WALLET_JOURNAL = "wallet_journal", _("Wallet Journal")


class UpdateStatusBaseModel(models.Model):
    """
    A Model to track the status of the last update of one section.

    The concrete model adds the `owner` foreign key and the `section` field
    with the choices of its `UpdateSection` class.
    """

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

    def __str__(self) -> str:
        return f"{self.owner} - {self.section}"

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self.owner,
                self.section,
            )
            return False

        if not self.is_success or not self.last_run_finished_at:
            return True

        section_time_stale = app_settings.LEDGER_STALE_TYPES.get(self.section, 60)
        stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)

        try:
            return self.last_run_finished_at <= stale
        except AttributeError:
            return True

    def reset(self) -> None:
        """Reset this update status."""
        self.is_success = None
        self.error_message = ""
        self.has_token_error = False
        self.last_run_at = timezone.now()
        self.last_run_finished_at = None
        self.save()


class UpdateManager:
    """Manager class to handle update operations for owners.
    This class provides methods to manage and track update statuses for owners.

    Args:
        owner (Any): The owner model
        update_section (Any): The update section class
        update_status (Any): The update status class
    """

    def __init__(
        self,
        owner: Any,
        update_section: Any,
        update_status: Any,
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
        try:
            data = fetch_func(owner=self.owner, force_refresh=force_refresh)
            logger.debug(
                "%s: Update has changed, section: %s", self.owner, section.label
            )
            return UpdateSectionResult(
                is_changed=True,
                is_updated=True,
                data=data,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return self._handle_update_exception(section, exc, catch_token_error=False)

    def _handle_update_exception(
        self,
        section: models.TextChoices,
        exc: Exception,
        catch_token_error: bool = True,
    ) -> UpdateSectionResult:
        """
        Handle and categorize exceptions occurred during section updates.

        Args:
            section (models.TextChoices): The section that was being updated.
            exc (Exception): The exception that was raised.
            catch_token_error (bool): Whether to catch TokenError or re-raise it.

        Returns:
            UpdateSectionResult: The structured result of the failed update operation.

        Raises:
            Exception: `exc` again if `retry_task_on_esi_error` retries on it,
                and `TokenError` if `catch_token_error` is False.
        """
        if is_retryable_esi_error(exc):
            logger.debug(
                "%s: %s: Retryable ESI error, raising it for a task retry: %s: %s",
                self.owner,
                section.label,
                type(exc).__name__,
                exc,
            )
            raise exc

        if isinstance(exc, HTTPNotModified):
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

        if isinstance(exc, HTTPServerError):
            error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.debug(
                "%s: %s: ESI server error: %s",
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

        if isinstance(exc, TokenError):
            if not catch_token_error:
                raise exc
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

        error_message = (
            f"{type(exc).__name__} ({exc.status_code}): {str(exc)}"
            if isinstance(exc, HTTPClientError)
            else f"{type(exc).__name__}: {str(exc)}"
        )
        is_token_problem = isinstance(exc, HTTPClientError) and exc.status_code in [
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        ]
        if is_token_problem:
            logger.warning(
                "%s: %s: Update has Token Error: %s %s",
                self.owner,
                section.label,
                error_message,
                exc.status_code,
            )
        elif isinstance(exc, HTTPClientError):
            logger.debug(
                "%s: %s: Update has Client Error: %s %s",
                self.owner,
                section.label,
                error_message,
                exc.status_code,
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
            UpdateSectionResult: The result of the update operation.
        """
        try:
            return method(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return self._handle_update_exception(section, exc)

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
        self, section: Any, force_refresh: bool = False, *args, **kwargs
    ) -> UpdateSectionResult:
        """
        Execute an update for a specific section end-to-end.

        This method:
        1. Resets the status for the section.
        2. Resolves the corresponding update method on self.owner.
        3. Inspects the method's parameters and injects force_refresh if accepted.
        4. Calls perform_update_status with full ESI exception handling.
        5. Updates and logs the section status log.

        A retryable ESI error is recorded as failed run of the section and
        raised again, so `retry_task_on_esi_error` can retry the task.

        Args:
            section (Any): The section to update (enum or string value).
            force_refresh (bool): Whether to force a refresh.
            *args: Additional positional arguments for the update method.
            **kwargs: Additional keyword arguments for the update method.

        Returns:
            UpdateSectionResult: The result of the update operation.

        Raises:
            Exception: A retryable ESI error (see `is_retryable_esi_error`).
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

        try:
            result = self.perform_update_status(section_enum, method, *args, **kwargs)
        except Exception as exc:
            # Only retryable ESI errors get here. Record the failed run,
            # so the section is not left "in progress" and counts as stale.
            self.update_section_log(
                section_enum,
                UpdateSectionResult(
                    is_changed=False,
                    is_updated=False,
                    error_message=f"{type(exc).__name__}: {str(exc)}",
                ),
            )
            raise
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
            if self.update_section_class is None or self.update_status_model is None:
                raise AttributeError(
                    f"{self.__class__.__name__} must define 'update_section_class' "
                    "and 'update_status_model' to use UpdateManagerMixin."
                )
            self._update_manager = UpdateManager(
                owner=self,
                update_section=self.update_section_class,
                update_status=self.update_status_model,
            )
        return self._update_manager

    # pylint: disable=keyword-arg-before-vararg
    def execute_section(
        self, section: Any, force_refresh: bool = False, *args, **kwargs
    ) -> UpdateSectionResult:
        """Shortcut to execute a section update via the update_manager."""
        return self.update_manager.execute_section(
            section, force_refresh=force_refresh, *args, **kwargs
        )

    def get_sections_to_update(self, force_refresh: bool = False) -> list[str]:
        """Shortcut to get sections needing update via the update_manager."""
        return self.update_manager.get_sections_to_update(force_refresh=force_refresh)
