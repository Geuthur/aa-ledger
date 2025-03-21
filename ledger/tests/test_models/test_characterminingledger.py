from django.test import TestCase
from django.utils import timezone
from eveuniverse.models import EveSolarSystem, EveType

from ledger.models.characteraudit import CharacterMiningLedger
from ledger.tests.testdata.generate_characteraudit import (
    add_charactermaudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_miningledger import create_miningledger
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.corporationaudit"


class TestCharacterMiningLedgerModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )
        cls.audit = add_charactermaudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        cls.eve_type = EveType.objects.get(id=17425)
        cls.eve_system = EveSolarSystem.objects.get(id=30004783)

        cls.miningentry = create_miningledger(
            character=cls.audit,
            id=1,
            date=timezone.now(),
            type=cls.eve_type,
            system=cls.eve_system,
            quantity=100,
        )
        cls.miningrecord = {
            "date": timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            "type_id": 1,
            "solar_system_id": 1,
        }

    def test_str(self):
        self.assertEqual(str(self.miningentry), "Gneuten's Character Data 1")

    def test_create_primary_key(self):
        # when
        primary_key = CharacterMiningLedger.create_primary_key(
            self.audit.character.character_id, self.miningrecord
        )
        # then
        self.assertEqual(primary_key, "20240101-1-1001-1")
