# Layer: L4 — Domain Engine (DELEGATING SHIM)
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Delegating shim to hoc_spine transaction coordinator — ITER3.4 consolidation
# Reference: ITER3.4 (Consolidate System Runtime to hoc_spine)
#
# ================================================================================
# ITER3.4 SHIM NOTE:
# This module is a thin delegating shim. All logic lives in hoc_spine.
# Worker and other callers continue using this import path for backward compat.
#
# CANONICAL LOCATION: app.hoc.cus.hoc_spine.drivers.transaction_coordinator
# ================================================================================

"""
Transaction Coordinator (Delegating Shim)

This module delegates to the canonical implementation in hoc_spine.
All classes, types, and functions are re-exported from:

    app.hoc.cus.hoc_spine.drivers.transaction_coordinator

Usage (unchanged):

    from app.services.governance.transaction_coordinator import (
        RunCompletionTransaction,
        get_transaction_coordinator,
        TransactionFailed,
        TRANSACTION_COORDINATOR_ENABLED,
    )

See: docs/memory-pins/TODO_ITER3.4.md
"""

# Re-export everything from the canonical hoc_spine implementation
from app.hoc.cus.hoc_spine.drivers.transaction_coordinator import (
    # Feature flags
    RAC_ROLLBACK_AUDIT_ENABLED,
    TRANSACTION_COORDINATOR_ENABLED,
    # Enums
    TransactionPhase,
    # Exceptions
    TransactionFailed,
    RollbackNotSupportedError,
    # Dataclasses
    DomainResult,
    TransactionResult,
    RollbackAction,
    # Main class
    RunCompletionTransaction,
    # Factory functions
    get_transaction_coordinator,
    create_transaction_coordinator,
)

# Explicit __all__ for documentation
__all__ = [
    # Feature flags
    "RAC_ROLLBACK_AUDIT_ENABLED",
    "TRANSACTION_COORDINATOR_ENABLED",
    # Enums
    "TransactionPhase",
    # Exceptions
    "TransactionFailed",
    "RollbackNotSupportedError",
    # Dataclasses
    "DomainResult",
    "TransactionResult",
    "RollbackAction",
    # Main class
    "RunCompletionTransaction",
    # Factory functions
    "get_transaction_coordinator",
    "create_transaction_coordinator",
]
