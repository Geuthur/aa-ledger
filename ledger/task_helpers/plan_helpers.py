"""
Planetary Helpers
"""

from django.utils import timezone
from eveuniverse.models import EvePlanet

from ledger.decorators import log_timing
from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails
from ledger.providers import esi
from ledger.task_helpers.core_helpers import get_token
from ledger.task_helpers.etag_helpers import NotModifiedError, etag_results

logger = get_extension_logger(__name__)


def convert_datetime_to_str(data):
    if isinstance(data, dict):
        return {k: convert_datetime_to_str(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_datetime_to_str(i) for i in data]
    if isinstance(data, timezone.datetime):
        return data.isoformat()
    return data


# pylint: disable=too-many-locals
@log_timing(logger)
def update_character_planetary(character_id, force_refresh=False):
    # pylint: disable=import-outside-toplevel, cyclic-import
    from ledger.tasks import update_char_planets_details

    audit_char = CharacterAudit.objects.get(character__character_id=character_id)
    logger.debug("Updating planets for: %s", audit_char.character.character_name)

    token = get_token(character_id, CharacterPlanet.get_esi_scopes())

    if not token:
        return "No Tokens"

    try:
        planet_items_data = (
            esi.client.Planetary_Interaction.get_characters_character_id_planets(
                character_id=character_id
            )
        )

        planet_items = etag_results(
            planet_items_data, token, force_refresh=force_refresh
        )

        _current_planets = CharacterPlanet.objects.filter(
            character=audit_char
        ).values_list("planet_id", flat=True)

        _planets_ids = []
        _planets_new = []
        _planets_update = []

        for planet in planet_items:
            eve_planet, _ = EvePlanet.objects.get_or_create_esi(id=planet["planet_id"])
            _planets_ids.append(eve_planet.id)

            try:
                e_planet = CharacterPlanet.objects.get(
                    character=audit_char, planet=eve_planet
                )
                prim_key = e_planet.id
            except CharacterPlanet.DoesNotExist:
                prim_key = None

            planet = CharacterPlanet(
                id=prim_key,
                character=audit_char,
                planet=eve_planet,
                upgrade_level=planet["upgrade_level"],
                num_pins=planet["num_pins"],
                last_update=timezone.now(),
            )

            if eve_planet.id not in _current_planets:
                _planets_new.append(planet)
            else:
                _planets_update.append(planet)

        if _planets_new:
            CharacterPlanet.objects.bulk_create(_planets_new)
        if _planets_update:
            CharacterPlanet.objects.bulk_update(
                _planets_update, fields=["upgrade_level", "num_pins", "last_update"]
            )

        # Delete Planets that are no longer in the list
        obsolete_planets = set(_current_planets) - set(_planets_ids)
        CharacterPlanet.objects.filter(
            character=audit_char, planet_id__in=obsolete_planets
        ).delete()
        # Delete Planet Details that are no longer in the list
        CharacterPlanetDetails.objects.filter(
            planet__character=audit_char, planet__planet_id__in=obsolete_planets
        ).delete()

    except NotModifiedError:
        logger.debug("No New Planet data for: %s", audit_char.character.character_name)

    for planet in CharacterPlanet.objects.filter(character=audit_char):
        update_char_planets_details.apply_async(
            args=[character_id, planet.planet_id],
            kwargs={"force_refresh": False},
            priority=8,
        )

    audit_char.last_update_planetary = timezone.now()
    audit_char.save()
    audit_char.is_active()

    return ("Finished planets update for: %s", audit_char.character.character_name)


@log_timing(logger)
def update_character_planetary_details(character_id, planet_id, force_refresh=False):
    planet_char = CharacterPlanet.objects.get(
        character__character__character_id=character_id, planet__id=planet_id
    )

    logger.debug(
        "Updating planet details %s for: %s",
        planet_char.planet.name,
        planet_char.character.character.character_name,
    )

    token = get_token(character_id, CharacterPlanet.get_esi_scopes())

    if not token:
        return "No Tokens"

    try:
        planet_details_data = esi.client.Planetary_Interaction.get_characters_character_id_planets_planet_id(
            character_id=character_id, planet_id=planet_id
        )

        planet_details_items = etag_results(
            planet_details_data, token, force_refresh=force_refresh
        )
        # Convert Time to string
        planet_details_items = convert_datetime_to_str(planet_details_items)

        planet, created = CharacterPlanetDetails.objects.update_or_create(
            planet=planet_char,
            defaults={
                "links": planet_details_items["links"],
                "pins": planet_details_items["pins"],
                "routes": planet_details_items["routes"],
                "last_update": timezone.now(),
            },
        )

        if not created:
            # Set Alert if Extractor Heads are expired
            if planet.is_expired() and planet.last_alert is None:
                logger.debug(
                    "Planet %s Extractor Heads Expired for: %s",
                    planet.planet.planet.name,
                    planet.planet.character.character.character_name,
                )
                planet.last_alert = timezone.now()

            # Reset Alert after 1 day
            if (
                planet.last_alert is not None
                and planet.last_alert < timezone.now() - timezone.timedelta(days=1)
            ):
                logger.debug(
                    "Notification Reseted for %s Planet: %s",
                    planet.planet.character.character.character_name,
                    planet.planet.planet.name,
                )
                planet.last_alert = None
                planet.notification_sent = False

            planet.save()

    except NotModifiedError:
        logger.debug(
            "No New Planet Details data for: %s",
            planet_char.character.character.character_name,
        )
        return (
            "No New Planet Details data for: %s",
            planet_char.character.character.character_name,
        )

    return (
        "Finished planets details update for: %s",
        planet_char.character.character.character_name,
    )
