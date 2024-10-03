import sys
from unittest.mock import patch

from django.test import TestCase

from ledger.hooks import get_extension_logger

MODULE_PATH = "ledger.hooks"


class TestTemplateTags(TestCase):
    def test_logger_fail(self):
        with self.assertRaises(TypeError):
            get_extension_logger(1234)
