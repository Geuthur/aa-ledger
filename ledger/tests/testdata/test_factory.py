"""Test to ensure that the factories are working correctly."""

# AA Ledger
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.factory import (
    CharacterOwnerFactory,
    CorporationOwnerFactory,
    EveCorporationInfoFactory,
    EveEntityFactory,
    UserMainFactory,
)


class TestFactory(LedgerTestCase):
    """Test the factories."""

    def test_can_create_user(self):
        """Test that a user can be created."""
        user = UserMainFactory()
        self.assertTrue(user.has_perm("ledger.basic_access"))

    def test_can_create_character_owner(self):
        """Test that a character owner can be created."""
        owner = CharacterOwnerFactory()
        self.assertTrue(owner.eve_character)

    def test_can_create_corporation_owner(self):
        """Test that a corporation owner can be created."""
        owner = CorporationOwnerFactory()
        self.assertTrue(owner.eve_corporation)

    def test_can_create_character_owner_from_user(self):
        """Test that a character owner can be created from a user."""
        user = UserMainFactory()
        owner = CharacterOwnerFactory(user=user)
        self.assertEqual(owner.eve_character, user.profile.main_character)

    def test_can_create_corporation_owner_from_user(self):
        """Test that a corporation owner can be created from a user."""
        user = UserMainFactory()
        owner = CorporationOwnerFactory(user=user)
        self.assertEqual(owner.eve_corporation, user.profile.main_character.corporation)

    def test_can_create_eveentity(self):
        """Test that an EveEntity can be created."""
        entity = EveEntityFactory()
        self.assertTrue(entity.name)
        self.assertTrue(entity.category in ["character", "corporation", "alliance"])

    def test_can_create_custom_eveentity(self):
        """Test that a custom EveEntity can be created."""
        entity = EveEntityFactory(name="Test Corp", category="corporation")
        self.assertEqual(entity.name, "Test Corp")
        self.assertEqual(entity.category, "corporation")
