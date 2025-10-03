"""
Corporation Audit Model
"""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.models import Token

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.managers.corporation_audit_manager import CorporationAuditManager
from ledger.managers.corporation_journal_manager import (
    CorporationDivisionManager,
    CorporationWalletManager,
)
from ledger.models.characteraudit import WalletJournalEntry
from ledger.models.general import (
    AuditBase,
    UpdateStatus,
)
from ledger.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationAudit(AuditBase):
    """A model to store corporation information."""

    class UpdateSection(models.TextChoices):
        WALLET_DIVISION_NAMES = "wallet_division_names", _("Divisions Names")
        WALLET_DIVISION = "wallet_division", _("Divisions")
        WALLET_JOURNAL = "wallet_journal", _("Wallet Journal")

        @classmethod
        def get_sections(cls) -> list[str]:
            """Return list of section values."""
            return [choice.value for choice in cls]

        @property
        def method_name(self) -> str:
            """Return method name for this section."""
            return f"update_{self.value}"

    corporation_name = models.CharField(max_length=100, null=True, default=None)

    active = models.BooleanField(default=True)

    corporation = models.OneToOneField(
        EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="ledger_corporationaudit",
    )

    objects = CorporationAuditManager()

    def __str__(self) -> str:
        try:
            return f"{self.corporation.corporation_name} ({self.id})"
        except AttributeError:
            return f"{self.corporation} ({self.id})"

    class Meta:
        default_permissions = ()
        permissions = (
            ("corp_audit_manager", "Has Access to own Corporations."),
            ("corp_audit_admin_manager", "Has access to all Corporations."),
        )

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

    @property
    def get_status(self) -> UpdateStatus:
        """Get the status of this corporation."""
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = CorporationAudit.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

    @property
    def update_status(self):
        return self.ledger_corporation_update_status

    def get_token(self, scopes, req_roles) -> Token:
        """Get the token for this corporation."""
        if "esi-characters.read_corporation_roles.v1" not in scopes:
            scopes.append("esi-characters.read_corporation_roles.v1")

        char_ids = EveCharacter.objects.filter(
            corporation_id=self.corporation.corporation_id
        ).values("character_id")

        tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

        for token in tokens:
            try:
                roles = esi.client.Character.GetCharactersCharacterIdRoles(
                    character_id=token.character_id, token=token
                ).result(force_refresh=True)

                has_roles = False
                for role in roles.roles:
                    if role in req_roles:
                        has_roles = True

                if has_roles:
                    return token
            except TokenError as e:
                logger.error(
                    "Token ID: %s (%s)",
                    token.pk,
                    e,
                )
        return False

    def update_wallet_division_names(self, force_refresh: bool) -> None:
        return self.ledger_corporation_division.update_or_create_esi_names(
            self, force_refresh=force_refresh
        )

    def update_wallet_division(self, force_refresh: bool) -> None:
        return self.ledger_corporation_division.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_wallet_journal(self, force_refresh: bool) -> None:
        return CorporationWalletJournalEntry.objects.update_or_create_esi(
            self, force_refresh=force_refresh
        )


class CorporationWalletDivision(models.Model):
    objects = CorporationDivisionManager()

    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_division",
    )
    name = models.CharField(max_length=100, null=True, default=None)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    division_id = models.IntegerField()

    class Meta:
        default_permissions = ()


class CorporationWalletJournalEntry(WalletJournalEntry):
    division = models.ForeignKey(
        CorporationWalletDivision,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_journal",
    )

    objects = CorporationWalletManager()

    def __str__(self):
        return f"Corporation Wallet Journal: RefType: {self.ref_type} - {self.first_party.name} -> {self.second_party.name}: {self.amount} ISK"

    @classmethod
    def get_visible(cls, user):
        corps_vis = CorporationAudit.objects.visible_to(user)
        return cls.objects.filter(division__corporation__in=corps_vis)


class CorporationUpdateStatus(UpdateStatus):
    """A Model to track the status of the last update."""

    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        related_name="ledger_corporation_update_status",
    )
    section = models.CharField(
        max_length=32, choices=CorporationAudit.UpdateSection.choices, db_index=True
    )

    def __str__(self) -> str:
        return f"{self.corporation} - {self.section} - {self.is_success}"
