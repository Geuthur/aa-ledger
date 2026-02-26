"""
Character Audit Model
"""

# Django
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eve_sde.models import ItemType
from eve_sde.models.map import SolarSystem
from eveuniverse.models import EveMarketPrice

# AA Ledger
from ledger import __title__
from ledger.app_settings import (
    LEDGER_CACHE_KEY,
    LEDGER_USE_COMPRESSED,
)
from ledger.errors import TokenDoesNotExist
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.managers.character_audit_manager import (
    CharacterAuditManager,
)
from ledger.managers.character_journal_manager import CharWalletManager
from ledger.managers.character_mining_manager import CharacterMiningLedgerEntryManager
from ledger.models.general import (
    UpdateSectionResult,
    UpdateStatusBaseModel,
    WalletJournalEntry,
)
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    UpdateManager,
    UpdateStatus,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class CharacterOwner(models.Model):
    """A model to store character information."""

    objects: CharacterAuditManager = CharacterAuditManager()

    class Meta:
        default_permissions = ()
        permissions = (
            ("char_audit_manager", "Has access to all characters for own Corp"),
            ("char_audit_admin_manager", "Has access to all characters"),
        )

    id = models.AutoField(primary_key=True)

    character_name = models.CharField(max_length=100, null=True, default=None)

    eve_character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="ledger_character"
    )

    active = models.BooleanField(default=True)

    balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    def __str__(self) -> str:
        try:
            return f"{self.eve_character.character_name} ({self.id})"
        except AttributeError:
            return f"{self.character_name} ({self.id})"

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            # Mining Ledger
            "esi-industry.read_character_mining.v1",
            # Wallet / Market /  Contracts
            "esi-wallet.read_character_wallet.v1",
            "esi-contracts.read_character_contracts.v1",
            # Planetary Interaction
            "esi-planets.manage_planets.v1",
        ]

    @property
    def get_status(self) -> UpdateStatusBaseModel:
        """Get the status of this character."""
        if self.active is False:
            return UpdateStatus.DISABLED

        qs = CharacterOwner.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return UpdateStatus(total_update_status)

    @cached_property
    def alt_ids(self) -> models.QuerySet[EveCharacter]:
        """Get all alt IDs for this Owner."""
        alt_ids = (
            EveCharacter.objects.filter(
                character_ownership__user=self.eve_character.character_ownership.user
            )
            .order_by("character_id")
            .values_list("character_id", flat=True)
        )
        return alt_ids

    @cached_property
    def is_orphan(self) -> bool:
        """
        Return True if this character is an orphan else False.

        An orphan is a character that is not owned anymore by a user.
        """
        return self.character_ownership is None

    @cached_property
    def character_ownership(self) -> bool:
        """
        Return the character ownership object of this character.
        """
        try:
            return self.eve_character.character_ownership
        except ObjectDoesNotExist:
            return None

    @property
    def update_manager(self):
        """Return the Update Manager helper for this owner."""
        return UpdateManager(
            owner=self,
            update_section=CharacterUpdateSection,
            update_status=CharacterUpdateStatus,
        )

    @property
    def mining_ledger(self):
        """Get the mining ledger for this character."""
        return self.ledger_character_mining

    @property
    def wallet_journal(self):
        """Get the wallet journal for this character."""
        return self.ledger_character_journal

    @property
    def update_status(self):
        return self.ledger_update_status

    def get_portrait(self, size: int = 64, as_html: bool = False) -> str:
        """
        Get the character portrait URL.

        Args:
            size (int, optional): The size of the portrait.
            as_html (bool, optional): Whether to return the portrait as an HTML img tag.
        Returns:
            str: The URL of the character portrait or an HTML img tag.
        """
        return get_character_portrait_url(
            character_id=self.eve_character.character_id,
            size=size,
            character_name=self.eve_character.character_name,
            as_html=as_html,
        )

    def get_token(self, scopes=None) -> Token:
        """Get the token for this character."""
        if self.is_orphan:  # pylint: disable=using-constant-test
            raise TokenDoesNotExist(
                f"Character {self} is an orphan and has no token."
            ) from None

        token = (
            Token.objects.filter(character_id=self.eve_character.character_id)
            .require_scopes(scopes if scopes else self.get_esi_scopes())
            .require_valid()
            .first()
        )
        if not token:
            raise TokenDoesNotExist(
                f"Token does not exist for {self} with scopes {scopes}"
            )
        return token

    def update_wallet_journal(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_journal.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_mining_ledger(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_mining.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_planets(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_planet.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_planets_details(self, force_refresh: bool) -> UpdateSectionResult:
        return self.ledger_character_planet_details.update_or_create_esi(
            self, force_refresh=force_refresh
        )


class CharacterWalletJournalEntry(WalletJournalEntry):
    objects: CharWalletManager = CharWalletManager()

    class Meta:
        indexes = (
            models.Index(fields=["character"]),
            models.Index(fields=["date"]),
            models.Index(fields=["amount"]),
            models.Index(fields=["entry_id"]),
            models.Index(fields=["ref_type"]),
            models.Index(fields=["first_party"]),
            models.Index(fields=["second_party"]),
        )
        default_permissions = ()

    character = models.ForeignKey(
        CharacterOwner,
        on_delete=models.CASCADE,
        related_name="ledger_character_journal",
    )

    def __str__(self):
        return f"Character Wallet Journal: RefType: {self.ref_type} - {self.first_party} -> {self.second_party}: {self.amount} ISK"

    @classmethod
    def get_visible(cls, user):
        chars_vis = CharacterOwner.objects.visible_to(user)
        return cls.objects.filter(character__in=chars_vis)


class CharacterMiningLedger(models.Model):
    objects: CharacterMiningLedgerEntryManager = CharacterMiningLedgerEntryManager()

    class Meta:
        default_permissions = ()

    id = models.CharField(max_length=50, primary_key=True)
    character = models.ForeignKey(
        CharacterOwner, on_delete=models.CASCADE, related_name="ledger_character_mining"
    )
    date = models.DateTimeField()
    type = models.ForeignKey(
        ItemType, on_delete=models.CASCADE, related_name="ledger_evetype"
    )
    system = models.ForeignKey(
        SolarSystem, on_delete=models.CASCADE, related_name="ledger_evesolarsystem"
    )
    quantity = models.IntegerField()

    price_per_unit = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, default=None
    )

    @staticmethod
    def create_primary_key(character_id, mining_record):
        return f"{mining_record.date.strftime('%Y%m%d')}-{mining_record.type_id}-{character_id}-{mining_record.solar_system_id}"

    @staticmethod
    def update_evemarket_price():  # Dont want to make a task only for this
        """Update Prices for the EveMarketPrice."""
        updated = 0
        cached_update = cache.get(f"{LEDGER_CACHE_KEY}-eve-market-price", False)
        if cached_update is False:
            updated = EveMarketPrice.objects.update_from_esi()
            cache.set(
                f"{LEDGER_CACHE_KEY}-eve-market-price", None, (60 * 60 * 24)
            )  # Cache for 24 hours
            logger.debug(f"Updated {updated} for entries EveMarketPrice")
        return updated

    def get_npc_price(self):
        """Get the NPC price for the type."""
        try:
            if LEDGER_USE_COMPRESSED:
                type_name = f"Compressed {self.type.name}"
                # price = ItemType.objects.get(name=type_name).market_price.average_price
                price = EveMarketPrice.objects.get(
                    eve_type__name=type_name
                ).average_price
            else:
                price = EveMarketPrice.objects.get(eve_type=self.type).average_price
        except (EveMarketPrice.DoesNotExist, ItemType.DoesNotExist):
            price = None
        return price

    def __str__(self) -> str:
        return f"{self.character} {self.id}"


class CharacterUpdateStatus(UpdateStatusBaseModel):
    """A Model to track the status of the last update."""

    owner = models.ForeignKey(
        CharacterOwner, on_delete=models.CASCADE, related_name="ledger_update_status"
    )
    section = models.CharField(
        max_length=32, choices=CharacterUpdateSection.choices, db_index=True
    )

    def __str__(self) -> str:
        return f"{self.owner} - {self.section}"

    class Meta:
        default_permissions = ()
