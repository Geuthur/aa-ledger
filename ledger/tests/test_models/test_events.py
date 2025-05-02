# Standard Library
from datetime import timedelta
from unittest.mock import patch

# Django
from django.test import TestCase
from django.utils import timezone

# AA Ledger
from ledger.models.events import Events

MODULE_PATH = "ledger.models.general"


class TestGeneralModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.events = Events()
        cls.events.id = 1
        cls.events.title = "Test Title"
        cls.events.date_start = timezone.now()
        cls.events.date_end = timezone.now() + timedelta(days=1)
        cls.events.description = "Test Description"
        cls.events.char_ledger = True
        cls.events.location = "Test Location"

    def test_str(self):
        self.assertEqual(str(self.events), "Event 1")
