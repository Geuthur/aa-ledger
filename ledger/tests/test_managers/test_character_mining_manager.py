# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase
from eveuniverse.models import EveSolarSystem, EveType

# AA Ledger
from ledger.tests.testdata.esi_stub import esi_client_stub_openapi
from ledger.tests.testdata.generate_characteraudit import (
    create_characteraudit_from_evecharacter,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.managers.character_mining_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi")
@patch("ledger.models.characteraudit.CharacterMiningLedger.update_evemarket_price")
class TestCharacterMiningManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()
        cls.audit = create_characteraudit_from_evecharacter(1001)

        cls.eve_type = EveType.objects.get(id=17425)
        cls.eve_system = EveSolarSystem.objects.get(id=30004783)

    def test_update_mining_ledger(self, _, __, mock_esi):
        # given
        mock_esi.client = esi_client_stub_openapi
        self.audit.update_mining_ledger(force_refresh=False)

        obj = self.audit.ledger_character_mining.filter(
            date__contains="2014-10-29"
        ).first()
        self.assertEqual(obj.quantity, 5000)
        self.assertEqual(obj.system_id, 30004783)
        self.assertEqual(obj.type_id, 17425)
