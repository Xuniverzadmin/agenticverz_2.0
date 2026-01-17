# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Limits runtime evaluation (PIN-LIM-03)
# Callers: services/limits/*, worker/runtime/*
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: LIMITS_MANAGEMENT_AUDIT.md, Evaluation Order Contract

"""
Limits Runtime Package

Provides deterministic limit evaluation at runtime:
- LimitsEvaluator: Core decision engine
- OverrideResolver: Apply active overrides
"""

from app.runtime.limits.evaluator import LimitsEvaluator, EvaluationResult
from app.runtime.limits.override_resolver import OverrideResolver

__all__ = [
    "LimitsEvaluator",
    "EvaluationResult",
    "OverrideResolver",
]
