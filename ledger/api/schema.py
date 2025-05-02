# Standard Library
from datetime import datetime
from typing import Any

# Third Party
from ninja import Schema


class EveName(Schema):
    id: int
    name: str
    cat: str | None = None


class CharacterPlanet(Schema):
    character_id: int | None = None
    character_name: str | None = None
    planet: str | None = None
    planet_id: int | None = None
    upgrade_level: int | None = None
    num_pins: int | None = None
    last_update: datetime | None = None


class CharacterAdmin(Schema):
    character: dict | None = None


class CorporationAdmin(Schema):
    corporation: dict | None = None


class AllianceAdmin(Schema):
    alliance: dict | None = None


class Ledger(Schema):
    ratting: list | None = None
    billboard: Any | None = None
    total: dict | None = None
