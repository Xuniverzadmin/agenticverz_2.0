# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Role: Runtime gate middleware exports
# Reference: PIN-401 Track A (Production Wiring)

"""
Runtime Gate Middleware

Track A production wiring - enforcement of Phase 6-9 at request boundaries.

Gates enforce existing provider decisions without adding new logic:
- Lifecycle Gate: Blocks SDK execution for non-ACTIVE tenants
- Protection Gate: Applies rate limits and abuse protection
- Billing Gate: Enforces plan limits at execution boundaries
"""

from app.api.middleware.lifecycle_gate import (
    LifecycleGate,
    require_active_lifecycle,
    require_sdk_execution,
    require_writes_allowed,
)
from app.api.middleware.protection_gate import (
    ProtectionGate,
    require_protection_allow,
    check_protection,
)
from app.api.middleware.billing_gate import (
    BillingGate,
    require_billing_active,
    check_billing_limit,
)

__all__ = [
    # Lifecycle
    "LifecycleGate",
    "require_active_lifecycle",
    "require_sdk_execution",
    "require_writes_allowed",
    # Protection
    "ProtectionGate",
    "require_protection_allow",
    "check_protection",
    # Billing
    "BillingGate",
    "require_billing_active",
    "check_billing_limit",
]
