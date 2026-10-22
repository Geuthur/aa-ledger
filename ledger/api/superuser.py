# Standard Library
from http import HTTPStatus
from typing import Literal

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__, tasks
from ledger.api import schema
from ledger.api.helpers.superuser import (
    build_character_inspection_response,
    build_corporation_inspection_response,
    build_superuser_owners_list,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import General
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

ADMIN_TASK_PRIORITY = 7


class ApiEndpoints:
    tags = ["Superuser"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "superuser/owners/",
            response={
                HTTPStatus.OK: list[schema.SuperuserOwnerSchema],
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="List all character and corporation owners for superuser administration",
        )
        def get_superuser_owners(request: WSGIRequest):
            if not General.has_management_access(request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            return build_superuser_owners_list(request.user)

        @api.post(
            "superuser/owners/{str:owner_type}/{int:owner_id}/update/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Queue update for a character or corporation owner",
        )
        def trigger_superuser_owner_update(
            request: WSGIRequest,
            owner_type: Literal["character", "corporation"],
            owner_id: int,
            payload: schema.SuperuserOwnerUpdateRequest,
        ):
            if not General.has_management_access(request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "character":
                owner = (
                    CharacterOwner.objects.manage_to(request.user)
                    .select_related("eve_character")
                    .filter(eve_character__character_id=owner_id)
                    .first()
                )
                if not owner:
                    return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}

                tasks.update_character.apply_async(
                    kwargs={
                        "eve_id": owner_id,
                        "force_refresh": payload.force_refresh,
                        "update_alts": True,
                    },
                    priority=ADMIN_TASK_PRIORITY,
                )
                return schema.MessageSchema(
                    message=_("Queued update for %(name)s")
                    % {"name": owner.eve_character.character_name}
                )

            if owner_type == "corporation":
                owner = (
                    CorporationOwner.objects.manage_to(request.user)
                    .select_related("eve_corporation")
                    .filter(eve_corporation__corporation_id=owner_id)
                    .first()
                )
                if not owner:
                    return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}

                tasks.update_corporation.apply_async(
                    kwargs={
                        "eve_id": owner_id,
                        "force_refresh": payload.force_refresh,
                    },
                    priority=ADMIN_TASK_PRIORITY,
                )
                return schema.MessageSchema(
                    message=_("Queued update for %(name)s")
                    % {"name": owner.eve_corporation.corporation_name}
                )

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}

        @api.delete(
            "superuser/owners/{str:owner_type}/{int:owner_id}/",
            response={
                HTTPStatus.OK: schema.MessageSchema,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Delete a character or corporation owner from ledger",
        )
        def delete_superuser_owner(
            request: WSGIRequest,
            owner_type: Literal["character", "corporation"],
            owner_id: int,
        ):
            if not General.has_delete_access(owner_type=owner_type, user=request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "character":
                owner = (
                    CharacterOwner.objects.manage_to(request.user)
                    .select_related("eve_character")
                    .filter(eve_character__character_id=owner_id)
                    .first()
                )
                if not owner:
                    return HTTPStatus.NOT_FOUND, {"error": _("Character not found.")}

                name = owner.eve_character.character_name
                owner.delete()
                return schema.MessageSchema(
                    message=_("%(name)s successfully deleted") % {"name": name}
                )

            if owner_type == "corporation":
                owner = (
                    CorporationOwner.objects.manage_to(request.user)
                    .select_related("eve_corporation")
                    .filter(eve_corporation__corporation_id=owner_id)
                    .first()
                )
                if not owner:
                    return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}

                name = owner.eve_corporation.corporation_name
                owner.delete()
                return schema.MessageSchema(
                    message=_("%(name)s successfully deleted") % {"name": name}
                )

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}

        @api.get(
            "superuser/owners/{str:owner_type}/{int:owner_id}/inspect/",
            response={
                HTTPStatus.OK: schema.AdministrationResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
                HTTPStatus.NOT_FOUND: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Inspect an owner administration view for superuser",
        )
        def inspect_superuser_owner(
            request: WSGIRequest,
            owner_type: Literal["character", "corporation"],
            owner_id: int,
        ):
            if not General.has_management_access(request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied.")}

            if owner_type == "character":
                return build_character_inspection_response(request.user, owner_id)

            if owner_type == "corporation":
                return build_corporation_inspection_response(request.user, owner_id)

            return HTTPStatus.NOT_FOUND, {"error": _("Invalid owner type.")}
