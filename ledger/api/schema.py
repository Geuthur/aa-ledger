from datetime import datetime
from typing import Dict, List, Optional

from ninja import Schema


class Message(Schema):
    message: str


class Character(Schema):
    character_name: str
    character_id: int
    corporation_id: int
    corporation_name: str
    alliance_id: Optional[int] = None
    alliance_name: Optional[str] = None


class Corporation(Schema):
    corporation_id: int
    corporation_name: str
    alliance_id: Optional[int] = None
    alliance_name: Optional[str] = None


class EveName(Schema):
    id: int
    name: str
    cat: Optional[str] = None


class CharacterWalletEvent(Schema):
    character: Optional[Character] = None
    id: Optional[int] = None
    date: Optional[datetime] = None
    first_party: Optional[EveName] = None
    second_party: Optional[EveName] = None
    ref_type: Optional[str] = None
    balance: Optional[float] = None
    amount: Optional[float] = None
    reason: Optional[str] = None


class CharacterLedger(Schema):
    ratting: Optional[List] = None
    total: Optional[Dict] = None
    billboard: Optional[Dict] = None


class CharacterLedgerTemplate(Schema):
    character: Optional[str] = None


class CorporationWalletEvent(Schema):
    division: str
    id: int
    date: datetime
    first_party: EveName
    second_party: EveName
    ref_type: str
    balance: float
    amount: float
    reason: Optional[str] = None


class CorporationLedger(Schema):
    ratting: Optional[List] = None
    total: Optional[Dict] = None
    billboard: Optional[Dict] = None
