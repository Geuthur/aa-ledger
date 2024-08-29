"""
Planetary Model
"""

from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EvePlanet

from ledger.hooks import get_extension_logger
from ledger.models.characteraudit import CharacterAudit

logger = get_extension_logger(__name__)


class CharacterPlanet(models.Model):

    id = models.AutoField(primary_key=True)

    character = models.ForeignKey(
        CharacterAudit, on_delete=models.CASCADE, related_name="ledger_characterplanet"
    )

    upgrade_level = models.IntegerField(
        default=0, help_text=_("Upgrade level of the planet")
    )

    num_pins = models.IntegerField(
        default=0, help_text=_("Number of pins on the planet")
    )

    planet_id = models.ForeignKey(
        EvePlanet, on_delete=models.CASCADE, related_name="ledger_planet"
    )

    last_update = models.DateTimeField(null=True, default=None, blank=True)

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    # objects = AuditCharacterManager()

    def __str__(self):
        return f"Planet Data: {self.character.character.character_name} - {self.planet_id.name}"

    @classmethod
    def get_esi_scopes(cls) -> List[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            "esi-planets.manage_planets.v1",
        ]


class CharacterPlanetDetails(models.Model):

    id = models.AutoField(primary_key=True)

    planet = models.ForeignKey(
        CharacterPlanet,
        on_delete=models.CASCADE,
        related_name="ledger_characterplanetdetails",
    )

    links = models.JSONField(null=True, default=None, blank=True)
    pins = models.JSONField(null=True, default=None, blank=True)
    routes = models.JSONField(null=True, default=None, blank=True)

    last_update = models.DateTimeField(null=True, default=None, blank=True)

    # objects = AuditCharacterManager()

    def __str__(self):
        return f"Planet Details Data: {self.character.character.character_name} - {self.planet_id.name}"

    def get_planet_expiry_date(self):
        expiry_dates = []
        for pin in self.pins:
            expiry_dates.append(pin["expiry_time"])
        return min(expiry_dates)
