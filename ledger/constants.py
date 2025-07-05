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

COMMAND_CENTER = [
    2129,
    2130,
    2131,
    2132,
    2136,
    2137,
    2138,
    2139,
    2140,
    2141,
    2142,
    2143,
    2144,
    2145,
    2146,
    2147,
    2148,
    2149,
    2150,
    2151,
    2152,
    2153,
    2154,
    2155,
    2156,
    2157,
    2158,
    2159,
    2160,
    2254,
    2524,
    2525,
    2533,
    2534,
    2549,
    2550,
    2551,
    2574,
    2576,
    2577,
    2568,
    2581,
    2582,
    2585,
    2586,
]
SPACEPORTS = [2256, 2542, 2543, 2544, 2552, 2555, 2556, 2557]
STORAGE_FACILITY = [2257, 2535, 2536, 2541, 2558, 2560, 2561, 2562]
EXTRACTOR_CONTROL_UNIT = [2848, 3060, 3061, 3062, 3063, 3064, 3067, 3068]
P0_PRODUCTS_SOLID = [2267, 2270, 2272, 2306, 2307]
P0_PRODUCTS_LIQUID_GAS = [2268, 2308, 2309, 2310, 2311]
P0_PRODUCTS_ORGANIC = [2073, 2286, 2287, 2288, 2305]
P0_PRODUCTS = P0_PRODUCTS_SOLID + P0_PRODUCTS_LIQUID_GAS + P0_PRODUCTS_ORGANIC
P1_PRODUCTS = [
    2389,
    2390,
    2392,
    2393,
    2395,
    2396,
    2397,
    2398,
    2399,
    2400,
    2401,
    3645,
    3683,
    3779,
    9828,
]
P2_PRODUCTS = [
    44,
    2312,
    2317,
    2319,
    2321,
    2327,
    2328,
    2329,
    2463,
    3689,
    3691,
    3693,
    3695,
    3697,
    3725,
    3775,
    3828,
    983,
    9832,
    9836,
    9838,
    9840,
    9842,
    15317,
]
P3_PRODUCTS = [
    2344,
    2345,
    2346,
    2348,
    2349,
    2351,
    2352,
    2354,
    2358,
    2360,
    2361,
    2366,
    2367,
    9834,
    9846,
    9848,
    12836,
    17136,
    17392,
    17898,
    28974,
]
P4_PRODUCTS = [2867, 2868, 2869, 2870, 2871, 2872, 2875, 2876]
P5_PRODUCTS = []


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
INSURANCE = ["insurance"]
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
