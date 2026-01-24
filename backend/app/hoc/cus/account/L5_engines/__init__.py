# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: Account domain engines - business logic composition
# Location: hoc/cus/account/L5_engines/
# Reference: PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md

"""
Account L5 Engines

CUSTOMER-facing account engines.

NOTE: iam_service.py was moved to internal/platform/iam/engines/
because it declares AUDIENCE: INTERNAL.

For INTERNAL IAM operations, use:
    from app.hoc.int.platform.iam.L5_engines import get_iam_service

For CUSTOMER account operations:
    from app.hoc.cus.account.L5_engines import get_accounts_facade
"""

from app.hoc.cus.account.L5_engines.email_verification import (
    EmailVerificationService,
    EmailVerificationError,
    VerificationResult,
    get_email_verification_service,
)
from app.hoc.cus.account.L5_engines.tenant_engine import (
    TenantEngine,
    TenantEngineError,
    QuotaExceededError,
    get_tenant_engine,
)
from app.hoc.cus.account.L5_engines.user_write_engine import (
    UserWriteService,
)
from app.hoc.cus.account.L5_engines.accounts_facade import (
    AccountsFacade,
    get_accounts_facade,
)
from app.hoc.cus.account.L5_engines.notifications_facade import (
    NotificationsFacade,
    get_notifications_facade,
)

__all__ = [
    # email_verification
    "EmailVerificationService",
    "EmailVerificationError",
    "VerificationResult",
    "get_email_verification_service",
    # tenant_engine
    "TenantEngine",
    "TenantEngineError",
    "QuotaExceededError",
    "get_tenant_engine",
    # user_write_engine (class name not yet renamed to UserWriteEngine)
    "UserWriteService",
    # accounts_facade
    "AccountsFacade",
    "get_accounts_facade",
    # notifications_facade
    "NotificationsFacade",
    "get_notifications_facade",
]
