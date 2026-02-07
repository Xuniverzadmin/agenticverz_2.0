# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Cost write service facade — delegates to L6 cost_write_driver
# Callers: L2 APIs (cost_intelligence.py)
# Allowed Imports: L6 drivers
# Forbidden Imports: L1, L2
# Reference: PIN-520 Phase 1 (L4 Uniformity Initiative)
# artifact_class: CODE

"""
Cost Write Engine (L5)

Thin L5 facade over the L6 CostWriteDriver. Provides backwards-compatible
CostWriteService class that cost_intelligence.py expects.

PIN-520 Phase 1: This file enables the migration path for cost_intelligence.py
to eventually route through L4 registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

# Re-export CostWriteDriver as CostWriteService for backwards compatibility
from app.hoc.cus.analytics.L6_drivers.cost_write_driver import (
    CostWriteDriver as CostWriteService,
    get_cost_write_driver,
)


def get_cost_write_service(session: Session) -> CostWriteService:
    """Get cost write service instance.

    Backwards-compatible accessor that delegates to L6 driver.
    """
    return get_cost_write_driver(session)


__all__ = [
    "CostWriteService",
    "get_cost_write_service",
]
