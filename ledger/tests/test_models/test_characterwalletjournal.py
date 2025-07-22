# Standard Library
from unittest.mock import PropertyMock, patch

# Django
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Ledger
from ledger.models.corporationaudit import (
    CorporationAudit,
)
from ledger.models.general import EveEntity
from ledger.tests.testdata.generate_characteraudit import (
    add_characteraudit_character_to_user,
    create_user_from_evecharacter_with_access,
)
from ledger.tests.testdata.generate_walletjournal import (
    create_wallet_journal_entry,
)
from ledger.tests.testdata.load_allianceauth import load_allianceauth
from ledger.tests.testdata.load_eveentity import load_eveentity
from ledger.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "ledger.models.corporationaudit"


class TestCharacterWalletJournalModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()
        load_eveentity()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001,
        )
        cls.audit = add_characteraudit_character_to_user(
            cls.user, cls.character_ownership.character.character_id
        )
        cls.eve_character_first_party = EveEntity.objects.get(eve_id=1001)
        cls.eve_character_second_party = EveEntity.objects.get(eve_id=1002)
        cls.journal_entry = create_wallet_journal_entry(
            journal_type="character",
            character=cls.audit,
            entry_id=1,
            amount=1000,
            balance=1000000,
            date=timezone.datetime.replace(
                timezone.now(),
                year=2024,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ),
            description="Test",
            first_party=cls.eve_character_first_party,
            second_party=cls.eve_character_second_party,
            ref_type="test",
        )

    def test_str(self):
        self.assertEqual(
            str(self.journal_entry),
            f"Character Wallet Journal: RefType: test - {self.eve_character_first_party.name} -> {self.eve_character_second_party.name}: 1000 ISK",
        )

    def test_get_visible_should_get_empty_list(self):
        self.assertEqual(
            list(self.journal_entry.get_visible(self.user)), [self.journal_entry]
        )
