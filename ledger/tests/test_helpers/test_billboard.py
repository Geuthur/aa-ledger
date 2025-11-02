# Standard Library
from unittest.mock import MagicMock, Mock, patch

# Django
from django.core.cache import cache
from django.test import TestCase

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

MODULE_PATH = "ledger.helpers.etag"
