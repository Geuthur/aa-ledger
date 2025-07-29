# Standard Library
from unittest.mock import MagicMock

# Django
from django.test import TestCase

# AA Ledger
from ledger.templatetags.ledger import get_item, month_days, month_name, range_filter


class TestTemplateTags(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def test_month_name(self):
        # Test for valid month number
        self.assertEqual(month_name(1), "January")
        self.assertEqual(month_name(12), "December")

        # Test for invalid month number
        self.assertEqual(month_name(0), "")
        self.assertEqual(month_name(15), "")

    def test_month_days(self):
        # Test for a valid date
        date_info = {"year": 2023, "month": 2}
        self.assertEqual(month_days(date_info), list(range(1, 29)))

        # Test for a date with missing year
        date_info = {"month": 2}
        self.assertEqual(month_days(date_info), list(range(1, 29)))

        # Test for a date with missing month
        date_info = {"year": 2023}
        self.assertEqual(month_days(date_info), list(range(1, 32)))

    def test_range_filter(self):
        # Test for a valid value
        self.assertEqual(list(range_filter(5)), [1, 2, 3, 4, 5])

        # Test for zero value
        self.assertEqual(list(range_filter(0)), [])

        # Test for negative value
        self.assertEqual(list(range_filter(-3)), [])

    def test_get_item(self):
        # Test for valid key
        data = {"key": "value"}
        self.assertEqual(get_item(data, "key"), "value")

        # Test for invalid key
        self.assertEqual(get_item(data, "invalid_key"), {})

        # Test for non-dictionary input
        self.assertEqual(get_item("not a dict", "key"), {})
