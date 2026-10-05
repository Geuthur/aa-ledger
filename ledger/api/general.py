# Standard Library
from http import HTTPStatus
from typing import Literal

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.urls import reverse
from django.utils.translation import gettext as _

# AA Ledger
from ledger import __title__, tasks
from ledger.api import schema
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import UserSettings

ADMIN_TASK_PRIORITY = 7


class ApiEndpoints:
    tags = ["General"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "menu/",
            response={
                HTTPStatus.OK: schema.MenuSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the navigation menu of the current user",
        )
        def get_menu(request: WSGIRequest):
            user = request.user
            if not user.has_perm("ledger.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            issues = (
                CharacterOwner.objects.annotate_total_update_status_user(user=user)
                .aggregate(total_failed=Sum("num_sections_failed"))
                .get("total_failed")
            ) or 0

            left_links = [
                schema.MenuLink(
                    name=_("Character Ledger"), link="/", badge=issues or None
                ),
                schema.MenuLink(name=_("Planetary Ledger"), link="/planetary/"),
            ]
            if user.has_perm("ledger.advanced_access"):
                left_links += [
                    schema.MenuLink(name=_("Corporation Ledger"), link="/corporation/"),
                    schema.MenuLink(name=_("Alliance Ledger"), link="/alliance/"),
                ]

            left_links.append(schema.MenuLink(name=_("Settings"), link="/settings/"))

            # The SSO flows are server-side views, so these are full page links
            add_links = [
                schema.MenuLink(
                    name=_("Add Character"),
                    link=reverse("ledger:add_char"),
                    is_external=True,
                )
            ]
            if user.has_perm("ledger.manage_access"):
                add_links += [
                    schema.MenuLink(
                        name=_("Add Corporation"),
                        link=reverse("ledger:add_corp"),
                        is_external=True,
                    ),
                    schema.MenuLink(
                        name=_("Add Alliance"),
                        link=reverse("ledger:add_ally"),
                        is_external=True,
                    ),
                ]

            right_links = [*add_links]
            if user.is_superuser:
                right_links.append(
                    schema.MenuLink(name=_("Administration"), link="/admin/")
                )

            return schema.MenuSchema(left_links=left_links, right_links=right_links)

        @api.get(
            "user/",
            response={
                HTTPStatus.OK: schema.UserData,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the current user and permissions",
        )
        def get_user(request: WSGIRequest):
            user = request.user
            if not user.has_perm("ledger.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            main_character = getattr(user.profile, "main_character", None)
            if main_character is None:
                return schema.UserData(
                    user_id=user.id,
                    is_admin=user.is_superuser,
                    can_manage=user.has_perm("ledger.manage_access"),
                    has_advanced_access=user.has_perm("ledger.advanced_access"),
                )

            return schema.UserData(
                user_id=user.id,
                character_id=main_character.character_id,
                character_name=main_character.character_name,
                corporation_id=main_character.corporation_id,
                corporation_name=main_character.corporation_name,
                alliance_id=main_character.alliance_id,
                alliance_name=main_character.alliance_name,
                portrait=get_character_portrait_url(
                    character_id=main_character.character_id,
                    character_name=main_character.character_name,
                ),
                is_admin=user.is_superuser,
                can_manage=user.has_perm("ledger.manage_access"),
                has_advanced_access=user.has_perm("ledger.advanced_access"),
            )

        @api.get(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get the settings of the current user",
        )
        def get_user_settings(request: WSGIRequest):
            if not request.user.has_perm("ledger.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            settings, __ = UserSettings.objects.get_or_create(user=request.user)
            return schema.UserSettingsSchema(
                disable_notifications=settings.disable_notifications
            )

        @api.put(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Update the settings of the current user",
        )
        def update_user_settings(
            request: WSGIRequest, payload: schema.UserSettingsUpdateRequest
        ):
            if not request.user.has_perm("ledger.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            settings, __ = UserSettings.objects.get_or_create(user=request.user)
            settings.disable_notifications = payload.disable_notifications
            settings.save(update_fields=["disable_notifications"])
            return schema.UserSettingsSchema(
                disable_notifications=settings.disable_notifications
            )

        @api.post(
            "admin/update/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Queue an update for one or all characters/corporations",
        )
        def queue_update(request: WSGIRequest, payload: schema.AdminUpdateRequest):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            return self._queue_update(
                target=payload.target,
                eve_id=payload.eve_id,
                force_refresh=payload.force_refresh,
            )

    def _queue_update(
        self,
        target: Literal["characters", "corporations"],
        eve_id: int | None,
        force_refresh: bool,
    ) -> schema.MessageSchema | tuple[int, dict]:
        """Queue the update task for one owner or for all owners of a kind."""
        if target == "characters":
            if eve_id is None:
                tasks.update_all_characters.apply_async(
                    kwargs={"force_refresh": force_refresh},
                    priority=ADMIN_TASK_PRIORITY,
                )
                return schema.MessageSchema(message=_("Queued Update All Characters"))
            if not CharacterOwner.objects.filter(
                eve_character__character_id=eve_id
            ).exists():
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            tasks.update_character.apply_async(
                kwargs={"eve_id": eve_id, "force_refresh": force_refresh},
                priority=ADMIN_TASK_PRIORITY,
            )
            return schema.MessageSchema(message=_("Queued Update for Character"))

        if eve_id is None:
            tasks.update_all_corporations.apply_async(
                kwargs={"force_refresh": force_refresh},
                priority=ADMIN_TASK_PRIORITY,
            )
            return schema.MessageSchema(message=_("Queued Update All Corporations"))
        if not CorporationOwner.objects.filter(
            eve_corporation__corporation_id=eve_id
        ).exists():
            return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}
        tasks.update_corporation.apply_async(
            kwargs={"eve_id": eve_id, "force_refresh": force_refresh},
            priority=ADMIN_TASK_PRIORITY,
        )
        return schema.MessageSchema(message=_("Queued Update for Corporation"))
