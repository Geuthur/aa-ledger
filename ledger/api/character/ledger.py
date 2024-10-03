from ninja import NinjaAPI

from allianceauth.authentication.models import UserProfile

from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_character
from ledger.api.managers.character_manager import CharacterProcess
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit

logger = get_extension_logger(__name__)


# pylint: disable=duplicate-code
class LedgerApiEndpoints:
    tags = ["CharacerLedger"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/ledger/year/{year}/month/{month}/",
            response={200: list[schema.Ledger], 403: str},
            tags=self.tags,
        )
        def get_character_ledger(request, character_id: int, year: int, month: int):
            request_main = request.GET.get("main", False)
            perm, main = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            # Create the Ledger
            if character_id == 0 or request_main:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            ledger = CharacterProcess(characters, year, month)
            output = ledger.generate_ledger()

            return output

        @api.get(
            "account/{character_id}/billboard/year/{year}/month/{month}/",
            response={200: list[schema.Billboard], 403: str},
            tags=self.tags,
        )
        def get_billboard_ledger(request, character_id: int, year: int, month: int):
            request_main = request.GET.get("main", False)
            perm, main = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            # Create the Ledger
            if character_id == 0 or request_main:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            ledger = CharacterProcess(characters, year, month)
            output = ledger.generate_billboard()

            return output

        @api.get(
            "account/ledger/admin/",
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
