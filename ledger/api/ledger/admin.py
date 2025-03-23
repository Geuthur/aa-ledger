import logging

from ninja import NinjaAPI

from allianceauth.authentication.models import UserProfile

from ledger.api import schema
from ledger.models import CorporationAudit
from ledger.models.characteraudit import CharacterAudit

logger = logging.getLogger(__name__)


class LedgerAdminApiEndpoints:
    tags = ["LedgerAdmin"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/ledger/admin/",
            response={200: list[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_character_admin(request):
            chars_visible = CharacterAudit.objects.visible_eve_characters(request.user)

            if chars_visible is None:
                return 403, "Permission Denied"

            chars_ids = chars_visible.values_list("character_id", flat=True)

            users_char_ids = UserProfile.objects.filter(
                main_character__isnull=False, main_character__character_id__in=chars_ids
            )

            character_dict = {}

            for character in users_char_ids:
                # pylint: disable=broad-exception-caught
                try:
                    character_dict[character.main_character.character_id] = {
                        "character_id": character.main_character.character_id,
                        "character_name": character.main_character.character_name,
                        "corporation_id": character.main_character.corporation_id,
                        "corporation_name": character.main_character.corporation_name,
                    }
                except AttributeError:
                    continue

            output = []
            output.append({"character": character_dict})

            return output

        @api.get(
            "character/planetary/admin/",
            response={200: list[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_planetary_admin(request):
            chars_ids = CharacterAudit.objects.visible_eve_characters(
                request.user
            ).values_list("character_id", flat=True)

            users_char_ids = UserProfile.objects.filter(
                main_character__isnull=False, main_character__character_id__in=chars_ids
            )

            if not chars_ids:
                return 403, "Permission Denied"

            character_dict = {}

            for character in users_char_ids:
                # pylint: disable=broad-exception-caught
                try:
                    character_dict[character.main_character.character_id] = {
                        "character_id": character.main_character.character_id,
                        "character_name": character.main_character.character_name,
                        "corporation_id": character.main_character.corporation_id,
                        "corporation_name": character.main_character.corporation_name,
                    }
                except Exception:
                    continue

            output = []
            output.append({"character": character_dict})

            return output

        @api.get(
            "corporation/ledger/admin/",
            response={200: list[schema.CorporationAdmin], 403: str},
            tags=self.tags,
        )
        def get_corporation_admin(request):
            corporations = CorporationAudit.objects.visible_to(request.user)

            if corporations is None:
                return 403, "Permission Denied"

            corporation_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    corporation_dict[corporation.corporation.corporation_id] = {
                        "corporation_id": corporation.corporation.corporation_id,
                        "corporation_name": corporation.corporation.corporation_name,
                    }
                except Exception:
                    continue

            output = []
            output.append({"corporation": corporation_dict})

            return output

        @api.get(
            "alliance/ledger/admin/",
            response={200: list[schema.AllianceAdmin], 403: str},
            tags=self.tags,
        )
        def get_alliance_admin(request):
            corporations = CorporationAudit.objects.visible_to(request.user)

            if corporations is None:
                return 403, "Permission Denied"

            alliance_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    alliance_dict[corporation.corporation.alliance.alliance_id] = {
                        "alliance_id": corporation.corporation.alliance.alliance_id,
                        "alliance_name": corporation.corporation.alliance.alliance_name,
                    }
                except Exception:
                    continue
            output = []
            output.append({"alliance": alliance_dict})

            return output
