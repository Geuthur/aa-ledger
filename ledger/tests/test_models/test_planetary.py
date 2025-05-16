# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
)
from ledger.tests.testdata.generate_planets import (
    _planetary_data,
    create_character_planet,
    create_character_planet_details,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.planetary"


class TestPlanetModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.audit = create_characteraudit_from_evecharacter(1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)

    def test_str(self):
        self.assertEqual(str(self.planetary), "Planet Data: Gneuten - Test Planet I")

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.planetary.get_esi_scopes(), ["esi-planets.manage_planets.v1"]
        )


class TestPlanetaryDetailsModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.planet_params = {
            "upgrade_level": 5,
            "num_pins": 5,
        }

        cls.audit = create_characteraudit_from_evecharacter(1001)
        cls.planetary = create_character_planet(cls.audit, 4001, **cls.planet_params)
        cls.planetarydetails = create_character_planet_details(
            cls.planetary, **_planetary_data
        )

    def test_details_str(self):
        self.assertEqual(
            str(self.planetarydetails), "Planet Details Data: Gneuten - Test Planet I"
        )

    def test_count_extractors(self):
        extractors_count = self.planetarydetails.count_extractors()

        self.assertEqual(extractors_count, 2)

    def test_get_planet_install_date(self):
        install_time = self.planetarydetails.get_planet_install_date()

        expected_install_date = timezone.datetime(
            2024, 8, 12, 17, 17, 2, tzinfo=timezone.utc
        )
        self.assertEqual(install_time, expected_install_date)

    def test_get_planet_expiry_date(self):
        expected_expiry_date = timezone.datetime(
            2024, 8, 26, 17, 17, 2, tzinfo=timezone.utc
        )
        self.assertEqual(
            self.planetarydetails.get_planet_expiry_date(), expected_expiry_date
        )

    def test_is_expired(self):
        self.assertEqual(self.planetarydetails.is_expired, True)

    def test_get_types(self):
        self.assertEqual(
            self.planetarydetails.get_types(), [9832, 3645, 2390, 2268, 2309]
        )

    @patch(MODULE_PATH + ".timezone.now")
    def test_is_percent_correct(self, mock_now):
        fixed_date = timezone.make_aware(timezone.datetime(2024, 8, 20, 17, 17, 2))
        mock_now.return_value = fixed_date

        extractor_info = self.planetarydetails.get_extractors_info()
        expected_percent = 57.14
        for _, value in extractor_info.items():
            self.assertIn(
                "progress_percentage", value
            )  # Check if the key exists in the nested dictionary
            self.assertEqual(value["progress_percentage"], expected_percent)

    def test_get_planet_install_date_none(self):
        planetary_details = create_character_planet_details(self.planetary)
        planetary_details.pins = []
        self.assertIsNone(planetary_details.get_planet_install_date())

    def test_get_planet_expiry_date_none(self):
        planetary_details = create_character_planet_details(self.planetary)
        planetary_details.pins = []
        self.assertIsNone(planetary_details.get_planet_expiry_date())

    @patch("django.utils.timezone.now")
    def test_is_expired_false(self, mock_now):
        mock_now.return_value = timezone.datetime(2023, 10, 1, tzinfo=timezone.utc)
        future_date = mock_now.return_value + timezone.timedelta(days=10)

        planetary_details = create_character_planet_details(self.planetary)
        planetary_details.pins = [{"expiry_time": future_date.isoformat()}]
        self.assertFalse(planetary_details.is_expired)

    def test_is_expired_empty(self):
        planetary_details = create_character_planet_details(self.planetary)
        planetary_details.pins = [{"expiry_time": None}]
        self.assertFalse(planetary_details.is_expired)
