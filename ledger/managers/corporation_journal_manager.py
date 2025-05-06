# Standard Library
from decimal import Decimal
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, Round
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__, app_settings
from ledger.constants import (
    ASSETS,
    BOUNTY_PRIZES,
    CONTRACT,
    DAILY_GOAL_REWARD,
    DONATION,
    ESS_TRANSFER,
    INCURSION,
    INSURANCE,
    LP,
    MARKET,
    MISSION_REWARD,
    PRODUCTION,
    RENTAL,
    SKILL,
    TRAVELING,
)
from ledger.decorators import log_timing
from ledger.errors import DatabaseError
from ledger.models.general import EveEntity
from ledger.providers import esi
from ledger.task_helpers.etag_helpers import etag_results

if TYPE_CHECKING:
    # AA Ledger
    from ledger.models.corporationaudit import (
        CorporationAudit,
        CorporationWalletDivision,
    )
    from ledger.models.general import UpdateSectionResult

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Filters
BOUNTY_FILTER = Q(ref_type__in=BOUNTY_PRIZES, amount__gt=0)
ESS_FILTER = Q(ref_type__in=ESS_TRANSFER, amount__gt=0)
INCURSION_FILTER = Q(ref_type__in=INCURSION, amount__gt=0)
MISSION_FILTER = Q(ref_type__in=MISSION_REWARD, amount__gt=0)
DAILY_GOAL_REWARD_FILTER = Q(ref_type__in=DAILY_GOAL_REWARD, amount__gt=0)
CITADEL_FILTER = Q(ref_type__in=PRODUCTION, amount__gt=0)

MISC_FILTER = Q(
    ref_type__in=[
        *ASSETS,
        *CONTRACT,
        *DAILY_GOAL_REWARD,
        *DONATION,
        *INCURSION,
        *INSURANCE,
        *MISSION_REWARD,
        *PRODUCTION,
        *MARKET,
        *TRAVELING,
        *LP,
    ],
    amount__gt=0,
)

COSTS_FILTER = Q(
    ref_type__in=[
        *ASSETS,
        *CONTRACT,
        *INSURANCE,
        *LP,
        *MARKET,
        *TRAVELING,
        *PRODUCTION,
        *SKILL,
        *RENTAL,
    ],
    amount__lt=0,
)


class CorporationWalletQuerySet(models.QuerySet):
    def _convert_corp_tax(self, ess: models.QuerySet) -> Decimal:
        """Convert corp tax to correct amount for character ledger"""
        amount = (ess / app_settings.LEDGER_CORP_TAX) * (
            100 - app_settings.LEDGER_CORP_TAX
        )
        return amount

    def annotate_bounty_income(self) -> models.QuerySet:
        return self.annotate(
            bounty_income=Coalesce(
                Sum(
                    "amount",
                    filter=(BOUNTY_FILTER),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )

    def annotate_ess_income(self, is_character: bool = False) -> models.QuerySet:
        if is_character:
            return self.annotate(
                ess_income=Round(
                    Coalesce(
                        Sum(
                            self._convert_corp_tax(F("amount")),
                            filter=(ESS_FILTER),
                        ),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                    precision=2,
                )
            )
        return self.annotate(
            ess_income=Coalesce(
                Sum(
                    F("amount"),
                    filter=(ESS_FILTER),
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
                    filter=(MISC_FILTER),
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
                    filter=Q(COSTS_FILTER) & Q(amount__lt=0),
                ),
                Value(0),
                output_field=DecimalField(),
            )
        )


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

        for division in divisions:
            current_page = 1
            total_pages = 1
            while current_page <= total_pages:
                journal_items_ob = esi.client.Wallet.get_corporations_corporation_id_wallets_division_journal(
                    corporation_id=corporation.corporation.corporation_id,
                    division=division.division_id,
                    page=current_page,
                )
                journal_items = etag_results(
                    journal_items_ob, token, force_refresh=force_refresh
                )

                self._update_or_create_objs(division, journal_items)
                current_page += 1

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

        _min_time = timezone.now()
        items = []
        for item in objs:
            _min_time = min(_min_time, item.get("date"))

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
        """Update or Create a wallet journal entry from ESI data."""
        return corporation.update_section_if_changed(
            section=corporation.UpdateSection.WALLET_DIVISION,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, corporation: "CorporationAudit", force_refresh: bool = False
    ) -> None:
        """Fetch wallet journal entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = corporation.get_token(scopes=req_scopes, req_roles=req_roles)

        names = {}

        division_obj = esi.client.Corporation.get_corporations_corporation_id_divisions(
            corporation_id=corporation.corporation.corporation_id,
        )

        division_items = etag_results(division_obj, token, force_refresh=force_refresh)

        for division in division_items.get("wallet"):
            names[division.get("division")] = division.get("name")

        divisions_items_obj = esi.client.Wallet.get_corporations_corporation_id_wallets(
            corporation_id=corporation.corporation.corporation_id
        )

        division_items = etag_results(
            divisions_items_obj, token, force_refresh=force_refresh
        )
        self._update_or_create_objs(corporation, division_items, names)

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        corporation: "CorporationAudit",
        objs: list,
        names: dict,
    ) -> None:
        """Update or Create wallet journal entries from objs data."""
        for division in objs:
            self.update_or_create(
                corporation=corporation,
                division_id=division.get("division"),
                defaults={
                    "balance": division.get("balance"),
                    "name": names.get(division.get("division"), "Unknown"),
                },
            )


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)
