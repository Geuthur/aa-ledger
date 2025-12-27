"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

# AA Ledger
from ledger.models.general import EveEntity
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
    create_division,
    create_owner_from_user,
    create_wallet_journal_entry,
)
from ledger.views.corporation.corporation_ledger import (
    corporation_data_export_generate,
    corporation_data_export_run_update,
)

MODULE_PATH = "ledger.views.corporation.corporation_ledger"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestCorporationLedgerView(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")
        cls.user = add_new_permission_to_user(cls.user, "ledger.advanced_access")
        cls.user = add_new_permission_to_user(cls.user, "ledger.manage_access")

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.journal_entry = create_wallet_journal_entry(
            owner_type="corporation",
            division=cls.division,
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
            entry_id=10,
            ref_type="player_donation",
            context_id=1,
            amount=1000,
            balance=2000,
        )

    def test_corporation_data_export_generate(self, mock_tasks, mock_messages):
        """
        Test should generate corporation data export

        This test verifies that when a user with the appropriate permissions
        attempts to generate a data export for a corporation they own, the system
        successfully starts the export process and provides appropriate feedback.

        ## Results: Data export process is started successfully.
        """
        # Test Data
        corporation_id = self.audit.eve_corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse(
                "ledger:corporation_data_export_generate",
                kwargs={"corporation_id": corporation_id},
            ),
            data=form_data,
        )
        request.user = self.superuser

        # Test Action
        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(
            request,
            f"Data export for {corporation_id} has been started. This can take a couple of minutes. You will get a notification once it is completed.",
        )
        mock_tasks.export_data_ledger.apply_async.assert_called_once()

    def test_corporation_data_export_generate_no_permission(
        self, mock_tasks, mock_messages
    ):
        """
        Test should not generate corporation data export due to no permission

        This test verifies that when a user without the appropriate permissions
        attempts to generate a data export for a corporation they own, the system
        prevents the export process and provides an appropriate error message.

        ## Results: Permission Denied error is returned.
        """
        # Test Data
        corporation_id = self.audit.eve_corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse(
                "ledger:corporation_data_export_generate",
                kwargs={"corporation_id": corporation_id},
            ),
            data=form_data,
        )
        add_new_permission_to_user(self.user2, "ledger.manage_access")
        request.user = self.user2

        # Test Action
        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    def test_corporation_data_export_generate_corporation_not_found(
        self, mock_tasks, mock_messages
    ):
        """
        Test should not generate corporation data export due to corporation not found

        This test verifies that when a user attempts to generate a data export
        for a non-existent corporation, the system prevents the export process and
        provides an appropriate error message.

        ## Results: Corporation not found message is returned.
        """
        # Test Data
        corporation_id = 9999  # Non-existent corporation ID
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "2016",
        }

        request = self.factory.post(
            reverse(
                "ledger:corporation_data_export_generate",
                kwargs={"corporation_id": corporation_id},
            ),
            data=form_data,
        )
        request.user = self.user

        # Test Action
        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    def test_corporation_data_export_generate_invalid_form(
        self, mock_tasks, mock_messages
    ):
        """
        Test should not generate corporation data export due to invalid form

        This test verifies that when a user submits an invalid form
        while attempting to generate a data export for a corporation they own,
        the system prevents the export process and provides an appropriate error message.

        ## Results: Invalid form submission message is returned.
        """
        # Test Data
        corporation_id = self.audit.eve_corporation.corporation_id
        mock_tasks.export_data_ledger.apply_async = Mock()

        form_data = {
            "year": "invalid_year",  # Invalid year
        }

        request = self.factory.post(
            reverse("ledger:corporation_data_export_generate", args=[corporation_id]),
            data=form_data,
        )

        request.user = self.user

        # Test Action
        response = corporation_data_export_generate(
            request, corporation_id=corporation_id
        )

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Invalid form submission.")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    @patch(MODULE_PATH + ".data_exporter.LedgerCSVExporter.decoder")
    def test_corporation_data_export_run_update(
        self, mock_decoder, mock_tasks, mock_messages
    ):
        """
        Test should run corporation data export update task

        This test verifies that when a user with the appropriate permissions
        attempts to run a data export update for a corporation they own, the system
        successfully starts the update process and provides appropriate feedback.

        ## Results: Data export update process is started successfully.
        """
        # Test Data
        corporation_id = self.audit.eve_corporation.corporation_id
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (2001, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )

        request.user = self.user

        # Test Action
        response = corporation_data_export_run_update(request, hash_code=hashcode)

        # Exptected Results
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
        """
        Test should not run corporation data export update task due to no permission


        This test verifies that when a user without the appropriate permissions
        attempts to run a data export update for a corporation they own, the system
        prevents the update process and provides an appropriate error message.

        ## Results: Permission Denied error is returned.
        """
        # Test Data
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (2001, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )

        add_new_permission_to_user(self.user2, "ledger.manage_access")
        request.user = self.user2

        # Test Action
        response = corporation_data_export_run_update(request, hash_code=hashcode)

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.error.assert_called_once_with(request, "Permission Denied")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()

    @patch(MODULE_PATH + ".data_exporter.LedgerCSVExporter.decoder")
    def test_corporation_data_export_run_update_corporation_not_found(
        self, mock_decoder, mock_tasks, mock_messages
    ):
        """
        Test should not run corporation data export update task due to corporation not found

        This test verifies that when a user attempts to run a data export
        update for a non-existent corporation, the system prevents the update process and
        provides an appropriate error message.

        ## Results: Corporation not found message is returned.
        """
        # Test Data
        hashcode = "testhashcode"
        mock_tasks.export_data_ledger.apply_async = Mock()
        mock_decoder.return_value = (9999, 1, 2016, 1)

        request = self.factory.get(
            reverse("ledger:corporation_data_export_run_update", args=[hashcode]),
        )
        request.user = self.user

        # Test Action
        response = corporation_data_export_run_update(request, hash_code=hashcode)

        # Exptected Results
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        mock_messages.info.assert_called_once_with(request, "Corporation not found")
        mock_tasks.export_data_ledger.apply_async.assert_not_called()
