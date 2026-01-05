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
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.helpers.core import (
    get_characterowner_or_none,
)
from ledger.api.helpers.icons import (
    get_character_details_info_button,
    get_ref_type_details_popover_button,
)
from ledger.api.schema import (
    BillboardSchema,
    CategorySchema,
    CharacterLedgerSchema,
    LedgerDetailsResponse,
    LedgerDetailsSummary,
    LedgerResponse,
    OwnerLedgerRequestInfo,
    OwnerSchema,
    UpdateStatusSchema,
)
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.cache import CacheManager
from ledger.helpers.ref_type import RefTypeManager
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterOwner,
    CharacterWalletJournalEntry,
)
from ledger.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class LedgerCharacterSchema(Schema):
    character: OwnerSchema
    ledger: CharacterLedgerSchema
    update_status: UpdateStatusSchema
    actions: str = ""


class CharacterLedgerResponse(LedgerResponse):
    """
    Schema for Character Ledger Response.

    This schema represents the response structure for a character's ledger,
    extending the base :class:`LedgerResponse` to include character-specific information.

    Attributes:
        information (OwnerLedgerRequestInfo): Information about the ledger request.
        characters (list[LedgerCharacterSchema]): List of character ledger data.
    """

    information: OwnerLedgerRequestInfo
    characters: list[LedgerCharacterSchema]


class CharacterApiEndpoints:
    tags = ["Character"]

    # pylint: disable=too-many-statements, function-redefined
    # flake8: noqa: F811
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/date/{year}/",
            response={200: CharacterLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger(request: WSGIRequest, character_id: int, year: int):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                character_id=character_id,
                year=year,
            )

        @api.get(
            "character/{character_id}/date/{year}/{month}/",
            response={200: CharacterLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger(
            request: WSGIRequest, character_id: int, year: int, month: int
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                character_id=character_id,
                year=year,
                month=month,
            )

        @api.get(
            "character/{character_id}/date/{year}/{month}/{day}/",
            response={200: CharacterLedgerResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger(
            request: WSGIRequest,
            character_id: int,
            year: int,
            month: int,
            day: int,
        ):
            """Get the ledger for a character for a specific year. Admin Endpoint."""
            return self._ledger_api_response(
                request=request,
                character_id=character_id,
                year=year,
                month=month,
                day=day,
            )

    def _create_datatable_footer(
        self,
        characters: list[LedgerCharacterSchema],
        request_info: OwnerLedgerRequestInfo,
    ) -> OwnerLedgerRequestInfo:
        """
        Create the footer HTML for the Ledger datatable.

        This Helper function creates the footer HTML for the Ledger datatable
        by summing up the respective fields from the list of characters.

        Args:
            characters (list[LedgerCharacterSchema]): The list of character ledger data.

        Returns:
            str: The generated footer HTML.
        """
        total_bounty = sum(char.ledger.bounty for char in characters)
        total_ess = sum(char.ledger.ess for char in characters)
        total_mining = sum(char.ledger.mining for char in characters)
        total_costs = sum(char.ledger.costs for char in characters)
        total_miscellaneous = sum(char.ledger.miscellaneous for char in characters)
        total_total = sum(char.ledger.total for char in characters)

        # Generate Details Link
        url = get_character_details_info_button(
            character_id=request_info.owner_id,
            request_info=request_info,
        )

        # Skip Footer if no Totals
        if total_total == 0:
            return ""

        info_title = _("This amount is displayed for information only")
        info_html = f"""
            <i class="fa-regular fa-circle-question"
                data-bs-tooltip="aa-ledger" data-bs-placement="top"
                title="{info_title}"
            >
            </i>
        """

        footer_html = f"""
            <tr>
                <th class="border-top">{_("Summary")}</th>
                <th class="border-top text-end">{intcomma(value=int(total_bounty), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_ess), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_mining), use_l10n=True)} ISK {info_html}</th>
                <th class="border-top text-end">{intcomma(value=int(total_miscellaneous), use_l10n=True)} ISK</th>
                <th class="border-top text-end">{intcomma(value=int(total_costs), use_l10n=True)} ISK</th>
                <th class="border-start border-top text-end">{intcomma(value=int(total_total), use_l10n=True)} ISK</th>
                <th class="border-top">{url}</th>
            </tr>
        """
        request_info.footer_html = footer_html
        return request_info

    # pylint: disable=too-many-locals
    def generate_character_data(
        self, owner: CharacterOwner, request_info: OwnerLedgerRequestInfo
    ) -> list[CharacterLedgerResponse]:
        """
        Generate the ledger data for all alts of a character owner.

        This Helper function generates the ledger data for all alts of a character owner
        based on the provided date query.

        Args:
            owner (CharacterOwner): The character owner object.
            request_info (LedgerRequestInfo): The request information containing date and section details.
        Returns:
            list[LedgerCharacterSchema]: A list of ledger responses for each character.
        """
        # Initalize Cache Manager
        cache_manager = CacheManager()
        # Get All Alts for this Owner
        characters = CharacterOwner.objects.filter(
            eve_character__character_id__in=owner.alt_ids
        )

        # Create Ledger Response for each Character
        character_ledger_list: list[LedgerCharacterSchema] = []
        for character in characters:
            # Get Journal Data
            wallet_journal = (
                character.ledger_character_journal.filter(
                    **request_info.to_date_query(),
                )
                # Exclude Zero Amount Entries
                .exclude(amount=Decimal("0.00"))
                # Exclude Internal Donations between Alts
                .exclude(
                    Q(ref_type="player_donation")
                    & (
                        Q(first_party__in=owner.alt_ids)
                        & Q(second_party__in=owner.alt_ids)
                    )
                ).order_by("-date")
            )

            mining_journal = character.ledger_character_mining.filter(
                **request_info.to_date_query(),
            ).order_by("-date")

            # Get IDs for Hashing
            entry_ids = wallet_journal.values_list("entry_id", flat=True)
            mining_pks = mining_journal.values_list("type_id", flat=True)
            header_ids = list(entry_ids) + list(mining_pks)

            # Skip Character if no Ledger Entries
            if len(header_ids) == 0:
                logger.debug(f"Skipping Character {character} - No Ledger Entries")
                continue

            # Add Character ID to header ids to ensure uniqueness
            header_ids.append(character.eve_character.character_id)

            # Create Ledger Hash
            wallet_journal_hash = cache_manager.create_ledger_hash(header_ids)

            # Get Cached Ledger if Available
            response_ledger = cache_manager.get_cache_ledger(
                ledger_hash=wallet_journal_hash
            )
            if response_ledger is False:
                logger.debug(f"Ledger Cache Miss for Character: {character}")

                # Aggregate Data
                character_bounty = wallet_journal.aggregate_bounty()
                character_ess = wallet_journal.aggregate_ess()
                character_mining = mining_journal.aggregate_mining()
                character_costs = wallet_journal.aggregate_costs()
                character_miscellaneous = wallet_journal.aggregate_miscellaneous()

                total = sum(
                    [
                        character_bounty,
                        character_ess,
                        character_miscellaneous,
                        character_costs,
                    ]
                )

                response_ledger = LedgerCharacterSchema(
                    character=OwnerSchema(
                        character_id=character.eve_character.character_id,
                        character_name=character.eve_character.character_name,
                        icon=character.get_portrait(size=32, as_html=True),
                    ),
                    ledger=CharacterLedgerSchema(
                        bounty=character_bounty,
                        ess=character_ess,
                        mining=character_mining,
                        costs=character_costs,
                        miscellaneous=character_miscellaneous,
                        total=total,
                    ),
                    update_status=UpdateStatusSchema(
                        status=owner.get_status,
                    ),
                    actions=get_character_details_info_button(
                        character_id=character.eve_character.character_id,
                        request_info=request_info,
                        section="single",
                    ),
                )
                # Cache Ledger Response
                cache_manager.set_cache_ledger(
                    ledger_hash=wallet_journal_hash,
                    ledger_data=response_ledger,
                )

            # Add Character Ledger to List
            character_ledger_list.append(response_ledger)
        return character_ledger_list

    # pylint: disable=too-many-locals
    def generate_billboard_data(
        self,
        owner: CharacterOwner,
        character_ledger_list: list[LedgerCharacterSchema],
        request_info: OwnerLedgerRequestInfo,
    ) -> BillboardSchema:
        """
        Generate the billboard data for the given character IDs.

        This Helper function generates the billboard data for the given character IDs
        based on the provided date query.

        Args:
            character_ids (list[int]): The list of character IDs.
            character_ledger_list (list[LedgerCharacterSchema]): The list of character ledger data.
            request_info (LedgerRequestInfo): The request information containing date and section details.
        Returns:
            LedgerBillboard: The generated billboard data.
        """
        # Initialize Billboard System
        billboard = BillboardSystem()
        # Initialize Cache Manager
        cache_manager = CacheManager()

        # Get Wallet and Mining Journal Entries
        wallet_journal = (
            CharacterWalletJournalEntry.objects.filter(
                character__eve_character__character_id__in=owner.alt_ids,
                **request_info.to_date_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Donations between Alts
            .exclude(
                Q(ref_type="player_donation")
                & (Q(first_party__in=owner.alt_ids) & Q(second_party__in=owner.alt_ids))
            ).order_by("-date")
        )

        mining_journal = CharacterMiningLedger.objects.filter(
            character__eve_character__character_id__in=owner.alt_ids,
            **request_info.to_date_query(),
        ).order_by("-date")

        # Get IDs for Hashing
        entry_ids = wallet_journal.values_list("entry_id", flat=True)
        mining_pks = mining_journal.values_list("type_id", flat=True)
        header_ids = list(entry_ids) + list(mining_pks)
        # add character ids to header ids to ensure uniqueness
        header_ids.extend(owner.alt_ids)

        # Skip Character if no Ledger Entries
        if len(header_ids) == 0:
            logger.debug(
                f"No Ledger Entries for Billboard Generation for Character IDs: {owner.alt_ids}"
            )
            return BillboardSchema()

        # Create Ledger Hash
        wallet_journal_hash = cache_manager.create_ledger_hash(header_ids)

        # Get Cached Billboard if Available
        response_billboard = cache_manager.get_cache_billboard(
            billboard_hash=wallet_journal_hash
        )
        if response_billboard is False:
            logger.debug(f"Billboard Cache Miss for Character IDs: {owner.alt_ids}")
            # Create Timelines
            wallet_timeline = (
                billboard.create_timeline(wallet_journal)
                .annotate_bounty_income()
                .annotate_ess_income()
                .annotate_miscellaneous()
            )
            mining_timeline = billboard.create_timeline(mining_journal).annotate_mining(
                with_period=True
            )

            # Generate the billboard data
            billboard.create_or_update_results(wallet_timeline)
            billboard.add_category(mining_timeline, category="mining")

            # Generate XY Series
            series, categories = billboard.generate_xy_series()
            if series and categories:
                billboard.create_xy_chart(
                    title=_("Ratting Income Over Time"),
                    categories=categories,
                    series=series,
                )

            # Generate Chord Data
            for char_data in character_ledger_list:
                bounty = char_data.ledger.bounty
                ess = char_data.ledger.ess
                mining_val = char_data.ledger.mining
                miscellaneous = char_data.ledger.miscellaneous
                costs = char_data.ledger.costs

                billboard.chord_add_data(
                    chord_from=char_data.character.character_name,
                    chord_to=_("Bounty"),
                    value=abs(bounty),
                )
                billboard.chord_add_data(
                    chord_from=char_data.character.character_name,
                    chord_to=_("ESS"),
                    value=abs(ess),
                )
                billboard.chord_add_data(
                    chord_from=char_data.character.character_name,
                    chord_to=_("Mining"),
                    value=abs(mining_val),
                )
                billboard.chord_add_data(
                    chord_from=char_data.character.character_name,
                    chord_to=_("Miscellaneous"),
                    value=abs(miscellaneous),
                )
                billboard.chord_add_data(
                    chord_from=char_data.character.character_name,
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
            cache_manager.set_cache_billboard(
                billboard_hash=wallet_journal_hash,
                billboard_data=response_billboard,
            )
        # Billboard Data Generation Logic Here
        return response_billboard

    # pylint: disable=too-many-positional-arguments
    def _ledger_api_response(
        self,
        request,
        character_id: int,
        year: int,
        month: int = None,
        day: int = None,
        section: str = None,
    ) -> CharacterLedgerResponse | tuple[int, dict]:
        """
        Helper function to generate ledger response for various date parameters.

        This function consolidates the common logic for generating the ledger response
        based on the provided date parameters (year, month, day) and section.

        Args:
            request (WSGIRequest): The incoming request object.
            character_id (int): The character ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').

        Returns:
            CharacterLedgerResponse | tuple[int, dict]: The ledger response or error tuple.
        """

        perms, owner = get_characterowner_or_none(
            request=request, character_id=character_id
        )

        if owner is None:
            return 404, {"error": _("Character not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this character.")
            }

        # Build Request Info
        request_info = OwnerLedgerRequestInfo(
            owner_id=owner.eve_character.character_id,
            year=year,
            month=month,
            day=day,
            section=section,
        )

        # Generate Character Ledger Data
        character_ledger_list = self.generate_character_data(
            owner=owner,
            request_info=request_info,
        )

        # Generate Billboard Data
        billboard = self.generate_billboard_data(
            owner=owner,
            character_ledger_list=character_ledger_list,
            request_info=request_info,
        )

        # Update Request Info with Available Data
        self._create_datatable_footer(
            characters=character_ledger_list, request_info=request_info
        )

        response_ledger = CharacterLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.eve_character.character_id,
                character_name=owner.eve_character.character_name,
                icon=owner.get_portrait(as_html=True),
            ),
            information=request_info,
            characters=character_ledger_list,
            billboard=billboard,
            actions=get_character_details_info_button(
                character_id=owner.eve_character.character_id,
                request_info=request_info,
            ),
        )

        return response_ledger


class CharacterDetailsApiEndpoints:
    tags = ["Character Details"]

    # pylint: disable=too-many-statements, function-redefined
    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/date/{year}/section/{section}/view/details/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger_details(
            request: WSGIRequest, character_id: int, year: int, section: str
        ):
            return self._ledger_details_api_response(
                request=request,
                character_id=character_id,
                year=year,
                section=section,
            )

        @api.get(
            "character/{character_id}/date/{year}/{month}/section/{section}/view/details/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger_details(
            request: WSGIRequest, character_id: int, year: int, month: int, section: str
        ):
            return self._ledger_details_api_response(
                request=request,
                character_id=character_id,
                year=year,
                month=month,
                section=section,
            )

        @api.get(
            "character/{character_id}/date/{year}/{month}/{day}/section/{section}/view/details/",
            response={200: LedgerDetailsResponse, 403: dict, 404: dict},
            tags=self.tags,
        )
        def get_character_ledger_details(
            request: WSGIRequest,
            character_id: int,
            year: int,
            month: int,
            day: int,
            section: str,
        ):
            return self._ledger_details_api_response(
                request=request,
                character_id=character_id,
                year=year,
                month=month,
                day=day,
                section=section,
            )

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
        journal: QuerySet[CharacterWalletJournalEntry],
        mining: QuerySet[CharacterMiningLedger],
        request_info: OwnerLedgerRequestInfo,
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

        # Mining Income from Mining Ledger Journal (Only as Information not counted in Summary)
        mining_income = mining.aggregate_mining()
        if mining_income > 0:
            monthly_mining = CategorySchema(
                name=_("Mining Income"),
                amount=mining_income,
                average=mining_income / avg / 30,
                average_tick=mining_income / avg / 30 / 20,
                ref_types=get_ref_type_details_popover_button(
                    ref_types=["mining"],
                ),
            )

            daily_mining = CategorySchema(
                name=_("Mining Income"),
                amount=mining_income,
                average=mining_income / avg,
                average_tick=mining_income / avg / 20,
                ref_types=get_ref_type_details_popover_button(
                    ref_types=["mining"],
                ),
            )

            hourly_mining = CategorySchema(
                name=_("Mining Income"),
                amount=mining_income,
                average=mining_income / avg / 24,
                average_tick=mining_income / avg / 24 / 20,
                ref_types=get_ref_type_details_popover_button(
                    ref_types=["mining"],
                ),
            )
            monthly_list.append(monthly_mining)
            daily_list.append(daily_mining)
            hourly_list.append(hourly_mining)

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

    def create_character_details(
        self,
        owner: CharacterOwner,
        request_info: OwnerLedgerRequestInfo,
    ) -> dict:
        """
        Create the character amounts for the Information View.
        """
        # Determine Character IDs based on Section
        char_ids = (
            owner.alt_ids
            if request_info.section == "summary"
            else [owner.eve_character.character_id]
        )

        wallet_journal = (
            CharacterWalletJournalEntry.objects.filter(
                character__eve_character__character_id__in=char_ids,
                **request_info.to_date_query(),
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Donations between Alts
            .exclude(
                Q(ref_type="player_donation")
                & (Q(first_party__in=owner.alt_ids) & Q(second_party__in=owner.alt_ids))
            ).order_by("-date")
        )

        mining_journal = CharacterMiningLedger.objects.filter(
            character__eve_character__character_id__in=char_ids,
            **request_info.to_date_query(),
        )

        response_ledger_details: LedgerDetailsResponse = self._create_ledger_details(
            journal=wallet_journal,
            mining=mining_journal,
            request_info=request_info,
        )
        return response_ledger_details

    # pylint: disable=too-many-positional-arguments
    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        character_id: int,
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
            character_id (int): The character ID.
            year (int): The year for the ledger data.
            month (int, optional): The month for the ledger data. Defaults to None.
            day (int, optional): The day for the ledger data. Defaults to None.
            section (str): The section type ('single' or 'summary').
        Returns:
            LedgerDetailsResponse | tuple[int, dict]: The ledger details response or error tuple.
        """
        perms, owner = get_characterowner_or_none(
            request=request, character_id=character_id
        )

        if owner is None:
            return 404, {"error": _("Character not found in Ledger.")}

        if perms is False:
            return 403, {
                "error": _("You do not have permission to view this character.")
            }

        request_info = OwnerLedgerRequestInfo(
            owner_id=owner.eve_character.character_id,
            year=year,
            month=month,
            day=day,
            section=section,
        )

        return self.create_character_details(
            owner=owner,
            request_info=request_info,
        )
