# Standard Library
import datetime as dt
import random
import string

# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Scope, Token

# Alliance Auth (External Libs)
from eve_sde.models.map import Planet, SolarSystem
from eve_sde.models.types import ItemType

# AA Ledger
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterOwner,
    CharacterUpdateStatus,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import (
    CorporationOwner,
    CorporationUpdateStatus,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)
from ledger.models.general import EveEntity
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails


def dt_eveformat(my_dt: dt.datetime) -> str:
    """Convert datetime to EVE Online ISO format (YYYY-MM-DDTHH:MM:SS)

    Args:
        my_dt (datetime): Input datetime
    Returns:
        str: datetime in EVE Online ISO format
    """

    my_dt_2 = dt.datetime(
        my_dt.year, my_dt.month, my_dt.day, my_dt.hour, my_dt.minute, my_dt.second
    )

    return my_dt_2.isoformat()


def random_string(char_count: int) -> str:
    """returns a random string of given length"""
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(char_count)
    )


def _generate_token(
    character_id: int,
    character_name: str,
    owner_hash: str | None = None,
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    scopes: list | None = None,
    timestamp_dt: dt.datetime | None = None,
    expires_in: int = 1200,
) -> dict:
    """Generates the input to create a new SSO test token.

    Args:
        character_id (int): Character ID
        character_name (str): Character Name
        owner_hash (Optional[str], optional): Character Owner Hash. Defaults to None.
        access_token (str, optional): Access Token string. Defaults to "access_token".
        refresh_token (str, optional): Refresh Token string. Defaults to "refresh_token".
        scopes (Optional[list], optional): List of scope names. Defaults to None.
        timestamp_dt (Optional[dt.datetime], optional): Timestamp datetime. Defaults to None.
        expires_in (int, optional): Expiry time in seconds. Defaults to 1200
    Returns:
        dict: The generated token dict
    """
    if timestamp_dt is None:
        timestamp_dt = dt.datetime.utcnow()
    if scopes is None:
        scopes = [
            "esi-mail.read_mail.v1",
            "esi-wallet.read_character_wallet.v1",
            "esi-universe.read_structures.v1",
        ]
    if owner_hash is None:
        owner_hash = random_string(28)
    token = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "timestamp": int(timestamp_dt.timestamp()),
        "CharacterID": character_id,
        "CharacterName": character_name,
        "ExpiresOn": dt_eveformat(timestamp_dt + dt.timedelta(seconds=expires_in)),
        "Scopes": " ".join(list(scopes)),
        "TokenType": "Character",
        "CharacterOwnerHash": owner_hash,
        "IntellectualProperty": "EVE",
    }
    return token


def _store_as_Token(token: dict, user: object) -> Token:
    """Stores a generated token dict as Token object for given user

    Args:
        token (dict): Generated token dict
        user (User): Alliance Auth User
    Returns:
        Token: The created Token object
    """
    character_tokens = user.token_set.filter(character_id=token["CharacterID"])
    if character_tokens.exists():
        token["CharacterOwnerHash"] = character_tokens.first().character_owner_hash
    obj = Token.objects.create(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        user=user,
        character_id=token["CharacterID"],
        character_name=token["CharacterName"],
        token_type=token["TokenType"],
        character_owner_hash=token["CharacterOwnerHash"],
    )
    for scope_name in token["Scopes"].split(" "):
        scope, _ = Scope.objects.get_or_create(name=scope_name)
        obj.scopes.add(scope)
    return obj


def add_new_token(
    user: User,
    character: EveCharacter,
    scopes: list[str] | None = None,
    owner_hash: str | None = None,
) -> Token:
    """Generate a new token for a user based on a character and makes the given user it's owner.

    Args:
        user: Alliance Auth User
        character: EveCharacter to create the token for
        scopes: list of scope names
        owner_hash: optional owner hash to use for the token
    Returns:
        Token: The created Token object
    """
    return _store_as_Token(
        _generate_token(
            character_id=character.character_id,
            character_name=character.character_name,
            owner_hash=owner_hash,
            scopes=scopes,
        ),
        user,
    )


def add_character_to_user(
    user: User,
    character: EveCharacter,
    is_main: bool = False,
    scopes: list[str] | None = None,
    disconnect_signals: bool = False,
) -> CharacterOwnership:
    """Add an existing :class:`EveCharacter` to a User, optionally as main character.

    Args:
        user (User): The User to whom the EveCharacter will be added.
        character (EveCharacter): The EveCharacter to add to the User.
        is_main (bool, optional): Whether to set the EveCharacter as the User's main
            character. Defaults to ``False``.
        scopes (list[str] | None, optional): List of scope names to assign to the
            character's token. If ``None``, defaults to `["publicData"]`. Defaults to ``None``.
        disconnect_signals (bool, optional): Whether to disconnect signals during
            the addition. Defaults to ``False``.
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """

    if not scopes:
        scopes = ["publicData"]

    if disconnect_signals:
        AuthUtils.disconnect_signals()

    add_new_token(user, character, scopes)

    if is_main:
        user.profile.main_character = character
        user.profile.save()
        user.save()

    if disconnect_signals:
        AuthUtils.connect_signals()

    return CharacterOwnership.objects.get(user=user, character=character)


def create_user_from_evecharacter(
    character_id: int,
    permissions: list[str] | None = None,
    scopes: list[str] | None = None,
) -> tuple[User, CharacterOwnership]:
    """Create new allianceauth user from EveCharacter object.

    Args:
        character_id (int): ID of eve character
        permissions (list[str] | None): list of permission names, e.g. `"my_app.my_permission"`
        scopes (list[str] | None): list of scope names
    Returns:
        tuple(User, CharacterOwnership): Created Alliance Auth User and CharacterOwnership
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    user = AuthUtils.create_user(auth_character.character_name.replace(" ", "_"))
    character_ownership = add_character_to_user(
        user, auth_character, is_main=True, scopes=scopes
    )
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
    return user, character_ownership


def add_permission_to_user(
    user: User,
    permissions: list[str] | None = None,
) -> User:
    """Add permission to existing allianceauth user.
    Args:
        user (User): Alliance Auth User
        permissions (list[str] | None): list of permission names, e.g. `"my_app.my_permission"`
    Returns:
        User: Updated Alliance Auth User
    """
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
            return user
    raise ValueError("No permissions provided to add to user.")


def create_ledger_owner(
    eve_character: EveCharacter, owner_type="character", **kwargs
) -> CharacterOwner | CorporationOwner:
    """
    Create a Ledger Owner (CharacterOwner or CorporationOwner) from an EveCharacter.
    The type of owner created depends on the owner_type parameter.
    Args:
        eve_character (EveCharacter): The EveCharacter to create the owner from.
        owner_type (str, optional): Type of owner, either "character" or "corporation"
    Returns:
        (CharacterOwner or CorporationOwner): The created ledger owner.

    """
    if owner_type == "character":
        defaults = {
            "character_name": eve_character.character_name,
        }
        defaults.update(kwargs)
        owner = CharacterOwner.objects.get_or_create(
            eve_character=eve_character,
            defaults=defaults,
        )[0]
        return owner
    if owner_type == "corporation":
        defaults = {
            "corporation_name": eve_character.corporation.corporation_name,
        }
        defaults.update(kwargs)
        owner = CorporationOwner.objects.get_or_create(
            eve_corporation=eve_character.corporation,
            defaults=defaults,
        )[0]
        return owner
    raise ValueError("owner_type must be either 'character' or 'corporation'")


def create_update_status(
    owner: CharacterOwner,
    section: str,
    error_message="",
    owner_type="character",
    **kwargs,
) -> CharacterUpdateStatus | CorporationUpdateStatus:
    """
    Create an Update Status for a CharacterOwner or CorporationOwner.
    The type of update status created depends on the owner_type parameter.

    Args:
        owner (CharacterOwner | CorporationOwner): The owner for whom to create the update status.
        section (str): The section for the update status.
        error_message (str, optional): The error message for the update status.
        tax_type (str, optional): Type of tax owner, either "corporation" or "alliance"
        **kwargs: Additional fields for the Update Status
    Returns:
        (CharacterUpdateStatus or CorporationUpdateStatus): The created update status.
    """
    params = {
        "owner": owner,
        "section": section,
        "error_message": error_message,
    }
    params.update(kwargs)
    if owner_type == "corporation":
        update_status = CorporationUpdateStatus(**params)
    else:
        update_status = CharacterUpdateStatus(**params)
    update_status.save()
    return update_status


def create_owner_from_user(
    user: User, owner_type="character", **kwargs
) -> CharacterOwner | CorporationOwner:
    """
    Create a CharacterOwner or CorporationOwner from a user.
    The type of owner created depends on the owner_type parameter.

    Args:
        user (User): The user to create the owner from.
        owner_type (str): Type of owner, either "character" or "corporation"
    """
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    return create_ledger_owner(eve_character, owner_type=owner_type, **kwargs)


def create_owner_from_evecharacter(
    character_id: int, owner_type="character", **kwargs
) -> CharacterOwner | CorporationOwner:
    """
    Create a CharacterOwner or CorporationOwner from an existing EveCharacter.
    The type of owner created depends on the owner_type parameter.

    Args:
        character_id (int): ID of the EveCharacter to create the owner from.
        owner_type (str): Type of owner, either "character" or "corporation"
    Returns:
        CharacterOwner | CorporationOwner: The created ledger owner.
    """

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_ledger_owner(
        character_ownership.character, owner_type=owner_type, **kwargs
    )


def create_user_from_evecharacter_with_access(
    character_id: int, disconnect_signals: bool = True, owner_type="character"
) -> tuple[User, CharacterOwnership]:
    """
    Create user with basic access from an existing EveCharacter and use it as main.

    Args:
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during user creation. Defaults to True.
        owner_type (str, optional): Type of owner, either "character" or "corporation"
    Returns:
        tuple(User, CharacterOwnership): Created Alliance Auth User and CharacterOwnership
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    username = StateBackend.iterate_username(auth_character.character_name)
    user = AuthUtils.create_user(username, disconnect_signals=disconnect_signals)
    user = AuthUtils.add_permission_to_user_by_name(
        "ledger.basic_access", user, disconnect_signals=disconnect_signals
    )

    if owner_type == "character":
        scopes = CharacterOwner.get_esi_scopes()
    else:
        scopes = CorporationOwner.get_esi_scopes()

    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=scopes,
        disconnect_signals=disconnect_signals,
    )
    return user, character_ownership


def add_new_permission_to_user(
    user: User,
    permission_name: str,
    disconnect_signals: bool = True,
) -> User:
    """Add a new permission to an existing allianceauth user.

    Args:
        user (User): Alliance Auth User
        permission_name (str): Permission name, e.g. `"my_app.my_permission"`
        disconnect_signals (bool, optional): Whether to disconnect signals during addition. Defaults to True.
    Returns:
        User: Updated Alliance Auth User
    """
    return AuthUtils.add_permission_to_user_by_name(
        permission_name, user, disconnect_signals=disconnect_signals
    )


def add_auth_character_to_user(
    user: User,
    character_id: int,
    disconnect_signals: bool = True,
    owner_type="character",
) -> CharacterOwnership:
    """Add an existing :class:`EveCharacter` to a User.

    Args:
        user (User): Alliance Auth User
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during addition. Defaults to True.
        owner_type (str, optional): Type of owner, either "character" or "corporation"
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)

    if owner_type == "character":
        scopes = CharacterOwner.get_esi_scopes()
    else:
        scopes = CorporationOwner.get_esi_scopes()

    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=scopes,
        disconnect_signals=disconnect_signals,
    )


def add_owner_to_user(
    user: User,
    character_id: int,
    disconnect_signals: bool = True,
    owner_type="character",
    **kwargs,
) -> CharacterOwner | CorporationOwner:
    """
    Add a CharacterOwner or CorporationOwner character to a user.
    The type of owner created depends on the owner_type parameter.

    Args:
        user (User): Alliance Auth User
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during addition. Defaults to True.
        owner_type (str): Type of owner, either "character" or "corporation"
    Returns:
        CharacterOwner | CorporationOwner: The created owner.
    """
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_ledger_owner(
        character_ownership.character, owner_type=owner_type, **kwargs
    )


def create_miningledger(
    character: CharacterOwner,
    id: int,
    date: str,
    type: ItemType,
    system: SolarSystem,
    quantity: int,
    **kwargs,
) -> CharacterMiningLedger:
    """
    Create a CharacterMiningLedger

    Args:
        character (CharacterOwner): The character.
        id (int): The ID of the mining ledger.
        date (str): The date of the mining ledger.
        type (ItemType): The type of the mined item.
        system (EveSolarSystem): The solar system where mining took place.
        quantity (int): The quantity mined.
        **kwargs: Fields for the CharacterMiningLedger
    Returns:
        CharacterMiningLedger: The created mining ledger.
    """
    params = {
        "character": character,
        "id": id,
        "date": date,
        "type": type,
        "system": system,
        "quantity": quantity,
    }
    params.update(kwargs)
    mining_ledger = CharacterMiningLedger(**params)
    mining_ledger.save()
    return mining_ledger


def create_division(
    corporation: CorporationOwner, balance: float, division_id: int, **kwargs
) -> CorporationWalletDivision:
    """
    Create a CorporationWalletDivision

    Args:
        corporation (CorporationOwner): The corporation.
        balance (float): The balance of the division.
        division_id (int): The division ID.
        **kwargs: Fields for the CorporationWalletDivision
    Returns:
        CorporationWalletDivision: The created division.
    """
    params = {
        "corporation": corporation,
        "balance": balance,
        "division_id": division_id,
    }
    params.update(kwargs)
    division = CorporationWalletDivision(**params)
    division.save()
    return division


def create_wallet_journal_entry(
    date: str,
    description: str,
    first_party: EveEntity,
    second_party: EveEntity,
    entry_id: int,
    ref_type: str,
    owner_type="character",
    **kwargs,
) -> CorporationWalletJournalEntry:
    """
    Create a CorporationWalletJournalEntry

    Args:
        division (CorporationWalletDivision): The division.
        date (str): The date of the journal entry.
        description (str): The description of the journal entry.
        first_party (EveEntity): The first party entity.
        second_party (EveEntity): The second party entity.
        entry_id (int): The entry ID.
        ref_type (str): The reference type.
        **kwargs: Fields for the CorporationWalletJournalEntry
    Returns:
        CorporationWalletJournalEntry: The created journal entry.
    """
    params = {
        "date": date,
        "description": description,
        "first_party": first_party,
        "second_party": second_party,
        "entry_id": entry_id,
        "ref_type": ref_type,
    }
    params.update(kwargs)
    if owner_type == "corporation":
        journal_entry = CorporationWalletJournalEntry(**params)
    else:
        journal_entry = CharacterWalletJournalEntry(**params)
    journal_entry.save()
    return journal_entry


def create_character_planet(
    owner: CharacterOwner, planet_id: int, **kwargs
) -> CharacterPlanet:
    """Create a CharacterPlanet from CharacterOwner and planet_id."""
    params = {
        "character": owner,
        "eve_planet": Planet.objects.get(id=planet_id),
    }
    params.update(kwargs)
    planet = CharacterPlanet(**params)
    planet.save()
    return planet


def create_character_planet_details(
    planet: CharacterPlanet, **kwargs
) -> CharacterPlanetDetails:
    """Create a CharacterPlanetDetails from CharacterPlanet."""
    params = {
        "character": planet.character,
        "planet": planet,
    }
    params.update(kwargs)
    planetdetails = CharacterPlanetDetails(**params)
    planetdetails.save()
    return planetdetails
