from typing import List

from ninja import NinjaAPI

from django.db.models import Q

from ledger import app_settings
from ledger.api import schema
from ledger.api.helpers import get_alts_queryset, get_main_character

if app_settings.LEDGER_MEMBERAUDIT_USE:
    from memberaudit.models import CharacterWalletJournalEntry
else:
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry,
    )

from ledger.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class LedgerJournalApiEndpoints:
    tags = ["CharacerJournal"]

    def __init__(self, api: NinjaAPI):

        @api.get(
            "account/{character_id}/wallet/",
            response={200: List[schema.CharacterWalletEvent], 403: str},
            tags=self.tags,
        )
        def get_character_wallet(request, character_id: int):
            if character_id == 0:
                character_id = request.user.profile.main_character.character_id
            response, main = get_main_character(request, character_id)

            if not response:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            filters = (
                Q(character__eve_character__in=characters)
                if app_settings.LEDGER_MEMBERAUDIT_USE
                else Q(character__character__in=characters)
            )

            wallet_journal = CharacterWalletJournalEntry.objects.filter(
                filters
            ).select_related("first_party", "second_party")[:35000]
            output = []
            if wallet_journal:
                for w in wallet_journal:
                    output.append(
                        {
                            "character": (
                                w.character.character
                                if not app_settings.LEDGER_MEMBERAUDIT_USE
                                else w.character.eve_character
                            ),
                            "id": w.entry_id,
                            "date": w.date,
                            "first_party": {
                                "id": (
                                    w.first_party.eve_id
                                    if not app_settings.LEDGER_MEMBERAUDIT_USE
                                    else w.first_party.id
                                ),
                                "name": w.first_party.name,
                                "cat": w.first_party.category,
                            },
                            "second_party": {
                                "id": (
                                    w.second_party.eve_id
                                    if not app_settings.LEDGER_MEMBERAUDIT_USE
                                    else w.second_party.id
                                ),
                                "name": w.second_party.name,
                                "cat": w.second_party.category,
                            },
                            "ref_type": w.ref_type,
                            "amount": w.amount,
                            "balance": w.balance,
                            "reason": w.reason,
                        }
                    )

            return output
