import logging
from typing import Any

from ninja import NinjaAPI

from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import UserProfile

from ledger.api import schema
from ledger.api.helpers import get_character
from ledger.models import CorporationAudit
from ledger.models.characteraudit import CharacterAudit

logger = logging.getLogger(__name__)


class LedgerAdminApiEndpoints:
    tags = ["LedgerAdmin"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/overview/",
            response={200: list[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_character_overview(request):
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
            "planetary/overview/",
            response={200: list[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_planetary_overview(request):
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
            "corporation/overview/",
            response={200: list[schema.CorporationAdmin], 403: str},
            tags=self.tags,
        )
        def get_corporation_overview(request):
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
            "alliance/overview/",
            response={200: list[schema.AllianceAdmin], 403: str},
            tags=self.tags,
        )
        def get_alliance_overview(request):
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

        @api.get(
            "character/{character_id}/view/dashboard/",
            response={200: Any, 403: str},
            tags=self.tags,
        )
        def get_character_dashboard(request, character_id: int):
            perms, character = get_character(request, character_id)

            if not perms:
                return 403, "Permission Denied"
            if perms is None:
                return 403, "Character not found"

            linked_characters = (
                character.character_ownership.user.character_ownerships.all()
            )
            linked_characters_ids = linked_characters.values_list(
                "character__character_id", flat=True
            )

            characters = CharacterAudit.objects.filter(
                character__character_id__in=linked_characters_ids
            )

            active_characters = characters.filter(active=True).count()
            inactive_characters = characters.filter(active=False).count()
            audit_total_characters = characters.count()
            missing_characters = len(linked_characters_ids) - audit_total_characters

            has_issues = False

            for char in characters:
                if not char.is_active():
                    has_issues = True

            if has_issues:
                status_msg = _("Please re-register issued characters")
            else:
                status_msg = _("All characters are up to date")

            output = {
                "dashboard": "Character Dashboard",
                "status": status_msg,
                "statistics": "Character Statistics",
                "auth_characters": len(linked_characters_ids),
                "active_characters": f"{active_characters} / {audit_total_characters}",
                "inactive_characters": inactive_characters,
                "missing_characters": missing_characters,
            }

            return output
