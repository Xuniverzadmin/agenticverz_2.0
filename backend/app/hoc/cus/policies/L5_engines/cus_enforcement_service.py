# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Customer enforcement service - LLM integration policy enforcement
# Temporal:
#   Trigger: api, sdk
#   Execution: sync
# Callers: cus_enforcement.py
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 2, PIN-468

"""
CusEnforcementService (SWEEP-03 Batch 2)

PURPOSE:
    Enforcement policy evaluation for customer LLM integrations.
    Called by cus_enforcement.py API endpoints.

INTERFACE:
    - CusEnforcementService (alias for CusEnforcementEngine)
    - EnforcementResult (enum)
    - EnforcementReason (dataclass)
    - EnforcementDecision (dataclass)
    - get_cus_enforcement_service(session) -> CusEnforcementService

IMPLEMENTATION NOTES:
    Re-exports from existing cus_enforcement_engine.py which is already
    properly structured with L4/L6 separation.
    Future work may fully migrate the implementation to HOC.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Re-export from existing engine
# =============================================================================
# The enforcement engine already has proper L4/L6 separation
# This module provides the HOC import path for callers

from app.services.cus_enforcement_engine import (
    CusEnforcementEngine,
    EnforcementDecision,
    EnforcementReason,
    EnforcementResult,
    get_cus_enforcement_engine,
)

# =============================================================================
# HOC Aliases
# =============================================================================

# Alias for backward compatibility
CusEnforcementService = CusEnforcementEngine


def get_cus_enforcement_service() -> CusEnforcementService:
    """Get the CusEnforcementService instance.

    Returns:
        CusEnforcementService instance

    Note:
        Delegates to get_cus_enforcement_engine() which creates the engine
        with proper L6 driver injection.
    """
    return get_cus_enforcement_engine()


__all__ = [
    "CusEnforcementService",
    "CusEnforcementEngine",
    "EnforcementResult",
    "EnforcementReason",
    "EnforcementDecision",
    "get_cus_enforcement_service",
    "get_cus_enforcement_engine",
]
