# Standard Library
from http import HTTPStatus

# Django
from django.db import connection
from django.urls import reverse
from django.utils import timezone

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
)


class TestCorporationLedgerApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.manage_user)
        cls.division = DivisionFactory(
            corporation=cls.audit, division_id=1, balance=1000000
        )
        CorporationJournalFactory(
            division=cls.division,
            amount=1000,
            date=timezone.now().replace(
                year=2016, month=10, day=29, hour=0, minute=0, second=0, microsecond=0
            ),
            ref_type="bounty_prizes",
        )
        cls.base_url = (
            f"{reverse('ledger:index')}api/corporation/"
            f"{cls.audit.eve_corporation.corporation_id}"
        )
        cls.url = f"{cls.base_url}/ledger/?year=2016&month=10&day=29"

    def test_get_ledger_should_aggregate_directly_from_journal(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["entities"]), 1)
        self.assertEqual(data["entities"][0]["ledger"]["bounty"], 1000)

    def test_get_ledger_should_not_create_cache_tables(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        self.client.get(self.url)

        # Expected Result
        tables = connection.introspection.table_names()
        self.assertNotIn("ledger_corporationledgerentry", tables)
        self.assertNotIn("ledger_corporationbillboardentry", tables)

    def test_get_ledger_should_return_403_without_permission(self):
        # Test Data
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_ledger_should_return_years_and_divisions(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        data = response.json()
        self.assertEqual(data["years"], [2016])
        self.assertEqual(data["divisions"][0]["division_id"], 1)

    def test_get_ledger_should_filter_by_division(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(f"{self.url}&division_id=99")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["entities"], [])

    def test_get_ledger_should_not_return_html(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertNotIn("<", response.content.decode())

    def test_get_ledger_should_return_422_for_day_without_month(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(f"{self.base_url}/ledger/?year=2016&day=29")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)

    def test_get_details_should_return_category_totals(self):
        # Test Data
        self.client.force_login(self.manage_user)
        corporation_id = self.audit.eve_corporation.corporation_id

        # Test Action
        response = self.client.get(
            f"{self.base_url}/details/?year=2016&month=10&day=29"
            f"&entity_id={corporation_id}&section=single"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["total"]["summary"], 1000)
        self.assertEqual(data["summary"][0]["amount"], 1000)
        self.assertIsInstance(data["summary"][0]["ref_types"], list)

    def test_get_details_should_return_empty_response_without_data(self):
        # Test Data
        self.client.force_login(self.manage_user)
        corporation_id = self.audit.eve_corporation.corporation_id

        # Test Action
        response = self.client.get(
            f"{self.base_url}/details/?year=2010&entity_id={corporation_id}"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["summary"], [])
        self.assertEqual(response.json()["total"]["summary"], 0)
