# Layer: L6 — Drivers
# AUDIENCE: CUSTOMER
# Role: Database operations for control persistence, limit storage, audit trail

# PIN-520 Phase 1: Alias scoped_execution for backwards compatibility
# recovery.py imports from scoped_execution (without _driver suffix)
from app.hoc.cus.controls.L6_drivers.scoped_execution_driver import (
    BoundExecutionScope,
    ExecutionScope,
    RiskClass,
    ScopedExecutionContext,
    ScopedExecutionRequired,
    ScopedExecutionResult,
    ScopeActionMismatch,
    ScopeExhausted,
    ScopeExpired,
    ScopeIncidentMismatch,
    ScopeNotFound,
    ScopeStore,
    get_scope_store,
    requires_scoped_execution,
)

# Backwards compatibility: expose as scoped_execution submodule
# Allows: from app.hoc.cus.controls.L6_drivers.scoped_execution import ...
import sys
from app.hoc.cus.controls.L6_drivers import scoped_execution_driver as scoped_execution
sys.modules["app.hoc.cus.controls.L6_drivers.scoped_execution"] = scoped_execution

__all__ = [
    # scoped_execution exports
    "BoundExecutionScope",
    "ExecutionScope",
    "RiskClass",
    "ScopedExecutionContext",
    "ScopedExecutionRequired",
    "ScopedExecutionResult",
    "ScopeActionMismatch",
    "ScopeExhausted",
    "ScopeExpired",
    "ScopeIncidentMismatch",
    "ScopeNotFound",
    "ScopeStore",
    "get_scope_store",
    "requires_scoped_execution",
    "scoped_execution",
]
