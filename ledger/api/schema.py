# Standard Library
from datetime import datetime
from typing import Any

# Third Party
from ninja import Schema

# Django
from django.utils import timezone


class EveName(Schema):
    id: int
    name: str
    cat: str | None = None


class OwnerSchema(Schema):
    character_id: int
    character_name: str
    icon: str | None = None


class EveTypeSchema(Schema):
    id: int
    name: str
    description: str | None = None
    group_id: int | None = None
    group_name: str | None = None
    market_group_id: int | None = None
    market_group_name: str | None = None
    icon: str | None = None


class PlanetSchema(Schema):
    id: int
    name: str
    type: EveTypeSchema
    upgrade_level: int
    num_pins: int
    last_update: timezone.datetime


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


class ProgressBarSchema(Schema):
    percentage: str
    html: str


class ExtractorSchema(Schema):
    item_id: int
    item_name: str
    icon: str | None = None
    install_time: str
    expiry_time: str
    progress: ProgressBarSchema
