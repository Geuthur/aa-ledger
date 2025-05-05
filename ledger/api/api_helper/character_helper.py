# Standard Library
import logging
from collections import defaultdict
from decimal import Decimal

# Django
from django.db.models import Q, QuerySet
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# AA Ledger
from ledger.api.api_helper.aggregator import AggregateLedger, AggregateMining
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.api.api_helper.information_helper import (
    InformationData,
)
from ledger.api.helpers import get_alts_queryset
from ledger.helpers.core import events_filter
from ledger.models.characteraudit import (
    CharacterMiningLedger,
    CharacterWalletJournalEntry,
)
from ledger.models.corporationaudit import (
    CorporationWalletJournalEntry,
)

logger = logging.getLogger(__name__)


class CharacterGlances:
    """CharacterGlances class to process the glances for the character."""

    def __init__(
        self, char_journal: QuerySet, corp_journal: QuerySet, mining_journal: QuerySet
    ):
        self.glance_char = AggregateLedger(char_journal)
        self.glance_corp = AggregateLedger(corp_journal)
        self.glance_mining = AggregateMining(mining_journal)
        self.glance_day_char = char_journal.filter(
            date__year=timezone.now().year,
            date__month=timezone.now().month,
            date__day=timezone.now().day,
        )
        self.glance_day_corp = corp_journal.filter(
            date__year=timezone.now().year,
            date__month=timezone.now().month,
            date__day=timezone.now().day,
        )
        self.glance_day_mining = mining_journal.filter(
            date__year=timezone.now().year,
            date__month=timezone.now().month,
            date__day=timezone.now().day,
        )


# pylint: disable=too-many-instance-attributes
class CharacterProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(
        self,
        main: EveCharacter,
        chars: QuerySet[EveCharacter],
        date: timezone.datetime,
        view=None,
    ):
        self.main = main
        self.chars = chars
        self.date = date
        self.view = view
        self.current_date = timezone.now()

        self._init_journal()

    def _filter_date(self):
        # pylint: disable=duplicate-code
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)
        return filter_date

    def _init_journal(self):
        """Initialize the data for the ledger"""
        self.chars_ids = [char.character_id for char in self.chars]
        self.alt_ids = self.chars_ids
        if len(self.chars) == 1:
            self.alt_ids = get_alts_queryset(self.main).values_list(
                "character_id", flat=True
            )

        self.character_journal = CharacterWalletJournalEntry.objects.filter(
            self._filter_date(), character__character__character_id__in=self.chars_ids
        )
        self.mining_journal = CharacterMiningLedger.objects.filter(
            self._filter_date(), character__character__character_id__in=self.chars_ids
        )
        self.corporation_journal = self._init_corporation_journal(self.chars_ids)

        self.glances = CharacterGlances(
            char_journal=self.character_journal,
            corp_journal=self.corporation_journal,
            mining_journal=self.mining_journal,
        )

    def _init_corporation_journal(self, chars_ids: list[int]):
        """Get the involved characters for the corporation"""
        corporation_journal = CorporationWalletJournalEntry.objects.filter(
            self._filter_date(),
            Q(first_party_id__in=chars_ids) | Q(second_party_id__in=chars_ids),
        )

        # Exclude Corp Tax Events
        corporation_journal = events_filter(corporation_journal)

        return corporation_journal

    def generate_ledger(self):
        ratting = {}
        billboard = BillboardSystem(self.view)

        def process_character(char):
            """Helper method to process a single character."""
            bounty = self.glances.glance_char.aggregate_bounty(char.character_id)
            ess = self.glances.glance_corp.aggregate_ess(
                char.character_id, is_character=True
            )
            mining = self.glances.glance_mining.aggregate_mining(char.character_id)
            miscellaneous = self.glances.glance_char.aggregate_miscellaneous(
                char.character_id
            )
            donation = self.glances.glance_char.aggregate_donation(
                char.character_id, exclude=self.alt_ids
            )
            daily_goal = self.glances.glance_corp.aggregate_daily_goal(
                char.character_id, is_character=True
            )
            miscellaneous += donation + daily_goal
            costs = self.glances.glance_char.aggregate_costs(char.character_id)

            if bounty == 0 and ess == 0 and miscellaneous == 0 and costs == 0:
                return None

            data = {
                "main_id": char.character_id,
                "main_name": char.character_name,
                "entity_type": "character",
                "total_amount": bounty,
                "total_amount_ess": ess,
                "total_amount_mining": mining,
                "total_amount_others": miscellaneous,
                "total_amount_costs": costs,
            }
            return data

        for char in self.chars:
            data = process_character(char)
            if data:
                ratting[char.character_id] = data
                billboard.chord_add_char_data_from_dict(data)

        # Add Character Journal to the billboard
        rattingbar_timeline = billboard.create_timeline(self.character_journal)
        rattingbar = rattingbar_timeline.annotate_bounty_income().annotate_miscellaneous_with_exclude(
            exclude=self.alt_ids
        )
        billboard.create_or_update_results(rattingbar)

        # Add Corporation Journal to the billboard
        rattingbar_timeline = billboard.create_timeline(self.corporation_journal)
        rattingbar = rattingbar_timeline.annotate_ess_income(is_character=True)
        billboard.create_or_update_results(rattingbar)

        billboard.create_ratting_bar()

        # Aggregate totals
        totals = {
            "total_amount": self.glances.glance_char.aggregate_bounty(self.chars_ids),
            "total_amount_ess": self.glances.glance_corp.aggregate_ess(
                self.chars_ids, is_character=True
            ),
            "total_amount_mining": self.glances.glance_mining.aggregate_mining(
                self.chars_ids
            ),
            "total_amount_costs": self.glances.glance_char.aggregate_costs(
                self.chars_ids
            ),
            "total_amount_others": (
                self.glances.glance_char.aggregate_miscellaneous(self.chars_ids)
                + self.glances.glance_corp.aggregate_daily_goal(
                    self.chars_ids, is_character=True
                )
                + self.glances.glance_char.aggregate_donation(
                    self.chars_ids, exclude=self.alt_ids
                )
            ),
        }
        totals["total_amount_all"] = (
            totals["total_amount"]
            + totals["total_amount_ess"]
            + totals["total_amount_mining"]
            + totals["total_amount_others"]
            + totals["total_amount_costs"]
        )

        output = {
            "ratting": sorted(list(ratting.values()), key=lambda x: x["main_name"]),
            "billboard": billboard.dict,
            "total": totals,
        }

        return output

    def generate_template(self):
        """Generate the template for the character"""
        information_dict = {}

        # Create the Ledger
        ledger_data = InformationData(
            character=self.main,
            date=self.date,
            view=self.view,
            current_date=self.current_date,
        )

        day_glance = AggregateLedger(self.glances.glance_day_char)
        day_glance_corp = AggregateLedger(self.glances.glance_day_corp)
        day_glance_mining = AggregateMining(self.glances.glance_day_mining)

        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts["bounty_income"] = {
            "total_amount": self.glances.glance_char.aggregate_bounty(self.chars_ids),
            "total_amount_day": day_glance.aggregate_bounty(self.chars_ids),
        }

        amounts["mission_income"] = {
            "total_amount": self.glances.glance_char.aggregate_mission(self.chars_ids),
            "total_amount_day": day_glance.aggregate_mission(self.chars_ids),
        }

        amounts["mining"] = {
            "total_amount": self.glances.glance_mining.aggregate_mining(self.chars_ids),
            "total_amount_day": day_glance_mining.aggregate_mining(self.chars_ids),
        }

        amounts["incursion_income"] = {
            "total_amount": self.glances.glance_char.aggregate_incursion(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_incursion(self.chars_ids),
        }

        amounts["market_income"] = {
            "total_amount": self.glances.glance_char.aggregate_market(
                second_party=self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_market(
                second_party=self.chars_ids
            ),
        }

        amounts["contract_income"] = {
            "total_amount": self.glances.glance_char.aggregate_contract(self.chars_ids),
            "total_amount_day": day_glance.aggregate_contract(self.chars_ids),
        }

        amounts["donation_income"] = {
            "total_amount": self.glances.glance_char.aggregate_donation(
                self.chars_ids, exclude=self.alt_ids
            ),
            "total_amount_day": day_glance.aggregate_donation(
                self.chars_ids, exclude=self.alt_ids
            ),
        }

        amounts["insurance_income"] = {
            "total_amount": self.glances.glance_char.aggregate_insurance(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_insurance(self.chars_ids),
        }

        amounts["milestone_income"] = {
            "total_amount": self.glances.glance_char.aggregate_milestone_reward(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_milestone_reward(self.chars_ids),
        }

        amounts["market_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_market_cost(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_market_cost(self.chars_ids),
        }

        amounts["contract_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_contract_cost(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_contract_cost(self.chars_ids),
        }

        amounts["lp_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_lp_cost(self.chars_ids),
            "total_amount_day": day_glance.aggregate_lp_cost(self.chars_ids),
        }

        amounts["production_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_production_cost(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_production_cost(self.chars_ids),
        }

        amounts["traveling_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_traveling(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_traveling(self.chars_ids),
        }

        amounts["asset_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_assets(self.chars_ids),
            "total_amount_day": day_glance.aggregate_assets(self.chars_ids),
        }

        amounts["skill_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_skill(self.chars_ids),
            "total_amount_day": day_glance.aggregate_skill(self.chars_ids),
        }

        amounts["insurance_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_insurance_cost(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_insurance_cost(self.chars_ids),
        }

        amounts["planetary_cost"] = {
            "total_amount": self.glances.glance_char.aggregate_planetary(
                self.chars_ids
            ),
            "total_amount_day": day_glance.aggregate_planetary(self.chars_ids),
        }

        # Corporation Stuff

        amounts["ess_income"] = {
            "total_amount": self.glances.glance_corp.aggregate_ess(
                self.chars_ids, is_character=True
            ),
            "total_amount_day": day_glance_corp.aggregate_ess(
                self.chars_ids, is_character=True
            ),
        }

        amounts["daily_goal_income"] = {
            "total_amount": self.glances.glance_corp.aggregate_daily_goal(
                self.chars_ids, is_character=True
            ),
            "total_amount_day": day_glance_corp.aggregate_daily_goal(
                self.chars_ids, is_character=True
            ),
        }

        information_dict.update(
            {
                "main_id": ledger_data.id,
                "main_name": ledger_data.name,
                "date": ledger_data.information_date,
            }
        )
        information_dict = ledger_data._generate_amounts_dict(amounts, information_dict)
        return information_dict
