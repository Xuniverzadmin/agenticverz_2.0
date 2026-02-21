# capability_id: CAP-012
# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access drivers for account domain
# Reference: PHASE2_EXTRACTION_PROTOCOL.md, ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
account / drivers

L6 drivers for account data access operations.
All drivers are pure data access - no business logic.
"""

from app.hoc.cus.account.L6_drivers.accounts_facade_driver import (
    AccountsFacadeDriver,
    get_accounts_facade_driver,
)
from app.hoc.cus.account.L6_drivers.tenant_driver import (
    TenantDriver,
    get_tenant_driver,
)
from app.hoc.cus.account.L6_drivers.user_write_driver import (
    UserWriteDriver,
    get_user_write_driver,
)

__all__ = [
    # accounts_facade_driver
    "AccountsFacadeDriver",
    "get_accounts_facade_driver",
    # tenant_driver
    "TenantDriver",
    "get_tenant_driver",
    # user_write_driver
    "UserWriteDriver",
    "get_user_write_driver",
]
