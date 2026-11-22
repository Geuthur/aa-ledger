# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile

# AA Ledger
from ledger.api import schema
from ledger.helpers.eveonline import (
    get_alliance_logo_url,
    get_character_portrait_url,
    get_corporation_logo_url,
)
from ledger.models.characteraudit import CharacterOwner
from ledger.models.corporationaudit import CorporationOwner
from ledger.models.general import General


class ApiEndpoints:
    tags = ["LedgerAdmin"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "overview/",
            response={
                HTTPStatus.OK: schema.LedgerOverviewResponse,
                HTTPStatus.FORBIDDEN: schema.ErrorSchema,
            },
            tags=self.tags,
            summary="Get unified overview of all owners (characters, corporations, alliances) visible to user",
        )
        def get_overview(request: WSGIRequest):
            user = request.user
            owners: list[schema.LedgerOverviewOwnerSchema] = []

            # 1. Characters
            chars_ids = CharacterOwner.objects.visible_to(user).values_list(
                "eve_character__character_id", flat=True
            )
            planetary_char_ids = set(
                CharacterOwner.objects.visible_eve_characters(user).values_list(
                    "character_id", flat=True
                )
            )
            can_manage = General.objects.has_manage_access(user)

            profiles = (
                UserProfile.objects.filter(
                    main_character__isnull=False,
                    main_character__character_id__in=chars_ids,
                )
                .select_related("main_character")
                .order_by("main_character__character_name")
            )
            char_error_ids = set(
                CharacterOwner.objects.filter(
                    ledger_update_status__is_success=False
                ).values_list("eve_character__character_id", flat=True)
            )

            for profile in profiles:
                char = profile.main_character
                owners.append(
                    schema.LedgerOverviewOwnerSchema(
                        id=char.character_id,
                        name=char.character_name,
                        type="character",
                        type_display=str(_("Character")),
                        portrait_url=get_character_portrait_url(char.character_id, 64),
                        subtitle=char.corporation_name,
                        active=True,
                        has_planetary=(char.character_id in planetary_char_ids),
                        can_manage=can_manage or (profile.user_id == user.id),
                        has_errors=(char.character_id in char_error_ids),
                    )
                )

            # 2. Corporations & Alliances
            if General.objects.has_advanced_access(user):
                corps = (
                    CorporationOwner.objects.visible_to(user)
                    .select_related("eve_corporation", "eve_corporation__alliance")
                    .order_by("eve_corporation__corporation_name")
                )
                corp_error_ids = set(
                    CorporationOwner.objects.filter(
                        ledger_corporation_update_status__is_success=False
                    ).values_list("eve_corporation__corporation_id", flat=True)
                )
                alliances_dict = {}
                for corp in corps:
                    eve_corp = corp.eve_corporation
                    owners.append(
                        schema.LedgerOverviewOwnerSchema(
                            id=eve_corp.corporation_id,
                            name=eve_corp.corporation_name,
                            type="corporation",
                            type_display=str(_("Corporation")),
                            portrait_url=get_corporation_logo_url(
                                eve_corp.corporation_id, 64
                            ),
                            subtitle=(
                                eve_corp.alliance.alliance_name
                                if eve_corp.alliance
                                else None
                            ),
                            active=True,
                            has_planetary=False,
                            can_manage=can_manage,
                            has_errors=(eve_corp.corporation_id in corp_error_ids),
                        )
                    )
                    if eve_corp.alliance:
                        alliances_dict[eve_corp.alliance.alliance_id] = (
                            eve_corp.alliance
                        )

                for ally in sorted(
                    alliances_dict.values(), key=lambda a: a.alliance_name.lower()
                ):
                    owners.append(
                        schema.LedgerOverviewOwnerSchema(
                            id=ally.alliance_id,
                            name=ally.alliance_name,
                            type="alliance",
                            type_display=str(_("Alliance")),
                            portrait_url=get_alliance_logo_url(ally.alliance_id, 64),
                            subtitle=None,
                            active=True,
                            has_planetary=False,
                            can_manage=can_manage,
                        )
                    )

            return schema.LedgerOverviewResponse(owners=owners)
