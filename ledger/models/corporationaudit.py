"""
Corporation Audit Model
"""

# Django
from django.db import models

from allianceauth.eveonline.models import EveCorporationInfo

from ledger.hooks import get_extension_logger
from ledger.managers.corpaudit_manager import CorpAuditManager
from ledger.managers.corpjournal_manager import CorpWalletManager
from ledger.models.characteraudit import WalletJournalEntry

logger = get_extension_logger(__name__)


class CorporationAudit(models.Model):

    objects = CorpAuditManager()

    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="ledger_corporationaudit",
    )

    last_update_wallet = models.DateTimeField(null=True, default=None, blank=True)

    def __str__(self):
        return f"{self.corporation.corporation_name}'s Corporation Data"

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
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
        ]

    class Meta:
        default_permissions = ()
        permissions = (("corp_audit_admin_manager", "Has access to all Corporations"),)


class CorporationWalletDivision(models.Model):
    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_division",
    )
    name = models.CharField(max_length=100, null=True, default=None)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    division = models.IntegerField()

    class Meta:
        default_permissions = ()


class CorporationWalletJournalEntry(WalletJournalEntry):
    division = models.ForeignKey(CorporationWalletDivision, on_delete=models.CASCADE)

    objects = CorpWalletManager()

    def __str__(self):
        return f"Corporation Wallet Journal: {self.first_party.name} '{self.ref_type}' {self.second_party.name}: {self.amount} isk"

    @classmethod
    def get_visible(cls, user):
        corps_vis = CorporationAudit.objects.visible_to(user)
        return cls.objects.filter(division__corporation__in=corps_vis)
