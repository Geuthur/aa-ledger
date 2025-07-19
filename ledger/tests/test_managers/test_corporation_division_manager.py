# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter

# AA Ledger
# AA TaxSystem
from ledger.tests.testdata.esi_stub import esi_client_stub
from ledger.tests.testdata.generate_corporationaudit import (
    create_corporationaudit_from_user,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.corporation_journal_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".etag_results")
class TestDivisionManager(NoSocketsTestCase):
    """Test Division Manager for Corporation Divisions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )
        cls.audit = create_corporationaudit_from_user(cls.user)

    def test_update_division_names(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        self.audit.update_wallet_division_names(force_refresh=False)

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.name, "Rechnungen")

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.name, "Ship Replacment Abteilung")

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.name, "Partner")

    def test_update_division(self, mock_etag, mock_esi):
        # given
        mock_esi.client = esi_client_stub
        mock_etag.side_effect = lambda ob, token, force_refresh=False: ob.results()

        self.audit.update_wallet_division(force_refresh=False)

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=2
        )
        self.assertEqual(obj.balance, 0)

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=4
        )
        self.assertEqual(obj.balance, 1600000000)

        obj = self.audit.ledger_corporation_division.get(
            corporation__corporation__corporation_id=2001, division_id=6
        )
        self.assertEqual(obj.balance, 0)
