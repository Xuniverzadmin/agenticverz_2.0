# Layer: L5 — Execution & Workers
# Product: system-wide
# Role: Step-level enforcement for governance

"""
Enforcement Package

Contains step-level enforcement guarantees:
- step_enforcement: Same-step enforcement (GAP-016)
- enforcement_guard: Step-level guarantee (GAP-030)
"""

from app.hoc.int.worker.enforcement.step_enforcement import (
    enforce_before_step_completion,
    StepEnforcementError,
    EnforcementResult,
    EnforcementHaltReason,
)
from app.hoc.int.worker.enforcement.enforcement_guard import (
    enforcement_guard,
    EnforcementSkippedError,
    EnforcementCheckpoint,
    require_enforcement,
)

__all__ = [
    # GAP-016: Same-step enforcement
    "enforce_before_step_completion",
    "StepEnforcementError",
    "EnforcementResult",
    "EnforcementHaltReason",
    # GAP-030: Enforcement guard
    "enforcement_guard",
    "EnforcementSkippedError",
    "EnforcementCheckpoint",
    "require_enforcement",
]
