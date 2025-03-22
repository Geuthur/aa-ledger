from django.contrib.auth.models import User
from eveuniverse.models import EveType

from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testing import add_character_to_user

from ledger.models.characteraudit import CharacterAudit


def create_character(eve_character: EveCharacter, **kwargs) -> CharacterAudit:
    """Create a Skillfarm Character from EveCharacter"""
    params = {
        "character_name": eve_character.character_name,
        "character": eve_character,
    }
    params.update(kwargs)
    character = CharacterAudit(**params)
    character.save()
    return character


def create_user_from_evecharacter_with_access(
    character_id: int, disconnect_signals: bool = True
) -> tuple[User, CharacterOwnership]:
    """Create user with access from an existing eve character and use it as main."""
    auth_character = EveCharacter.objects.get(character_id=character_id)
    username = StateBackend.iterate_username(auth_character.character_name)
    user = AuthUtils.create_user(username, disconnect_signals=disconnect_signals)
    user = AuthUtils.add_permission_to_user_by_name(
        "ledger.basic_access", user, disconnect_signals=disconnect_signals
    )
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=CharacterAudit.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )
    return user, character_ownership


def create_characteraudit_character(character_id: int, **kwargs) -> CharacterAudit:
    """Create a Audit Character from a existing EveCharacter"""

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_character(character_ownership.character, **kwargs)


def add_auth_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True
) -> CharacterOwnership:
    auth_character = EveCharacter.objects.get(character_id=character_id)
    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=CharacterAudit.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )


def add_charactermaudit_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True, **kwargs
) -> CharacterAudit:
    """Add a Character Audit Character to a user"""
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_character(character_ownership.character, **kwargs)
