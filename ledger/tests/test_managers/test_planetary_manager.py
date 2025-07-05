# Standard Library
from sys import audit
from unittest.mock import patch

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
)
from ledger.tests.testdata.generate_planets import create_character_planet
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.character_planetary_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
class TestPlanetaryManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_from_evecharacter(1001)

    def test_update_planets(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        self.audit.update_planets(force_refresh=False)

        self.assertSetEqual(
            set(self.audit.ledger_character_planet.values_list("planet_id", flat=True)),
            {4001, 4002},
        )
        obj = self.audit.ledger_character_planet.get(planet_id=4001)
        self.assertEqual(obj.planet_id, 4001)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)

        obj = self.audit.ledger_character_planet.get(planet_id=4002)
        self.assertEqual(obj.planet_id, 4002)
        self.assertEqual(obj.upgrade_level, 5)
        self.assertEqual(obj.num_pins, 5)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
class TestPlanetaryDetailsManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_from_evecharacter(1001)
        cls.planet = create_character_planet(
            characteraudit=cls.audit, planet_id=4001, upgrade_level=5, num_pins=5
        )

    def test_update_planets_details(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        self.audit.update_planets_details(force_refresh=False)

        self.assertSetEqual(
            set(
                self.audit.ledger_character_planet_details.values_list(
                    "planet__planet_id", flat=True
                )
            ),
            {4001},
        )
