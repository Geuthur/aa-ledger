"""
Corporation Audit Model
"""

from typing import List

# Django
from django.db import models

from allianceauth.eveonline.models import EveCorporationInfo

from ledger.hooks import get_extension_logger
from ledger.managers.corpaudit_manager import CorpAuditManager
from ledger.models.characteraudit import WalletJournalEntry

logger = get_extension_logger(__name__)


class CorpSteuer(models.Model):
    character_id = models.PositiveIntegerField(null=True)
    character_name = models.CharField(max_length=100, null=True)
    status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    date = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        default_permissions = ()
        permissions = (("steuer_admin_access", "Has access to Tax Administration"),)


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
    def get_esi_scopes(cls) -> List[str]:
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
        permissions = (
            (
                "corp_audit_admin_access",
                "Has access to all Corporation Audit",
            ),
        )


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

    def __str__(self):
        return str(
            "Corporatuin Wallet Journal: %s '%s' %s: %s isk",
            self.first_party.name,
            self.ref_type,
            self.second_party.name,
            self.amount,
        )
