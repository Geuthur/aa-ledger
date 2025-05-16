# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA Ledger
from ledger.models.corporationaudit import CorporationAudit, CorporationUpdateStatus
from ledger.tests.testdata.generate_characteraudit import (
    add_auth_character_to_user,
    create_user_from_evecharacter_with_access,
)


def create_corporationaudit(eve_character: EveCharacter, **kwargs) -> CorporationAudit:
    """Create a LedgerAudit Corporation from EveCharacter"""
    params = {
        "corporation_name": eve_character.corporation_name,
        "corporation": eve_character.corporation,
    }
    params.update(kwargs)
    corporation = CorporationAudit(**params)
    corporation.save()
    return corporation


def create_corporation_update_status(
    corporation_audit: CorporationAudit, **kwargs
) -> CorporationUpdateStatus:
    """Create a Update Status for a Character Audit"""
    params = {
        "corporation": corporation_audit,
    }
    params.update(kwargs)
    update_status = CorporationUpdateStatus(**params)
    update_status.save()
    return update_status


def create_corporationaudit_from_user(user: User, **kwargs) -> CorporationAudit:
    """Create a Character Audit from a user"""
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    kwargs.update({"eve_character": eve_character})
    return create_corporationaudit(**kwargs)


def create_corporationaudit_from_evecharacter(
    character_id: int, **kwargs
) -> CorporationAudit:
    """Create a Audit Character from a existing EveCharacter"""

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_corporationaudit(character_ownership.character, **kwargs)


def add_corporationaudit_corporation_to_user(
    user: User, character_id: int, disconnect_signals: bool = True, **kwargs
) -> CorporationAudit:
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_corporationaudit(character_ownership.character, **kwargs)
