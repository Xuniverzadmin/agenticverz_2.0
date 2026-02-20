# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide (Recovery API)
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: recovery_patterns
#   Writes: recovery_patterns, recovery_suggestions
# Database:
#   Scope: domain (recovery)
#   Models: RecoveryPattern, RecoverySuggestion
# Role: DB write driver for Recovery APIs (DB boundary crossing)
# Callers: L5 engines, api/recovery_ingest.py, api/recovery.py
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-250 Phase 2B Batch 4
# NOTE: Reclassified L4→L6 (2026-01-24) - Has Session import, DB write operations
#       Renamed recovery_write_service.py → recovery_write_driver.py (BANNED_NAMING fix)

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# DB write operations with atomic UPSERT via ON CONFLICT DO UPDATE
# Transaction boundaries are explicit and safe to retry
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

"""
Recovery Write Service - DB write operations for Recovery APIs.

Phase 2B Batch 4: Extracted from api/recovery_ingest.py and api/recovery.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
- SQL text preserved exactly (no changes)
- UPSERT logic preserved exactly
- Transaction boundaries preserved exactly
"""

from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session


class RecoveryWriteService:
    """
    Sync DB write operations for Recovery APIs.

    Write-only facade. No policy logic, no branching beyond DB operations.
    Raw SQL preserved exactly as extracted from API files.
    """

    def __init__(self, session: Session):
        self.session = session

    def upsert_recovery_candidate(
        self,
        failure_match_id: str,
        suggestion: str,
        confidence: float,
        explain_json: str,
        error_code: str,
        error_signature: str,
        source: str,
        idempotency_key: str,
    ) -> Tuple[int, bool, int]:
        """
        Atomic upsert: INSERT ... ON CONFLICT DO UPDATE RETURNING.

        SQL preserved exactly from recovery_ingest.py.

        Args:
            failure_match_id: Failure match UUID
            suggestion: Generated suggestion text
            confidence: Initial confidence score
            explain_json: JSON explanation (already serialized)
            error_code: Error type/code
            error_signature: Error signature hash
            source: Source of the failure
            idempotency_key: Idempotency UUID

        Returns:
            Tuple of (candidate_id, is_insert, occurrence_count)
        """
        result = self.session.execute(
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
        return (row[0], row[1], row[2])

    def get_candidate_by_idempotency_key(self, idempotency_key: str) -> Optional[Tuple[int, str]]:
        """
        Get candidate by idempotency key (for conflict handling).

        SQL preserved exactly from recovery_ingest.py.

        Args:
            idempotency_key: Idempotency UUID

        Returns:
            Tuple of (id, failure_match_id) or None
        """
        result = self.session.execute(
            text(
                """
                SELECT id, failure_match_id
                FROM recovery_candidates
                WHERE idempotency_key = CAST(:key AS uuid)
            """
            ),
            {"key": idempotency_key},
        )
        row = result.fetchone()
        return (row[0], str(row[1])) if row else None

    def enqueue_evaluation_db_fallback(
        self,
        candidate_id: int,
        idempotency_key: str,
    ) -> bool:
        """
        Enqueue evaluation to DB fallback via stored function.

        SQL preserved exactly from recovery_ingest.py.

        Args:
            candidate_id: Candidate ID to evaluate
            idempotency_key: Idempotency UUID

        Returns:
            True if enqueued successfully
        """
        self.session.execute(
            text(
                """
                SELECT m10_recovery.enqueue_work(
                    :candidate_id,
                    CAST(:idempotency_key AS uuid),
                    0,
                    'db_fallback'
                )
            """
            ),
            {
                "candidate_id": candidate_id,
                "idempotency_key": idempotency_key,
            },
        )
        return True

    def update_recovery_candidate(
        self,
        candidate_id: int,
        updates: list,
        params: Dict[str, Any],
    ) -> None:
        """
        Update recovery candidate with dynamic field list.

        SQL pattern preserved exactly from recovery.py.

        Args:
            candidate_id: Candidate ID to update
            updates: List of SQL SET clauses (e.g., ["status = :status"])
            params: Parameter dict including candidate_id
        """
        query = f"UPDATE recovery_candidates SET {', '.join(updates)} WHERE id = :id"
        self.session.execute(text(query), params)

    def insert_suggestion_provenance(
        self,
        suggestion_id: int,
        event_type: str,
        details_json: str,
        action_id: Optional[int],
        confidence_before: float,
        actor: str = "api",
    ) -> None:
        """
        Insert provenance record for a suggestion update.

        SQL preserved exactly from recovery.py.

        Args:
            suggestion_id: Candidate/suggestion ID
            event_type: Event type (executed, success, failure, manual_override)
            details_json: JSON details (already serialized)
            action_id: Selected action ID (optional)
            confidence_before: Confidence before this event
            actor: Actor name
        """
        self.session.execute(
            text(
                """
                INSERT INTO m10_recovery.suggestion_provenance
                (suggestion_id, event_type, details, action_id, confidence_before, actor)
                VALUES (:suggestion_id, :event_type, CAST(:details AS jsonb), :action_id, :confidence_before, :actor)
            """
            ),
            {
                "suggestion_id": suggestion_id,
                "event_type": event_type,
                "details": details_json,
                "action_id": action_id,
                "confidence_before": confidence_before,
                "actor": actor,
            },
        )

    # REMOVED: commit() helper — L6 DOES NOT COMMIT (L4 coordinator owns transaction boundary)

    # REMOVED: rollback() helper — L6 DOES NOT ROLLBACK (L4 coordinator owns transaction boundary)
