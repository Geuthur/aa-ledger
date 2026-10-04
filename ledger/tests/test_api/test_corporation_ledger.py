# Standard Library
from http import HTTPStatus

# Django
from django.db import connection
from django.urls import reverse
from django.utils import timezone

# Alliance Auth (External Libs)
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
    EveEntityFactory,
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


class TestCorporationLedgerMembers(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.manage_user)
        division = DivisionFactory(corporation=cls.audit, division_id=1)
        cls.main = cls.manage_user.profile.main_character
        cls.alt = EveCharacterFactory()
        add_character_to_user(cls.manage_user, cls.alt)
        date = timezone.now().replace(
            year=2016, month=10, day=29, hour=0, minute=0, second=0, microsecond=0
        )
        # Create both parties first, the factory otherwise takes the next free ID.
        parties = {
            character: EveEntityFactory(
                eve_id=character.character_id,
                name=character.character_name,
                category="character",
            )
            for character in (cls.main, cls.alt)
        }
        for character, amount in ((cls.main, 1000), (cls.alt, 300)):
            CorporationJournalFactory(
                division=division,
                amount=amount,
                date=date,
                ref_type="bounty_prizes",
                first_party=parties[character],
            )
        cls.url = (
            f"{reverse('ledger:index')}api/corporation/"
            f"{cls.audit.eve_corporation.corporation_id}/ledger/"
            "?year=2016&month=10&day=29"
        )

    def test_get_ledger_should_return_the_contribution_of_every_character(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        entity = response.json()["entities"][0]
        self.assertEqual(entity["ledger"]["bounty"], 1300)
        bounty = {
            member["character_id"]: member["ledger"]["bounty"]
            for member in entity["members"]
        }
        self.assertEqual(
            bounty,
            {self.main.character_id: 1000, self.alt.character_id: 300},
        )
