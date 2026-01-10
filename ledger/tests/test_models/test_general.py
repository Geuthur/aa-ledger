# Standard Library
from datetime import timedelta
from unittest.mock import patch

# Django
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase

MODULE_PATH = "ledger.models.general"


class TestGeneralModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eveentity = EveEntity(
            name="Test",
            eve_id=123,
            category="corporation",
            last_update=timezone.now() - timedelta(days=8),
        )

    def test_str(self):
        """Test the string representation of EveEntity."""
        # Expected Result
        self.assertEqual(str(self.eveentity), "Test")

    def test_repr(self):
        """Test the repr representation of EveEntity."""
        self.eveentity.category = "corporation"
        # Expected Result
        self.assertEqual(
            repr(self.eveentity),
            "EveEntity(id=123, category='corporation', name='Test')",
        )

    def test_is_alliance(self):
        """Test is_alliance property"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_ALLIANCE
        self.assertTrue(self.eveentity.is_alliance)

        # Expected Result
        self.eveentity.category = "Invalid Category"
        self.assertFalse(self.eveentity.is_alliance)

    def test_is_corporation(self):
        """Test is_corporation property"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_CORPORATION
        self.assertTrue(self.eveentity.is_corporation)

        # Expected Result
        self.eveentity.category = "Invalid Category"
        self.assertFalse(self.eveentity.is_corporation)

    def test_is_character(self):
        """Test is_character property"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_CHARACTER
        self.assertTrue(self.eveentity.is_character)

        # Expected Result
        self.eveentity.category = "Invalid Category"
        self.assertFalse(self.eveentity.is_character)

    @patch(MODULE_PATH + ".EveAllianceInfo.generic_logo_url")
    def test_icon_url_alliance(self, mock_generic_logo_url):
        """Test icon_url for alliance category"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_ALLIANCE
        mock_generic_logo_url.return_value = "Test URL"

        # Expected Result
        self.assertEqual(self.eveentity.icon_url(), "Test URL")

    @patch(MODULE_PATH + ".EveCorporationInfo.generic_logo_url")
    def test_icon_url_corporation(self, mock_generic_logo_url):
        """Test icon_url for corporation category"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_CORPORATION
        mock_generic_logo_url.return_value = "Test URL"

        # Expected Result
        self.assertEqual(self.eveentity.icon_url(), "Test URL")

    @patch(MODULE_PATH + ".EveCharacter.generic_portrait_url")
    def test_icon_url_character(self, mock_generic_portrait_url):
        """Test icon_url for character category"""
        # Test Data
        self.eveentity.category = self.eveentity.CATEGORY_CHARACTER
        mock_generic_portrait_url.return_value = "Test URL"

        # Expected Result
        self.assertEqual(self.eveentity.icon_url(), "Test URL")

    def test_icon_url_not_implemented(self):
        """Test icon_url raises NotImplementedError for invalid category"""
        # Expected Result
        self.eveentity.category = "Invalid Category"
        with self.assertRaises(NotImplementedError):
            self.eveentity.icon_url()

    def test_needs_update(self):
        """Test needs_update method"""
        # Expected Result
        self.assertTrue(self.eveentity.needs_update())
