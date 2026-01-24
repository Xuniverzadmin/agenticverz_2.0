# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: Canonical export surface for failure intelligence domain concepts
# Callers: L5 workers, L3 adapters, L8 tests (test_failure_catalog_m9.py)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-267 (CI Logic Issue Tracker)

"""
Failure Intelligence Domain Facade (L4).

This module provides the canonical public interface for failure classification
and recovery intelligence. It re-exports stable domain concepts from their
implementation locations, hiding internal job/service placement from callers.

Design Principle:
    "Tests do not define architecture. Architecture defines tests."

    Tests import from this facade. The facade decides which implementations
    to expose. Implementation modules can be refactored without breaking
    the public contract.

Exports:
    compute_signature(error_code: str, error_message: Optional[str] = None) -> str
        Compute deterministic signature for error grouping.
        Uses SHA256 of normalized error code + message prefix.
        Returns 16-character hex signature.

    suggest_category(error_codes: List[str]) -> str
        Classify error codes into semantic category.
        Returns: TRANSIENT, PERMISSION, RESOURCE, VALIDATION,
                 INFRASTRUCTURE, PLANNER, or PERMANENT

    suggest_recovery(error_codes: List[str]) -> str
        Suggest recovery mode based on error codes.
        Returns: RETRY_EXPONENTIAL, RETRY_WITH_JITTER, ESCALATE, or ABORT

    aggregate_patterns(raw_patterns: List[Dict]) -> List[Dict]
        Aggregate patterns by signature for deduplication.
        Groups similar errors that may have slightly different messages.

    get_summary_stats(patterns: List[Dict]) -> Dict
        Generate summary statistics for logging/alerting.

Usage:
    from app.domain.failure_intelligence import (
        compute_signature,
        suggest_category,
        suggest_recovery,
        aggregate_patterns,
        get_summary_stats,
    )

    signature = compute_signature("ERR_TIMEOUT", "Connection timed out")
    category = suggest_category(["timeout", "network"])
    recovery = suggest_recovery(["rate_limit", "429"])
"""

# Import from implementation modules and re-export with stable public names
from app.jobs.failure_classification_engine import (
    aggregate_patterns,
    compute_signature,
    get_summary_stats,
)
from app.services.recovery_rule_engine import (
    classify_error_category as suggest_category,
)
from app.services.recovery_rule_engine import (
    suggest_recovery_mode as suggest_recovery,
)

__all__ = [
    "compute_signature",
    "suggest_category",
    "suggest_recovery",
    "aggregate_patterns",
    "get_summary_stats",
]
