# Standard Library
from decimal import Decimal
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.character import create_ledger_details
from ledger.api.helpers.core import (
    get_alliance_or_none,
    get_available_years,
)
from ledger.api.schema import (
    BillboardSchema,
    DateFilter,
    EntitySchema,
    ErrorSchema,
    LedgerDetailsResponse,
    LedgerResponse,
    LedgerSchema,
    OwnerSchema,
    Section,
    UpdateStatusSchema,
)
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.eveonline import get_alliance_logo_url, get_corporation_logo_url
from ledger.models.corporationaudit import (
    CorporationOwner,
    CorporationWalletJournalEntry,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class LedgerAllianceSchema(Schema):
    corporation: EntitySchema
    ledger: LedgerSchema
    update_status: UpdateStatusSchema | None = None


class AllianceLedgerResponse(LedgerResponse):
    """
    Schema for Alliance Ledger API Response

    Attributes:
        corporations (list[LedgerAllianceSchema]): A list of ledger entities associated with the alliance.
    """

    corporations: list[LedgerAllianceSchema]


class AllianceApiEndpoints:
    tags = ["Alliance"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "alliance/{alliance_id}/ledger/",
            response={
                HTTPStatus.OK: AllianceLedgerResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the ledger of an alliance and its corporations",
        )
        def get_alliance_ledger(
            request: WSGIRequest, alliance_id: int, filters: Query[DateFilter]
        ):
            return self._ledger_api_response(
                request=request, alliance_id=alliance_id, filters=filters
            )

    # pylint: disable=too-many-locals
    def generate_corporation_data(
        self,
        owner: EveAllianceInfo,
        filters: DateFilter,
        user_corp_ids: set[int] | None = None,
    ) -> tuple[list[LedgerAllianceSchema], BillboardSchema]:
        """
        Generate the ledger and billboard data for all corporations of the alliance.

        Args:
            owner (EveAllianceInfo): The alliance owner object.
            filters (DateFilter): The requested date range.
            user_corp_ids (set[int] | None): Corporation IDs of the requesting user.
        Returns:
            tuple[list[LedgerAllianceSchema], BillboardSchema]: Ledger rows and chart data.
        """
        corporations = CorporationOwner.objects.filter(
            eve_corporation__alliance__alliance_id=owner.alliance_id
        )
        corporation_ids = [corp.eve_corporation.corporation_id for corp in corporations]

        corporations_journal = filters.filter(
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__in=corporations
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                Q(first_party_id__in=corporation_ids)
                & Q(second_party_id__in=corporation_ids)
            )
        )

        alliance_ledger_list: list[LedgerAllianceSchema] = []
        for corporation in corporations:
            corporation_id = corporation.eve_corporation.corporation_id
            wallet_journal = filters.filter(
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation=corporation
                )
                # Exclude Zero Amount Entries
                .exclude(amount=Decimal("0.00"))
                # Exclude Internal Transfers
                .exclude(first_party_id=corporation_id, second_party_id=corporation_id)
            )

            if not wallet_journal.exists():
                continue

            bounty = wallet_journal.aggregate_bounty()
            ess = wallet_journal.aggregate_ess()
            miscellaneous = wallet_journal.aggregate_miscellaneous()
            costs = wallet_journal.aggregate_costs()

            is_member = bool(user_corp_ids and corporation_id in user_corp_ids)
            alliance_ledger_list.append(
                LedgerAllianceSchema(
                    corporation=EntitySchema(
                        entity_id=corporation_id,
                        entity_name=corporation.eve_corporation.corporation_name,
                        icon=get_corporation_logo_url(
                            corporation_id=corporation_id,
                            corporation_name=corporation.eve_corporation.corporation_name,
                        ),
                        is_member=is_member,
                    ),
                    ledger=LedgerSchema(
                        bounty=bounty,
                        ess=ess,
                        miscellaneous=miscellaneous,
                        costs=costs,
                        total=sum([bounty, ess, miscellaneous, costs]),
                    ),
                    update_status=UpdateStatusSchema(status=corporation.get_status),
                )
            )

        xy_chart, chord_chart = BillboardSystem().create_billboards(
            filters=filters,
            wallet_journal=corporations_journal,
            ledger_list=alliance_ledger_list,
        )
        return alliance_ledger_list, BillboardSchema(
            xy_chart=xy_chart, chord_chart=chord_chart
        )

    def _ledger_api_response(
        self, request, alliance_id: int, filters: DateFilter
    ) -> AllianceLedgerResponse | tuple[int, dict]:
        """Build the ledger response for an alliance and the given date."""
        perms, owner = get_alliance_or_none(request=request, alliance_id=alliance_id)

        if owner is None:
            return HTTPStatus.NOT_FOUND, {"error": _("Alliance not found in Ledger.")}

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this alliance.")
            }

        user_corp_ids: set[int] = set()
        if request.user.is_authenticated:
            user_corp_ids = set(
                CharacterOwnership.objects.filter(user=request.user).values_list(
                    "character__corporation_id", flat=True
                )
            )

        corporation_ledger_list, billboard = self.generate_corporation_data(
            owner=owner, filters=filters, user_corp_ids=user_corp_ids
        )

        return AllianceLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.alliance_id,
                character_name=owner.alliance_name,
                icon=get_alliance_logo_url(
                    alliance_id=owner.alliance_id,
                    alliance_name=owner.alliance_name,
                ),
            ),
            corporations=corporation_ledger_list,
            billboard=billboard,
            years=get_available_years(
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation__eve_corporation__alliance__alliance_id=owner.alliance_id
                )
            ),
        )


class AllianceDetailsApiEndpoints:
    tags = ["Alliance Details"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "alliance/{alliance_id}/details/",
            response={
                HTTPStatus.OK: LedgerDetailsResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the income and cost breakdown of an alliance entity",
        )
        def get_alliance_ledger_details(
            request: WSGIRequest,
            alliance_id: int,
            entity_id: int,
            filters: Query[DateFilter],
            section: Section = "summary",
        ):
            return self._ledger_details_api_response(
                request=request,
                alliance_id=alliance_id,
                entity_id=entity_id,
                filters=filters,
                section=section,
            )

    def create_entity_details(
        self,
        owner: EveAllianceInfo,
        entity_id: int,
        filters: DateFilter,
        section: Section,
    ) -> LedgerDetailsResponse:
        """Create the category breakdown for the alliance or one of its corporations."""
        if owner.alliance_id == entity_id:
            corporation_ids = list(
                CorporationOwner.objects.filter(
                    eve_corporation__alliance__alliance_id=owner.alliance_id
                ).values_list("eve_corporation__corporation_id", flat=True)
            )
            division_query = Q(
                division__corporation__eve_corporation__alliance__alliance_id=owner.alliance_id
            )
            exclude_query = None
            if corporation_ids:
                exclude_query = Q(first_party_id__in=corporation_ids) & Q(
                    second_party_id__in=corporation_ids
                )
        else:
            exclude_query = Q(first_party_id=entity_id, second_party_id=entity_id)
            division_query = Q(
                division__corporation__eve_corporation__corporation_id=entity_id
            )

        wallet_journal = filters.filter(
            CorporationWalletJournalEntry.objects.filter(division_query)
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
        )

        if exclude_query is not None:
            wallet_journal = wallet_journal.exclude(exclude_query)

        return create_ledger_details(
            journal=wallet_journal, filters=filters, section=section
        )

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        alliance_id: int,
        entity_id: int,
        filters: DateFilter,
        section: Section,
    ) -> LedgerDetailsResponse | tuple[int, dict]:
        """Build the details response for an alliance entity and the given date."""
        perms, owner = get_alliance_or_none(request=request, alliance_id=alliance_id)

        if owner is None:
            return HTTPStatus.NOT_FOUND, {"error": _("Alliance not found in Ledger.")}

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this alliance.")
            }

        return self.create_entity_details(
            owner=owner,
            entity_id=entity_id,
            filters=filters,
            section=section,
        )
