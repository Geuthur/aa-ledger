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

# Alliance Auth (External Libs)
from eve_sde.models.map import Constellation, Planet, Region, SolarSystem
from eve_sde.models.types import ItemCategory, ItemGroup, ItemType


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

    for item_category in _entities_data.get("EveCategory"):
        ItemCategory.objects.create(
            id=item_category.get("id"),
            name=item_category.get("name"),
            published=item_category.get("published"),
        )

    for item_group in _entities_data.get("EveGroup"):
        ItemGroup.objects.create(
            id=item_group.get("id"),
            name=item_group.get("name"),
            category=ItemCategory.objects.get(id=item_group.get("category_id")),
            published=item_group.get("published"),
        )

    for item_type in _entities_data.get("EveType"):
        ItemType.objects.create(
            id=item_type.get("id"),
            name=item_type.get("name"),
            group=ItemGroup.objects.get(id=item_type.get("group_id")),
            capacity=item_type.get("capacity"),
            description=item_type.get("description"),
            icon_id=item_type.get("icon_id"),
            mass=item_type.get("mass"),
            portion_size=item_type.get("portion_size"),
            radius=item_type.get("radius"),
            published=item_type.get("published"),
            volume=item_type.get("volume"),
        )

    for region in _entities_data.get("EveRegion"):
        Region.objects.create(
            id=region.get("id"),
            name=region.get("name"),
            description=region.get("description"),
        )

    for constellation in _entities_data.get("EveConstellation"):
        Constellation.objects.create(
            id=constellation.get("id"),
            name=constellation.get("name"),
            region=Region.objects.get(id=constellation.get("region_id")),
            x=constellation.get("position_x"),
            y=constellation.get("position_y"),
            z=constellation.get("position_z"),
        )

    for solar_system in _entities_data.get("EveSolarSystem"):
        SolarSystem.objects.create(
            id=solar_system.get("id"),
            name=solar_system.get("name"),
            constellation=Constellation.objects.get(
                id=solar_system.get("constellation_id")
            ),
            security_status=solar_system.get("security_status"),
            x=solar_system.get("position_x"),
            y=solar_system.get("position_y"),
            z=solar_system.get("position_z"),
        )

    for planet in _entities_data.get("EvePlanet"):
        Planet.objects.create(
            id=planet.get("id"),
            name=planet.get("name"),
            solar_system=SolarSystem.objects.get(id=planet.get("solar_system_id")),
            item_type=ItemType.objects.get(id=planet.get("type_id")),
        )
