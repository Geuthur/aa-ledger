# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock

# Third Party
import pook

# Alliance Auth
from esi.errors import TokenError

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import CorporationOwnerFactory
from ledger.tests.testdata.utils import add_new_token

MODULE_PATH = "ledger.managers.corporation_journal_manager"


class TestDivisionManager(LedgerTestCase):
    """Test Division Manager for Corporation Divisions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.token = add_new_token(
            user=cls.user,
            character=cls.user_character,
            scopes=cls.audit.get_esi_scopes(),
        )
        cls.audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_division_names(self):
        """Test updating the corporation division names.

        This test verifies that the division names for a corporation are correctly updated
        from ESI data.

        ### Expected Result
        - Division names are updated correctly.
        - Divisions have correct names.
        """
        # Test Data
        # Mock ESI response for corporation divisions names
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/divisions",
            reply=HTTPStatus.OK,
            response_json={
                "hangar": [
                    {"division": 1, "name": "Test Hangar"},
                    {"division": 2, "name": "Officer Hangar"},
                    {"division": 3, "name": "Schiffe"},
                    {"division": 4, "name": "Lager"},
                    {"division": 5, "name": "Wertvoll"},
                    {"division": 6, "name": "Produktion"},
                    {"division": 7, "name": "Blueprints"},
                ],
                "wallet": [
                    {"division": 1, "name": None},
                    {"division": 2, "name": "Rechnungen"},
                    {"division": 3, "name": "Event's"},
                    {"division": 4, "name": "Ship Replacment Abteilung"},
                    {"division": 5, "name": "Roaming"},
                    {"division": 6, "name": "Partner"},
                    {"division": 7, "name": "Backup"},
                ],
            },
        )

        # Test Action
        self.audit.update_wallet_division_names(force_refresh=False)

        # Expected Results
        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=2,
        )
        self.assertEqual(obj.name, "Rechnungen")

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=4,
        )
        self.assertEqual(obj.name, "Ship Replacment Abteilung")

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=6,
        )
        self.assertEqual(obj.name, "Partner")

    def test_update_division_names_no_token(self):
        """Test updating the corporation division names with no valid token.

        This test verifies that an appropriate error is raised when there is no valid token
        for the corporation.

        ### Expected Result
        - TokenError is raised indicating no valid token found.
        """
        # Test Data
        # Mock get_token to return None to simulate no valid token
        self.audit.get_token = MagicMock(return_value=None)

        # Test Action & Expected Result
        with self.assertRaises(TokenError) as context:
            self.audit.update_wallet_division_names(force_refresh=False)

        self.assertIn("No valid token found for corporation", str(context.exception))

    @pook.on
    def test_update_division(self):
        """
        Test updating the corporation division balances.

        This test verifies that the division balances for a corporation are correctly updated
        from ESI data.

        ### Expected Result
        - Division balances are updated correctly.
        - Divisions have correct balances.
        """
        # Test Data
        # Mock ESI response for corporation divisions
        pook.get(
            url=f"https://esi.evetech.net/corporations/{self.audit.eve_corporation.corporation_id}/wallets",
            reply=HTTPStatus.OK,
            response_headers={"X-Pages": "1"},
            response_json=[
                {"balance": 0, "division": 1},
                {"balance": 0, "division": 2},
                {"balance": 0, "division": 3},
                {"balance": 500000, "division": 4},
                {"balance": 0, "division": 5},
                {"balance": 250000, "division": 6},
                {"balance": 0, "division": 7},
            ],
        )
        # Test Action
        self.audit.update_wallet_division(force_refresh=False)

        # Expected Results
        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=2,
        )
        self.assertEqual(obj.balance, 0)

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=4,
        )
        self.assertEqual(obj.balance, 500000)

        obj = self.audit.ledger_corporation_division.get(
            corporation__eve_corporation__corporation_id=self.audit.eve_corporation.corporation_id,
            division_id=6,
        )
        self.assertEqual(obj.balance, 250000)

    def test_update_division_no_token(self):
        """
        Test updating the corporation division balances with no valid token.

        This test verifies that an appropriate error is raised when there is no valid token
        for the corporation.

        ### Expected Result
        - TokenError is raised indicating no valid token found.
        """
        # Test Data
        # Mock get_token to return None to simulate no valid token
        self.audit.get_token = MagicMock(return_value=None)

        # Test Action & Expected Result
        with self.assertRaises(TokenError) as context:
            self.audit.update_wallet_division(force_refresh=False)

        self.assertIn("No valid token found for corporation", str(context.exception))
