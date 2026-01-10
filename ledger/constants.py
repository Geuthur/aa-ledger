"""
Constants
"""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

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


class MonthChoice(models.TextChoices):
    JANUARY = 1, _("January")
    FEBRUARY = 2, _("February")
    MARCH = 3, _("March")
    APRIL = 4, _("April")
    MAY = 5, _("May")
    JUNE = 6, _("June")
    JULY = 7, _("July")
    AUGUST = 8, _("August")
    SEPTEMBER = 9, _("September")
    OCTOBER = 10, _("October")
    NOVEMBER = 11, _("November")
    DECEMBER = 12, _("December")


class DayChoice(models.TextChoices):
    DAY_1 = 1, _("1")
    DAY_2 = 2, _("2")
    DAY_3 = 3, _("3")
    DAY_4 = 4, _("4")
    DAY_5 = 5, _("5")
    DAY_6 = 6, _("6")
    DAY_7 = 7, _("7")
    DAY_8 = 8, _("8")
    DAY_9 = 9, _("9")
    DAY_10 = 10, _("10")
    DAY_11 = 11, _("11")
    DAY_12 = 12, _("12")
    DAY_13 = 13, _("13")
    DAY_14 = 14, _("14")
    DAY_15 = 15, _("15")
    DAY_16 = 16, _("16")
    DAY_17 = 17, _("17")
    DAY_18 = 18, _("18")
    DAY_19 = 19, _("19")
    DAY_20 = 20, _("20")
    DAY_21 = 21, _("21")
    DAY_22 = 22, _("22")
    DAY_23 = 23, _("23")
    DAY_24 = 24, _("24")
    DAY_25 = 25, _("25")
    DAY_26 = 26, _("26")
    DAY_27 = 27, _("27")
    DAY_28 = 28, _("28")
    DAY_29 = 29, _("29")
    DAY_30 = 30, _("30")
    DAY_31 = 31, _("31")
