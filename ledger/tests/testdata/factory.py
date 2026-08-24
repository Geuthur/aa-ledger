# Standard Library
from typing import Generic, TypeVar

# Third Party
import factory
import factory.fuzzy

# Django
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from eve_sde.models import (
    Constellation,
    ItemCategory,
    ItemGroup,
    ItemType,
    Planet,
    Region,
    SolarSystem,
)

# AA Ledger
from ledger.models import (
    CharacterMiningLedger,
    CharacterOwner,
    CharacterPlanet,
    CharacterPlanetDetails,
    CharacterWalletJournalEntry,
    CorporationOwner,
    CorporationUpdateStatus,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
    EveEntity,
    EveMarketPrice,
)
from ledger.models.characteraudit import CharacterUpdateStatus
from ledger.models.helpers.update_manager import (
    CharacterUpdateSection,
    CorporationUpdateSection,
)
from ledger.tests.testdata.utils import add_character_to_user

T = TypeVar("T")
User = get_user_model()


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


class UserFactory(factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[User]):
    """Generate a User object."""

    class Meta:
        model = User
        django_get_or_create = ("username",)
        exclude = ("_generated_name",)

    _generated_name = factory.Faker("name")
    username = factory.LazyAttribute(lambda obj: obj._generated_name.replace(" ", "_"))
    first_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[0])
    last_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[1])
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com"
    )

    @factory.post_generation
    def permissions(obj, create, extracted, **kwargs):
        """Set default permissions. Overwrite with `permissions=["app.perm1"]`."""
        if not create:
            return
        permissions = extracted or []
        for permission_name in permissions:
            AuthUtils.add_permission_to_user_by_name(permission_name, obj)

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        """Reset permission cache to force an update."""
        super()._after_postgeneration(obj, create, results)
        if hasattr(obj, "_perm_cache"):
            del obj._perm_cache
        if hasattr(obj, "_user_perm_cache"):
            del obj._user_perm_cache


class UserMainFactory(UserFactory):
    """Generate a User object with a main character and default permissions for Ledger."""

    permissions__ = ["ledger.basic_access"]

    @factory.post_generation
    def main_character(obj, create, _, **kwargs):
        if not create:
            return
        if "character" in kwargs:
            character = kwargs["character"]
        else:
            character_name = f"{obj.first_name} {obj.last_name}"
            character = EveCharacterFactory(character_name=character_name)

        scopes = kwargs.get("scopes", CharacterOwner.get_esi_scopes())

        add_character_to_user(
            user=obj, character=character, is_main=True, scopes=scopes
        )


class EveAllianceInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveAllianceInfo]
):
    """Generate an EveAllianceInfo object."""

    class Meta:
        model = EveAllianceInfo
        django_get_or_create = ("alliance_id", "alliance_name")

    alliance_name = factory.Faker("catch_phrase")
    alliance_ticker = factory.LazyAttribute(lambda obj: obj.alliance_name[:4].upper())
    executor_corp_id = 0

    @factory.lazy_attribute
    def alliance_id(self):
        last_id = (
            EveAllianceInfo.objects.aggregate(Max("alliance_id"))["alliance_id__max"]
            or 99_000_000
        )
        return last_id + 1


class EveCorporationInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCorporationInfo]
):
    """Generate an EveCorporationInfo object."""

    class Meta:
        model = EveCorporationInfo
        django_get_or_create = ("corporation_id", "corporation_name")

    corporation_name = factory.Faker("catch_phrase")
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation_name[:4].upper()
    )
    member_count = factory.fuzzy.FuzzyInteger(1000)

    @factory.lazy_attribute
    def corporation_id(self):
        last_id = (
            EveCorporationInfo.objects.aggregate(Max("corporation_id"))[
                "corporation_id__max"
            ]
            or 98_000_000
        )
        return last_id + 1

    @factory.post_generation
    def create_alliance(obj, create, extracted, **kwargs):
        if not create or extracted is False or obj.alliance:
            return
        obj.alliance = EveAllianceInfoFactory(executor_corp_id=obj.corporation_id)


class EveCharacterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCharacter]
):
    """
    Generate an EveCharacter object.

    Args:
        character_name (str): The name of the EveCharacter.
        corporation (EveCorporationInfo, optional): The EveCorporationInfo object associated with the character. If not provided, it will be created.
        corporation_id (int): The ID of the corporation associated with the character.
        corporation_name (str): The name of the corporation associated with the character.
        corporation_ticker (str): The ticker of the corporation associated with the character.
        character_id (int): The unique ID for the character. If not provided, it will be generated.
        alliance_id (int): The ID of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_name (str): The name of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_ticker (str): The ticker of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
    """

    class Meta:
        model = EveCharacter
        django_get_or_create = ("character_id", "character_name")
        exclude = ("corporation",)

    character_name = factory.Faker("name")
    corporation = factory.SubFactory(EveCorporationInfoFactory)
    corporation_id = factory.LazyAttribute(lambda obj: obj.corporation.corporation_id)
    corporation_name = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_name
    )
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_ticker
    )

    @factory.lazy_attribute
    def character_id(self):
        last_id = (
            EveCharacter.objects.aggregate(Max("character_id"))["character_id__max"]
            or 90_000_000
        )
        return last_id + 1

    @factory.lazy_attribute
    def alliance_id(self):
        return (
            self.corporation.alliance.alliance_id if self.corporation.alliance else None
        )

    @factory.lazy_attribute
    def alliance_name(self):
        return (
            self.corporation.alliance.alliance_name if self.corporation.alliance else ""
        )

    @factory.lazy_attribute
    def alliance_ticker(self):
        return (
            self.corporation.alliance.alliance_ticker
            if self.corporation.alliance
            else ""
        )


class EveEntityFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveEntity]
):
    """
    Generate an EveEntity object.

    Args:
        name (str): The name of the EveEntity.
        category (str): The category of the EveEntity, which can be "character", "corporation", or "alliance".
        id (int): The unique ID for the EveEntity. If not provided, it will be generated.
    """

    class Meta:
        model = EveEntity
        django_get_or_create = ("eve_id", "name")

    name = factory.Faker("name")
    category = factory.fuzzy.FuzzyChoice(["character", "corporation", "alliance"])

    @factory.lazy_attribute
    def eve_id(self):
        last_id = (
            EveEntity.objects.aggregate(Max("eve_id"))["eve_id__max"] or 90_000_000
        )
        return last_id + 1


class CorporationOwnerFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationOwner]
):
    """
    Generate a CorporationOwner object.

    Args:
        user (User, optional): The user associated with the corporation owner. If not provided, it will be created.
        eve_corporation (EveCorporationInfo): The EveCorporationInfo object associated with the corporation owner.
        name (str): The name of the corporation owner, derived from the EveCorporationInfo object.
    """

    class Meta:
        model = CorporationOwner
        exclude = ("user",)

    user = factory.SubFactory(
        UserMainFactory,
        main_character__scopes=CorporationOwner.get_esi_scopes(),
    )
    eve_corporation = factory.LazyAttribute(
        lambda o: o.user.profile.main_character.corporation
    )
    corporation_name = factory.LazyAttribute(
        lambda o: o.eve_corporation.corporation_name
    )


class CharacterOwnerFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CharacterOwner]
):
    """
    Generate a CharacterOwner object.

    Args:
        user (User, optional): The user associated with the character owner. If not provided, it will be created.
        eve_character (EveEntity): The EveEntity object associated with the character owner.
        name (str): The name of the character owner, derived from the EveCharacter object.
    """

    class Meta:
        model = CharacterOwner
        exclude = ("user",)

    user = factory.SubFactory(UserMainFactory)
    eve_character = factory.LazyAttribute(lambda o: o.user.profile.main_character)
    character_name = factory.LazyAttribute(lambda o: o.eve_character.character_name)
    active = True
    balance = factory.fuzzy.FuzzyDecimal(1000, 1000000, 2)


class DivisionFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationWalletDivision],
):
    """
    Generate a CorporationWalletDivision object.

    Args:
        name (str): The name of the division.
        balance (Decimal): The balance of the division.
        corporation (CorporationOwner, optional): The corporation associated with the division. If not provided, it will be created.
        division_id (int): The unique ID for the division.
    """

    class Meta:
        model = CorporationWalletDivision
        django_get_or_create = ("division_id",)

    name = factory.Faker("name")
    balance = factory.fuzzy.FuzzyDecimal(1000, 1000000, 2)
    corporation = factory.SubFactory(CorporationOwnerFactory)

    @factory.lazy_attribute
    def division_id(self):
        last_id = (
            CorporationWalletDivision.objects.filter(
                corporation=self.corporation
            ).aggregate(Max("division_id"))["division_id__max"]
            or 0
        )
        return last_id + 1


class CharacterJournalFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterWalletJournalEntry],
):
    """Generate a CharacterWalletJournalEntry object.

    Args:
        character (CharacterOwner, optional): The character associated with the journal entry. If not provided, it will be created.
        entry_id (int): The unique entry ID for the journal entry.
        amount (Decimal): The amount of the journal entry.
        balance (Decimal): The balance after the journal entry.
        context_id (int): The context ID associated with the journal entry.
        context_id_type (str): The type of the context ID.
        date (datetime): The date and time of the journal entry.
        description (str): A description of the journal entry.
        first_party (EveEntity, optional): The first party involved in the journal entry. If not provided, it will be created.
        id (int): The unique ID for the journal entry.
        reason (str): The reason for the journal entry.
        ref_type (str): The reference type of the journal entry.
        second_party (EveEntity, optional): The second party involved in the journal entry. If not provided, it will be created.
        tax (Decimal): The tax amount associated with the journal entry.
        tax_receiver_id (int): The ID of the tax receiver associated with the journal entry.
    """

    _CONTEXT_ID_TYPE_CHOICES = [
        "structure_id",
        "station_id",
        "market_transaction_id",
        "character_id",
        "corporation_id",
        "alliance_id",
        "eve_system",
        "industry_job_id",
        "contract_id",
        "planet_id",
        "system_id",
        "type_id",
    ]

    _REF_TYPE_CHOICES = [
        "bounty_prizes",
        "market_transaction",
        "industry_job",
        "contract_reward",
        "industry_job_tax",
        "planetary_tax",
        "ess_escrow_transfer",
    ]

    class Meta:
        model = CharacterWalletJournalEntry
        django_get_or_create = ("entry_id",)

    character = factory.SubFactory(CharacterOwnerFactory)
    entry_id = factory.Sequence(lambda n: n + 1)

    amount = factory.fuzzy.FuzzyDecimal(-100000, 100000, 0)
    balance = factory.LazyAttribute(lambda o: o.character.balance + o.amount)
    context_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    context_id_type = factory.fuzzy.FuzzyChoice(_CONTEXT_ID_TYPE_CHOICES)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    description = factory.Faker("sentence")
    first_party = factory.SubFactory(EveEntityFactory)
    id = factory.Sequence(lambda n: n + 1)
    reason = factory.Faker("sentence")
    ref_type = factory.fuzzy.FuzzyChoice(_REF_TYPE_CHOICES)
    second_party = factory.SubFactory(EveEntityFactory)
    tax = factory.fuzzy.FuzzyDecimal(0, 10000, 2)
    tax_receiver_id = factory.fuzzy.FuzzyInteger(1, 1000000)


class CorporationJournalFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationWalletJournalEntry],
):
    """Generate a CorporationWalletJournalEntry object.

    Args:
        division (CorporationWalletDivision, optional): The division associated with the journal entry. If not provided, it will be created.
        entry_id (int): The unique entry ID for the journal entry.
        amount (Decimal): The amount of the journal entry.
        balance (Decimal): The balance after the journal entry.
        context_id (int): The context ID associated with the journal entry.
        context_id_type (str): The type of the context ID.
        date (datetime): The date and time of the journal entry.
        description (str): A description of the journal entry.
        first_party (EveEntity, optional): The first party involved in the journal entry. If not provided, it will be created.
        id (int): The unique ID for the journal entry.
        reason (str): The reason for the journal entry.
        ref_type (str): The reference type of the journal entry.
        second_party (EveEntity, optional): The second party involved in the journal entry. If not provided, it will be created.
        tax (Decimal): The tax amount associated with the journal entry.
        tax_receiver_id (int): The ID of the tax receiver associated with the journal entry.
    """

    _CONTEXT_ID_TYPE_CHOICES = [
        "structure_id",
        "station_id",
        "market_transaction_id",
        "character_id",
        "corporation_id",
        "alliance_id",
        "eve_system",
        "industry_job_id",
        "contract_id",
        "planet_id",
        "system_id",
        "type_id",
    ]

    _REF_TYPE_CHOICES = [
        "bounty_prizes",
        "market_transaction",
        "industry_job",
        "contract_reward",
        "industry_job_tax",
        "planetary_tax",
        "ess_escrow_transfer",
    ]

    class Meta:
        model = CorporationWalletJournalEntry
        django_get_or_create = ("entry_id",)

    division = factory.SubFactory(DivisionFactory)
    entry_id = factory.Sequence(lambda n: n + 1)

    amount = factory.fuzzy.FuzzyDecimal(-100000, 100000, 0)
    balance = factory.LazyAttribute(lambda o: o.division.balance + o.amount)
    context_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    context_id_type = factory.fuzzy.FuzzyChoice(_CONTEXT_ID_TYPE_CHOICES)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    description = factory.Faker("sentence")
    first_party = factory.SubFactory(EveEntityFactory)
    id = factory.Sequence(lambda n: n + 1)
    reason = factory.Faker("sentence")
    ref_type = factory.fuzzy.FuzzyChoice(_REF_TYPE_CHOICES)
    second_party = factory.SubFactory(EveEntityFactory)
    tax = factory.fuzzy.FuzzyDecimal(0, 10000, 2)
    tax_receiver_id = factory.fuzzy.FuzzyInteger(1, 1000000)


class CharacterUpdateStatusFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterUpdateStatus],
):
    """Generate a CharacterUpdateStatus object for testing."""

    class Meta:
        model = CharacterUpdateStatus
        django_get_or_create = ("owner", "section")

    owner = factory.SubFactory(CharacterOwnerFactory)
    section = factory.fuzzy.FuzzyChoice(CharacterUpdateSection)
    is_success = True
    error_message = ""
    has_token_error = False
    last_run_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_run_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )


class CorporationUpdateStatusFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationUpdateStatus],
):
    """Generate a CorporationUpdateStatus object for testing."""

    class Meta:
        model = CorporationUpdateStatus
        django_get_or_create = ("owner", "section")

    owner = factory.SubFactory(CorporationOwnerFactory)
    section = factory.fuzzy.FuzzyChoice(CorporationUpdateSection)
    is_success = None
    error_message = ""
    has_token_error = False
    last_run_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_run_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )


class ItemCategoryFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemCategory]
):
    """Generate an ItemCategory object for testing."""

    class Meta:
        model = ItemCategory
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    published = True
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)


class ItemGroupFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemGroup]
):
    """Generate an ItemGroup object for testing."""

    class Meta:
        model = ItemGroup
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    anchorable = False
    anchored = False
    category = factory.SubFactory(ItemCategoryFactory)
    fittable_non_singleton = False
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)
    published = True
    use_base_price = False


class ItemTypeFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[ItemType]
):
    """Generate an ItemType object for testing."""

    class Meta:
        model = ItemType
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    base_price = factory.fuzzy.FuzzyFloat(1, 10000, 2)
    capacity = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    description = factory.Faker("sentence")
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    graphic_id = factory.fuzzy.FuzzyInteger(0, 100)
    group = factory.SubFactory(ItemGroupFactory)
    icon_id = factory.fuzzy.FuzzyInteger(0, 100)
    market_group = None  # This can be set to a MarketGroup object if needed
    mass = factory.fuzzy.FuzzyDecimal(0, 1000, 2)
    meta_group_id_raw = factory.fuzzy.FuzzyInteger(0, 10)
    portion_size = factory.fuzzy.FuzzyInteger(0, 1000)
    published = True
    race_id = factory.fuzzy.FuzzyInteger(0, 10)
    radius = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    sound_id = None  # Not needed for testing, can be set to a Sound object if needed
    variation_parent_type_id = (
        None  # Not needed for testing, can be set to an ItemType object if needed
    )
    volume = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    packaged_volume = factory.fuzzy.FuzzyFloat(0, 1000, 2)


class RegionFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Region]
):
    """Generate a Region object for testing."""

    class Meta:
        model = Region
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    description = factory.Faker("sentence")
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    nebular_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)


class ConstellationFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Constellation]
):
    """Generate a Constellation object for testing."""

    class Meta:
        model = Constellation
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    region = factory.SubFactory(RegionFactory)
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)


class SolarSystemFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[SolarSystem]
):
    """Generate a SolarSystem object for testing."""

    class Meta:
        model = SolarSystem
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    border = False
    constellation = factory.SubFactory(ConstellationFactory)
    corridor = False
    faction_id_raw = factory.fuzzy.FuzzyInteger(0, 100)
    fringe = False
    hub = False
    international = False
    luminosity = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    radius = factory.fuzzy.FuzzyFloat(0, 1000, 2)
    regional = False
    security_class = factory.fuzzy.FuzzyChoice([None, "A", "B", "C", "D", "E"])
    security_status = factory.fuzzy.FuzzyFloat(0, 1, 2)
    visual_effect = (
        None  # Not needed for testing, can be set to a VisualEffect object if needed
    )
    wormhole_class_id_raw = factory.fuzzy.FuzzyInteger(0, 10)
    security_status = factory.fuzzy.FuzzyFloat(0, 1, 2)

    x_2d = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y_2d = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)


class PlanetFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Planet]
):
    """Generate a Planet object for testing."""

    class Meta:
        model = Planet
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")

    x = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    y = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)
    z = factory.fuzzy.FuzzyFloat(-1000, 1000, 2)

    celestial_index = factory.fuzzy.FuzzyInteger(1, 100)
    item_type = factory.SubFactory(ItemTypeFactory)
    orbit_id_raw = factory.fuzzy.FuzzyInteger(1, 100)
    orbit_index = factory.fuzzy.FuzzyInteger(1, 100)
    radius = factory.fuzzy.FuzzyFloat(1, 1000, 2)
    solar_system = factory.SubFactory(SolarSystemFactory)


class CharacterPlanetFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterPlanet],
):
    """Generate a CharacterPlanet object for testing."""

    class Meta:
        model = CharacterPlanet
        django_get_or_create = ("character", "eve_planet")

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")

    character = factory.SubFactory(CharacterOwnerFactory)
    eve_planet = factory.SubFactory(PlanetFactory)
    upgrade_level = factory.fuzzy.FuzzyInteger(0, 5)
    num_pins = factory.fuzzy.FuzzyInteger(0, 100)


class CharacterPlanetDetailsFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterPlanetDetails],
):
    """Generate a CharacterPlanetDetails object for testing."""

    class Meta:
        model = CharacterPlanetDetails
        django_get_or_create = ("character", "planet")

    id = factory.Sequence(lambda n: n + 1)
    planet = factory.SubFactory(CharacterPlanetFactory)
    character = factory.SubFactory(CharacterOwnerFactory)

    links = None
    pins = None
    routes = None
    factories = None

    last_alert = None

    notification = False
    notification_sent = False


class CharacterMiningLedgerFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CharacterMiningLedger],
):
    """Generate a CharacterMiningLedger object for testing."""

    class Meta:
        model = CharacterMiningLedger
        django_get_or_create = ("character", "id")

    character = factory.SubFactory(CharacterOwnerFactory)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    type = factory.SubFactory(ItemTypeFactory)
    system = factory.SubFactory(SolarSystemFactory)
    id = factory.LazyAttribute(
        lambda o: (
            f"{o.date.strftime('%Y%m%d')}-{o.type.pk}-{o.character.eve_id}-{o.system.pk}"
        )
    )
    quantity = factory.fuzzy.FuzzyInteger(1, 10000)
    price_per_unit = factory.fuzzy.FuzzyDecimal(1, 10000, 2)

    @factory.post_generation
    def eve_market_price(obj, create, _, **kwargs):
        """Set the Eve market price for the CharacterMiningLedger."""
        if not create:
            return
        EveMarketPrice.objects.get_or_create(
            eve_type=obj.type,
            adjusted_price=factory.fuzzy.FuzzyDecimal(1, 10000, 2).fuzz(),
            average_price=factory.fuzzy.FuzzyDecimal(1, 10000, 2).fuzz(),
            updated_at=timezone.now(),
        )[0]
