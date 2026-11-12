# AA Ledger
from ledger.tests.testdata.factory import UserMainFactory


def create_manage_own_user():
    """User with manage own corporation access (basic, advanced, corp audit manager, manage access)."""
    return UserMainFactory(
        permissions__=[
            "ledger.basic_access",
            "ledger.advanced_access",
            "ledger.corp_audit_manager",
            "ledger.manage_access",
        ]
    )


def create_manage_user():
    """User with manage corporations access (basic, advanced, corp audit admin manager, manage access)."""
    return UserMainFactory(
        permissions__=[
            "ledger.basic_access",
            "ledger.advanced_access",
            "ledger.corp_audit_admin_manager",
            "ledger.manage_access",
        ]
    )
