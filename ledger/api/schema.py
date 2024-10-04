from datetime import datetime

from ninja import Schema

from ledger.api.managers.billboard_manager import BillboardDict


class Message(Schema):
    message: str


class Character(Schema):
    character_name: str
    character_id: int
    corporation_id: int
    corporation_name: str
    alliance_id: int | None = None
    alliance_name: str | None = None


class Corporation(Schema):
    corporation_id: int
    corporation_name: str
    alliance_id: int | None = None
    alliance_name: str | None = None


class EveName(Schema):
    id: int
    name: str
    cat: str | None = None


class CharacterWalletEvent(Schema):
    character: Character | None = None
    id: int | None = None
    date: datetime | None = None
    first_party: EveName | None = None
    second_party: EveName | None = None
    ref_type: str | None = None
    balance: float | None = None
    amount: float | None = None
    reason: str | None = None


class CharacterPlanet(Schema):
    character_id: int | None = None
    character_name: str | None = None
    planet: str | None = None
    planet_id: int | None = None
    upgrade_level: int | None = None
    num_pins: int | None = None
    last_update: datetime | None = None


class CharacterPlanetDetails(Schema):
    character_id: int | None = None
    character_name: str | None = None
    planet: str | None = None
    planet_id: int | None = None
    planet_type_id: int | None = None
    upgrade_level: int | None = None
    expiry_date: datetime | None = None
    expired: bool | None = None
    alarm: bool | None = None
    products: dict | None = None
    products_info: dict | None = None
    extractors: dict | None = None
    last_update: datetime | None = None


class CharacterLedger(Schema):
    ratting: list | None = None
    total: dict | None = None
    billboard: BillboardDict | None = None


class CharacterLedgerTemplate(Schema):
    character: str | None = None


class CharacterAdmin(Schema):
    character: dict | None = None


class CorporationAdmin(Schema):
    corporation: dict | None = None


class AllianceAdmin(Schema):
    alliance: dict | None = None


class CorporationWalletEvent(Schema):
    division: str
    id: int
    date: datetime
    first_party: EveName
    second_party: EveName
    ref_type: str
    balance: float
    amount: float
    reason: str | None = None


class Ledger(Schema):
    ratting: list | None = None
    total: dict | None = None


class Billboard(Schema):
    billboard: BillboardDict | None = None
