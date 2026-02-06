# AA Ledger
from ledger.tests import LedgerTestCase

MODULE_PATH = "ledger.helpers.ledger_data"


class TestCharacterWalletJournalModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_footer_text_class(self):
        # AA Ledger
        from ledger.helpers.ledger_data import get_footer_text_class

        self.assertEqual(get_footer_text_class(10), "text-success")
        self.assertEqual(get_footer_text_class(-10), "text-danger")
        self.assertEqual(get_footer_text_class(0), "")
        self.assertEqual(get_footer_text_class(10, mining=True), "text-info")
