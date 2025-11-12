# Standard Library
import json
from pathlib import Path

# Alliance Auth (External Libs)
from app_utils.esi_testing import EsiClientStub

# AA Ledger
from ledger.tests.testdata.esi_stub_migration import EsiClientStubOpenApi, EsiEndpoint


class CharacterJournalContext:
    """Context for character wallet journal ESI operations."""

    amount: float
    balance: float
    context_id: int
    context_id_type: str
    date: str
    description: str
    first_party_id: int
    id: int
    reason: str
    ref_type: str
    second_party_id: int
    tax: float
    tax_receiver_id: int


def load_test_data():
    file_path = Path(__file__).parent / "esi.json"
    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


_esi_data = load_test_data()

_endpoints = [
    EsiEndpoint(
        "Character",
        "GetCharactersCharacterIdRoles",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCharactersCharacterIdWalletJournal",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCharactersCharacterIdWallet",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Corporation",
        "GetCorporationsCorporationIdDivisions",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWallets",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWalletsDivisionJournal",
        "corporation_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Industry",
        "GetCharactersCharacterIdMining",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Planetary_Interaction",
        "GetCharactersCharacterIdPlanets",
        "character_id",
        needs_token=False,
    ),
    EsiEndpoint(
        "Planetary_Interaction",
        "GetCharactersCharacterIdPlanetsPlanetId",
        ("character_id", "planet_id"),
        needs_token=False,
    ),
    EsiEndpoint(
        "Universe",
        "PostUniverseNames",
        "body",
        needs_token=False,
    ),
    EsiEndpoint(
        "Universe",
        "PostUniverseIds",
        "body",
        needs_token=False,
    ),
]

esi_client_stub = EsiClientStub(_esi_data, endpoints=_endpoints)
esi_client_stub_openapi = EsiClientStubOpenApi(_esi_data, endpoints=_endpoints)
esi_client_error_stub = EsiClientStub(_esi_data, endpoints=_endpoints, http_error=502)
