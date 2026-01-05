# Standard Library
from decimal import Decimal

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.helpers.core import (
    get_alliance_or_none,
)
from ledger.api.helpers.icons import (
    get_alliance_details_info_button,
    get_ref_type_details_popover_button,
)
from ledger.api.schema import (
    AllianceLedgerRequestInfo,
    BillboardSchema,
    CategorySchema,
    EntitySchema,
    LedgerDetailsResponse,
    LedgerDetailsSummary,
    LedgerResponse,
    LedgerSchema,
    OwnerSchema,
    UpdateStatusSchema,
)
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.cache import CacheManager
from ledger.helpers.eveonline import get_alliance_logo_url, get_corporation_logo_url
from ledger.helpers.ref_type import RefTypeManager
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
    actions: str = ""


class AllianceLedgerResponse(LedgerResponse):
    """
    Schema for Alliance Ledger API Response

    This schema represents the structure of the response returned by the Alliance Ledger API.
    extending the base :class:`LedgerResponse` to include alliance-specific data.

    Attributes:
        information (AllianceLedgerRequestInfo): Information about the alliance ledger request.
        corporations (list[LedgerAllianceSchema]): A list of ledger entities associated with the alliance.
    """

    information: AllianceLedgerRequestInfo
    corporations: list[LedgerAllianceSchema]


class AllianceApiEndpoints:
    tags = ["Alliance"]

    # pylint: disable=too-many-statements, function-redefined, duplicate-code
    # flake8: noqa: F811
    def __init__(self, api: NinjaAPI):
        self.cache_manager = CacheManager()

        @api.get(
            "alliance/{alliance_id}/date/{year}/",
            response={200: AllianceLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_ledger(request: WSGIRequest, alliance_id: int, year: int):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                alliance_id=alliance_id,
                year=year,
            )

        @api.get(
            "alliance/{alliance_id}/date/{year}/{month}/",
            response={200: AllianceLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_ledger(
            request: WSGIRequest, alliance_id: int, year: int, month: int
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                alliance_id=alliance_id,
                year=year,
                month=month,
            )

        @api.get(
            "alliance/{alliance_id}/date/{year}/{month}/{day}/",
            response={200: AllianceLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_ledger(
            request: WSGIRequest,
            alliance_id: int,
            year: int,
            month: int,
            day: int,
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                alliance_id=alliance_id,
                year=year,
                month=month,
                day=day,
            )

    # pylint: disable=duplicate-code
    def _create_datatable_footer(
        self,
        corporations: list[LedgerAllianceSchema],
        request_info: AllianceLedgerRequestInfo,
    ) -> AllianceLedgerRequestInfo:
        """
        Create the footer HTML for the Ledger datatable.

        This Helper function creates the footer HTML for the Ledger datatable
        by summing up the respective fields from the list of corporations.

        Args:
            corporations (list[LedgerAllianceSchema]): The list of corporation ledger data.
            request_info (AllianceLedgerRequestInfo): The request information object.
        Returns:
            str: The generated footer HTML.
        """
        total_bounty = sum(entity.ledger.bounty for entity in corporations)
        total_ess = sum(entity.ledger.ess for entity in corporations)
        total_costs = sum(entity.ledger.costs for entity in corporations)
        total_miscellaneous = sum(
            entity.ledger.miscellaneous for entity in corporations
        )
        total_total = sum(entity.ledger.total for entity in corporations)

        # Generate Details Link
        url = get_alliance_details_info_button(
            entity_id=request_info.owner_id,
            request_info=request_info,
        )

        # Skip Footer if no Totals
        if total_total == 0:
            return ""

        footer_html = f"""
            <tr>
                <th class="border-top">{_("Summary")}</th>
                <th class="border-top text-end">{intcomma(value=int(total_bounty), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_ess), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_miscellaneous), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_costs), use_l10n=True)} ISK</th>
                <th class="border-start border-top text-end">{intcomma(value=int(total_total), use_l10n=True)} ISK</th>
                <th class="border-top">{url}</th>
            </tr>
        """
        request_info.footer_html = footer_html
        return request_info

    def generate_corporation_data(
        self,
        owner: EveAllianceInfo,
        request_info: AllianceLedgerRequestInfo,
    ):
        """
        Generate the corporation ledger data for the alliance.

        This Helper function generates the corporation ledger data for all corporation of the Alliance
        based on the provided request information.

        Args:
            owner (EveAllianceInfo): The alliance owner object.
            request_info (AllianceLedgerRequestInfo): The request information object.
        Returns:
            list[LedgerAllianceSchema]: The generated alliance ledger data.

        """
        corporations = CorporationOwner.objects.filter(
            eve_corporation__alliance__alliance_id=owner.alliance_id
        )

        alliance_ledger_list: list[LedgerAllianceSchema] = []
        for corporation in corporations:
            wallet_journal = (
                CorporationWalletJournalEntry.objects.filter(
                    division__corporation=corporation,
                    **request_info.to_date_query(),
                )
                # Exclude Zero Amount Entries
                .exclude(amount=Decimal("0.00"))
                # Exclude Internal Transfers
                .exclude(
                    first_party_id=corporation.eve_corporation.corporation_id,
                    second_party_id=corporation.eve_corporation.corporation_id,
                )
            )

            if not wallet_journal.exists():
                continue

            # Get IDs for Hashing
            header_ids = list(wallet_journal.values_list("entry_id", flat=True))

            # Add Alliance ID to header ids to ensure uniqueness
            header_ids.append(owner.alliance_id)

            # Create Ledger Hash
            wallet_journal_hash = self.cache_manager.create_ledger_hash(header_ids)

            # Get Cached Ledger if Available
            response_ledger = self.cache_manager.get_cache_ledger(
                ledger_hash=wallet_journal_hash
            )
            if response_ledger is False:
                logger.debug(f"Ledger Cache Miss for: {corporation}")

                # Aggregate Data
                bounty = wallet_journal.aggregate_bounty()
                ess = wallet_journal.aggregate_ess()
                miscellaneous = wallet_journal.aggregate_miscellaneous()
                costs = wallet_journal.aggregate_costs()

                total = sum(
                    [
                        bounty,
                        ess,
                        miscellaneous,
                        costs,
                    ]
                )

                response_ledger = LedgerAllianceSchema(
                    corporation=EntitySchema(
                        entity_id=corporation.eve_corporation.corporation_id,
                        entity_name=corporation.eve_corporation.corporation_name,
                        icon=get_corporation_logo_url(
                            corporation_id=corporation.eve_corporation.corporation_id,
                            corporation_name=corporation.eve_corporation.corporation_name,
                            as_html=True,
                        ),
                    ),
                    ledger=LedgerSchema(
                        bounty=bounty,
                        ess=ess,
                        miscellaneous=miscellaneous,
                        costs=costs,
                        total=total,
                    ),
                    update_status=UpdateStatusSchema(
                        status=corporation.get_status,
                    ),
                    actions=get_alliance_details_info_button(
                        entity_id=corporation.eve_corporation.corporation_id,
                        request_info=request_info,
                    ),
                )
                # Cache Ledger Response
                self.cache_manager.set_cache_ledger(
                    ledger_hash=wallet_journal_hash,
                    ledger_data=response_ledger,
                )

            # Add to Corporation Ledger List
            alliance_ledger_list.append(response_ledger)
        return alliance_ledger_list

    # pylint: disable=too-many-locals
    def generate_billboard_data(
        self,
        owner: EveAllianceInfo,
        alliance_ledger_list: list[LedgerAllianceSchema],
        request_info: AllianceLedgerRequestInfo,
    ) -> BillboardSchema:
        """
        Generate the billboard data for the corporation ledger.

        This Helper function generates the billboard data for the corporation
        based on the provided alliance ledger data.

        Args:
            owner (CorporationOwner): The corporation owner object.
            alliance_ledger_list (list[LedgerAllianceSchema]): The list of alliance ledger data.
            request_info (LedgerRequestInfo): The request information object.
        Returns:
            BillboardSchema: The generated billboard data.
        """
        billboard = BillboardSystem()

        corporations = CorporationOwner.objects.filter(
            eve_corporation__alliance__alliance_id=owner.alliance_id
        )

        # Get Wallet Journal Entries
        corp_wallet_journal = (
            CorporationWalletJournalEntry.objects.filter(
                division__corporation__in=corporations,
                **request_info.to_date_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Transfers
            .exclude(
                Q(
                    first_party_id__in=[
                        corp.eve_corporation.corporation_id for corp in corporations
                    ]
                )
                & Q(
                    second_party_id__in=[
                        corp.eve_corporation.corporation_id for corp in corporations
                    ]
                )
            )
        )

        # Get IDs for Hashing
        header_ids = list(corp_wallet_journal.values_list("entry_id", flat=True))

        # Add Alliance ID to header ids to ensure uniqueness
        header_ids.append(owner.alliance_id)

        # Skip Alliance if no Ledger Entries
        if len(header_ids) == 0:
            return BillboardSchema()

        # Create Ledger Hash
        wallet_journal_hash = self.cache_manager.create_ledger_hash(header_ids)

        # Get Cached Billboard if Available
        response_billboard = self.cache_manager.get_cache_billboard(
            billboard_hash=wallet_journal_hash
        )

        if response_billboard is False:
            logger.debug(f"Billboard Cache for: {owner}")
            # Create Timelines
            wallet_timeline = (
                billboard.create_timeline(corp_wallet_journal)
                .annotate_bounty_income()
                .annotate_ess_income()
                .annotate_miscellaneous()
            )

            # Generate the billboard data
            billboard.create_or_update_results(wallet_timeline)

            # Generate XY Series
            series, categories = billboard.generate_xy_series()
            if series and categories:
                billboard.create_xy_chart(
                    title=_("Ratting Income Over Time"),
                    categories=categories,
                    series=series,
                )

            # Generate Chord Data
            for entity_data in alliance_ledger_list:
                bounty = entity_data.ledger.bounty
                ess = entity_data.ledger.ess
                miscellaneous = entity_data.ledger.miscellaneous
                costs = entity_data.ledger.costs

                billboard.chord_add_data(
                    chord_from=entity_data.corporation.entity_name,
                    chord_to=_("Bounty"),
                    value=abs(bounty),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.corporation.entity_name,
                    chord_to=_("ESS"),
                    value=abs(ess),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.corporation.entity_name,
                    chord_to=_("Miscellaneous"),
                    value=abs(miscellaneous),
                )
                billboard.chord_add_data(
                    chord_from=entity_data.corporation.entity_name,
                    chord_to=_("Costs"),
                    value=abs(costs),
                )

            # Handle Chord Overflow
            billboard.chord_handle_overflow()

            response_billboard = BillboardSchema(
                xy_chart=billboard.dict.rattingbar,
                chord_chart=billboard.dict.charts,
            )
            # Cache Billboard Response
            self.cache_manager.set_cache_billboard(
                billboard_hash=wallet_journal_hash,
                billboard_data=response_billboard,
            )
        # Billboard Data Generation Logic Here
        return response_billboard

    # pylint: disable=duplicate-code
    def _ledger_api_response(
        self,
        request,
        alliance_id: int,
        year: int,
        month: int = None,
        day: int = None,
    ) -> AllianceLedgerResponse | tuple[int, dict]:
        """
        Helper function to generate ledger response for various date parameters.

        This function consolidates the common logic for generating the ledger response
        based on the provided date parameters (year, month, day) and section.

        Args:
            request (WSGIRequest): The incoming request object.
            alliance_id (int): The alliance ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').

        Returns:
            AllianceLedgerResponse | tuple[int, dict]: The ledger response or error tuple.
        """
        perms, owner = get_alliance_or_none(request=request, alliance_id=alliance_id)

        if owner is None:
            return 404, {"error": _("Alliance not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this alliance.")
            }

        # Build Request Info
        request_info = AllianceLedgerRequestInfo(
            owner_id=owner.alliance_id,
            year=year,
            month=month,
            day=day,
        )

        # Generate Corporation Ledger Data
        corporation_ledger_list = self.generate_corporation_data(
            owner=owner,
            request_info=request_info,
        )

        # Generate Billboard Data
        billboard = self.generate_billboard_data(
            owner=owner,
            alliance_ledger_list=corporation_ledger_list,
            request_info=request_info,
        )

        # Update Request Info with Available Data
        self._create_datatable_footer(
            corporations=corporation_ledger_list, request_info=request_info
        )

        response_ledger = AllianceLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.alliance_id,
                character_name=owner.alliance_name,
                icon=get_alliance_logo_url(
                    alliance_id=owner.alliance_id,
                    alliance_name=owner.alliance_name,
                    as_html=True,
                ),
            ),
            information=request_info,
            corporations=corporation_ledger_list,
            billboard=billboard,
            actions=get_alliance_details_info_button(
                entity_id=owner.alliance_id,
                request_info=request_info,
            ),
        )

        return response_ledger


class AllianceDetailsApiEndpoints:
    tags = ["Alliance Details"]

    # pylint: disable=too-many-statements, function-redefined, too-many-arguments
    def __init__(self, api: NinjaAPI):
        @api.get(
            "alliance/{alliance_id}/date/{year}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_ledger_details(
            request: WSGIRequest,
            alliance_id: int,
            year: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                alliance_id=alliance_id,
                entity_id=entity_id,
                year=year,
                section=section,
            )

        @api.get(
            "alliance/{alliance_id}/date/{year}/{month}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_alliance_ledger_details(
            request: WSGIRequest,
            alliance_id: int,
            year: int,
            month: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                alliance_id=alliance_id,
                entity_id=entity_id,
                year=year,
                month=month,
                section=section,
            )

        @api.get(
            "alliance/{alliance_id}/date/{year}/{month}/{day}/section/{section}/view/details/{entity_id}/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        # pylint: disable=too-many-positional-arguments
        def get_alliance_ledger_details(
            request: WSGIRequest,
            alliance_id: int,
            year: int,
            month: int,
            day: int,
            section: str,
            entity_id: int,
        ):
            return self._ledger_details_api_response(
                request=request,
                alliance_id=alliance_id,
                entity_id=entity_id,
                year=year,
                month=month,
                day=day,
                section=section,
            )

    # pylint: disable=duplicate-code
    def _create_datatable_footer(self, value: float) -> str:
        """Create the footer HTML for the datatable."""
        footer_html = f"""
            <tr>
                <th>{_('Summary')}</th>
                <th class="text-end">{intcomma(value=int(value), use_l10n=True)} ISK</th>
                <th></th>
            </tr>
        """
        return footer_html

    # pylint: disable=too-many-locals
    def _create_ledger_details(
        self,
        journal: QuerySet[CorporationWalletJournalEntry],
        request_info: AllianceLedgerRequestInfo,
    ) -> LedgerDetailsResponse:
        """
        Generate the detailed ledger data for a character.
        This Helper function generates the detailed ledger data for a character
        based on the provided date query.

        Args:
            journal (QuerySet): The wallet journal entries.
            mining (QuerySet): The mining ledger entries. Defaults to None.
            request_info (LedgerRequestInfo): The request information containing date and section details.
        Returns:
            LedgerDetailsResponse: The generated ledger details response.
        """
        ref_types = RefTypeManager.get_all_categories()

        avg = request_info.day if request_info.day else timezone.now().day
        if request_info.section == "summary":
            avg = 365

        monthly_list = []
        daily_list = []
        hourly_list = []
        summary = 0
        # Income/Cost Ref Types
        for ref_type, value in ref_types.items():
            ref_type_name = ref_type.lower()
            for kind, income_flag in (("income", True), ("cost", False)):
                kwargs = {"ref_type": value, "income": income_flag}
                amount = journal.aggregate_ref_type(**kwargs)
                if (income_flag and amount > 0) or (not income_flag and amount < 0):
                    monthly = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount,
                        average=amount / avg / 30,
                        average_tick=amount / avg / 30 / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )

                    daily = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount / avg,
                        average=amount / avg / 30,
                        average_tick=amount / avg / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )

                    hourly = CategorySchema(
                        name=_(
                            f"{ref_type_name.replace('_', ' ').title()} {kind.capitalize()}"
                        ),
                        amount=amount / avg / 24,
                        average=amount / avg / 24 / 30,
                        average_tick=amount / avg / 24 / 20,
                        ref_types=get_ref_type_details_popover_button(ref_types=value),
                    )
                    # Add Amounts
                    summary += amount
                    monthly_list.append(monthly)
                    daily_list.append(daily)
                    hourly_list.append(hourly)

        if summary == 0:
            return None

        return LedgerDetailsResponse(
            summary=monthly_list,
            daily=daily_list,
            hourly=hourly_list,
            total=LedgerDetailsSummary(
                summary=self._create_datatable_footer(summary),
                daily=self._create_datatable_footer(
                    summary / avg,
                ),
                hourly=self._create_datatable_footer(
                    summary / avg / 24,
                ),
            ),
        )

    def create_entity_details(
        self,
        owner: EveAllianceInfo,
        entity_id: int,
        request_info: AllianceLedgerRequestInfo,
    ) -> dict:
        """
        Create the entity amounts for the Information View.
        """
        # Get Division Query
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

        # Get Wallet Journal Entries
        wallet_journal = (
            CorporationWalletJournalEntry.objects.filter(
                division_query,
                **request_info.to_date_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
        )

        # Exclude Internal Transfers only when we have a meaningful exclude_query
        if exclude_query is not None:
            wallet_journal = wallet_journal.exclude(exclude_query)

        response_ledger_details: LedgerDetailsResponse = self._create_ledger_details(
            journal=wallet_journal,
            request_info=request_info,
        )
        return response_ledger_details

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        alliance_id: int,
        entity_id: int,
        year: int,
        month: int = None,
        day: int = None,
        section: str = "summary",
    ):
        """
        Helper function to generate ledger details response for various date parameters.

        This function consolidates the common logic for generating the ledger details response
        based on the provided date parameters character_id, (year, month, day) and section.

        Args:
            request (WSGIRequest): The incoming request object.
            alliance_id (int): The alliance ID.
            entity_id (int): The entity ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').
        Returns:
            LedgerDetailsResponse | tuple[int, dict]: The ledger details response or error tuple.
        """
        perms, owner = get_alliance_or_none(request=request, alliance_id=alliance_id)

        if owner is None:
            return 404, {"error": _("Alliance not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this alliance.")
            }

        request_info = AllianceLedgerRequestInfo(
            owner_id=owner.alliance_id,
            entity_id=entity_id,
            year=year,
            month=month,
            day=day,
            section=section,
        )

        return self.create_entity_details(
            owner=owner,
            entity_id=entity_id,
            request_info=request_info,
        )
