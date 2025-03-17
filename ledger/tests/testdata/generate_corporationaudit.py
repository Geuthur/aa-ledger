from django.contrib.auth.models import User

from allianceauth.eveonline.models import EveCharacter

from ledger.models.corporationaudit import CorporationAudit
from ledger.tests.testdata.generate_characteraudit import add_auth_character_to_user


def create_corporationaudit_from_evecharacter(
    eve_character: EveCharacter, **kwargs
) -> CorporationAudit:
    """Create a LedgerAudit Corporation from EveCharacter"""
    params = {
        "corporation_name": eve_character.corporation_name,
        "corporation": eve_character.corporation,
    }
    params.update(kwargs)
    corporation = CorporationAudit(**params)
    corporation.save()
    return corporation


def add_charactermaudit_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True, **kwargs
) -> CorporationAudit:
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_corporationaudit_from_evecharacter(
        character_ownership.character, **kwargs
    )
