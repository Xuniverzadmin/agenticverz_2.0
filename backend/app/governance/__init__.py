# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | cli | worker | sdk | auto_execute
#   Execution: sync
# Role: Governance enforcement infrastructure (structural, non-coercive)
# Callers: All EXECUTE-power paths
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2
# Reference: PIN-337

"""
PIN-337: Governance Enforcement Infrastructure

This module provides the MANDATORY execution kernel that all EXECUTE-power
paths must route through. This is STRUCTURAL governance - making ungoverned
execution physically impossible.

CONSTRAINTS (v1):
- Kernel MUST NOT block execution
- Kernel MUST NOT change business semantics
- Kernel MUST emit envelopes and record invocations
- Strictness is capability-scoped, not global
- v1 behavior is fully PERMISSIVE

The kernel is PHYSICS, not POLICY.
"""

from app.governance.kernel import (
    ExecutionKernel,
    InvocationContext,
    ExecutionResult,
    EnforcementMode,
    get_enforcement_mode,
)
from app.governance.decorator import governed

__all__ = [
    "ExecutionKernel",
    "InvocationContext",
    "ExecutionResult",
    "EnforcementMode",
    "get_enforcement_mode",
    "governed",
]
