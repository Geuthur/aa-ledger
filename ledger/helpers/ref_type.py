"""Helpers for wallet journals."""

# Standard Library
import enum

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# Unified Journal Reference Type Enum - All ref types in one place
class JournalRefType(enum.Enum):
    """All wallet journal reference types unified."""

    # Original ref types
    PLAYER_TRADING = 1
    MARKET_TRANSACTION = 2
    GM_CASH_TRANSFER = 3
    MISSION_REWARD = 7
    CLONE_ACTIVATION = 8
    INHERITANCE = 9
    PLAYER_DONATION = 10
    CORPORATION_PAYMENT = 11
    DOCKING_FEE = 12
    OFFICE_RENTAL_FEE = 13
    FACTORY_SLOT_RENTAL_FEE = 14
    REPAIR_BILL = 15
    BOUNTY = 16
    BOUNTY_PRIZE = 17
    INSURANCE = 19
    MISSION_EXPIRATION = 20
    MISSION_COMPLETION = 21
    SHARES = 22
    COURIER_MISSION_ESCROW = 23
    MISSION_COST = 24
    AGENT_MISCELLANEOUS = 25
    LP_STORE = 26
    AGENT_LOCATION_SERVICES = 27
    AGENT_DONATION = 28
    AGENT_SECURITY_SERVICES = 29
    AGENT_MISSION_COLLATERAL_PAID = 30
    AGENT_MISSION_COLLATERAL_REFUNDED = 31
    AGENTS_PREWARD = 32
    AGENT_MISSION_REWARD = 33
    AGENT_MISSION_TIME_BONUS_REWARD = 34
    CSPA = 35
    CSPAOFFLINEREFUND = 36
    CORPORATION_ACCOUNT_WITHDRAWAL = 37
    CORPORATION_DIVIDEND_PAYMENT = 38
    CORPORATION_REGISTRATION_FEE = 39
    CORPORATION_LOGO_CHANGE_COST = 40
    RELEASE_OF_IMPOUNDED_PROPERTY = 41
    MARKET_ESCROW = 42
    AGENT_SERVICES_RENDERED = 43
    MARKET_FINE_PAID = 44
    CORPORATION_LIQUIDATION = 45
    BROKERS_FEE = 46
    CORPORATION_BULK_PAYMENT = 47
    ALLIANCE_REGISTRATION_FEE = 48
    WAR_FEE = 49
    ALLIANCE_MAINTAINANCE_FEE = 50
    CONTRABAND_FINE = 51
    CLONE_TRANSFER = 52
    ACCELERATION_GATE_FEE = 53
    TRANSACTION_TAX = 54
    JUMP_CLONE_INSTALLATION_FEE = 55
    MANUFACTURING = 56
    RESEARCHING_TECHNOLOGY = 57
    RESEARCHING_TIME_PRODUCTIVITY = 58
    RESEARCHING_MATERIAL_PRODUCTIVITY = 59
    COPYING = 60
    REVERSE_ENGINEERING = 62
    CONTRACT_AUCTION_BID = 63
    CONTRACT_AUCTION_BID_REFUND = 64
    CONTRACT_COLLATERAL = 65
    CONTRACT_REWARD_REFUND = 66
    CONTRACT_AUCTION_SOLD = 67
    CONTRACT_REWARD = 68
    CONTRACT_COLLATERAL_REFUND = 69
    CONTRACT_COLLATERAL_PAYOUT = 70
    CONTRACT_PRICE = 71
    CONTRACT_BROKERS_FEE = 72
    CONTRACT_SALES_TAX = 73
    CONTRACT_DEPOSIT = 74
    CONTRACT_DEPOSIT_SALES_TAX = 75
    CONTRACT_AUCTION_BID_CORP = 77
    CONTRACT_COLLATERAL_DEPOSITED_CORP = 78
    CONTRACT_PRICE_PAYMENT_CORP = 79
    CONTRACT_BROKERS_FEE_CORP = 80
    CONTRACT_DEPOSIT_CORP = 81
    CONTRACT_DEPOSIT_REFUND = 82
    CONTRACT_REWARD_DEPOSITED = 83
    CONTRACT_REWARD_DEPOSITED_CORP = 84
    BOUNTY_PRIZES = 85
    ADVERTISEMENT_LISTING_FEE = 86
    MEDAL_CREATION = 87
    MEDAL_ISSUED = 88
    DNA_MODIFICATION_FEE = 90
    SOVEREIGNITY_BILL = 91
    BOUNTY_PRIZE_CORPORATION_TAX = 92
    AGENT_MISSION_REWARD_CORPORATION_TAX = 93
    AGENT_MISSION_TIME_BONUS_REWARD_CORPORATION_TAX = 94
    UPKEEP_ADJUSTMENT_FEE = 95
    PLANETARY_IMPORT_TAX = 96
    PLANETARY_EXPORT_TAX = 97
    PLANETARY_CONSTRUCTION = 98
    CORPORATE_REWARD_PAYOUT = 99
    BOUNTY_SURCHARGE = 101
    CONTRACT_REVERSAL = 102
    CORPORATE_REWARD_TAX = 103
    STORE_PURCHASE = 106
    STORE_PURCHASE_REFUND = 107
    DATACORE_FEE = 112
    WAR_FEE_SURRENDER = 113
    WAR_ALLY_CONTRACT = 114
    BOUNTY_REIMBURSEMENT = 115
    KILL_RIGHT_FEE = 116
    SECURITY_PROCESSING_FEE = 117
    INDUSTRY_JOB_TAX = 120
    INFRASTRUCTURE_HUB_MAINTENANCE = 122
    ASSET_SAFETY_RECOVERY_TAX = 123
    OPPORTUNITY_REWARD = 124
    PROJECT_DISCOVERY_REWARD = 125
    PROJECT_DISCOVERY_TAX = 126
    REPROCESSING_TAX = 127
    JUMP_CLONE_ACTIVATION_FEE = 128
    OPERATION_BONUS = 129
    RESOURCE_WARS_REWARD = 131
    DUEL_WAGER_ESCROW = 132
    DUEL_WAGER_PAYMENT = 133
    DUEL_WAGER_REFUND = 134
    REACTION = 135

    # V3 additions
    STRUCTURE_GATE_JUMP = 140

    # V4 additions
    EXTERNAL_TRADE_FREEZE = 136
    EXTERNAL_TRADE_THAW = 137
    EXTERNAL_TRADE_DELIVERY = 138
    SEASON_CHALLENGE_REWARD = 139
    SKILL_PURCHASE = 141
    ITEM_TRADER_PAYMENT = 142
    FLUX_TICKET_SALE = 143
    FLUX_PAYOUT = 144
    FLUX_TAX = 145
    FLUX_TICKET_REPAYMENT = 146
    REDEEMED_ISK_TOKEN = 147
    DAILY_CHALLENGE_REWARD = 148
    MARKET_PROVIDER_TAX = 149
    ESS_ESCROW_TRANSFER = 155
    MILESTONE_REWARD_PAYMENT = 156
    UNDER_CONSTRUCTION = 166
    ALLIGNMENT_BASED_GATE_TOLL = 168
    PROJECT_PAYOUTS = 170
    INSURGENCY_CORRUPTION_CONTRIBUTION_REWARD = 172
    INSURGENCY_SUPPRESSION_CONTRIBUTION_REWARD = 173
    DAILY_GOAL_PAYOUTS = 174
    DAILY_GOAL_PAYOUTS_TAX = 175
    COSMETIC_MARKET_COMPONENT_ITEM_PURCHASE = 178
    COSMETIC_MARKET_SKIN_SALE_BROKER_FEE = 179
    COSMETIC_MARKET_SKIN_PURCHASE = 180
    COSMETIC_MARKET_SKIN_SALE = 181
    COSMETIC_MARKET_SKIN_SALE_TAX = 182
    COSMETIC_MARKET_SKIN_TRANSACTION = 183
    SKYHOOK_CLAIM_FEE = 184
    AIR_CAREER_PROGRAM_REWARD = 185
    FREELANCE_JOBS_DURATION_FEE = 186
    FREELANCE_JOBS_BROADCASTING_FEE = 187
    FREELANCE_JOBS_REWARD_ESCROW = 188
    FREELANCE_JOBS_REWARD = 189
    FREELANCE_JOBS_ESCROW_REFUND = 190
    FREELANCE_JOBS_REWARD_CORPORATION_TAX = 191
    GM_PLEX_FEE_REFUND = 192


class RefTypeCategories:
    """Categories for wallet journal reference types."""

    # PVE Income
    BOUNTY_PRIZES = [
        JournalRefType.BOUNTY.name.lower(),
        JournalRefType.BOUNTY_PRIZE.name.lower(),
        JournalRefType.BOUNTY_PRIZES.name.lower(),
        JournalRefType.BOUNTY_REIMBURSEMENT.name.lower(),
        JournalRefType.BOUNTY_SURCHARGE.name.lower(),
    ]

    MISSION_REWARD = [
        JournalRefType.MISSION_REWARD.name.lower(),
        JournalRefType.MISSION_COMPLETION.name.lower(),
        JournalRefType.AGENT_MISSION_REWARD.name.lower(),
        JournalRefType.AGENT_MISSION_TIME_BONUS_REWARD.name.lower(),
        JournalRefType.AGENTS_PREWARD.name.lower(),
    ]

    ESS_TRANSFER = [
        JournalRefType.ESS_ESCROW_TRANSFER.name.lower(),
    ]

    INCURSION = [
        JournalRefType.RESOURCE_WARS_REWARD.name.lower(),
        JournalRefType.INSURGENCY_CORRUPTION_CONTRIBUTION_REWARD.name.lower(),
        JournalRefType.INSURGENCY_SUPPRESSION_CONTRIBUTION_REWARD.name.lower(),
        JournalRefType.CORPORATE_REWARD_PAYOUT.name.lower(),
    ]

    DAILY_GOAL_REWARD = [
        JournalRefType.DAILY_GOAL_PAYOUTS.name.lower(),
        JournalRefType.DAILY_CHALLENGE_REWARD.name.lower(),
        JournalRefType.SEASON_CHALLENGE_REWARD.name.lower(),
        JournalRefType.OPPORTUNITY_REWARD.name.lower(),
        JournalRefType.AIR_CAREER_PROGRAM_REWARD.name.lower(),
    ]

    # Trading Income
    MARKET = [
        JournalRefType.MARKET_TRANSACTION.name.lower(),
        JournalRefType.MARKET_ESCROW.name.lower(),
        JournalRefType.BROKERS_FEE.name.lower(),
        JournalRefType.TRANSACTION_TAX.name.lower(),
        JournalRefType.MARKET_FINE_PAID.name.lower(),
        JournalRefType.MARKET_PROVIDER_TAX.name.lower(),
    ]

    CONTRACT = [
        JournalRefType.CONTRACT_AUCTION_BID.name.lower(),
        JournalRefType.CONTRACT_AUCTION_BID_REFUND.name.lower(),
        JournalRefType.CONTRACT_COLLATERAL.name.lower(),
        JournalRefType.CONTRACT_REWARD_REFUND.name.lower(),
        JournalRefType.CONTRACT_AUCTION_SOLD.name.lower(),
        JournalRefType.CONTRACT_REWARD.name.lower(),
        JournalRefType.CONTRACT_COLLATERAL_REFUND.name.lower(),
        JournalRefType.CONTRACT_COLLATERAL_PAYOUT.name.lower(),
        JournalRefType.CONTRACT_PRICE.name.lower(),
        JournalRefType.CONTRACT_BROKERS_FEE.name.lower(),
        JournalRefType.CONTRACT_SALES_TAX.name.lower(),
        JournalRefType.CONTRACT_DEPOSIT.name.lower(),
        JournalRefType.CONTRACT_DEPOSIT_SALES_TAX.name.lower(),
        JournalRefType.CONTRACT_AUCTION_BID_CORP.name.lower(),
        JournalRefType.CONTRACT_COLLATERAL_DEPOSITED_CORP.name.lower(),
        JournalRefType.CONTRACT_PRICE_PAYMENT_CORP.name.lower(),
        JournalRefType.CONTRACT_BROKERS_FEE_CORP.name.lower(),
        JournalRefType.CONTRACT_DEPOSIT_CORP.name.lower(),
        JournalRefType.CONTRACT_DEPOSIT_REFUND.name.lower(),
        JournalRefType.CONTRACT_REWARD_DEPOSITED.name.lower(),
        JournalRefType.CONTRACT_REWARD_DEPOSITED_CORP.name.lower(),
        JournalRefType.CONTRACT_REVERSAL.name.lower(),
    ]

    CORPORATION_CONTRACT = [
        JournalRefType.CONTRACT_PRICE_PAYMENT_CORP.name.lower(),
    ]

    CORPORATION = [
        JournalRefType.CORPORATION_DIVIDEND_PAYMENT.name.lower(),
        JournalRefType.CORPORATION_REGISTRATION_FEE.name.lower(),
        JournalRefType.CORPORATION_LOGO_CHANGE_COST.name.lower(),
        JournalRefType.CORPORATION_BULK_PAYMENT.name.lower(),
    ]

    DONATION = [
        JournalRefType.CORPORATION_ACCOUNT_WITHDRAWAL.name.lower(),
        JournalRefType.PLAYER_DONATION.name.lower(),
        JournalRefType.AGENT_DONATION.name.lower(),
    ]

    INSURANCE = [
        JournalRefType.INSURANCE.name.lower(),
    ]

    MILESTONE_REWARD = [
        JournalRefType.MILESTONE_REWARD_PAYMENT.name.lower(),
        JournalRefType.PROJECT_DISCOVERY_REWARD.name.lower(),
        JournalRefType.PROJECT_PAYOUTS.name.lower(),
    ]

    # Production/Industry
    PRODUCTION = [
        JournalRefType.MANUFACTURING.name.lower(),
        JournalRefType.RESEARCHING_TECHNOLOGY.name.lower(),
        JournalRefType.RESEARCHING_TIME_PRODUCTIVITY.name.lower(),
        JournalRefType.RESEARCHING_MATERIAL_PRODUCTIVITY.name.lower(),
        JournalRefType.COPYING.name.lower(),
        JournalRefType.REVERSE_ENGINEERING.name.lower(),
        JournalRefType.INDUSTRY_JOB_TAX.name.lower(),
        JournalRefType.REACTION.name.lower(),
    ]

    # Planetary
    PLANETARY = [
        JournalRefType.PLANETARY_IMPORT_TAX.name.lower(),
        JournalRefType.PLANETARY_EXPORT_TAX.name.lower(),
        JournalRefType.PLANETARY_CONSTRUCTION.name.lower(),
    ]

    RENTAL = [
        JournalRefType.OFFICE_RENTAL_FEE.name.lower(),
        JournalRefType.FACTORY_SLOT_RENTAL_FEE.name.lower(),
        JournalRefType.SOVEREIGNITY_BILL.name.lower(),
        JournalRefType.INFRASTRUCTURE_HUB_MAINTENANCE.name.lower(),
    ]

    # Assets/Items
    ASSETS = [
        JournalRefType.REPAIR_BILL.name.lower(),
        JournalRefType.ASSET_SAFETY_RECOVERY_TAX.name.lower(),
        JournalRefType.REPROCESSING_TAX.name.lower(),
        JournalRefType.ITEM_TRADER_PAYMENT.name.lower(),
    ]

    # Traveling/Movement
    TRAVELING = [
        JournalRefType.DOCKING_FEE.name.lower(),
        JournalRefType.ACCELERATION_GATE_FEE.name.lower(),
        JournalRefType.JUMP_CLONE_INSTALLATION_FEE.name.lower(),
        JournalRefType.JUMP_CLONE_ACTIVATION_FEE.name.lower(),
        JournalRefType.CLONE_ACTIVATION.name.lower(),
        JournalRefType.CLONE_TRANSFER.name.lower(),
        JournalRefType.STRUCTURE_GATE_JUMP.name.lower(),
        JournalRefType.ALLIGNMENT_BASED_GATE_TOLL.name.lower(),
    ]

    # Propaganda/Information
    INFORMATION = [
        JournalRefType.ADVERTISEMENT_LISTING_FEE.name.lower(),
    ]

    # Skills/Learning
    SKILL = [
        JournalRefType.SKILL_PURCHASE.name.lower(),
        JournalRefType.DATACORE_FEE.name.lower(),
    ]

    # LP Store
    LP = [
        JournalRefType.LP_STORE.name.lower(),
    ]

    @classmethod
    def get_category_values(cls, category_name: str) -> list[str]:
        """Get all ref type values for a category."""
        return getattr(cls, category_name, [])

    @classmethod
    def get_all_categories(cls) -> dict[str, list[str]]:
        """Get all categories and their ref types."""
        return {
            "ASSETS": cls.ASSETS,
            "BOUNTY_PRIZES": cls.BOUNTY_PRIZES,
            "MISSION_REWARD": cls.MISSION_REWARD,
            "ESS_TRANSFER": cls.ESS_TRANSFER,
            "CORPORATION": cls.CORPORATION,
            "INCURSION": cls.INCURSION,
            "DAILY_GOAL_REWARD": cls.DAILY_GOAL_REWARD,
            "MARKET": cls.MARKET,
            "CONTRACT": cls.CONTRACT,
            "DONATION": cls.DONATION,
            "INSURANCE": cls.INSURANCE,
            "MILESTONE_REWARD": cls.MILESTONE_REWARD,
            "PRODUCTION": cls.PRODUCTION,
            "PLANETARY": cls.PLANETARY,
            "TRAVELING": cls.TRAVELING,
            "SKILL": cls.SKILL,
            "LP": cls.LP,
        }

    @classmethod
    def get_costs(cls) -> dict[str, list[str]]:
        """Get all cost categories and their ref types."""
        return {
            "ASSETS": cls.ASSETS,
            "CONTRACT": cls.CONTRACT,
            "CORPORATION": cls.CORPORATION,
            "DAILY_GOAL_REWARD": cls.DAILY_GOAL_REWARD,
            "DONATION": cls.DONATION,
            "INCURSION": cls.INCURSION,
            "INSURANCE": cls.INSURANCE,
            "LP": cls.LP,
            "MISSION_REWARD": cls.MISSION_REWARD,
            "MARKET": cls.MARKET,
            "PRODUCTION": cls.PRODUCTION,
            "PLANETARY": cls.PLANETARY,
            "RENTAL": cls.RENTAL,
            "INFORMATION": cls.INFORMATION,
            "SKILL": cls.SKILL,
            "TRAVELING": cls.TRAVELING,
        }

    @classmethod
    def get_costs_corporation(cls) -> dict[str, list[str]]:
        """Get all cost categories and their ref types."""
        return {
            "CONTRACT": cls.CORPORATION_CONTRACT,
        }

    @classmethod
    def get_miscellaneous(cls) -> dict[str, list[str]]:
        """Get all miscellaneous categories and their ref types."""
        return {
            "ASSETS": cls.ASSETS,
            "CONTRACT": cls.CONTRACT,
            "CORPORATION": cls.CORPORATION,
            "DAILY_GOAL_REWARD": cls.DAILY_GOAL_REWARD,
            "DONATION": cls.DONATION,
            "INCURSION": cls.INCURSION,
            "INSURANCE": cls.INSURANCE,
            "LP": cls.LP,
            "MISSION_REWARD": cls.MISSION_REWARD,
            "MARKET": cls.MARKET,
            "PRODUCTION": cls.PRODUCTION,
            "PLANETARY": cls.PLANETARY,
            "RENTAL": cls.RENTAL,
            "SKILL": cls.SKILL,
            "TRAVELING": cls.TRAVELING,
        }

    @classmethod
    def get_miscellaneous_corporation(cls) -> dict[str, list[str]]:
        """Get all miscellaneous categories and their ref types for corporations."""
        return {
            "DAILY_GOAL_REWARD": cls.DAILY_GOAL_REWARD,
        }

    @classmethod
    def costs(cls) -> list[str]:
        """Get all cost categories and their ref types."""
        costs_ref_types = cls.get_costs()
        costs = []
        for __, ref_types in costs_ref_types.items():
            costs.extend(ref_types)
        return costs

    @classmethod
    def costs_corporation(cls) -> list[str]:
        """Get all cost categories and their ref types for corporations."""
        costs_ref_types = cls.get_costs_corporation()
        costs = []
        for __, ref_types in costs_ref_types.items():
            costs.extend(ref_types)
        return costs

    @classmethod
    def miscellaneous(cls) -> list[str]:
        """Get all miscellaneous categories and their ref types."""
        misc_ref_types = cls.get_miscellaneous()
        miscellaneous = []
        for __, ref_types in misc_ref_types.items():
            miscellaneous.extend(ref_types)
        return miscellaneous

    @classmethod
    def miscellaneous_corporation(cls) -> list[str]:
        """Get all miscellaneous categories and their ref types for corporations."""
        misc_ref_types = cls.get_miscellaneous_corporation()
        miscellaneous = []
        for __, ref_types in misc_ref_types.items():
            miscellaneous.extend(ref_types)
        return miscellaneous
