from unittest.mock import PropertyMock, patch

from django.test import RequestFactory, TestCase
from django.utils import timezone

from ledger.models.characteraudit import (
    CharacterAudit,
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.planetary import CharacterPlanet, CharacterPlanetDetails
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary

MODULE_PATH = "ledger.models.planetary"


class TestCharacterAuditModel(TestCase):
    @classmethod
    def setUp(self):
        load_allianceauth()
        load_ledger_all()
        load_planetary()
        self.planetary = CharacterPlanet.objects.get(
            planet__id=4001, character__character__character_name="Gneuten"
        )

        self.planetarydetails = CharacterPlanetDetails.objects.get(
            planet__planet__id=4001,
            planet__character__character__character_name="Gneuten",
        )

    def test_str(self):
        self.assertEqual(str(self.planetary), "Planet Data: Gneuten - Test Planet I")

    def test_get_esi_scopes(self):
        self.assertEqual(
            self.planetary.get_esi_scopes(), ["esi-planets.manage_planets.v1"]
        )

    # Planetary Details

    def test_details_str(self):
        self.assertEqual(
            str(self.planetarydetails), "Planet Details Data: Gneuten - Test Planet I"
        )

    def test_count_extractors(self):
        self.assertEqual(self.planetarydetails.count_extractors(), 2)

    def test_get_planet_install_date(self):
        expected_install_date = timezone.datetime(
            2024, 8, 12, 17, 17, 2, tzinfo=timezone.utc
        )
        self.assertEqual(
            self.planetarydetails.get_planet_install_date(), expected_install_date
        )

    def test_get_planet_expiry_date(self):
        expected_expiry_date = timezone.datetime(
            2024, 8, 26, 17, 17, 2, tzinfo=timezone.utc
        )
        self.assertEqual(
            self.planetarydetails.get_planet_expiry_date(), expected_expiry_date
        )

    def test_is_expired(self):
        self.assertEqual(self.planetarydetails.is_expired(), True)

    def test_get_types(self):
        self.assertEqual(
            self.planetarydetails.get_types(), [9832, 3645, 2390, 2268, 2309]
        )

    def test_get_planet_install_date_none(self):
        self.planetarydetails.pins = []
        self.assertIsNone(self.planetarydetails.get_planet_install_date())

    def test_get_planet_expiry_date_none(self):
        self.planetarydetails.pins = []
        self.assertIsNone(self.planetarydetails.get_planet_expiry_date())

    @patch("django.utils.timezone.now")
    def test_is_expired_false(self, mock_now):
        mock_now.return_value = timezone.datetime(2023, 10, 1, tzinfo=timezone.utc)
        future_date = mock_now.return_value + timezone.timedelta(days=10)
        self.planetarydetails.pins = [{"expiry_time": future_date.isoformat()}]
        self.assertFalse(self.planetarydetails.is_expired())

    def test_is_expired_empty(self):
        self.planetarydetails.pins = [{"expiry_time": None}]
        self.assertFalse(self.planetarydetails.is_expired())
