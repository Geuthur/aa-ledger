from datetime import datetime

from django.test import RequestFactory, TestCase
from django.urls import reverse

from app_utils.testing import create_user_from_evecharacter

from ledger.api.helpers import get_corporations
from ledger.api.managers.template_manager import (
    TemplateData,
    TemplateProcess,
    TemplateTotal,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_char_audit, load_corp_audit

MODULE_PATH = (
    "ledger.api.managers.template_manager"  # replace with the actual module path
)


class TestTemplateData(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.admin_access",
                "ledger.char_audit_admin_access",
            ],
        )

    def test_post_init_month_zero(self):
        # given
        request = self.factory.get(
            reverse("ledger:ledger_index")
        )  # replace with the actual path
        request.user = self.user
        # when
        data = TemplateData(request=request, request_id=1001, year=2022, month=0)
        # then
        self.assertEqual(data.current_date.month, datetime.now().month)

    def test_post_init_month_eleven(self):
        # given
        request = self.factory.get(
            reverse("ledger:ledger_index")
        )  # replace with the actual path
        request.user = self.user
        # when
        data = TemplateData(request=request, request_id=1001, year=2022, month=11)
        # then
        self.assertEqual(data.current_date.month, 11)


class Test(TestCase):
    def test_to_dict(self):
        # given
        template_total = TemplateTotal(
            bounty=100,
            bounty_day=50,
            bounty_hour=10,
            ess=200,
            ess_day=100,
            ess_hour=20,
            mining=300,
            mining_day=150,
            contract=400,
            contract_day=200,
            contract_hour=40,
            transaction=500,
            transaction_day=250,
            transaction_hour=50,
            donation=600,
            donation_day=300,
            donation_hour=60,
            production_cost=700,
            production_cost_day=350,
            production_cost_hour=70,
            market_cost=800,
            market_cost_day=400,
            market_cost_hour=80,
        )
        # when
        result = template_total.to_dict()
        # then
        self.assertEqual(
            result,
            {
                "bounty": {
                    "total_amount": 100,
                    "total_amount_day": 50,
                    "total_amount_hour": 10,
                },
                "ess": {
                    "total_amount": 200,
                    "total_amount_day": 100,
                    "total_amount_hour": 20,
                },
                "mining": {"total_amount": 300, "total_amount_day": 150},
                "contract": {
                    "total_amount": 400,
                    "total_amount_day": 200,
                    "total_amount_hour": 40,
                },
                "transaction": {
                    "total_amount": 500,
                    "total_amount_day": 250,
                    "total_amount_hour": 50,
                },
                "donation": {
                    "total_amount": 600,
                    "total_amount_day": 300,
                    "total_amount_hour": 60,
                },
                "production_cost": {
                    "total_amount": 700,
                    "total_amount_day": 350,
                    "total_amount_hour": 70,
                },
                "market_cost": {
                    "total_amount": 800,
                    "total_amount_day": 400,
                    "total_amount_hour": 80,
                },
            },
        )


class TestTemplateTotal(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_char_audit()
        load_corp_audit()
        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
                "ledger.admin_access",
                "ledger.char_audit_admin_access",
            ],
        )

    def test_char_template(self):
        # given
        request = self.factory.get(
            reverse("ledger:ledger_index")
        )  # replace with the actual path
        request.user = self.user

        corporations = get_corporations(request)

        main_id = 1001

        overall_mode = main_id == 0

        # Create the Ledger
        ledger_data = TemplateData(request, main_id, 2024, 3)
        ledger = TemplateProcess(corporations, ledger_data, overall_mode)
        context = {"character": ledger.corporation_template()}
        # when
        # TODO Create Model Data for Journal Entries
        assert "character" in context
