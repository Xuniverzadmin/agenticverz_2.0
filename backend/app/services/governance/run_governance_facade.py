# Layer: L4 — Domain Engine (DELEGATING SHIM)
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Delegating shim to hoc_spine run governance facade — ITER3.4 consolidation
# Reference: ITER3.4 (Consolidate System Runtime to hoc_spine)
#
# ================================================================================
# ITER3.4 SHIM NOTE:
# This module is a thin delegating shim. All logic lives in hoc_spine.
# Worker and other callers continue using this import path for backward compat.
#
# CANONICAL LOCATION: app.hoc.cus.hoc_spine.orchestrator.run_governance_facade
# ================================================================================

"""
Run Governance Facade (Delegating Shim)

This module delegates to the canonical implementation in hoc_spine.
All classes, types, and functions are re-exported from:

    app.hoc.cus.hoc_spine.orchestrator.run_governance_facade

Usage (unchanged):

    from app.services.governance.run_governance_facade import get_run_governance_facade

    facade = get_run_governance_facade()
    policy_id = facade.create_policy_evaluation(
        run_id=run_id,
        tenant_id=tenant_id,
        run_status="succeeded",
    )

See: docs/memory-pins/TODO_ITER3.4.md
"""

# Re-export everything from the canonical hoc_spine implementation
from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
    # Feature flags
    RAC_ENABLED,
    # Main class
    RunGovernanceFacade,
    # Factory function
    get_run_governance_facade,
)

# Explicit __all__ for documentation
__all__ = [
    "RAC_ENABLED",
    "RunGovernanceFacade",
    "get_run_governance_facade",
]
