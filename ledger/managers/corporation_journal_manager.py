# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.decorators import log_timing
from ledger.errors import DatabaseError, NotModifiedError
from ledger.helpers.etag import etag_results
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.general import EveEntity
from ledger.providers import esi

if TYPE_CHECKING:
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
        self, corporation: "CorporationAudit", force_refresh: bool = False
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

        token = corporation.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions = CorporationWalletDivision.objects.filter(corporation=corporation)

        # Get the count of divisions to track not modified
        division_count = divisions.count()
        not_modified = 0

        for division in divisions:
            current_page = 1
            total_pages = 1
            while current_page <= total_pages:
                journal_items_ob = esi.client.Wallet.get_corporations_corporation_id_wallets_division_journal(
                    corporation_id=corporation.corporation.corporation_id,
                    division=division.division_id,
                    page=current_page,
                    token=token.valid_access_token(),
                )

                journal_items_ob.request_config.also_return_response = True
                __, headers = journal_items_ob.result()
                total_pages = int(headers.headers.get("X-Pages", 1))

                logger.debug(
                    "Fetching Journal Items for %s - Division: %s - Page: %s/%s",
                    corporation.corporation.corporation_name,
                    division.division_id,
                    current_page,
                    total_pages,
                )

                try:
                    journal_items = etag_results(
                        journal_items_ob,
                        token,
                        force_refresh=force_refresh,
                    )
                except NotModifiedError:
                    not_modified += 1
                    logger.debug(
                        "NotModifiedError: %s - Division: %s - Page: %s",
                        corporation.corporation.corporation_name,
                        division.division_id,
                        current_page,
                    )
                    current_page += 1
                    continue

                self._update_or_create_objs(division, journal_items)
                current_page += 1

        # Ensure only raise NotModifiedError if all divisions returned NotModified
        if not_modified == division_count:
            raise NotModifiedError()

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        division: "CorporationWalletDivision",
        objs: list,
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
            if item.get("id") not in _current_journal:
                if item.get("second_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("second_party_id"))
                    _current_eve_ids.add(item.get("second_party_id"))
                if item.get("first_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("first_party_id"))
                    _current_eve_ids.add(item.get("first_party_id"))

                wallet_item = self.model(  # pylint: disable=duplicate-code
                    division=division,
                    amount=item.get("amount"),
                    balance=item.get("balance"),
                    context_id=item.get("context_id"),
                    context_id_type=item.get("context_id_type"),
                    date=item.get("date"),
                    description=item.get("description"),
                    first_party_id=item.get("first_party_id"),
                    entry_id=item.get("id"),
                    reason=item.get("reason"),
                    ref_type=item.get("ref_type"),
                    second_party_id=item.get("second_party_id"),
                    tax=item.get("tax"),
                    tax_receiver_id=item.get("tax_receiver_id"),
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
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director"]

        token = corporation.get_token(scopes=req_scopes, req_roles=req_roles)

        division_obj = esi.client.Corporation.get_corporations_corporation_id_divisions(
            corporation_id=corporation.corporation.corporation_id,
        )

        division_names = etag_results(division_obj, token, force_refresh=force_refresh)

        self._update_or_create_objs_division(corporation, division_names)

    def _fetch_esi_data(
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = corporation.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions_items_obj = esi.client.Wallet.get_corporations_corporation_id_wallets(
            corporation_id=corporation.corporation.corporation_id
        )

        division_balances = etag_results(
            divisions_items_obj, token, force_refresh=force_refresh
        )
        self._update_or_create_objs(corporation, division_balances)

    @transaction.atomic()
    def _update_or_create_objs_division(
        self,
        corporation: "CorporationAudit",
        objs: list,
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs.get("wallet"):
            if division.get("division") == 1:
                name = _("Master Wallet")
            else:
                name = division.get("name", _("Unknown"))

            obj, created = self.get_or_create(
                corporation=corporation,
                division_id=division.get("division"),
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
                division_id=division.get("division"),
                defaults={
                    "balance": division.get("balance"),
                    "name": _("Unknown"),
                },
            )

            if not created:
                obj.balance = division.get("balance")
                obj.save()


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)
