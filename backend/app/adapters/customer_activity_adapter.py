# Layer: L3 — Boundary Adapter (Compatibility)
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Compatibility shim to canonical HOC adapter
# Callers: legacy import path `app.adapters.customer_activity_adapter`
# Allowed Imports: HOC canonical adapter only
# Forbidden Imports: legacy `app.services.*`
#
# First-principles note:
# Canonical implementation lives in:
#   app.hoc.cus.activity.adapters.customer_activity_adapter
# This module exists to prevent “two systems” drift while keeping the
# historical import path functional.

"""
Customer Activity Adapter (Compatibility Shim)

This module intentionally re-exports the canonical HOC adapter surface.

Canonical:
  `app.hoc.cus.activity.adapters.customer_activity_adapter`
"""

from app.hoc.cus.activity.adapters.customer_activity_adapter import (  # noqa: F401
    CustomerActivityAdapter,
    CustomerActivityDetail,
    CustomerActivityListResponse,
    CustomerActivitySummary,
    get_customer_activity_adapter,
)

__all__ = [
    "CustomerActivityAdapter",
    "CustomerActivitySummary",
    "CustomerActivityDetail",
    "CustomerActivityListResponse",
    "get_customer_activity_adapter",
]

