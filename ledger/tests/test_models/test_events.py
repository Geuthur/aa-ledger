from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from ledger.models.events import Events

MODULE_PATH = "ledger.models.general"


class TestGeneralModel(TestCase):
    def setUp(self):
        self.events = Events()
        self.events.id = 1
        self.events.title = "Test Title"
        self.events.date_start = timezone.now()
        self.events.date_end = timezone.now() + timedelta(days=1)
        self.events.description = "Test Description"
        self.events.char_ledger = True
        self.events.location = "Test Location"

    def test_str(self):
        self.assertEqual(str(self.events), "Event 1")
