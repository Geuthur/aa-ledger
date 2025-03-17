from unittest.mock import MagicMock, patch

from django.test import TestCase
from esi.models import Token

from ledger.task_helpers.core_helpers import (
    get_token,
)

MODULE_PATH = "ledger.task_helpers.core_helpers"


class CoreHelpersTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.mock_token = MagicMock(spec=Token)
        cls.mock_token.character_id = 1001
        cls.mock_token.valid_access_token.return_value = "token"

    @patch(MODULE_PATH + ".Token.objects.filter")
    def test_get_token(self, mock_token):
        mock_token.return_value.require_scopes.return_value.require_valid.return_value.first.return_value = (
            self.mock_token
        )
        token = get_token(1001, "esi-characters.read_notifications.v1")

        self.assertEqual(token.character_id, 1001)
        self.assertEqual(token.valid_access_token(), "token")

    def test_get_token_no_token(self):
        token = get_token(1001, "esi-characters.read_notifications.v1")

        self.assertFalse(token)
