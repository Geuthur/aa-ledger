# Standard Library
from datetime import datetime

# Third Party
from ninja import Schema

# Django
from django.utils import timezone

# AA Ledger
from ledger.helpers.billboard import ChartData


class OwnerSchema(Schema):
    """
    Schema for Character or Character Owner.

    Attributes:
        character_id (int): The ID of the character.
        character_name (str): The name of the character.
        icon (str | None): The URL of the character's icon, if available.
    """

    character_id: int
    character_name: str
    icon: str | None = None


class EntitySchema(Schema):
    """
    Schema for Entity or Corporation Owner.

    Attributes:
        entity_id (int): The ID of the entity.
        entity_name (str): The name of the entity.
        icon (str | None): The URL of the entity's icon, if available.
    """

    entity_id: int
    entity_name: str
    alt_ids: list[int] = []
    icon: str = ""
    popover: str = ""


class CategorySchema(Schema):
    name: str
    amount: float = 0.00
    average: float = 0.00
    average_tick: float = 0.00
    ref_types: str | None = None


class UpdateStatusSchema(Schema):
    last_update: datetime | None = None
    last_run: datetime | None = None
    status: str | None = None
    icon: str | None = None


class BillboardSchema(Schema):
    xy_chart: ChartData | None = None
    chord_chart: ChartData | None = None


class LedgerResponse(Schema):
    """
    Schema for Ledger Response.

    Attributes:
        owner (OwnerSchema): The owner of the ledger.
        billboard (BillboardSchema): Billboard data.
        actions (str, optional): HTML string for actions.
    """

    owner: OwnerSchema
    billboard: BillboardSchema
    actions: str = ""


class LedgerSchema(Schema):
    """

    Schema for Ledger Summary.

    Attributes:
        bounty (float): Amount related to bounties.
        ess (float): Amount related to ESS activities.
        costs (float): Amount related to costs.
        miscellaneous (float): Miscellaneous amount.
        total (float): Total amount.
    """

    bounty: float = 0.00
    ess: float = 0.00
    costs: float = 0.00
    miscellaneous: float = 0.00
    total: float = 0.00


class CharacterLedgerSchema(LedgerSchema):
    """
    Schema for Character Ledger extending LedgerSchema.

    Subclass of :class:`LedgerSchema`.

    Attributes:
        mining (float): Amount related to mining activities.
    """

    mining: float = 0.00


class OwnerLedgerRequestInfo(Schema):
    """Schema for Owner Ledger Request Information."""

    owner_id: int
    year: int
    month: int | None = None
    day: int | None = None
    section: str = "summary"
    dropdown_html: str | None = None
    footer_html: str | None = None

    def to_date_query(self) -> dict:
        date_query = {"date__year": self.year}
        if self.month is not None:
            date_query["date__month"] = self.month
        if self.day is not None:
            date_query["date__day"] = self.day
        return date_query


class CorporationLedgerRequestInfo(OwnerLedgerRequestInfo):
    """
    Schema for Corporation Ledger Request Information.

    Subclass of :class:`OwnerLedgerRequestInfo`.

    Attributes:
        entity_id (int | None): The ID of the entity.
        division_id (int | None): The ID of the division.
    """

    entity_id: int | None = None
    division_id: int | None = None

    def to_division_query(self) -> dict:
        division_query = {}
        if self.division_id is not None:
            division_query["division__division_id"] = self.division_id
        return division_query


class AllianceLedgerRequestInfo(OwnerLedgerRequestInfo):
    """
    Schema for Alliance Ledger Request Information.

    Subclass of :class:`OwnerLedgerRequestInfo`.

    Attributes:
        corporation_id (int | None): The ID of the corporation.
    """

    corporation_id: int | None = None


class LedgerDetailsSummary(Schema):
    """
    Schema for summary of ledger details.

    Attributes:
        summary (str): Summary of all categories.
        daily (str): Daily breakdown of categories.
        hourly (str): Hourly breakdown of categories.
    """

    summary: str = ""
    daily: str = ""
    hourly: str = ""


class LedgerDetailsResponse(Schema):
    """Flexible schema for detailed ledger categories.

    Attributes:
        summary (CategorySchema): Summary of all categories.
        daily (CategorySchema): Daily breakdown of categories.
        hourly (CategorySchema): Hourly breakdown of categories.
    """

    summary: list[CategorySchema]
    daily: list[CategorySchema]
    hourly: list[CategorySchema]
    total: LedgerDetailsSummary


class CharacterAdmin(Schema):
    character: dict | None = None


class CorporationAdmin(Schema):
    corporation: dict | None = None


class AllianceAdmin(Schema):
    alliance: dict | None = None


class EveTypeSchema(Schema):
    """
    Schema for EVE Online item types.

    Attributes:
        id (int): The ID of the item type.
        name (str): The name of the item type.
        description (str | None): The description of the item type, if available.
        group_id (int | None): The group ID of the item type, if available.
        group_name (str | None): The group name of the item type, if available.
        market_group_id (int | None): The market group ID of the item type, if available.
        market_group_name (str | None): The market group name of the item type, if available.
        icon (str | None): The URL of the item type's icon, if available.
    """

    id: int
    name: str
    description: str | None = None
    group_id: int | None = None
    group_name: str | None = None
    market_group_id: int | None = None
    market_group_name: str | None = None
    icon: str | None = None


class PlanetSchema(Schema):
    id: int
    name: str
    type: EveTypeSchema
    upgrade_level: int
    num_pins: int
    last_update: timezone.datetime


class CharacterPlanet(Schema):
    character_id: int | None = None
    character_name: str | None = None
    planet: str | None = None
    planet_id: int | None = None
    upgrade_level: int | None = None
    num_pins: int | None = None
    last_update: datetime | None = None


class ProgressBarSchema(Schema):
    percentage: str
    html: str


class ExtractorSchema(Schema):
    item_id: int
    item_name: str
    icon: str | None = None
    install_time: str
    expiry_time: str
    progress: ProgressBarSchema
