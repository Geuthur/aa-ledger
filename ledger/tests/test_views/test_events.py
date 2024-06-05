# Python
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from app_utils.testing import create_user_from_evecharacter

from ledger.models.events import Events
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.views.corporation.corp_events import (
    create_event,
    delete_event,
    edit_event,
    events_admin,
    events_index,
    load_events,
)


class EventViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=["ledger.basic_access", "ledger.event_admin_access"],
        )
        cls.event = Events.objects.create(
            title="Test Event",
            date_start="2022-01-01T00:00",
            date_end="2030-01-01T01:00",
            description="Test Description",
            char_ledger=False,
            location="Test Location",
        )

    def test_events_index(self):
        self.client.force_login(self.user)
        response = self.client.get("/ledger/events/")
        self.assertEqual(response.status_code, 200)

    def test_create_event(self):
        self.client.force_login(self.user)
        response = self.client.get("/ledger/events/create/")
        self.assertEqual(response.status_code, 200)

    def test_create_event_no_valid(self):
        request = self.factory.post("/ledger/events/create/")
        request.user = self.user
        response = create_event(request)
        self.assertEqual(response.status_code, 200)

    def test_create_event_post(self):
        request = self.factory.post(
            "/ledger/events/create/",
            {
                "title": "New Event",
                "date_start": timezone.now(),
                "date_end": timezone.now() + timezone.timedelta(days=1),
                "location": "New Location",
                "description": "New Description",
                "char_ledger": False,
            },
        )
        request.user = self.user
        response = create_event(request)
        self.assertEqual(response.status_code, 302)

    def test_edit_event_get(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/ledger/events/{self.event.id}/edit/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        self.assertContains(response, self.event.date_start)
        self.assertContains(response, self.event.date_end)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.location)

    def test_edit_event_post(self):
        self.client.force_login(self.user)
        response = self.client.post(f"/ledger/events/{self.event.id}/edit/")
        self.assertEqual(response.status_code, 200)

    def test_edit_event_post_entry(self):
        self.client.force_login(self.user)
        response = self.client.post(
            f"/ledger/events/{self.event.id}/edit/",
            {
                "title": "Updated Event",
                "date_start": self.event.date_start,
                "date_end": self.event.date_end,
                "location": "Updated Location",
                "description": "Updated Description",
                "char_ledger": self.event.char_ledger,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_event_get(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/ledger/events/{self.event.id}/delete/")
        self.assertEqual(response.status_code, 200)

    def test_delete_event_post(self):
        request = self.factory.post(f"/ledger/events/{self.event.id}/delete/")
        request.user = self.user
        response = delete_event(request, self.event.id)
        self.assertEqual(response.status_code, 302)

    def test_manage_event(self):
        request = self.factory.post("/ledger/events/admin/")
        request.user = self.user
        response = events_admin(request)
        self.assertEqual(response.status_code, 200)

    def test_load_events(self):
        request = self.factory.get("/ledger/events/load/")
        request.user = self.user
        response = load_events(request)
        self.assertEqual(response.status_code, 200)
