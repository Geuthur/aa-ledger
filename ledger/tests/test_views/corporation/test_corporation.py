"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporationaudit_from_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.generate_walletjournal import (
    create_division,
    create_wallet_journal_entry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse
from ledger.views.corporation.corporation_ledger import (
    corporation_data_export_generate,
    corporation_data_export_run_update,
)

MODULE_PATH = "ledger.views.corporation.corporation_ledger"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestCorporationLedgerView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.advanced_access",
                "ledger.manage_access",
            ],
        )

        cls.user_no_permissions, cls.character_ownership = (
            create_user_from_evecharacter(
                1002,
                permissions=[
                    "ledger.basic_access",
                    "ledger.advanced_access",
                    "ledger.manage_access",
                ],
            )
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division,
            context_id=1,
            entry_id=10,
            amount=1000,
            balance=2000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2016,
                month=10,
                day=29,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test Journal",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="player_donation",
        )

    def test_corporation_data_export_generate(self, mock_tasks, mock_messages):
        """Test should generate corporation data export"""
        corporation_id = self.audit.corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse("ledger:corporation_data_export_generate", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(
            request,
            f"Data export for {corporation_id} has been started. This can take a couple of minutes. You will get a notification once it is completed.",
        )
        mock_tasks.export_data_ledger.apply_async.assert_called_once()

    def test_corporation_data_export_generate_no_permission(
        self, mock_tasks, mock_messages
    ):
        """Test should not generate corporation data export due to no permission"""
        corporation_id = self.audit.corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse("ledger:corporation_data_export_generate", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user_no_permissions

        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    def test_corporation_data_export_generate_corporation_not_found(
        self, mock_tasks, mock_messages
    ):
        """Test should not generate corporation data export due to corporation not found"""
        corporation_id = 9999  # Non-existent corporation ID
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse("ledger:corporation_data_export_generate", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    def test_corporation_data_export_generate_invalid_form(
        self, mock_tasks, mock_messages
    ):
        """Test should not generate corporation data export due to invalid form"""
        corporation_id = self.audit.corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "invalid_year",  # Invalid year
        }

        request = self.factory.post(
            reverse("ledger:corporation_data_export_generate", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Invalid form submission.")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    @patch(MODULE_PATH + ".data_exporter.LedgerCSVExporter.decoder")
    def test_corporation_data_export_run_update(
        self, mock_decoder, mock_tasks, mock_messages
    ):
        """Test should run corporation data export update task"""
        corporation_id = self.audit.corporation.corporation_id
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (2001, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )

        request.user = self.user

        response = corporation_data_export_run_update(request, hash_code=hashcode)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(
            request,
            f"Data export for {corporation_id} has been started. This can take a couple of minutes. You will get a notification once it is completed.",
        )
        mock_tasks.export_data_ledger.apply_async.assert_called_once()

    @patch(MODULE_PATH + ".data_exporter.LedgerCSVExporter.decoder")
    def test_corporation_data_export_run_update_no_permission(
        self, mock_decoder, mock_tasks, mock_messages
    ):
        """Test should not run corporation data export update task due to no permission"""
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (2001, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )

        request.user = self.user_no_permissions

        response = corporation_data_export_run_update(request, hash_code=hashcode)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    @patch(MODULE_PATH + ".data_exporter.LedgerCSVExporter.decoder")
    def test_corporation_data_export_run_update_corporation_not_found(
        self, mock_decoder, mock_tasks, mock_messages
    ):
        """Test should not run corporation data export update task due to corporation not found"""
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (9999, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )

        request.user = self.user

        response = corporation_data_export_run_update(request, hash_code=hashcode)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()
