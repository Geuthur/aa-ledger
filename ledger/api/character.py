# Standard Library
from collections import defaultdict
from decimal import Decimal
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet, Sum
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Ledger
from ledger import __title__
from ledger.api.helpers.core import (
    get_available_years,
    get_characterowner_or_none,
)
from ledger.api.schema import (
    BillboardSchema,
    CategorySchema,
    CharacterLedgerSchema,
    CharacterRefTypeSchema,
    DateFilter,
    ErrorSchema,
    LedgerDetailsResponse,
    LedgerDetailsSummary,
    LedgerResponse,
    OwnerSchema,
    RefTypeAmountSchema,
    Section,
    UpdateStatusSchema,
)
from ledger.helpers.billboard import BillboardSystem
from ledger.helpers.eveonline import get_character_portrait_url
from ledger.helpers.ref_type import RefTypeManager
from ledger.models import EveEntity
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


class CharacterLedgerResponse(LedgerResponse):
    """
    Schema for Character Ledger Response.

    Attributes:
        characters (list[LedgerCharacterSchema]): List of character ledger data.
    """

    characters: list[LedgerCharacterSchema]


class CharacterApiEndpoints:
    tags = ["Character"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/ledger/",
            response={
                HTTPStatus.OK: CharacterLedgerResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the ledger of a character and its alts",
        )
        def get_character_ledger(
            request: WSGIRequest, character_id: int, filters: Query[DateFilter]
        ):
            return self._ledger_api_response(
                request=request, character_id=character_id, filters=filters
            )

    def generate_character_data(
        self, owner: CharacterOwner, filters: DateFilter
    ) -> tuple[list[LedgerCharacterSchema], BillboardSchema]:
        """
        Generate the ledger and billboard data for all alts of a character owner.

        Args:
            owner (CharacterOwner): The character owner object.
            filters (DateFilter): The requested date range.
        Returns:
            tuple[list[LedgerCharacterSchema], BillboardSchema]: Ledger rows and chart data.
        """
        characters = CharacterOwner.objects.filter(
            eve_character__character_id__in=owner.alt_ids
        )

        wallet_journal = filters.filter(
            CharacterWalletJournalEntry.objects.filter(
                character__eve_character__character_id__in=owner.alt_ids
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Donations between Alts
            .exclude(
                Q(ref_type="player_donation")
                & (Q(first_party__in=owner.alt_ids) & Q(second_party__in=owner.alt_ids))
            )
        ).order_by("-date")

        mining_journal = filters.filter(
            CharacterMiningLedger.objects.filter(
                character__eve_character__character_id__in=owner.alt_ids
            )
        ).order_by("-date")

        character_ledger_list: list[LedgerCharacterSchema] = []
        for character in characters:
            character_journal = wallet_journal.filter(character=character)
            character_mining_journal = mining_journal.filter(character=character)

            # Skip if No Data for Character
            if not character_journal.exists() and not character_mining_journal.exists():
                continue

            bounty = character_journal.aggregate_bounty()
            ess = character_journal.aggregate_ess()
            mining = character_mining_journal.aggregate_mining()
            costs = character_journal.aggregate_costs()
            miscellaneous = character_journal.aggregate_miscellaneous()

            character_ledger_list.append(
                LedgerCharacterSchema(
                    character=OwnerSchema(
                        character_id=character.eve_character.character_id,
                        character_name=character.eve_character.character_name,
                        icon=character.get_portrait(size=32),
                    ),
                    ledger=CharacterLedgerSchema(
                        bounty=bounty,
                        ess=ess,
                        mining=mining,
                        costs=costs,
                        miscellaneous=miscellaneous,
                        # Mining is shown for information only
                        total=sum([bounty, ess, miscellaneous, costs]),
                    ),
                    update_status=UpdateStatusSchema(status=character.get_status),
                )
            )

        xy_chart, chord_chart = BillboardSystem().create_billboards(
            filters=filters,
            wallet_journal=wallet_journal,
            ledger_list=character_ledger_list,
            mining_journal=mining_journal,
        )
        return character_ledger_list, BillboardSchema(
            xy_chart=xy_chart, chord_chart=chord_chart
        )

    def _ledger_api_response(
        self, request, character_id: int, filters: DateFilter
    ) -> CharacterLedgerResponse | tuple[int, dict]:
        """Build the ledger response for a character and the given date."""
        perms, owner = get_characterowner_or_none(
            request=request, character_id=character_id
        )

        if owner is None:
            return HTTPStatus.NOT_FOUND, {"error": _("Character not found in Ledger.")}

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this character.")
            }

        character_ledger_list, billboard = self.generate_character_data(
            owner=owner, filters=filters
        )

        return CharacterLedgerResponse(
            owner=OwnerSchema(
                character_id=owner.eve_character.character_id,
                character_name=owner.eve_character.character_name,
                icon=owner.get_portrait(),
            ),
            characters=character_ledger_list,
            billboard=billboard,
            years=get_available_years(
                CharacterWalletJournalEntry.objects.filter(
                    character__eve_character__character_id__in=owner.alt_ids
                )
            ),
        )


def _amounts_by_ref_type(journal: QuerySet, income: bool) -> dict[str, Decimal]:
    """Sum the journal per reference type, counting either income or costs."""
    entries = journal.filter(amount__gt=0) if income else journal.filter(amount__lt=0)
    return {
        row["ref_type"]: row["total"]
        for row in entries.order_by().values("ref_type").annotate(total=Sum("amount"))
    }


def _character_amounts_by_ref_type(
    journal: QuerySet, income: bool
) -> dict[str, dict[tuple[int, str], Decimal]]:
    """Sum the journal per reference type and character, counting either income or costs."""
    if journal.model.__name__ != "CorporationWalletJournalEntry":
        return {}

    entries = journal.filter(amount__gt=0) if income else journal.filter(amount__lt=0)
    char_amounts: dict[str, dict[tuple[int, str], Decimal]] = defaultdict(
        lambda: defaultdict(Decimal)
    )

    first_party_rows = (
        entries.filter(first_party__category=EveEntity.CATEGORY_CHARACTER)
        .order_by()
        .values("ref_type", "first_party_id", "first_party__name")
        .annotate(total=Sum("amount"))
    )
    for row in first_party_rows:
        char_amounts[row["ref_type"]][
            (row["first_party_id"], row["first_party__name"])
        ] += row["total"]

    second_party_rows = (
        entries.filter(second_party__category=EveEntity.CATEGORY_CHARACTER)
        .exclude(first_party__category=EveEntity.CATEGORY_CHARACTER)
        .order_by()
        .values("ref_type", "second_party_id", "second_party__name")
        .annotate(total=Sum("amount"))
    )
    for row in second_party_rows:
        char_amounts[row["ref_type"]][
            (row["second_party_id"], row["second_party__name"])
        ] += row["total"]

    return char_amounts


def _category_rows(
    categories: list[
        tuple[str, dict[str, Decimal], dict[str, dict[tuple[int, str], Decimal]]]
    ],
    amount_divisor: Decimal | int,
    average_divisor: Decimal | int,
    tick_divisor: Decimal | int,
) -> list[CategorySchema]:
    """Scale the amounts of every category and its reference types to one period."""
    return [
        CategorySchema(
            name=name,
            amount=sum(ref_amounts.values()) / amount_divisor,
            average=sum(ref_amounts.values()) / average_divisor,
            average_tick=sum(ref_amounts.values()) / tick_divisor,
            ref_types=[
                RefTypeAmountSchema(
                    ref_type=ref_type,
                    amount=value / amount_divisor,
                    characters=[
                        CharacterRefTypeSchema(
                            character_id=char_id,
                            character_name=char_name,
                            amount=float(char_val / amount_divisor),
                            icon=get_character_portrait_url(
                                character_id=char_id,
                                character_name=char_name,
                                size=32,
                            ),
                        )
                        for (char_id, char_name), char_val in sorted(
                            cat_char_amounts.get(ref_type, {}).items(),
                            key=lambda item: -abs(item[1]),
                        )
                    ],
                )
                for ref_type, value in ref_amounts.items()
            ],
        )
        for name, ref_amounts, cat_char_amounts in categories
    ]


# pylint: disable=too-many-locals
def create_ledger_details(
    journal: QuerySet,
    filters: DateFilter,
    section: Section,
    mining: QuerySet | None = None,
) -> LedgerDetailsResponse:
    """
    Aggregate a journal into per-category income and cost rows.

    Shared by the character, corporation and alliance details endpoints.

    Args:
        journal (QuerySet): The wallet journal entries.
        filters (DateFilter): The requested date range, used for the averages.
        section (str): `summary` averages over a year, `single` over the selected days.
        mining (QuerySet, optional): Mining entries, shown for information only.
    Returns:
        LedgerDetailsResponse: Category rows and totals. Empty if there is no data.
    """
    ref_types = RefTypeManager.get_all_categories()

    avg = filters.day if filters.day else timezone.now().day
    if section == "summary":
        avg = 365

    amounts = {
        flag: _amounts_by_ref_type(journal, income=flag) for flag in (True, False)
    }
    char_amounts = {
        flag: _character_amounts_by_ref_type(journal, income=flag)
        for flag in (True, False)
    }
    categories: list[
        tuple[str, dict[str, Decimal], dict[str, dict[tuple[int, str], Decimal]]]
    ] = []
    for category in RefTypeManager.CategoryChoice:
        for income_flag in (True, False):
            kind_label = _("Income from") if income_flag else _("Cost from")
            category_amounts = {
                ref_type: amounts[income_flag][ref_type]
                for ref_type in ref_types.get(category.value, [])
                if ref_type in amounts[income_flag]
            }
            if not category_amounts:
                continue
            name = _("%(kind)s %(category)s") % {
                "category": category.label,
                "kind": kind_label,
            }
            # Largest contribution first
            ordered = dict(
                sorted(category_amounts.items(), key=lambda item: -abs(item[1]))
            )
            cat_char_amounts = {
                ref_type: char_amounts[income_flag].get(ref_type, {})
                for ref_type in ordered
            }
            categories.append((name, ordered, cat_char_amounts))

    monthly_list = _category_rows(categories, 1, avg * 30, avg * 30 * 20)
    daily_list = _category_rows(categories, avg, avg * 30, avg * 20)
    hourly_list = _category_rows(categories, avg * 24, avg * 24 * 30, avg * 24 * 20)
    summary = sum(sum(ref_amounts.values()) for __, ref_amounts, _ in categories)

    if mining is not None:
        mining_income = mining.aggregate_mining()
        if mining_income > 0:
            for rows, divisor in (
                (monthly_list, avg * 30),
                (daily_list, avg),
                (hourly_list, avg * 24),
            ):
                rows.append(
                    CategorySchema(
                        name=_("Mining Income"),
                        amount=mining_income,
                        average=mining_income / divisor,
                        average_tick=mining_income / divisor / 20,
                        ref_types=[
                            RefTypeAmountSchema(ref_type="mining", amount=mining_income)
                        ],
                    )
                )

    return LedgerDetailsResponse(
        summary=monthly_list,
        daily=daily_list,
        hourly=hourly_list,
        total=LedgerDetailsSummary(
            summary=summary,
            daily=summary / avg,
            hourly=summary / avg / 24,
        ),
    )


class CharacterDetailsApiEndpoints:
    tags = ["Character Details"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "character/{character_id}/details/",
            response={
                HTTPStatus.OK: LedgerDetailsResponse,
                HTTPStatus.FORBIDDEN: ErrorSchema,
                HTTPStatus.NOT_FOUND: ErrorSchema,
            },
            tags=self.tags,
            summary="Get the income and cost breakdown of a character",
        )
        def get_character_ledger_details(
            request: WSGIRequest,
            character_id: int,
            filters: Query[DateFilter],
            section: Section = "summary",
        ):
            return self._ledger_details_api_response(
                request=request,
                character_id=character_id,
                filters=filters,
                section=section,
            )

    def create_character_details(
        self, owner: CharacterOwner, filters: DateFilter, section: Section
    ) -> LedgerDetailsResponse:
        """Create the category breakdown for a character or all of its alts."""
        char_ids = (
            owner.alt_ids
            if section == "summary"
            else [owner.eve_character.character_id]
        )

        wallet_journal = filters.filter(
            CharacterWalletJournalEntry.objects.filter(
                character__eve_character__character_id__in=char_ids
            )
            # Exclude Zero Amount Entries
            .exclude(amount=Decimal("0.00"))
            # Exclude Internal Donations between Alts
            .exclude(
                Q(ref_type="player_donation")
                & (Q(first_party__in=owner.alt_ids) & Q(second_party__in=owner.alt_ids))
            )
        ).order_by("-date")

        mining_journal = filters.filter(
            CharacterMiningLedger.objects.filter(
                character__eve_character__character_id__in=char_ids
            )
        )

        return create_ledger_details(
            journal=wallet_journal,
            mining=mining_journal,
            filters=filters,
            section=section,
        )

    def _ledger_details_api_response(
        self,
        request: WSGIRequest,
        character_id: int,
        filters: DateFilter,
        section: Section,
    ) -> LedgerDetailsResponse | tuple[int, dict]:
        """Build the details response for a character and the given date."""
        perms, owner = get_characterowner_or_none(
            request=request, character_id=character_id
        )

        if owner is None:
            return HTTPStatus.NOT_FOUND, {"error": _("Character not found in Ledger.")}

        if perms is False:
            return HTTPStatus.FORBIDDEN, {
                "error": _("You do not have permission to view this character.")
            }

        return self.create_character_details(
            owner=owner, filters=filters, section=section
        )
