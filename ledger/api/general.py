# Standard Library
from http import HTTPStatus
from typing import Literal

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Max, Sum
from django.urls import reverse
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from esi.models import Token

# AA Ledger
from ledger import tasks
from ledger.api import schema
from ledger.api.helpers.core import (
    _build_sections,
    _character_icon,
    get_characterowner_or_none,
    get_manage_corporation,
)
from ledger.helpers.eveonline import (
    get_alliance_logo_url,
    get_character_portrait_url,
    get_corporation_logo_url,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import General, UserSettings
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    CorporationUpdateSection,
)
from ledger.tasks import (
    update_character,
    update_corporation,
    update_user_characters,
)

ADMIN_TASK_PRIORITY = 7


def _get_user_added_corporation_ids(user) -> list[int]:
    """Return list of corporation IDs the user has personally added or owns."""
    if not user.is_authenticated:
        return []

    # Corps where user has an ESI token with corp audit scopes
    corp_scoped_chars = (
        Token.objects.filter(user=user)
        .require_scopes(CorporationOwner.get_esi_scopes())
        .values_list("character_id", flat=True)
    )
    corp_ids = set(
        EveCharacter.objects.filter(character_id__in=corp_scoped_chars).values_list(
            "corporation_id", flat=True
        )
    )

    # Corps where user has owned characters with tokens
    user_token_chars = Token.objects.filter(user=user).values_list(
        "character_id", flat=True
    )
    owned_corps = user.character_ownerships.filter(
        character__character_id__in=user_token_chars
    ).values_list("character__corporation_id", flat=True)
    corp_ids.update(owned_corps)

    return list(corp_ids)


class ApiEndpoints:
    tags = ["General"]

    # pylint: disable=too-many-statements
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
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            issues = (
                CharacterOwner.objects.annotate_total_update_status_user(user=user)
                .aggregate(total_failed=Sum("num_sections_failed"))
                .get("total_failed")
            ) or 0
            has_owner_errors = False
            if issues > 0:
                has_owner_errors = True

            left_links = [
                schema.MenuLink(name=_("Overview"), link="/"),
                schema.MenuLink(name=_("My Characters"), link="/character/"),
                schema.MenuLink(
                    name=_("Settings"),
                    link="/settings/",
                    badge=issues or None,
                    has_errors=has_owner_errors,
                ),
            ]

            # The SSO flows are server-side views, so these are full page links
            add_links = [
                schema.MenuLink(
                    name=_("Add Character"),
                    link=reverse("ledger:add_char"),
                    is_external=True,
                )
            ]
            if General.has_perm(user, General.Permission.MANAGE_ACCESS):
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
            can_manage_ledger = (
                user.is_superuser
                or CharacterOwner.objects.manage_to(user).exists()
                or CorporationOwner.objects.manage_to(user).exists()
            )
            if can_manage_ledger:
                right_links.append(
                    schema.MenuLink(name=_("Superuser"), link="/superuser/")
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
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            main_character = getattr(user.profile, "main_character", None)
            if main_character is None:
                return schema.UserData(
                    user_id=user.id,
                    is_admin=user.is_superuser,
                    can_manage=General.has_perm(user, General.Permission.MANAGE_ACCESS),
                    has_advanced_access=General.has_perm(
                        user, General.Permission.ADVANCED_ACCESS
                    ),
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
                can_manage=General.has_perm(user, General.Permission.MANAGE_ACCESS),
                has_advanced_access=General.has_perm(
                    user, General.Permission.ADVANCED_ACCESS
                ),
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
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
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
            if not General.has_perm(request.user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            settings, __ = UserSettings.objects.get_or_create(user=request.user)
            settings.disable_notifications = payload.disable_notifications
            settings.save(update_fields=["disable_notifications"])
            return schema.UserSettingsSchema(
                disable_notifications=settings.disable_notifications
            )

        @api.get(
            "settings/owners/",
            response={
                HTTPStatus.OK: schema.SettingsOwnersResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get all owners manageable by the user for Settings",
        )
        # pylint: disable=too-many-locals
        def get_settings_owners(request: WSGIRequest):
            user = request.user
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            user_char_ids = list(
                CharacterOwnership.objects.filter(user=user).values_list(
                    "character__character_id", flat=True
                )
            )

            # 1. Registered Characters
            characters = list(
                CharacterOwner.objects.filter(
                    eve_character__character_id__in=user_char_ids
                )
                .select_related("eve_character")
                .prefetch_related("ledger_update_status")
                .annotate(last_sync=Max("ledger_update_status__last_run_finished_at"))
                .order_by("eve_character__character_name")
            )
            registered_char_ids = [c.eve_character.character_id for c in characters]

            # Missing Characters
            missing_chars = (
                EveCharacter.objects.filter(character_id__in=user_char_ids)
                .exclude(character_id__in=registered_char_ids)
                .order_by("character_name")
            )

            registered_list: list[schema.SettingsOwnerSchema] = []
            for char in characters:
                sections, error_message = _build_sections(
                    char.ledger_update_status.all(), CharacterUpdateSection
                )
                status_str = str(char.get_status)
                has_error = status_str in ["error", "token_error"]
                registered_list.append(
                    schema.SettingsOwnerSchema(
                        id=char.eve_character.character_id,
                        name=char.eve_character.character_name,
                        owner_type="character",
                        avatar_url=_character_icon(
                            char.eve_character.character_id,
                            char.eve_character.character_name,
                        ),
                        subtitle=f"[{char.eve_character.corporation_ticker}]",
                        status=status_str,
                        has_error=has_error,
                        error_message=error_message,
                        last_sync=getattr(char, "last_sync", None),
                        sections=[
                            schema.SettingsOwnerSectionSchema(
                                section=s.section,
                                section_name=s.section_name,
                                is_success=s.is_success,
                                has_token_error=s.has_token_error,
                                error_message=s.error_message,
                                last_run_at=s.last_run_at,
                                last_run_finished_at=s.last_run_finished_at,
                            )
                            for s in sections
                        ],
                    )
                )

            # 2. Corporations: only those the user personally added
            user_corp_ids = _get_user_added_corporation_ids(user)
            corps = (
                CorporationOwner.objects.filter(
                    eve_corporation__corporation_id__in=user_corp_ids
                )
                .select_related("eve_corporation", "eve_corporation__alliance")
                .prefetch_related("ledger_corporation_update_status")
                .order_by("eve_corporation__corporation_name")
            )
            alliance_syncs: dict = {}
            for corp in corps:
                eve_corp = corp.eve_corporation
                sections, error_message = _build_sections(
                    corp.ledger_corporation_update_status.all(),
                    CorporationUpdateSection,
                )
                corp_last_sync = corp.ledger_corporation_update_status.aggregate(
                    latest=Max("last_run_finished_at")
                )["latest"]
                if eve_corp.alliance is not None:
                    alliance_syncs.setdefault(eve_corp.alliance, []).append(
                        corp_last_sync
                    )
                status_str = str(corp.get_status)
                has_error = status_str in ["error", "token_error"]
                registered_list.append(
                    schema.SettingsOwnerSchema(
                        id=eve_corp.corporation_id,
                        name=eve_corp.corporation_name,
                        owner_type="corporation",
                        avatar_url=get_corporation_logo_url(
                            eve_corp.corporation_id,
                            64,
                        ),
                        subtitle=(
                            f"[{eve_corp.corporation_ticker}]"
                            if eve_corp.corporation_ticker
                            else None
                        ),
                        status=status_str,
                        has_error=has_error,
                        error_message=error_message,
                        last_sync=corp_last_sync,
                        sections=[
                            schema.SettingsOwnerSectionSchema(
                                section=s.section,
                                section_name=s.section_name,
                                is_success=s.is_success,
                                has_token_error=s.has_token_error,
                                error_message=s.error_message,
                                last_run_at=s.last_run_at,
                                last_run_finished_at=s.last_run_finished_at,
                            )
                            for s in sections
                        ],
                    )
                )

            # Alliances are derived from the manageable corporations
            for alliance, syncs in alliance_syncs.items():
                synced = [s for s in syncs if s is not None]
                registered_list.append(
                    schema.SettingsOwnerSchema(
                        id=alliance.alliance_id,
                        name=alliance.alliance_name,
                        owner_type="alliance",
                        avatar_url=get_alliance_logo_url(alliance.alliance_id, 64),
                        subtitle=(
                            f"[{alliance.alliance_ticker}]"
                            if alliance.alliance_ticker
                            else None
                        ),
                        status="ok",
                        last_sync=max(synced) if synced else None,
                    )
                )

            # Missing list
            missing_list = [
                schema.SettingsMissingOwnerSchema(
                    id=char.character_id,
                    name=char.character_name,
                    avatar_url=_character_icon(char.character_id, char.character_name),
                    subtitle=char.corporation_name,
                )
                for char in missing_chars
            ]

            can_update = True
            cooldown_seconds = 0

            return schema.SettingsOwnersResponse(
                registered=registered_list,
                missing=missing_list,
                can_update=can_update,
                cooldown_seconds=cooldown_seconds,
            )

        @api.get(
            "settings/owners/{str:owner_type}/{int:owner_id}/unregistered/",
            response={
                HTTPStatus.OK: schema.SettingsUnregisteredResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="List members or corporations that are not registered in Ledger",
        )
        # pylint: disable=too-many-return-statements
        def get_settings_owner_unregistered(
            request: WSGIRequest, owner_type: str, owner_id: int
        ):
            user = request.user
            has_manage_access = General.has_management_access(user)
            if (
                not General.has_perm(user, General.Permission.BASIC_ACCESS)
                or not has_manage_access
            ):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "corporation":
                perm, owner = get_manage_corporation(request, owner_id)
                if owner is None:
                    if not General.has_admin_management_access(user):
                        return HTTPStatus.NOT_FOUND, {
                            "error": _("Corporation not found.")
                        }
                    if not EveCorporationInfo.objects.filter(
                        corporation_id=owner_id
                    ).exists():
                        return HTTPStatus.NOT_FOUND, {
                            "error": _("Corporation not found.")
                        }
                elif not perm and not General.has_admin_management_access(user):
                    return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

                registered_ids = CharacterOwner.objects.filter(
                    eve_character__corporation_id=owner_id
                ).values_list("eve_character__character_id", flat=True)
                characters = (
                    EveCharacter.objects.filter(corporation_id=owner_id)
                    .exclude(character_id__in=registered_ids)
                    .order_by("character_name")
                )
                items = [
                    schema.SettingsMissingOwnerSchema(
                        id=char.character_id,
                        name=char.character_name,
                        owner_type="character",
                        avatar_url=_character_icon(
                            char.character_id, char.character_name
                        ),
                        subtitle=char.corporation_name,
                    )
                    for char in characters
                ]
                return schema.SettingsUnregisteredResponse(
                    owner_type="corporation", owner_id=owner_id, items=items
                )

            if owner_type == "alliance":
                if not EveAllianceInfo.objects.filter(alliance_id=owner_id).exists():
                    return HTTPStatus.NOT_FOUND, {"error": _("Alliance not found.")}

                alliance_corps = CorporationOwner.objects.filter(
                    eve_corporation__alliance__alliance_id=owner_id
                )
                is_admin = General.has_admin_management_access(user)
                if not is_admin:
                    if not alliance_corps.intersection(
                        CorporationOwner.objects.manage_to(user)
                    ).exists():
                        return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

                registered_ids = alliance_corps.values_list(
                    "eve_corporation__corporation_id", flat=True
                )
                corporations = (
                    EveCorporationInfo.objects.filter(alliance__alliance_id=owner_id)
                    .exclude(corporation_id__in=registered_ids)
                    .order_by("corporation_name")
                )
                items = [
                    schema.SettingsMissingOwnerSchema(
                        id=corp.corporation_id,
                        name=corp.corporation_name,
                        owner_type="corporation",
                        avatar_url=get_corporation_logo_url(corp.corporation_id, 64),
                        subtitle=(
                            f"[{corp.corporation_ticker}]"
                            if corp.corporation_ticker
                            else None
                        ),
                    )
                    for corp in corporations
                ]
                return schema.SettingsUnregisteredResponse(
                    owner_type="alliance", owner_id=owner_id, items=items
                )

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}

        @api.post(
            "settings/owners/update-all/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.TOO_MANY_REQUESTS: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Trigger update for all user-owned characters and user-added corporations",
        )
        def trigger_update_all_settings_owners(request: WSGIRequest):
            user = request.user
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            # Update characters
            update_user_characters.apply_async(
                args=[user.id], kwargs={"force_refresh": False}
            )

            # Update only user's personally added corps (not via manage_to)
            user_corp_ids = _get_user_added_corporation_ids(user)
            corps = CorporationOwner.objects.filter(
                eve_corporation__corporation_id__in=user_corp_ids
            )
            for corp in corps:
                update_corporation.apply_async(
                    args=[corp.eve_corporation.corporation_id],
                    kwargs={"force_refresh": False},
                )

            return schema.MessageSchema(message=_("Update task queued for all owners."))

        @api.post(
            "settings/owners/{str:owner_type}/{int:owner_id}/update/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
                HTTPStatus.TOO_MANY_REQUESTS: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Trigger update for a single owner from settings",
        )
        # pylint: disable=too-many-return-statements
        def trigger_settings_owner_update(
            request: WSGIRequest, owner_type: str, owner_id: int
        ):
            user = request.user
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "character":
                perm, owner = get_characterowner_or_none(request, owner_id)
                if owner is None:
                    return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
                if not perm:
                    return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}
                update_character.apply_async(
                    args=[owner_id],
                    kwargs={"force_refresh": False, "update_alts": False},
                )
                return schema.MessageSchema(
                    message=_("Character update initiated successfully.")
                )

            if owner_type == "corporation":
                perm, owner = get_manage_corporation(request, owner_id)
                if owner is None:
                    return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}
                if not perm or not General.has_perm(
                    user, General.Permission.MANAGE_ACCESS
                ):
                    return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}
                update_corporation.apply_async(
                    args=[owner_id], kwargs={"force_refresh": False}
                )
                return schema.MessageSchema(
                    message=_("Corporation update initiated successfully.")
                )

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}

        @api.delete(
            "settings/owners/{str:owner_type}/{int:owner_id}/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Delete an owner from settings",
        )
        # pylint: disable=too-many-return-statements
        def delete_settings_owner(request: WSGIRequest, owner_type: str, owner_id: int):
            user = request.user
            if not General.has_perm(user, General.Permission.BASIC_ACCESS):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "character":
                perm, owner = get_characterowner_or_none(request, owner_id)
                if owner is None:
                    return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
                if not perm:
                    return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

                name = owner.eve_character.character_name
                owner.delete()
                return schema.MessageSchema(
                    message=_("%(name)s successfully deleted") % {"name": name}
                )

            if owner_type == "corporation":
                perm, owner = get_manage_corporation(request, owner_id)
                if owner is None:
                    return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}
                if not perm or not General.has_perm(
                    user, General.Permission.MANAGE_ACCESS
                ):
                    return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

                name = owner.eve_corporation.corporation_name
                owner.delete()
                return schema.MessageSchema(
                    message=_("%(name)s successfully deleted") % {"name": name}
                )

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}

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
                kwargs={
                    "eve_id": eve_id,
                    "force_refresh": force_refresh,
                    "update_alts": True,
                },
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
