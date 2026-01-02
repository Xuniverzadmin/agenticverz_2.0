# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: Domain package providing canonical exports for business rules
# Callers: L5 workers, L3 adapters, L8 tests
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-267

"""
L4 Domain Layer - Canonical business rule exports.

This package provides the stable public interface for domain concepts.
All domain logic should be accessed through this layer's exports.
"""

from app.domain.failure_intelligence import (
    aggregate_patterns,
    compute_signature,
    get_summary_stats,
    suggest_category,
    suggest_recovery,
)

__all__ = [
    "compute_signature",
    "suggest_category",
    "suggest_recovery",
    "aggregate_patterns",
    "get_summary_stats",
]
