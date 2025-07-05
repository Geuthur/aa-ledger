# Django
from django.test import RequestFactory, TestCase

# AA Ledger
from ledger.helpers.core import (
    add_info_to_context,
)
from ledger.tests.testdata.generate_corporationaudit import (
    add_corporationaudit_corporation_to_user,
    create_user_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001, permissions=["ledger.basic_access"]
        )
        cls.audit = add_corporationaudit_corporation_to_user(
            cls.user, cls.character_ownership.character.character_id
        )

    def test_add_info_to_context(self):
        # given
        request = self.factory.get("/")
        request.user = self.user

        context = {
            "theme": None,
            "issues": [],
        }
        # when
        result = add_info_to_context(request, context)
        # then
        self.assertEqual(result, context)
