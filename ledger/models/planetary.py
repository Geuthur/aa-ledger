"""
Planetary Model
"""

# Django
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eveuniverse.models import EvePlanet

# AA Ledger
from ledger import __title__
from ledger.managers.character_planetary_manager import (
    CharacterPlanetManager,
    PlanetDetailsManager,
)
from ledger.models.characteraudit import CharacterOwner, CharacterUpdateStatus
from ledger.models.helpers.update_manager import CharacterUpdateSection
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class CharacterPlanet(models.Model):
    """Model to store the planetary data of a character"""

    objects: CharacterPlanetManager = CharacterPlanetManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["character"]),
            models.Index(fields=["eve_planet"]),
        ]

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100, null=True, default=None)

    eve_planet = models.ForeignKey(
        EvePlanet, on_delete=models.CASCADE, related_name="ledger_planet"
    )

    character = models.ForeignKey(
        CharacterOwner, on_delete=models.CASCADE, related_name="ledger_character_planet"
    )

    upgrade_level = models.IntegerField(
        default=0, help_text=_("Upgrade level of the planet")
    )

    num_pins = models.IntegerField(
        default=0, help_text=_("Number of pins on the planet")
    )

    def __str__(self):
        return f"Planet Data: {self.character.eve_character.character_name} - {self.eve_planet.name}"

    @property
    def last_update(self) -> timezone.datetime:
        """Return the last update time of the planet."""
        try:
            last_update = CharacterUpdateStatus.objects.get(
                owner=self.character,
                section=CharacterUpdateSection.PLANETS,
            ).last_update_at
        except CharacterUpdateStatus.DoesNotExist:
            last_update = None
        return last_update

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            "esi-planets.manage_planets.v1",
        ]


class CharacterPlanetDetails(models.Model):
    """Model to store the details of a planet"""

    objects: PlanetDetailsManager = PlanetDetailsManager()

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(fields=["planet"]),
        ]

    id = models.AutoField(primary_key=True)

    planet = models.ForeignKey(
        CharacterPlanet,
        on_delete=models.CASCADE,
        related_name="ledger_planet_details",
    )

    character = models.ForeignKey(
        CharacterOwner,
        on_delete=models.CASCADE,
        related_name="ledger_character_planet_details",
    )

    links = models.JSONField(null=True, default=None, blank=True)
    pins = models.JSONField(null=True, default=None, blank=True)
    routes = models.JSONField(null=True, default=None, blank=True)
    factories = models.JSONField(null=True, default=None, blank=True)

    last_alert = models.DateTimeField(null=True, default=None, blank=True)

    notification = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Planet Details Data: {self.planet.character.eve_character.character_name} - {self.planet.eve_planet.name}"

    @property
    def is_expired(self):
        """
        Return False (not expired) when any extractor is running or when any
        'Processors' facility has an active resource. Otherwise return True.
        """
        # No factories means nothing is running, so expired
        if not self.factories:
            return True

        # Check all facilities for running extractors or active processor ressources
        try:
            factories = self.factories.values()
        except AttributeError:
            return True

        for factory in factories:
            # Extractor running?
            extractor = factory.get("extractor", {})
            if extractor.get("is_running", False):
                return False

            # Processors: any resource with is_active True?
            if factory.get("facility_type") == "Processors":
                for ressource in factory.get("ressources", []) or []:
                    if ressource.get("is_active", False):
                        return False
        return True

    @property
    def last_update(self) -> timezone.datetime:
        """Return the last update time of the planet details."""
        try:
            last_update = CharacterUpdateStatus.objects.get(
                character=self.character,
                section=CharacterUpdateSection.PLANETS_DETAILS,
            ).last_update_at
        except CharacterUpdateStatus.DoesNotExist:
            last_update = None
        return last_update
