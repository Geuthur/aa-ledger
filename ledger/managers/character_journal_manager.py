# Standard Library
from decimal import Decimal
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

# AA Ledger
from ledger import __title__
from ledger.app_settings import LEDGER_BULK_BATCH_SIZE
from ledger.decorators import log_timing
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.helpers.update_manager import CharacterUpdateSection
from ledger.providers import AppLogger, esi

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import CharactersCharacterIdWalletJournalGetItem

    # AA Ledger
    from ledger.models.characteraudit import (
        CharacterOwner,
    )
    from ledger.models.characteraudit import (
        CharacterWalletJournalEntry as CharacterWalletJournalEntryContext,
    )
    from ledger.models.general import UpdateSectionResult


logger = AppLogger(get_extension_logger(__name__), __title__)


class CharWalletIncomeFilter(models.QuerySet):
    # PvE - Income
    def annotate_bounty_income(self) -> models.QuerySet:
        return self.annotate(
            bounty_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.BOUNTY_PRIZES, amount__gt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess_income(self) -> models.QuerySet:
        return self.annotate(
            ess_income=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.ESS_TRANSFER, amount__gt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletOutSideFilter(CharWalletIncomeFilter):
    def annotate_miscellaneous(self) -> models.QuerySet:
        return self.annotate(
            miscellaneous=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__gt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_costs(self) -> models.QuerySet:
        return self.annotate(
            costs=Coalesce(
                Sum(
                    "amount",
                    filter=Q(ref_type__in=RefTypeManager.all_ref_types(), amount__lt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


class CharWalletCostQueryFilter(CharWalletOutSideFilter):
    pass


# pylint: disable=used-before-assignment
class CharWalletQuerySet(CharWalletCostQueryFilter):
    def aggregate_bounty(self) -> dict:
        """Aggregate bounty income."""
        return Decimal(
            self.filter(ref_type__in=RefTypeManager.BOUNTY_PRIZES).aggregate(
                total_bounty=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )["total_bounty"]
        )

    def aggregate_ess(self) -> dict:
        """Aggregate ESS income."""
        return Decimal(
            self.filter(ref_type__in=RefTypeManager.ESS_TRANSFER).aggregate(
                total_ess=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
            )["total_ess"]
        )

    def aggregate_costs(self, first_party=None, second_party=None) -> dict:
        """Aggregate costs. first_party wird für donation exkludiert."""
        qs = self
        cost_types = RefTypeManager.all_ref_types()

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            qs = qs.filter(first_party__in=first_party)

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            qs = qs.filter(Q(ref_type__in=cost_types))
        else:
            qs = qs.filter(Q(ref_type__in=cost_types))

        qs = qs.filter(amount__lt=0)
        return Decimal(
            qs.aggregate(
                total_costs=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )["total_costs"]
        )

    def aggregate_miscellaneous(self, first_party=None, second_party=None) -> dict:
        """Aggregate miscellaneous income. first_party wird nur für donation angewandt."""
        qs = self

        misc_types = RefTypeManager.all_ref_types()

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            qs = qs.filter(Q(ref_type__in=misc_types))
        else:
            qs = qs.filter(Q(ref_type__in=misc_types))

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            qs = qs.filter(second_party__in=second_party)

        qs = qs.filter(amount__gt=0)
        return Decimal(
            qs.aggregate(
                total_misc=Coalesce(
                    Sum("amount"), Value(0), output_field=DecimalField()
                )
            )["total_misc"]
        )

    def aggregate_ref_type(
        self,
        ref_type: list,
        first_party=None,
        second_party=None,
        income: bool = False,
    ) -> dict:
        """Aggregate income by ref_type."""
        qs = self.filter(ref_type__in=ref_type)

        if first_party is not None:
            if isinstance(first_party, int):
                first_party = [first_party]
            qs = qs.filter(first_party__in=first_party)

        if second_party is not None:
            if isinstance(second_party, int):
                second_party = [second_party]
            qs = qs.filter(second_party__in=second_party)

        if income:
            qs = qs.filter(amount__gt=0)
        else:
            qs = qs.filter(amount__lt=0)

        return Decimal(
            qs.aggregate(
                total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
            )["total"]
        )


class CharWalletManager(models.Manager["CharacterWalletJournalEntryContext"]):
    def get_queryset(self) -> CharWalletQuerySet:
        return CharWalletQuerySet(self.model, using=self._db)

    # pylint: disable=duplicate-code
    def annotate_bounty_income(self) -> models.QuerySet:
        """Annotate bounty income."""
        return self.get_queryset().annotate_bounty_income()

    # pylint: disable=duplicate-code
    def annotate_ess_income(self) -> models.QuerySet:
        """Annotate ess income."""
        return self.get_queryset().annotate_ess_income()

    # pylint: disable=duplicate-code
    def annotate_miscellaneous(self) -> models.QuerySet:
        """Annotate miscellaneous income."""
        return self.get_queryset().annotate_miscellaneous()

    # pylint: disable=duplicate-code
    def annotate_costs(self) -> models.QuerySet:
        """Annotate costs."""
        return self.get_queryset().annotate_costs()

    # pylint: disable=duplicate-code
    def aggregate_bounty(self) -> dict:
        """Aggregate bounty income."""
        return self.get_queryset().aggregate_bounty()

    # pylint: disable=duplicate-code
    def aggregate_ess(self) -> dict:
        """Aggregate ess income."""
        return self.get_queryset().aggregate_ess()

    # pylint: disable=duplicate-code
    def aggregate_costs(self, first_party=None, second_party=None) -> dict:
        """Aggregate costs."""
        return self.get_queryset().aggregate_costs(
            first_party=first_party, second_party=second_party
        )

    # pylint: disable=duplicate-code
    def aggregate_miscellaneous(self, first_party=None, second_party=None) -> dict:
        """Aggregate miscellaneous income."""
        return self.get_queryset().aggregate_miscellaneous(
            first_party=first_party, second_party=second_party
        )

    # pylint: disable=duplicate-code
    def aggregate_ref_type(
        self,
        ref_type: list,
        first_party=None,
        second_party=None,
        income: bool = False,
    ) -> dict:
        """Aggregate income by ref_type."""
        return self.get_queryset().aggregate_ref_type(
            ref_type=ref_type,
            first_party=first_party,
            second_party=second_party,
            income=income,
        )

    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "CharacterOwner", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create a wallet journal entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CharacterUpdateSection.WALLET_JOURNAL,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(self, owner: "CharacterOwner", force_refresh: bool) -> None:
        """Fetch wallet journal entries from ESI data."""
        req_scopes = ["esi-wallet.read_character_wallet.v1"]
        token = owner.get_token(scopes=req_scopes)

        operation = esi.client.Wallet.GetCharactersCharacterIdWalletJournal(
            character_id=owner.eve_character.character_id,
            token=token,
        )

        journal_items = operation.results(
            force_refresh=force_refresh,
        )

        self._update_or_create_objs(character=owner, objs=journal_items)

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        character: "CharacterOwner",
        objs: list["CharactersCharacterIdWalletJournalGetItem"],
    ) -> None:
        """Update or Create wallet journal entries from objs data."""
        # pylint: disable=import-outside-toplevel
        # AA Ledger
        from ledger.models.general import EveEntity

        _current_journal = self.filter(character=character).values_list(
            "entry_id", flat=True
        )
        _current_eve_ids = list(
            EveEntity.objects.all().values_list("eve_id", flat=True)
        )

        _new_names = []

        items = []
        for item in objs:
            if item.id not in _current_journal:
                if item.second_party_id not in _current_eve_ids:
                    _new_names.append(item.second_party_id)
                    _current_eve_ids.append(item.second_party_id)
                if item.first_party_id not in _current_eve_ids:
                    _new_names.append(item.first_party_id)
                    _current_eve_ids.append(item.first_party_id)

                asset_item = self.model(
                    character=character,
                    amount=item.amount,
                    balance=item.balance,
                    context_id=item.context_id,
                    context_id_type=item.context_id_type,
                    date=item.date,
                    description=item.description,
                    first_party_id=item.first_party_id,
                    entry_id=item.id,
                    reason=item.reason,
                    ref_type=item.ref_type,
                    second_party_id=item.second_party_id,
                    tax=item.tax,
                    tax_receiver_id=item.tax_receiver_id,
                )
                items.append(asset_item)

        created_names = EveEntity.objects.create_bulk_from_esi(_new_names)

        if created_names:
            self.bulk_create(items, batch_size=LEDGER_BULK_BATCH_SIZE)
        else:
            raise TokenError("ESI Fail")
