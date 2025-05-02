"""Generate AllianceAuth test objects from allianceauth.json."""

# Standard Library
import json
from pathlib import Path

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)


def _load_allianceauth_data():
    with open(Path(__file__).parent / "allianceauth.json", encoding="utf-8") as fp:
        return json.load(fp)


_entities_data = _load_allianceauth_data()


def load_allianceauth():
    """Load allianceauth test objects."""
    EveAllianceInfo.objects.all().delete()
    EveCorporationInfo.objects.all().delete()
    EveCharacter.objects.all().delete()
    for character_info in _entities_data.get("EveCharacter"):
        if character_info.get("alliance_id"):
            try:
                alliance = EveAllianceInfo.objects.get(
                    alliance_id=character_info.get("alliance_id")
                )
            except EveAllianceInfo.DoesNotExist:
                alliance = EveAllianceInfo.objects.create(
                    alliance_id=character_info.get("alliance_id"),
                    alliance_name=character_info.get("alliance_name"),
                    alliance_ticker=character_info.get("alliance_ticker"),
                    executor_corp_id=character_info.get("corporation_id"),
                )
        else:
            alliance = None
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=character_info.get("corporation_id")
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create(
                corporation_id=character_info.get("corporation_id"),
                corporation_name=character_info.get("corporation_name"),
                corporation_ticker=character_info.get("corporation_ticker"),
                member_count=99,
                alliance=alliance,
            )
        EveCharacter.objects.create(
            character_id=character_info.get("character_id"),
            character_name=character_info.get("character_name"),
            corporation_id=corporation.corporation_id,
            corporation_name=corporation.corporation_name,
            corporation_ticker=corporation.corporation_ticker,
            alliance_id=alliance.alliance_id if alliance else None,
            alliance_name=alliance.alliance_name if alliance else "",
            alliance_ticker=alliance.alliance_ticker if alliance else "",
        )
