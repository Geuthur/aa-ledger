# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.core.cache import cache
from django.test import TestCase

# AA Ledger
from ledger.helpers.core import (
    add_info_to_context,
)

MODULE_PATH = "ledger.view_helpers.core"


class TestViewHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_add_info_to_context(self):
        # given
        request = MagicMock()
        request.user = MagicMock()
        request.user.id = 99999999

        context = {"theme": None}
        # when
        result = add_info_to_context(request, context)
        # then
        self.assertEqual(result, context)
