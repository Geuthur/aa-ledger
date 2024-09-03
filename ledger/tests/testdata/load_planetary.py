"""Generate AllianceAuth test objects from allianceauth.json."""

import json
from datetime import date, datetime
from pathlib import Path

from eveuniverse.models import EveMarketPrice, EvePlanet, EveSolarSystem, EveType

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ledger.models.characteraudit import CharacterAudit
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails
from ledger.tests.testdata.planetary import planetary_data


def load_planetary():
    """Load test data for planetary."""
    CharacterPlanet.objects.all().delete()
    CharacterPlanet.objects.update_or_create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        planet=EvePlanet.objects.get(id=4001),
        defaults={
            "upgrade_level": 5,
            "num_pins": 5,
            "last_update": None,
        },
    )
    CharacterPlanet.objects.update_or_create(
        character=CharacterAudit.objects.get(character__character_name="Gneuten"),
        planet=EvePlanet.objects.get(id=4002),
        defaults={
            "upgrade_level": 5,
            "num_pins": 5,
            "last_update": None,
        },
    )

    CharacterPlanet.objects.update_or_create(
        character=CharacterAudit.objects.get(character__character_id=1002),
        planet=EvePlanet.objects.get(id=4001),
        defaults={
            "upgrade_level": 5,
            "num_pins": 5,
            "last_update": None,
        },
    )

    CharacterPlanetDetails.objects.all().delete()
    CharacterPlanetDetails.objects.update_or_create(
        planet=CharacterPlanet.objects.get(
            planet__id=4001, character__character__character_name="Gneuten"
        ),
        defaults=planetary_data,
    )
    CharacterPlanetDetails.objects.update_or_create(
        planet=CharacterPlanet.objects.get(
            planet__id=4002, character__character__character_name="Gneuten"
        ),
        defaults=planetary_data,
    )

    CharacterPlanetDetails.objects.update_or_create(
        planet=CharacterPlanet.objects.get(
            planet__id=4001, character__character__character_id=1002
        ),
        defaults=planetary_data,
    )
