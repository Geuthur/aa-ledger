from django.test import TestCase

from ledger.templatetags.ledger import ledger_init


class TestTemplateTags(TestCase):
    def test_ledger_init(self):
        result = ledger_init()
        self.assertIsNone(result)
