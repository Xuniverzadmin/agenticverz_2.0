# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide
# Role: S4 failure truth model, fact persistence
# Callers: L5 workers (on LLM failure)
# Reference: PIN-242 (Baseline Freeze)

"""
LLMFailureService - S4 Failure Truth Implementation

Implements PIN-196 requirements:
- Failure fact persistence (before any other action)
- Run state transition to FAILED
- Evidence capture (mandatory)
- No downstream contamination

ARCHITECTURE RULE: Explicit dependency injection, NO lazy service resolution.
See LESSONS_ENFORCED.md Invariant #10.

Critical Invariant:
> A failed run must never appear as "successful" or "completed with results."
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Type aliases for dependency injection
UuidFn = Callable[[], str]
ClockFn = Callable[[], datetime]

# Import from canonical locations
try:
    from app.utils.runtime import generate_uuid, utc_now
except ImportError:
    # Fallback for testing
    import uuid
    from datetime import timezone

    def generate_uuid() -> str:
        return str(uuid.uuid4())

    def utc_now() -> datetime:
        return datetime.now(timezone.utc)


VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "false").lower() == "true"


@dataclass
class LLMFailureFact:
    """
    Authoritative LLM failure fact.

    Must be persisted BEFORE any other action (PIN-196 Invariant 2).
    Evidence is mandatory (PIN-196 Invariant 4).
    """

    run_id: str
    tenant_id: str
    failure_type: str  # timeout, exception, invalid_output
    model: str
    error_code: str
    error_message: str
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Set on persistence
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    persisted: bool = False

    def __post_init__(self):
        if self.id is None:
            self.id = generate_uuid()
        if self.timestamp is None:
            self.timestamp = utc_now()

        # Validate failure_type
        valid_types = {"timeout", "exception", "invalid_output"}
        if self.failure_type not in valid_types:
            raise ValueError(f"failure_type must be one of {valid_types}, got {self.failure_type}")


@dataclass
class LLMFailureResult:
    """Result of failure persistence operation."""

    failure_id: str
    evidence_id: str
    run_marked_failed: bool
    timestamp: datetime


class LLMFailureService:
    """
    Service for handling LLM failures with S4 truth guarantees.

    PIN-196 Invariants Enforced:
    - Invariant 2: Failure first, always (persisted before classification)
    - Invariant 3: No silent healing (no retry/fallback/suppression)
    - Invariant 4: Evidence is mandatory (failure without evidence is invalid)
    - Invariant 5: Isolation holds under failure (tenant boundaries enforced)
    """

    def __init__(
        self,
        session: AsyncSession,
        uuid_fn: UuidFn = generate_uuid,
        clock_fn: ClockFn = utc_now,
    ):
        """
        Constructor requires explicit DI - no get_llm_failure_service() factory.

        Args:
            session: Database session (injected, not fetched)
            uuid_fn: UUID generator (for testing)
            clock_fn: Clock function (for testing)
        """
        self._session = session
        self._uuid_fn = uuid_fn
        self._clock_fn = clock_fn

    async def persist_failure_and_mark_run(
        self,
        failure: LLMFailureFact,
        auto_action: str = "mark_failed",
    ) -> LLMFailureResult:
        """
        Persist failure fact to DB, then mark run as FAILED.

        Order of operations (PIN-196 Critical):
        1. Persist failure fact
        2. Capture evidence (mandatory)
        3. Mark run as FAILED
        4. Verify no downstream contamination (in VERIFICATION_MODE)

        Args:
            failure: The failure fact to persist
            auto_action: Action to take (only "mark_failed" supported in S4)

        Returns:
            LLMFailureResult with IDs and status

        Raises:
            RuntimeError: If invariants are violated (VERIFICATION_MODE)
        """
        now = self._clock_fn()

        # STEP 1: Persist failure fact FIRST (Invariant 2)
        await self._persist_failure(failure, now)
        failure.persisted = True

        # STEP 2: Capture evidence (Invariant 4: Mandatory)
        evidence_id = await self._capture_evidence(failure, now)

        # STEP 3: Mark run as FAILED
        run_marked = await self._mark_run_failed(failure, now)

        # STEP 4: Verification mode contamination check
        if VERIFICATION_MODE:
            await self._verify_no_contamination(failure)

        await self._session.commit()

        return LLMFailureResult(
            failure_id=failure.id,
            evidence_id=evidence_id,
            run_marked_failed=run_marked,
            timestamp=now,
        )

    async def _persist_failure(self, failure: LLMFailureFact, timestamp: datetime) -> None:
        """Persist failure fact to run_failures table."""
        import json

        await self._session.execute(
            text(
                """
                INSERT INTO run_failures (
                    id, run_id, tenant_id, failure_type, error_code,
                    error_message, model, request_id, duration_ms,
                    metadata_json, created_at
                )
                VALUES (
                    :id, :run_id, :tenant_id, :failure_type, :error_code,
                    :error_message, :model, :request_id, :duration_ms,
                    :metadata_json, :created_at
                )
            """
            ),
            {
                "id": failure.id,
                "run_id": failure.run_id,
                "tenant_id": failure.tenant_id,
                "failure_type": failure.failure_type,
                "error_code": failure.error_code,
                "error_message": failure.error_message,
                "model": failure.model,
                "request_id": failure.request_id,
                "duration_ms": failure.duration_ms,
                "metadata_json": json.dumps(failure.metadata),
                "created_at": timestamp,
            },
        )

    async def _capture_evidence(self, failure: LLMFailureFact, timestamp: datetime) -> str:
        """Capture evidence for the failure (mandatory per Invariant 4)."""
        import json

        evidence_id = self._uuid_fn()

        evidence_data = {
            "failure_id": failure.id,
            "run_id": failure.run_id,
            "failure_type": failure.failure_type,
            "error_message": failure.error_message,
            "error_code": failure.error_code,
            "model": failure.model,
            "request_id": failure.request_id,
            "duration_ms": failure.duration_ms,
            "timestamp": timestamp.isoformat(),
            "verification_scenario": "S4",
        }

        await self._session.execute(
            text(
                """
                INSERT INTO failure_evidence (
                    id, failure_id, evidence_type, evidence_data,
                    is_immutable, created_at
                )
                VALUES (
                    :id, :failure_id, :evidence_type, :evidence_data,
                    :is_immutable, :created_at
                )
            """
            ),
            {
                "id": evidence_id,
                "failure_id": failure.id,
                "evidence_type": "llm_failure_capture",
                "evidence_data": json.dumps(evidence_data),
                "is_immutable": True,
                "created_at": timestamp,
            },
        )

        return evidence_id

    async def _mark_run_failed(self, failure: LLMFailureFact, timestamp: datetime) -> bool:
        """
        Mark the run as FAILED.

        Critical: Sets status='failed', success=false, error populated.
        Does NOT set recoveries (no implicit retry - Invariant 3).
        """
        result = await self._session.execute(
            text(
                """
                UPDATE worker_runs
                SET
                    status = 'failed',
                    success = false,
                    error = :error,
                    completed_at = :completed_at
                WHERE id = :run_id AND tenant_id = :tenant_id
                RETURNING id
            """
            ),
            {
                "run_id": failure.run_id,
                "tenant_id": failure.tenant_id,
                "error": f"{failure.error_code}: {failure.error_message}",
                "completed_at": timestamp,
            },
        )

        updated = result.fetchone()
        return updated is not None

    async def _verify_no_contamination(self, failure: LLMFailureFact) -> None:
        """
        Verify no downstream artifacts were created (AC-4).

        Only runs in VERIFICATION_MODE.
        Raises RuntimeError if contamination detected.
        """
        # Check for cost records
        cost_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_records
                WHERE request_id = :run_id OR request_id LIKE :pattern
            """
            ),
            {"run_id": failure.run_id, "pattern": f"%{failure.run_id}%"},
        )
        if cost_check.scalar() > 0:
            raise RuntimeError(f"FAILURE_CONTAMINATION_VIOLATION: Cost record created for failed run {failure.run_id}")

        # Check for advisories
        advisory_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_anomalies
                WHERE metadata->>'run_id' = :run_id
            """
            ),
            {"run_id": failure.run_id},
        )
        if advisory_check.scalar() > 0:
            raise RuntimeError(f"FAILURE_CONTAMINATION_VIOLATION: Advisory created for failed run {failure.run_id}")

        # Check for incidents (except llm_failure type)
        incident_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_value LIKE :pattern
                AND trigger_type != 'llm_failure'
            """
            ),
            {"pattern": f"%run_id={failure.run_id}%"},
        )
        if incident_check.scalar() > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Non-failure incident created for failed run {failure.run_id}"
            )

    async def get_failure_by_run_id(self, run_id: str, tenant_id: str) -> Optional[LLMFailureFact]:
        """
        Retrieve failure fact by run ID (with tenant isolation).

        Returns None if no failure exists (not an error condition).
        """
        result = await self._session.execute(
            text(
                """
                SELECT id, run_id, tenant_id, failure_type, error_code,
                       error_message, model, request_id, duration_ms,
                       metadata_json, created_at
                FROM run_failures
                WHERE run_id = :run_id AND tenant_id = :tenant_id
            """
            ),
            {"run_id": run_id, "tenant_id": tenant_id},
        )

        row = result.fetchone()
        if not row:
            return None

        import json

        return LLMFailureFact(
            id=row[0],
            run_id=row[1],
            tenant_id=row[2],
            failure_type=row[3],
            error_code=row[4],
            error_message=row[5],
            model=row[6],
            request_id=row[7],
            duration_ms=row[8],
            metadata=json.loads(row[9]) if row[9] else {},
            timestamp=row[10],
            persisted=True,
        )
