from unittest.mock import MagicMock, call, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_ledger import load_ledger_all
from ledger.tests.testdata.load_planetary import load_planetary

MODULE_PATH = "ledger.tasks"


class TestTasks(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_allianceauth()
        load_ledger_all()
        load_planetary()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.user2, cls.character_ownership2 = create_user_from_evecharacter(
            1002,
            permissions=[
                "ledger.basic_access",
            ],
        )

        cls.token = cls.user.token_set.first()
        cls.corporation = cls.character_ownership.character.corporation
