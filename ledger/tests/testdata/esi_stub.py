import json
from pathlib import Path

from app_utils.esi_testing import EsiClientStub, EsiEndpoint


def load_test_data():
    file_path = Path(__file__).parent / "esi.json"
    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


_esi_data = load_test_data()

_endpoints = [
    EsiEndpoint(
        "Character",
        "get_characters_character_id_roles",
        "character_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Wallet",
        "get_characters_character_id_wallet_journal",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "get_characters_character_id_wallet",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Corporation",
        "get_corporations_corporation_id_divisions",
        "corporation_id",
        needs_token=True,
    ),
    EsiEndpoint(
        "Wallet",
        "get_corporations_corporation_id_wallets",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "get_corporations_corporation_id_wallets_division_journal",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Industry",
        "get_characters_character_id_mining",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Planetary_Interaction",
        "get_characters_character_id_planets",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Planetary_Interaction",
        "get_characters_character_id_planets_planet_id",
        "character_id, planet_id",
        needs_token=False,
    ),
]

esi_client_stub = EsiClientStub(_esi_data, endpoints=_endpoints)
esi_client_error_stub = EsiClientStub(_esi_data, endpoints=_endpoints, http_error=True)
