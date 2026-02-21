# capability_id: CAP-001
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Danger Fences - Encapsulated patterns for known-dangerous operations
# Callers: Recovery services, workers
# Allowed Imports: L6 only
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-268 (GU-004), PIN-267 (Test System Protection Rule)

"""
Danger Fences Module (PIN-268 GU-004)

This module contains DANGER FENCE helpers - explicit functions that encapsulate
known-dangerous patterns. These exist to:

1. Prevent reimplementation of patterns with known race conditions
2. Centralize documentation of why patterns are dangerous
3. Provide safe entry points that handle edge cases correctly
4. Make it impossible to accidentally introduce known bugs

GOVERNANCE RULE:
- Any code touching these patterns MUST use these helpers
- Reimplementing the patterns elsewhere is a governance violation
- See PIN-267 for test protection rules
- See docs/invariants/ for invariant documentation

Race Conditions Documented Here:
- Dual-constraint race on recovery_candidates (uq_rc_fmid_sig)
"""

import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)


# =============================================================================
# DANGER FENCE: Recovery Candidate Upsert
# =============================================================================


class RecoveryEnqueueError(Exception):
    """
    Exception raised when recovery candidate enqueue fails due to race condition.

    This exception indicates the dual-constraint race occurred:
    - recovery_candidates_failure_match_id_key vs uq_rc_fmid_sig

    The caller should retry with exponential backoff.
    """

    def __init__(self, failure_match_id: str, original_error: Exception):
        self.failure_match_id = failure_match_id
        self.original_error = original_error
        super().__init__(f"Recovery enqueue race condition for {failure_match_id}: {original_error}")


def enqueue_recovery_candidate_safely(
    session: Session,
    failure_match_id: str,
    error_signature: str,
    suggestion: str,
    confidence: float,
    explain_json: str,
    error_code: str,
    source: str,
    idempotency_key: str,
    max_retries: int = 3,
) -> Tuple[int, bool, int]:
    """
    DANGER FENCE: Safely enqueue a recovery candidate with dual-constraint handling.

    WARNING: This function exists to avoid the uq_rc_fmid_sig race condition.
    Do not reimplement recovery candidate enqueue logic elsewhere.
    See PIN-267 (Test System Protection) and PIN-268 (GU-004).

    The recovery_candidates table has two unique constraints on failure_match_id:
    1. recovery_candidates_failure_match_id_key (full constraint)
    2. uq_rc_fmid_sig (partial index: failure_match_id, error_signature WHERE NOT NULL)

    Under high concurrency, these constraints can trigger in unpredictable order,
    causing UniqueViolation that ON CONFLICT doesn't catch.

    This function handles the race by:
    1. Using ON CONFLICT (failure_match_id) for the primary constraint
    2. Catching UniqueViolation from uq_rc_fmid_sig and retrying
    3. Logging the race condition for monitoring

    Args:
        session: Database session
        failure_match_id: Failure match UUID
        error_signature: Error signature (may be None for some failures)
        suggestion: Generated suggestion text
        confidence: Initial confidence score
        explain_json: JSON explanation (already serialized)
        error_code: Error type/code
        source: Source of the failure
        idempotency_key: Idempotency UUID
        max_retries: Maximum retry attempts on race condition

    Returns:
        Tuple of (candidate_id, is_insert, occurrence_count)

    Raises:
        RecoveryEnqueueError: If race condition persists after retries

    Reference:
        - PIN-267 Section 3.3: Dual-constraint race documentation
        - PIN-268 GU-004: Danger fence requirement
        - tests/invariants/test_m10_invariants.py: Invariant tests
        - docs/invariants/M10_RECOVERY_INVARIANTS.md: Invariant documentation
    """
    from psycopg2.errors import UniqueViolation
    from sqlalchemy.exc import IntegrityError

    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            # Use ON CONFLICT (failure_match_id) - the full unique constraint
            # This handles the primary constraint correctly
            # Note: error_signature is included in INSERT but not in conflict target
            result = session.execute(
                text(
                    """
                    INSERT INTO recovery_candidates (
                        failure_match_id,
                        suggestion,
                        confidence,
                        explain,
                        error_code,
                        error_signature,
                        source,
                        created_by,
                        idempotency_key,
                        occurrence_count,
                        last_occurrence_at
                    ) VALUES (
                        CAST(:failure_match_id AS uuid),
                        :suggestion,
                        :confidence,
                        CAST(:explain AS jsonb),
                        :error_code,
                        :error_signature,
                        :source,
                        'ingest_api',
                        CAST(:idempotency_key AS uuid),
                        1,
                        now()
                    )
                    ON CONFLICT (failure_match_id) DO UPDATE
                    SET
                        occurrence_count = recovery_candidates.occurrence_count + 1,
                        last_occurrence_at = now(),
                        updated_at = now()
                    RETURNING id, (xmax = 0) AS is_insert, occurrence_count
                """
                ),
                {
                    "failure_match_id": failure_match_id,
                    "suggestion": suggestion,
                    "confidence": confidence,
                    "explain": explain_json,
                    "error_code": error_code,
                    "error_signature": error_signature,
                    "source": source,
                    "idempotency_key": idempotency_key,
                },
            )
            row = result.fetchone()

            if attempt > 0:
                logger.info(
                    "Recovery enqueue succeeded after %d retries for %s",
                    attempt,
                    failure_match_id,
                )

            return (row[0], row[1], row[2])

        except IntegrityError as e:
            # Check if this is the uq_rc_fmid_sig race condition
            if isinstance(e.orig, UniqueViolation):
                if "uq_rc_fmid_sig" in str(e.orig):
                    # This is the known dual-constraint race
                    logger.warning(
                        "Recovery enqueue race condition (attempt %d/%d) for %s: %s",
                        attempt + 1,
                        max_retries,
                        failure_match_id,
                        e,
                    )
                    last_error = e
                    session.rollback()
                    continue

            # Not the expected race condition - re-raise
            raise

    # All retries exhausted
    logger.error(
        "Recovery enqueue failed after %d retries for %s",
        max_retries,
        failure_match_id,
    )
    raise RecoveryEnqueueError(failure_match_id, last_error)


# =============================================================================
# DANGER FENCE REGISTRY
# =============================================================================

# Document all known dangerous patterns here for discoverability
DANGER_FENCES = {
    "recovery_candidate_enqueue": {
        "function": "enqueue_recovery_candidate_safely",
        "race_condition": "uq_rc_fmid_sig dual-constraint",
        "root_cause": "Partial unique index conflicts with full unique constraint",
        "documentation": [
            "PIN-267 Section 3.3",
            "PIN-268 GU-004",
            "docs/invariants/M10_RECOVERY_INVARIANTS.md",
            "tests/invariants/test_m10_invariants.py",
        ],
        "forbidden_patterns": [
            "Direct INSERT INTO recovery_candidates without using this helper",
            "ON CONFLICT (failure_match_id, error_signature) - won't work with partial index",
        ],
    },
}


def get_danger_fence_documentation() -> Dict[str, Any]:
    """
    Get documentation for all registered danger fences.

    Returns:
        Dictionary mapping fence names to their documentation
    """
    return DANGER_FENCES.copy()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "RecoveryEnqueueError",
    "enqueue_recovery_candidate_safely",
    "get_danger_fence_documentation",
    "DANGER_FENCES",
]
