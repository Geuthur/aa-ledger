# AA Ledger
from ledger.models.general import General
from ledger.tests.testdata.factory import UserMainFactory


def create_manage_own_user():
    """User with manage own corporation access (basic, advanced, corp audit manager, manage access)."""
    return UserMainFactory(
        permissions__=[
            General.get_perm(General.Permission.BASIC_ACCESS),
            General.get_perm(General.Permission.ADVANCED_ACCESS),
            General.get_perm(General.Permission.CORP_AUDIT_MANAGER),
            General.get_perm(General.Permission.MANAGE_ACCESS),
        ]
    )


def create_manage_user():
    """User with manage corporations access (basic, advanced, corp audit admin manager, manage access)."""
    return UserMainFactory(
        permissions__=[
            General.get_perm(General.Permission.BASIC_ACCESS),
            General.get_perm(General.Permission.ADVANCED_ACCESS),
            General.get_perm(General.Permission.CORP_AUDIT_ADMIN_MANAGER),
            General.get_perm(General.Permission.MANAGE_ACCESS),
        ]
    )
