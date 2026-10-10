# Standard Library
from datetime import timedelta
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Max
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api import schema
from ledger.api.helpers.core import (
    get_all_corporations_from_alliance,
    get_alliance_or_none,
    get_characterowner_or_none,
    get_corporationowner_or_none,
    get_manage_corporation,
)
from ledger.app_settings import LEDGER_MANUAL_UPDATE_COOLDOWN
from ledger.helpers.eveonline import (
    get_alliance_logo_url,
    get_character_portrait_url,
    get_corporation_logo_url,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.providers import AppLogger
from ledger.tasks import update_user_characters

logger = AppLogger(get_extension_logger(__name__), __title__)

ERRORS = {
    HTTPStatus.FORBIDDEN: schema.ErrorSchema,
    HTTPStatus.NOT_FOUND: schema.ErrorSchema,
    HTTPStatus.TOO_MANY_REQUESTS: schema.ErrorSchema,
}


def _character_icon(character_id: int, character_name: str) -> str:
    return get_character_portrait_url(
        character_id=character_id, character_name=character_name, size=64
    )


class ApiEndpoints:
    """Registered owners of an account, corporation or alliance and their removal."""

    tags = ["Administration"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{int:character_id}/administration/",
            response={HTTPStatus.OK: schema.AdministrationResponse, **ERRORS},
            tags=self.tags,
            summary="Get the registered and missing characters of an account",
        )
        # pylint: disable=too-many-locals
        def get_character_administration(request: WSGIRequest, character_id: int):
            perm, owner = get_characterowner_or_none(request, character_id)

            if owner is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            characters = list(
                CharacterOwner.objects.filter(
                    eve_character__character_id__in=owner.alt_ids
                )
                .select_related("eve_character")
                .annotate(last_sync=Max("ledger_update_status__last_run_finished_at"))
                .order_by("eve_character__character_name")
            )
            registered_ids = [char.eve_character.character_id for char in characters]
            missing = EveCharacter.objects.filter(
                character_id__in=owner.alt_ids
            ).exclude(character_id__in=registered_ids)

            auth_count = len(owner.alt_ids)
            active_count = sum(1 for char in characters if char.active)
            inactive_count = len(characters) - active_count
            issues = [
                char.eve_character.character_name
                for char in characters
                if char.ledger_update_status.filter(is_success=False).exists()
            ]

            sync_times = [
                char.last_sync
                for char in characters
                if getattr(char, "last_sync", None) is not None
            ]
            account_last_sync = max(sync_times) if sync_times else None

            user_id = (
                owner.eve_character.character_ownership.user_id
                if owner.character_ownership
                else request.user.id
            )
            cache_key = f"aa_ledger_user_update_cooldown_{user_id}"
            cooldown_expiry = cache.get(cache_key)
            now = timezone.now()

            if cooldown_expiry and cooldown_expiry > now:
                can_update = False
                cooldown_seconds = int((cooldown_expiry - now).total_seconds())
            elif (
                account_last_sync
                and (now - account_last_sync).total_seconds()
                < LEDGER_MANUAL_UPDATE_COOLDOWN
            ):
                can_update = False
                cooldown_seconds = int(
                    LEDGER_MANUAL_UPDATE_COOLDOWN
                    - (now - account_last_sync).total_seconds()
                )
            else:
                can_update = True
                cooldown_seconds = 0

            return schema.AdministrationResponse(
                owner=schema.OwnerSchema(
                    character_id=character_id,
                    character_name=owner.eve_character.character_name,
                    icon=_character_icon(
                        character_id, owner.eve_character.character_name
                    ),
                ),
                dashboard=schema.DashboardSchema(
                    auth_count=auth_count,
                    active_count=active_count,
                    inactive_count=inactive_count,
                    missing_count=auth_count - len(characters),
                    issues=issues,
                ),
                registered=[
                    schema.AdminOwnerSchema(
                        owner_id=char.eve_character.character_id,
                        name=char.eve_character.character_name,
                        icon=_character_icon(
                            char.eve_character.character_id,
                            char.eve_character.character_name,
                        ),
                        status=char.get_status,
                        last_sync=char.last_sync,
                    )
                    for char in characters
                ],
                missing=[
                    schema.AdminOwnerSchema(
                        owner_id=char.character_id,
                        name=char.character_name,
                        icon=_character_icon(char.character_id, char.character_name),
                    )
                    for char in missing.order_by("character_name")
                ],
                last_sync=account_last_sync,
                can_update=can_update,
                cooldown_seconds=cooldown_seconds,
            )

        @api.post(
            "character/{int:character_id}/update/",
            response={HTTPStatus.OK: schema.MessageSchema, **ERRORS},
            tags=self.tags,
            summary="Queue an update for all characters of the user owning this character",
        )
        def trigger_character_update(request: WSGIRequest, character_id: int):
            perm, owner = get_characterowner_or_none(request, character_id)

            if owner is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            user_id = (
                owner.eve_character.character_ownership.user_id
                if owner.character_ownership
                else request.user.id
            )

            characters = list(
                CharacterOwner.objects.filter(
                    eve_character__character_id__in=owner.alt_ids
                ).annotate(last_sync=Max("ledger_update_status__last_run_finished_at"))
            )
            sync_times = [
                char.last_sync
                for char in characters
                if getattr(char, "last_sync", None) is not None
            ]
            account_last_sync = max(sync_times) if sync_times else None

            cache_key = f"aa_ledger_user_update_cooldown_{user_id}"
            cooldown_expiry = cache.get(cache_key)
            now = timezone.now()

            remaining_cooldown = 0
            if cooldown_expiry and cooldown_expiry > now:
                remaining_cooldown = int((cooldown_expiry - now).total_seconds())
            elif (
                account_last_sync
                and (now - account_last_sync).total_seconds()
                < LEDGER_MANUAL_UPDATE_COOLDOWN
            ):
                remaining_cooldown = int(
                    LEDGER_MANUAL_UPDATE_COOLDOWN
                    - (now - account_last_sync).total_seconds()
                )

            if remaining_cooldown > 0:
                return HTTPStatus.TOO_MANY_REQUESTS, {
                    "error": _(
                        "Update is on cooldown. Please wait %(seconds)d seconds."
                    )
                    % {"seconds": remaining_cooldown}
                }

            cache.set(
                cache_key,
                now + timedelta(seconds=LEDGER_MANUAL_UPDATE_COOLDOWN),
                timeout=LEDGER_MANUAL_UPDATE_COOLDOWN,
            )
            update_user_characters.apply_async(
                args=[user_id], kwargs={"force_refresh": True}
            )
            return schema.MessageSchema(
                message=_("Character update initiated successfully.")
            )

        @api.delete(
            "character/{int:character_id}/",
            response={HTTPStatus.OK: schema.MessageSchema, **ERRORS},
            tags=self.tags,
            summary="Remove a character from the ledger",
        )
        def delete_character(request: WSGIRequest, character_id: int):
            perm, owner = get_characterowner_or_none(request, character_id)

            if owner is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            name = owner.eve_character.character_name
            owner.delete()
            return schema.MessageSchema(
                message=_("%(name)s successfully deleted") % {"name": name}
            )

        @api.get(
            "corporation/{int:corporation_id}/administration/",
            response={HTTPStatus.OK: schema.AdministrationResponse, **ERRORS},
            tags=self.tags,
            summary="Get the registration and members of a corporation",
        )
        def get_corporation_administration(request: WSGIRequest, corporation_id: int):
            perm, owner = get_corporationowner_or_none(request, corporation_id)

            if owner is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            corporation = owner.eve_corporation
            members = list(
                CharacterOwnership.objects.filter(
                    character__corporation_id=corporation.corporation_id
                )
                .select_related("character")
                .order_by("character__character_name")
            )
            auth_count = EveCorporationInfo.objects.get(
                corporation_id=corporation.corporation_id
            ).member_count

            registered_ids = set(
                CharacterOwner.objects.filter(
                    eve_character__corporation_id=corporation.corporation_id
                ).values_list("eve_character__character_id", flat=True)
            )

            missing_characters = [
                member.character
                for member in members
                if member.character.character_id not in registered_ids
            ]

            corp_last_sync = owner.ledger_corporation_update_status.aggregate(
                latest=Max("last_run_finished_at")
            )["latest"]

            return schema.AdministrationResponse(
                owner=schema.OwnerSchema(
                    character_id=corporation.corporation_id,
                    character_name=corporation.corporation_name,
                    icon=get_corporation_logo_url(
                        corporation_id=corporation.corporation_id,
                        corporation_name=corporation.corporation_name,
                        size=64,
                    ),
                ),
                dashboard=schema.DashboardSchema(
                    auth_count=auth_count,
                    active_count=len(members),
                    missing_count=auth_count - len(members),
                ),
                registered=[
                    schema.AdminOwnerSchema(
                        owner_id=corporation.corporation_id,
                        name=corporation.corporation_name,
                        icon=get_corporation_logo_url(
                            corporation_id=corporation.corporation_id,
                            corporation_name=corporation.corporation_name,
                            size=64,
                        ),
                        status=owner.get_status,
                        last_sync=corp_last_sync,
                    )
                ],
                last_sync=corp_last_sync,
                missing=[
                    schema.AdminOwnerSchema(
                        owner_id=char.character_id,
                        name=char.character_name,
                        icon=_character_icon(
                            char.character_id,
                            char.character_name,
                        ),
                    )
                    for char in missing_characters
                ],
                members=[
                    schema.AltSchema(
                        character_id=member.character.character_id,
                        character_name=member.character.character_name,
                        icon=_character_icon(
                            member.character.character_id,
                            member.character.character_name,
                        ),
                        is_registered=member.character.character_id in registered_ids,
                    )
                    for member in members
                ],
            )

        @api.delete(
            "corporation/{int:corporation_id}/",
            response={HTTPStatus.OK: schema.MessageSchema, **ERRORS},
            tags=self.tags,
            summary="Remove a corporation from the ledger",
        )
        def delete_corporation(request: WSGIRequest, corporation_id: int):
            perm, owner = get_manage_corporation(request, corporation_id)

            if owner is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}
            if not perm or not request.user.has_perm("ledger.manage_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            name = owner.eve_corporation.corporation_name
            owner.delete()
            return schema.MessageSchema(
                message=_("%(name)s successfully deleted") % {"name": name}
            )

        @api.get(
            "alliance/{int:alliance_id}/administration/",
            response={HTTPStatus.OK: schema.AdministrationResponse, **ERRORS},
            tags=self.tags,
            summary="Get the registered and missing corporations of an alliance",
        )
        def get_alliance_administration(request: WSGIRequest, alliance_id: int):
            perm, alliance = get_alliance_or_none(request, alliance_id)

            if alliance is None:
                return HTTPStatus.NOT_FOUND, {"error": _("Alliance not found.")}
            if not perm:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            corps_tuple = get_all_corporations_from_alliance(request, alliance_id)
            corps_qs = corps_tuple[1] if corps_tuple else None
            if corps_qs is None:
                corporations = CorporationOwner.objects.none()
            else:
                corporations = corps_qs.select_related("eve_corporation").annotate(
                    last_sync=Max(
                        "ledger_corporation_update_status__last_run_finished_at"
                    )
                )
            all_corporations = EveCorporationInfo.objects.filter(
                alliance__alliance_id=alliance_id
            )
            registered_ids = corporations.values_list(
                "eve_corporation__corporation_id", flat=True
            )
            missing = all_corporations.exclude(
                corporation_id__in=registered_ids
            ).order_by("corporation_name")

            auth_count = all_corporations.count()
            active_count = corporations.count()

            return schema.AdministrationResponse(
                owner=schema.OwnerSchema(
                    character_id=alliance.alliance_id,
                    character_name=alliance.alliance_name,
                    icon=get_alliance_logo_url(
                        alliance_id=alliance.alliance_id,
                        alliance_name=alliance.alliance_name,
                        size=64,
                    ),
                ),
                dashboard=schema.DashboardSchema(
                    auth_count=auth_count,
                    active_count=active_count,
                    missing_count=auth_count - active_count,
                ),
                registered=[
                    schema.AdminOwnerSchema(
                        owner_id=corporation.eve_corporation.corporation_id,
                        name=corporation.eve_corporation.corporation_name,
                        icon=get_corporation_logo_url(
                            corporation_id=corporation.eve_corporation.corporation_id,
                            corporation_name=corporation.eve_corporation.corporation_name,
                            size=64,
                        ),
                        status=corporation.get_status,
                        last_sync=getattr(corporation, "last_sync", None),
                    )
                    for corporation in corporations.order_by(
                        "eve_corporation__corporation_name"
                    )
                ],
                missing=[
                    schema.AdminOwnerSchema(
                        owner_id=corporation.corporation_id,
                        name=corporation.corporation_name,
                        icon=get_corporation_logo_url(
                            corporation_id=corporation.corporation_id,
                            corporation_name=corporation.corporation_name,
                            size=64,
                        ),
                    )
                    for corporation in missing
                ],
            )
