# Standard Library
from datetime import datetime
from typing import Literal

# Third Party
from ninja import Field, FilterSchema, Schema
from pydantic import model_validator

# AA Ledger
from ledger.helpers.billboard import BillboardData

Section = Literal["single", "summary"]


class ErrorSchema(Schema):
    """Schema for error responses."""

    error: str


class MessageSchema(Schema):
    """Schema for simple success responses."""

    message: str


class MenuLink(Schema):
    """A navigation link. `link` is relative to the app root unless `is_external` is set."""

    name: str
    link: str
    badge: int | None = None
    is_external: bool = False


class MenuSchema(Schema):
    left_links: list[MenuLink] = []
    right_links: list[MenuLink] = []


class UserData(Schema):
    """The current user, its main character and the permissions the UI depends on."""

    user_id: int
    character_id: int = 0
    character_name: str = ""
    corporation_id: int = 0
    corporation_name: str = ""
    alliance_id: int | None = None
    alliance_name: str | None = None
    portrait: str | None = None
    is_admin: bool = False
    can_manage: bool = False
    has_advanced_access: bool = False


class UserSettingsSchema(Schema):
    """Notification settings of the current user."""

    disable_notifications: bool


class UserSettingsUpdateRequest(Schema):
    """User-editable notification preferences."""

    disable_notifications: bool


class AdminUpdateRequest(Schema):
    """Request to queue an update. Without `eve_id` all owners of the target are updated."""

    target: Literal["characters", "corporations"]
    eve_id: int | None = None
    force_refresh: bool = False


class DateFilter(FilterSchema):
    """Date query parameters shared by all ledger endpoints, applied to `date`."""

    year: int = Field(..., ge=2003, le=2100, q="date__year")
    month: int | None = Field(None, ge=1, le=12, q="date__month")
    day: int | None = Field(None, ge=1, le=31, q="date__day")

    @model_validator(mode="after")
    def _day_requires_month(self):
        if self.day is not None and self.month is None:
            raise ValueError("day requires month")
        return self


class CorporationLedgerFilter(DateFilter):
    """Query parameters for corporation ledgers, optionally limited to one division."""

    division_id: int | None = Field(None, q="division__division_id")


class PlanetSelection(FilterSchema):
    """Selects one planet, or all planets of the character if omitted."""

    planet_id: int | None = Field(None, q="planet__id")


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


class AltSchema(Schema):
    """Alt character that is included in an entity's ledger."""

    character_id: int
    character_name: str
    icon: str | None = None
    is_registered: bool = False


class EntitySchema(Schema):
    """
    Schema for Entity or Corporation Owner.

    Attributes:
        entity_id (int): The ID of the entity.
        entity_name (str): The name of the entity.
        alt_ids (list[int]): The IDs of all characters included in the entity.
        alts (list[AltSchema]): The alt characters included in the entity.
        icon (str | None): The URL of the entity's icon, if available.
    """

    entity_id: int
    entity_name: str
    alt_ids: list[int] = []
    alts: list[AltSchema] = []
    icon: str | None = None
    is_member: bool = False


class RefTypeAmountSchema(Schema):
    """Amount that a single reference type contributed to a category."""

    ref_type: str
    amount: float = 0.00


class CategorySchema(Schema):
    name: str
    amount: float = 0.00
    average: float = 0.00
    average_tick: float = 0.00
    # Only the reference types with entries, largest absolute amount first.
    ref_types: list[RefTypeAmountSchema] = []


class UpdateStatusSchema(Schema):
    last_update: datetime | None = None
    last_run: datetime | None = None
    status: str | None = None
    icon: str | None = None


class BillboardSchema(Schema):
    xy_chart: BillboardData | None = None
    chord_chart: BillboardData | None = None


class LedgerResponse(Schema):
    """
    Schema for Ledger Response.

    Attributes:
        owner (OwnerSchema): The owner of the ledger.
        billboard (BillboardSchema): Billboard data.
    """

    owner: OwnerSchema
    billboard: BillboardSchema
    years: list[int] = []


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


class AltLedgerSchema(AltSchema):
    """Contribution of one alt character to the ledger of its entity."""

    ledger: LedgerSchema


class CharacterLedgerSchema(LedgerSchema):
    """
    Schema for Character Ledger extending LedgerSchema.

    Subclass of :class:`LedgerSchema`.

    Attributes:
        mining (float): Amount related to mining activities.
    """

    mining: float = 0.00


class LedgerDetailsSummary(Schema):
    """
    Schema for the totals of ledger details.

    Attributes:
        summary (float): Total of all categories.
        daily (float): Daily average of all categories.
        hourly (float): Hourly average of all categories.
    """

    summary: float = 0.00
    daily: float = 0.00
    hourly: float = 0.00


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


class DivisionSchema(Schema):
    """A wallet division of a corporation."""

    division_id: int
    name: str


class CharacterOverview(Schema):
    character_id: int
    character_name: str
    corporation_id: int
    corporation_name: str


class CorporationOverview(Schema):
    corporation_id: int
    corporation_name: str


class AllianceOverview(Schema):
    alliance_id: int
    alliance_name: str


class DashboardSchema(Schema):
    """Statistics shown on the administration dashboards."""

    auth_count: int
    active_count: int
    inactive_count: int | None = None
    missing_count: int
    issues: list[str] = []


class AdminOwnerSchema(Schema):
    """A character, corporation or alliance in the administration lists."""

    owner_id: int
    name: str
    icon: str | None = None
    status: str | None = None


class AdministrationResponse(Schema):
    """
    Everything the administration page of an account, corporation or alliance shows.

    Attributes:
        owner: The account's main character, corporation or alliance.
        dashboard: Registration statistics.
        registered: Entries registered in the ledger.
        missing: Entries that exist but are not registered.
        members: Characters of a corporation that are known to Auth.
    """

    owner: OwnerSchema
    dashboard: DashboardSchema
    registered: list[AdminOwnerSchema] = []
    missing: list[AdminOwnerSchema] = []
    members: list[AltSchema] = []


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
    last_update: datetime | None = None


class CharacterPlanet(Schema):
    character_id: int | None = None
    character_name: str | None = None
    planet: str | None = None
    planet_id: int | None = None
    upgrade_level: int | None = None
    num_pins: int | None = None
    last_update: datetime | None = None


class ExtractorSchema(Schema):
    item_id: int
    item_name: str
    icon: str | None = None
    install_time: str
    expiry_time: str
    progress: float
