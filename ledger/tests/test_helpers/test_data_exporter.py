# Standard Library
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, Mock, patch
from zipfile import ZipFile

# Django
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Ledger
from ledger.helpers import data_exporter
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

MODULE_PATH = "ledger.helpers.data_exporter"


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

        cls.user_alliance, cls.character_ownership_alliance = (
            create_user_from_evecharacter(
                1003,
                permissions=[
                    "ledger.basic_access",
                    "ledger.advanced_access",
                    "ledger.manage_access",
                ],
            )
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

        cls.audit_alliance = create_corporationaudit_from_user(cls.user_alliance)

        cls.eve_character_first_party = EveEntity.objects.get(eve_id=2001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1001)

        cls.division = create_division(
            corporation=cls.audit, name="MEGA KONTO", balance=1000000, division_id=1
        )

        cls.division_alliance = create_division(
            corporation=cls.audit_alliance,
            name="MEGA KONTO",
            balance=1000000,
            division_id=1,
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

        cls.journal_entry_alliance = create_wallet_journal_entry(
            journal_type="corporation",
            division=cls.division_alliance,
            context_id=2,
            entry_id=20,
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

    def test_int_or_none(self):
        """Test should return integer or None."""
        self.assertEqual(data_exporter.int_or_none(100), 100)
        self.assertIsNone(data_exporter.int_or_none("invalid"))

    def test_file_to_zip(self):
        """Test should create a zip file from given files."""
        with TemporaryDirectory() as tmpdirname_1, TemporaryDirectory() as tmpdirname_2:
            # given
            source_file = Path(tmpdirname_1) / "test.csv"
            with source_file.open("w") as fp:
                fp.write("test file")
            destination = Path(tmpdirname_2)

            zip_file = data_exporter.file_to_zip(source_file, destination=destination)
            with ZipFile(zip_file, "r") as testzip:
                namelist = testzip.namelist()
            self.assertIn(source_file.name, namelist)

    def test_default_destination(self):
        """Test should return default destination path."""
        with TemporaryDirectory() as tmpdirname:
            with patch(
                "ledger.helpers.data_exporter.default_destination",
                return_value=Path(tmpdirname),
            ):
                destination = data_exporter.default_destination()
                self.assertEqual(destination, Path(tmpdirname))

    def test_export_ledger_to_archive_corporation(self):
        """Test should export corporation ledger to archive."""
        with TemporaryDirectory():
            ledger_type = "corporation"

            corporation_id = self.audit.corporation.corporation_id
            year = 2016

            result = data_exporter.export_ledger_to_archive(
                ledger_type=ledger_type,
                entity_id=corporation_id,
                division_id=None,
                year=year,
                month=None,
            )
            # then
            output_file = Path(result)

            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.suffix, ".zip")
            output_file.unlink(missing_ok=True)  # Clean up the created file

    def test_export_ledger_to_archive_alliance(self):
        """Test should export alliance ledger to archive."""
        with TemporaryDirectory():
            ledger_type = "alliance"

            alliance_id = self.audit_alliance.corporation.alliance.alliance_id
            year = 2016

            result = data_exporter.export_ledger_to_archive(
                ledger_type=ledger_type,
                entity_id=alliance_id,
                division_id=None,
                year=year,
                month=None,
            )
            # then
            output_file = Path(result)

            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.suffix, ".zip")
            output_file.unlink(missing_ok=True)  # Clean up the created file
