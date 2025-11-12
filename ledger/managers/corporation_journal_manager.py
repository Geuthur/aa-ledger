# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.decorators import log_timing
from ledger.errors import DatabaseError
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.general import EveEntity
from ledger.providers import esi

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import CorporationsCorporationIdDivisionsGet as DivisionItem
    from esi.stubs import (
        CorporationsCorporationIdWalletsDivisionJournalGetItem as JournalItem,
    )

    # AA Ledger
    from ledger.models.corporationaudit import (
        CorporationAudit,
        CorporationWalletDivision,
    )

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationWalletQuerySet(models.QuerySet):
    # pylint: disable=duplicate-code
    def annotate_bounty_income(
        self,
    ) -> models.QuerySet:
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

    # pylint: disable=duplicate-code
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

    def aggregate_bounty(self) -> dict:
        """Aggregate bounty income."""
        return self.filter(ref_type__in=RefTypeManager.BOUNTY_PRIZES).aggregate(
            total_bounty=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_bounty"]

    def aggregate_ess(self) -> dict:
        """Aggregate ESS income."""
        return self.filter(ref_type__in=RefTypeManager.ESS_TRANSFER).aggregate(
            total_ess=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total_ess"]

    def aggregate_miscellaneous(self) -> dict:
        """Aggregate miscellaneous income (nur positive Beträge)."""
        return self.filter(
            ref_type__in=RefTypeManager.all_ref_types(), amount__gt=0
        ).aggregate(
            total_misc=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )[
            "total_misc"
        ]

    def aggregate_costs(self) -> dict:
        """Aggregate costs."""
        return self.filter(
            ref_type__in=RefTypeManager.all_ref_types(), amount__lt=0
        ).aggregate(
            total_costs=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )[
            "total_costs"
        ]

    # pylint: disable=too-many-positional-arguments, duplicate-code
    def aggregate_ref_type(
        self,
        ref_type: list,
        first_party=None,
        second_party=None,
        exclude=None,
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

        if exclude is not None:
            if isinstance(exclude, int):
                exclude = [exclude]
            qs = qs.exclude(first_party__in=exclude)

        if income:
            qs = qs.filter(amount__gt=0)
        else:
            qs = qs.filter(amount__lt=0)

        return qs.aggregate(
            total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total"]


class CorporationWalletManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a wallet journal entry from ESI data."""
        return corporation.update_section_if_changed(
            section=corporation.UpdateSection.WALLET_JOURNAL,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, audit: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch wallet journal entries from ESI data."""
        # AA Ledger
        # pylint: disable=import-outside-toplevel
        from ledger.models.corporationaudit import CorporationWalletDivision

        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = audit.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions = CorporationWalletDivision.objects.filter(corporation=audit)
        is_updated = False

        for division in divisions:
            # Make the ESI request
            operation = (
                esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                    corporation_id=audit.corporation.corporation_id,
                    division=division.division_id,
                    token=token,
                )
            )

            # pylint: disable=duplicate-code
            try:
                journal_items = operation.results(force_refresh=force_refresh)
                is_updated = True
            except HTTPNotModified:
                continue

            self._update_or_create_objs(division=division, objs=journal_items)
        # Raise if no update happened at all
        if not is_updated:
            raise HTTPNotModified(304, {"msg": "Wallet Journal has Not Modified"})

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        division: "CorporationWalletDivision",
        objs: list["JournalItem"],
    ) -> None:
        """Update or Create wallet journal entries from objs data."""
        _new_names = []
        _current_journal = set(
            list(
                self.filter(division=division)
                .order_by("-date")
                .values_list("entry_id", flat=True)[:20000]
            )
        )
        _current_eve_ids = set(
            list(EveEntity.objects.all().values_list("eve_id", flat=True))
        )

        items = []
        # pylint: disable=duplicate-code
        for item in objs:
            if item.id not in _current_journal:
                if item.second_party_id not in _current_eve_ids:
                    _new_names.append(item.second_party_id)
                    _current_eve_ids.add(item.second_party_id)
                if item.first_party_id not in _current_eve_ids:
                    _new_names.append(item.first_party_id)
                    _current_eve_ids.add(item.first_party_id)

                wallet_item = self.model(  # pylint: disable=duplicate-code
                    division=division,
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

                items.append(wallet_item)

        created_names = EveEntity.objects.create_bulk_from_esi(_new_names)

        if created_names:
            self.bulk_create(items)
        else:
            raise DatabaseError("DB Fail")

        logger.debug(
            "Created %s Journal Entries for %s",
            len(items),
            division.corporation.corporation_name,
        )


CorporationWalletManager = CorporationWalletManagerBase.from_queryset(
    CorporationWalletQuerySet
)


class CorporationDivisionQuerySet(models.QuerySet):
    pass


class CorporationDivisionManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return corporation.update_section_if_changed(
            section=corporation.UpdateSection.WALLET_DIVISION,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, audit: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]
        token = audit.get_token(scopes=req_scopes, req_roles=req_roles)

        # Make the ESI request
        operation = esi.client.Wallet.GetCorporationsCorporationIdWallets(
            corporation_id=audit.corporation.corporation_id,
            token=token,
        )
        division_items = operation.results(force_refresh=force_refresh)

        self._update_or_create_objs(corporation=audit, objs=division_items)

    @log_timing(logger)
    def update_or_create_esi_names(
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return corporation.update_section_if_changed(
            section=corporation.UpdateSection.WALLET_DIVISION_NAMES,
            fetch_func=self._fetch_esi_data_names,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data_names(
        self, audit: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director"]
        token = audit.get_token(scopes=req_scopes, req_roles=req_roles)

        # Make the ESI request
        operation = esi.client.Corporation.GetCorporationsCorporationIdDivisions(
            corporation_id=audit.corporation.corporation_id,
            token=token,
        )
        division_items = operation.results(force_refresh=force_refresh)

        self._update_or_create_objs_division(corporation=audit, objs=division_items)

    @transaction.atomic()
    def _update_or_create_objs_division(
        self,
        corporation: "CorporationAudit",
        objs: list["DivisionItem"],
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:  # list (hanger, wallet)
            for wallet in division.wallet:
                if wallet.division == 1:
                    name = _("Master Wallet")
                else:
                    name = getattr(wallet, "name", _("Unknown"))

                obj, created = self.get_or_create(
                    corporation=corporation,
                    division_id=wallet.division,
                    defaults={"balance": 0, "name": name},
                )
                if not created:
                    obj.name = name
                    obj.save()

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        corporation: "CorporationAudit",
        objs: list,
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:
            obj, created = self.get_or_create(
                corporation=corporation,
                division_id=division.division,
                defaults={
                    "balance": division.balance,
                    "name": _("Unknown"),
                },
            )

            if not created:
                obj.balance = division.balance
                obj.save()


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)
