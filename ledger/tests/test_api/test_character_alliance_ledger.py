# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse
from django.utils import timezone

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterJournalFactory,
    CharacterOwnerFactory,
    CorporationJournalFactory,
    CorporationOwnerFactory,
    DivisionFactory,
)

DATE = {"year": 2016, "month": 10, "day": 29, "hour": 0, "minute": 0, "second": 0}


class TestCharacterLedgerApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = CharacterOwnerFactory(user=cls.user)
        CharacterJournalFactory(
            character=cls.owner,
            amount=1000,
            date=timezone.now().replace(microsecond=0, **DATE),
            ref_type="bounty_prizes",
        )
        cls.url = (
            f"{reverse('ledger:index')}api/character/"
            f"{cls.owner.eve_character.character_id}/ledger/?year=2016&month=10&day=29"
        )

    def test_get_ledger_should_aggregate_directly_from_journal(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["characters"]), 1)
        self.assertEqual(data["characters"][0]["ledger"]["bounty"], 1000)

    def test_get_ledger_should_return_403_for_foreign_user(self):
        # Test Data
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestAllianceLedgerApi(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = CorporationOwnerFactory(user=cls.manage_user)
        division = DivisionFactory(corporation=cls.audit, balance=1000000)
        CorporationJournalFactory(
            division=division,
            amount=1000,
            date=timezone.now().replace(microsecond=0, **DATE),
            ref_type="bounty_prizes",
        )
        cls.url = (
            f"{reverse('ledger:index')}api/alliance/"
            f"{cls.audit.eve_corporation.alliance.alliance_id}/ledger/?year=2016&month=10&day=29"
        )

    def test_get_ledger_should_aggregate_directly_from_journal(self):
        # Test Data
        self.client.force_login(self.manage_user)

        # Test Action
        response = self.client.get(self.url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["corporations"]), 1)
        self.assertEqual(data["corporations"][0]["ledger"]["bounty"], 1000)
