from django.test import TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory


class TestAuthHooks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = UserMainFactory(permissions=["ledger.basic_access"])
        cls.html_menu = f"""
            <li class="d-flex flex-wrap m-2 p-2 pt-0 pb-0 mt-0 mb-0 me-0 pe-0">
                <i class="nav-link fas fa-book fa-fw fa-fw align-self-center me-3 active"></i>
                <a class="nav-link flex-fill align-self-center me-auto active" href="{reverse('ledger:ledger_index')}">
                    Geuthur - Ledger
                </a>
            </li>
        """

    def test_menu_hook(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ledger:ledger_index"))
        self.assertContains(response, self.html_menu, html=True)
