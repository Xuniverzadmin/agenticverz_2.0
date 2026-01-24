# Layer: L4 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: account domain - engines
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
account / engines

CUSTOMER-facing account engines.

NOTE: iam_service.py was moved to internal/platform/iam/engines/
because it declares AUDIENCE: INTERNAL.

For INTERNAL IAM operations, use:
    from app.hoc.int.platform.iam.engines import get_iam_service

For CUSTOMER account operations, use the facades:
    from app.hoc.cus.account.facades import get_accounts_facade
"""

from app.hoc.cus.account.engines.email_verification import (
    EmailVerificationService,
    EmailVerificationError,
    VerificationResult,
    get_email_verification_service,
)
from app.hoc.cus.account.engines.tenant_engine import (
    TenantEngine,
    TenantEngineError,
    QuotaExceededError,
    get_tenant_engine,
)
from app.hoc.cus.account.engines.user_write_engine import (
    UserWriteService,
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
]
