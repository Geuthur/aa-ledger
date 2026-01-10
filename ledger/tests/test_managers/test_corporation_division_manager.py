# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import override_settings

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.esi_stub_openapi import EsiEndpoint, create_esi_client_stub
from ledger.tests.testdata.utils import (
    create_owner_from_user,
)

MODULE_PATH = "ledger.managers.corporation_journal_manager"

LEDGER_CORPORATION_DIVISION_ENDPOINTS = [
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWalletsDivisionJournal",
        "corporation_id",
        "division",
    ),
    EsiEndpoint(
        "Wallet",
        "GetCorporationsCorporationIdWallets",
        "corporation_id",
    ),
    EsiEndpoint(
        "Corporation",
        "GetCorporationsCorporationIdDivisions",
        "corporation_id",
    ),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
class TestDivisionManager(LedgerTestCase):
    """Test Division Manager for Corporation Divisions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = create_owner_from_user(user=cls.user, owner_type="corporation")
        cls.token = cls.user_character.user.token_set.first()
        cls.audit.get_token = MagicMock(return_value=cls.token)

    def test_update_division_names(self, mock_esi):
        """Test updating the corporation division names.

        This test verifies that the division names for a corporation are correctly updated
        from ESI data.

        ### Expected Result
        - Division names are updated correctly.
        - Divisions have correct names.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CORPORATION_DIVISION_ENDPOINTS
        )

        # Test Action
        self.audit.update_wallet_division_names(force_refresh=False)

        # Expected Results
        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.name, "Rechnungen")

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.name, "Ship Replacment Abteilung")

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.name, "Partner")

    def test_update_division(self, mock_esi):
        """
        Test updating the corporation division balances.

        This test verifies that the division balances for a corporation are correctly updated
        from ESI data.

        ### Expected Result
        - Division balances are updated correctly.
        - Divisions have correct balances.
        """
        # Test Data
        mock_esi.client = create_esi_client_stub(
            endpoints=LEDGER_CORPORATION_DIVISION_ENDPOINTS
        )

        # Test Action
        self.audit.update_wallet_division(force_refresh=False)

        # Expected Results
        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.balance, 0)

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.balance, 1600000000)

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.balance, 0)
