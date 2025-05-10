"""Generate AllianceAuth test objects from allianceauth.json."""

# Standard Library
import json
from pathlib import Path

# Alliance Auth (External Libs)
from eveuniverse.models import EvePlanet

# AA Ledger
from ledger.models.characteraudit import CharacterAudit
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails


def _load_planetary_data():
    with open(Path(__file__).parent / "planetary.json", encoding="utf-8") as fp:
        return json.load(fp)


_planetary_data = _load_planetary_data()


def create_character_planet(
    characteraudit: CharacterAudit, planet_id: int, **kwargs
) -> CharacterPlanet:
    """Create a CharacterPlanet from CharacterAudit and planet_id."""
    params = {
        "character": characteraudit,
        "planet": EvePlanet.objects.get(id=planet_id),
    }
    params.update(kwargs)
    planet = CharacterPlanet(**params)
    planet.save()
    return planet


def create_character_planet_details(
    characterplanet: CharacterPlanet, **kwargs
) -> CharacterPlanetDetails:
    """Create a CharacterPlanetDetails from CharacterPlanet."""
    params = {
        "character": characterplanet.character,
        "planet": characterplanet,
    }
    params.update(kwargs)
    planetdetails = CharacterPlanetDetails(**params)
    planetdetails.save()
    return planetdetails
