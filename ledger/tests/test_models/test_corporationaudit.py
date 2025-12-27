# AA Ledger
from ledger.models.corporationaudit import CorporationOwner
from ledger.tests import LedgerTestCase
from ledger.tests.testdata.utils import (
    add_new_permission_to_user,
    create_owner_from_user,
)

MODULE_PATH = "ledger.models.corporationaudit"


class TestCorporationAuditModel(LedgerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.owner = create_owner_from_user(user=cls.user, owner_type="corporation")
        cls.owner2 = create_owner_from_user(user=cls.user2, owner_type="corporation")

    def test_str(self):
        """Test the string representation of CorporationOwner."""
        expected_str = CorporationOwner.objects.get(id=self.owner.pk)
        self.assertEqual(self.owner, expected_str)

    def test_get_esi_scopes(self):
        """
        Test the ESI scopes for CorporationOwner.

        ### Expected Result
        - Correct list of ESI scopes is returned.
        """
        self.assertEqual(
            self.owner.get_esi_scopes(),
            [
                # General
                "esi-search.search_structures.v1",
                "esi-universe.read_structures.v1",
                "esi-characters.read_corporation_roles.v1",
                # Mining
                "esi-industry.read_corporation_mining.v1",
                # wallets
                "esi-wallet.read_corporation_wallets.v1",
                "esi-markets.read_corporation_orders.v1",
                "esi-industry.read_corporation_jobs.v1",
                "esi-corporations.read_divisions.v1",
            ],
        )

    def test_visible_to_should_not_include_any_corporations(self):
        """
        Test access permissions for CorporationOwner without permissions.

        ### Expected Result
        - User without permissions cannot access any corporations.
        """
        corporation = CorporationOwner.objects.visible_to(self.user)
        self.assertNotIn(self.owner, corporation)
        self.assertNotIn(self.owner2, corporation)

    def test_visible_to_should_include_own_corporation_only(self):
        """
        Test access permissions for CorporationOwner with own corporation permission.

        ### Expected Result
        - User with own corporation permission can access their own corporation only.
        - User can not access other corporations.
        """
        self.user = add_new_permission_to_user(
            user=self.user, permission_name="ledger.advanced_access"
        )
        self.user.refresh_from_db()
        corporation = CorporationOwner.objects.visible_to(self.user)
        self.assertIn(self.owner, corporation)
        self.assertNotIn(self.owner2, corporation)
