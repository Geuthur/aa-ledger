# Standard Library
from collections import defaultdict
from decimal import Decimal

# Django
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.api.api_helper.aggregator import AggregateLedger
from ledger.api.api_helper.billboard_helper import BillboardSystem
from ledger.api.api_helper.information_helper import (
    InformationData,
)
from ledger.models.characteraudit import CharacterAudit
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)
from ledger.models.general import EveEntity

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationProcess:
    """JournalProcess class to process the journal entries."""

    def __init__(
        self,
        corporation: CorporationAudit,
        date: timezone.datetime,
        main_character: CharacterAudit,
        view=None,
    ):
        self.main_character = main_character
        self.corporation = corporation
        self.date = date
        self.view = view
        self.current_date = timezone.now()

        self._init_journal()

    # pylint: disable=duplicate-code
    def _filter_date(self):
        """Filter the date."""
        filter_date = Q(date__year=self.date.year)
        if self.view == "month":
            filter_date &= Q(date__month=self.date.month)
        elif self.view == "day":
            filter_date &= Q(date__month=self.date.month)
            filter_date &= Q(date__day=self.date.day)
        return filter_date

    def _init_journal(self):
        """Initialize the data for the ledger."""
        self.corporation_journal = CorporationWalletJournalEntry.objects.filter(
            self._filter_date(),
            division__corporation__corporation__corporation_id=self.corporation.corporation.corporation_id,
        )

        # Get Glances
        self.glance = AggregateLedger(self.corporation_journal)

        # Get Entity IDs from Character or Corporation
        if self.main_character:
            alts = self.main_character.alts
            self.entity_ids = EveEntity.objects.filter(
                eve_id__in=alts.values_list("character_id", flat=True),
            ).values_list("eve_id", flat=True)
        else:
            self.entity_ids = set(
                self.corporation_journal.values_list("second_party_id", flat=True)
            ) | set(self.corporation_journal.values_list("first_party_id", flat=True))

        self.glance_day = self.corporation_journal.filter(
            date__year=self.current_date.year,
            date__month=self.current_date.month,
            date__day=self.current_date.day,
        )

    def generate_ledger(self):
        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).prefetch_related(
            "user__profile__main_character",
        )

        main_dict = {}
        billboard = BillboardSystem(view=self.view)

        account_totals = defaultdict(int)

        def process_account(account):
            """Helper method to process a single account."""
            alts = account.user.character_ownerships.all().values_list(
                "character__character_id", flat=True
            )
            # Filter out alts that are not in the journal
            alts = set(alts).intersection(self.entity_ids)

            if not alts:
                return None

            bounty = self.glance.aggregate_bounty(alts)
            ess = self.glance.aggregate_ess(alts)
            miscellaneous = (
                self.glance.aggregate_production(
                    alts
                )  # Add Production Amount to Account
                + self.glance.aggregate_miscellaneous(alts)
                + self.glance.aggregate_donation(alts)  # Add Donation Amount to Account
            )

            if bounty > 0 or ess > 0 or miscellaneous > 0:
                data = {
                    "main_id": account.user.profile.main_character.character_id,
                    "main_name": account.user.profile.main_character.character_name,
                    "entity_type": "character",
                    "alt_names": list(alts),
                    "total_amount": bounty,
                    "total_amount_ess": ess,
                    "total_amount_others": miscellaneous,
                    "total_amount_costs": 0,
                }
                account_totals["bounty"] += bounty
                account_totals["ess"] += ess
                account_totals["miscellaneous"] += miscellaneous

                billboard.chord_add_data(
                    data["main_name"], _("Wallet"), (bounty + ess + miscellaneous)
                )
                return data
            return None

        for account in accounts:
            data = process_account(account)
            if data:
                main_dict[data["main_id"]] = data

        # Aggregate totals
        total_bounty = self.glance.aggregate_bounty()
        total_ess = self.glance.aggregate_ess()
        total_miscellaneous = (
            +self.glance.aggregate_miscellaneous()
            + self.glance.aggregate_donation()
            + self.glance.aggregate_corp_withdraw(
                exclude=self.corporation.corporation.corporation_id
            )  # Exclude Intern Transfers
        )
        total_costs = (
            self.glance.aggregate_costs()
            + self.glance.aggregate_corp_withdraw_cost(
                exclude=self.corporation.corporation.corporation_id
            )
        )  # Add Corporation Withdraws Costs

        # Substract account totals from the total amounts
        other_totals = {
            "bounty": total_bounty - account_totals["bounty"],
            "ess": total_ess - account_totals["ess"],
            "miscellaneous": total_miscellaneous - account_totals["miscellaneous"],
            "costs": total_costs,
        }

        if (
            total_bounty > 0
            or total_ess > 0
            or total_miscellaneous > 0
            or total_costs > 0
        ):
            data = {
                "main_id": self.corporation.corporation.corporation_id,
                "main_name": self.corporation.corporation.corporation_name,
                "entity_type": "corporation",
                "alt_names": None,
                "total_amount": other_totals["bounty"],
                "total_amount_ess": other_totals["ess"],
                "total_amount_others": other_totals["miscellaneous"],
                "total_amount_costs": other_totals["costs"],
            }
            main_dict[data["main_id"]] = data
            billboard.chord_add_data(
                data["main_name"],
                _("Wallet"),
                (
                    other_totals["bounty"]
                    + other_totals["ess"]
                    + other_totals["miscellaneous"]
                ),
            )

        # Add Rattingbar for the corporation
        rattingbar_timeline = billboard.create_timeline(self.corporation_journal)
        rattingbar = (
            rattingbar_timeline.annotate_bounty_income()
            .annotate_ess_income()
            .annotate_miscellaneous()
        )
        billboard.create_or_update_results(rattingbar)
        billboard.create_ratting_bar()

        # Order and Handle Overflow
        billboard.chord_handle_overflow()

        output = {
            "ratting": sorted(list(main_dict.values()), key=lambda x: x["main_name"]),
            "billboard": billboard.dict,
            "total": {
                "total_amount": total_bounty,
                "total_amount_ess": total_ess,
                "total_amount_others": total_miscellaneous,
                "total_amount_costs": total_costs,
                "total_amount_all": total_bounty
                + total_ess
                + total_miscellaneous
                + total_costs,
            },
        }

        return output

    def generate_template(self):
        """Generate the information for the corporation"""
        information_dict = {}
        exclude = None

        # Create the Ledger
        ledger_data = InformationData(
            character=self.main_character,
            corporation=self.corporation,
            date=self.date,
            view=self.view,
            current_date=self.current_date,
        )

        if self.corporation is not None:
            exclude = self.corporation.corporation.corporation_id

        day_aggregate = AggregateLedger(self.glance_day)

        amounts = defaultdict(lambda: defaultdict(Decimal))

        amounts["bounty_income"] = {
            "total_amount": self.glance.aggregate_bounty(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_bounty(self.entity_ids),
        }

        amounts["ess_income"] = {
            "total_amount": self.glance.aggregate_ess(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_ess(self.entity_ids),
        }

        amounts["mission_income"] = {
            "total_amount": self.glance.aggregate_mission(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_mission(self.entity_ids),
        }

        amounts["incursion_income"] = {
            "total_amount": self.glance.aggregate_incursion(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_incursion(self.entity_ids),
        }

        amounts["market_income"] = {
            "total_amount": self.glance.aggregate_market(second_party=self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_market(
                second_party=self.entity_ids
            ),
        }

        amounts["contract_income"] = {
            "total_amount": self.glance.aggregate_contract(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_contract(self.entity_ids),
        }

        amounts["donation_income"] = {
            "total_amount": self.glance.aggregate_donation(self.entity_ids)
            + self.glance.aggregate_corp_withdraw(self.entity_ids, exclude=exclude),
            "total_amount_day": day_aggregate.aggregate_donation(self.entity_ids)
            + day_aggregate.aggregate_corp_withdraw(self.entity_ids, exclude=exclude),
        }

        amounts["insurance_income"] = {
            "total_amount": self.glance.aggregate_insurance(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_insurance(self.entity_ids),
        }

        amounts["daily_goal_income"] = {
            "total_amount": self.glance.aggregate_daily_goal(self.entity_ids),
            "total_amount_day": day_aggregate.aggregate_daily_goal(self.entity_ids),
        }

        amounts["citadel_income"] = {
            "total_amount": (
                self.glance.aggregate_production(self.entity_ids)
                + self.glance.aggregate_traveling(self.entity_ids)
            ),
            "total_amount_day": (
                day_aggregate.aggregate_production(self.entity_ids)
                + day_aggregate.aggregate_traveling(self.entity_ids)
            ),
        }

        # Only Corporation will have costs
        if not self.main_character:
            amounts["asset_cost"] = {
                "total_amount": self.glance.aggregate_assets(self.entity_ids),
                "total_amount_day": day_aggregate.aggregate_assets(self.entity_ids),
            }

            amounts["market_cost"] = {
                "total_amount": self.glance.aggregate_market_cost(self.entity_ids),
                "total_amount_day": day_aggregate.aggregate_market_cost(
                    self.entity_ids
                ),
            }

            amounts["rental_cost"] = {
                "total_amount": self.glance.aggregate_rental(self.entity_ids),
                "total_amount_day": day_aggregate.aggregate_rental(self.entity_ids),
            }

            amounts["donation_cost"] = {
                "total_amount": self.glance.aggregate_corp_withdraw_cost(
                    self.entity_ids, exclude=exclude
                ),
                "total_amount_day": day_aggregate.aggregate_corp_withdraw_cost(
                    self.entity_ids, exclude=exclude
                ),
            }

            amounts["contract_cost"] = {
                "total_amount": self.glance.aggregate_contract_cost(self.entity_ids),
                "total_amount_day": day_aggregate.aggregate_contract_cost(
                    self.entity_ids
                ),
            }

            amounts["production_cost"] = {
                "total_amount": self.glance.aggregate_production_cost(self.entity_ids),
                "total_amount_day": day_aggregate.aggregate_production_cost(
                    self.entity_ids
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
