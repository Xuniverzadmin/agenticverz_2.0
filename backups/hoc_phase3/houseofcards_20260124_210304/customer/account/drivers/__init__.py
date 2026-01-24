# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access drivers for account domain
# Reference: PHASE2_EXTRACTION_PROTOCOL.md, ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
account / drivers

L6 drivers for account data access operations.
All drivers are pure data access - no business logic.
"""

from app.houseofcards.customer.account.drivers.accounts_facade_driver import (
    AccountsFacadeDriver,
    get_accounts_facade_driver,
)
from app.houseofcards.customer.account.drivers.tenant_driver import (
    TenantDriver,
    get_tenant_driver,
)
from app.houseofcards.customer.account.drivers.user_write_driver import (
    UserWriteDriver,
    get_user_write_driver,
)
from app.houseofcards.customer.account.drivers.worker_registry_driver import (
    WorkerRegistryService,
    WorkerRegistryError,
    WorkerNotFoundError,
    WorkerUnavailableError,
    get_worker_registry_service,
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
    # worker_registry_driver
    "WorkerRegistryService",
    "WorkerRegistryError",
    "WorkerNotFoundError",
    "WorkerUnavailableError",
    "get_worker_registry_service",
]
