"""
Constants
"""

# Embed colors
DISCORD_EMBED_COLOR_INFO = 0x5BC0DE
DISCORD_EMBED_COLOR_SUCCESS = 0x5CB85C
DISCORD_EMBED_COLOR_WARNING = 0xF0AD4E
DISCORD_EMBED_COLOR_DANGER = 0xD9534F

# Discord embed color map
DISCORD_EMBED_COLOR_MAP = {
    "info": DISCORD_EMBED_COLOR_INFO,
    "success": DISCORD_EMBED_COLOR_SUCCESS,
    "warning": DISCORD_EMBED_COLOR_WARNING,
    "danger": DISCORD_EMBED_COLOR_DANGER,
}

NPC_ENTITIES = [
    1000125,  # Concord Bounties (Bounty Prizes, ESS
    1000132,  # Secure Commerce Commission (Market Fees)
    1000413,  # Air Laboratories (Daily Login Rewards, etc.)
]

BOUNTY_PRIZES = ["bounty_prizes"]
ESS_TRANSFER = ["ess_escrow_transfer"]
MISSION_REWARD = ["agent_mission_reward", "agent_mission_time_bonus_reward"]
INCURSION = ["corporate_reward_payout"]

# Cost Ref Types
CONTRACT = [
    "contract_price",
    "contract_collateral",
    "contract_reward_deposited",
    "contract_brokers_fee",
    "contract_sales_tax",
    "contract_price_payment_corp",
    "contract_reward",
    "contract_reward_refund",
    "contract_collateral_refund",
    "contract_deposit_refund",
]
MARKET = [
    "market_escrow",
    "transaction_tax",
    "market_provider_tax",
    "brokers_fee",
    "market_transaction",
]
ASSETS = ["asset_safety_recovery_tax"]
TRAVELING = [
    "structure_gate_jump",
    "jump_clone_activation_fee",
    "jump_clone_installation_fee",
]
PRODUCTION = [
    "industry_job_tax",
    "manufacturing",
    "researching_time_productivity",
    "researching_material_productivity",
    "copying",
    "reprocessing_tax",
    "reaction",
]
SKILL = ["skill_purchase"]
PLANETARY = [
    "planetary_export_tax",
    "planetary_import_tax",
    "planetary_construction",
]
LP = ["lp_store"]
# Trading
DONATION = ["player_donation"]
INSURANCE = ["insurance"]
# MISC
MILESTONE_REWARD = ["milestone_reward_payment"]
DAILY_GOAL_REWARD = ["daily_goal_payouts"]

RENTAL = ["office_rental_fee"]
CORP_WITHDRAW = ["corporation_account_withdrawal"]
