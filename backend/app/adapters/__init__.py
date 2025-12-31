# Layer: L3 — Boundary Adapters
# Product: system-wide
# Role: Package for L3 boundary adapters
# Reference: PIN-258 Phase F

"""
L3 Boundary Adapters Package

This package contains L3 boundary adapters that translate between:
- L2 (API routes) - request handlers
- L4 (Domain commands) - domain decisions

Adapters must:
- Only import from L4 and L6
- Never import from L1, L2, or L5
- Translate requests, not make domain decisions
- Be thin (<200 LOC typically)
"""

from app.adapters.policy_adapter import (
    PolicyAdapter,
    PolicyEvaluationResult,
    PolicyViolation,
    get_policy_adapter,
)
from app.adapters.runtime_adapter import RuntimeAdapter, get_runtime_adapter
from app.adapters.workers_adapter import (
    ReplayResult,
    WorkerExecutionResult,
    WorkersAdapter,
    get_workers_adapter,
)

__all__ = [
    # Runtime adapter
    "RuntimeAdapter",
    "get_runtime_adapter",
    # Workers adapter
    "WorkersAdapter",
    "get_workers_adapter",
    "WorkerExecutionResult",
    "ReplayResult",
    # Policy adapter
    "PolicyAdapter",
    "get_policy_adapter",
    "PolicyEvaluationResult",
    "PolicyViolation",
]
