# Layer: L4 — Domain Engine (System Truth)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: S4 failure truth decisions
# Callers: L5 workers (on LLM failure)
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel (at runtime)
# Reference: PIN-468, PIN-196, DRIVER_ENGINE_CONTRACT.md

"""LLM Failure Engine - S4 Failure Truth Implementation

L4 engine for LLM failure decisions.

Decides: Failure validation, verification mode checks, contamination rules
Delegates: Data access to LLMFailureDriver

PIN-196 Requirements Enforced:
- Failure fact persistence (before any other action)
- Run state transition to FAILED
- Evidence capture (mandatory)
- No downstream contamination

Critical Invariant:
> A failed run must never appear as "successful" or "completed with results."
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from app.services.llm_failure_driver import (
    FailureRow,
    LLMFailureDriver,
    get_llm_failure_driver,
)

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


# DECISION: Verification mode flag
VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "false").lower() == "true"


@dataclass
class LLMFailureFact:
    """Authoritative LLM failure fact.

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

        # DECISION: Validate failure_type
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


class LLMFailureEngine:
    """L4 engine for LLM failure decisions.

    Decides: Failure validation, evidence requirements, contamination checks
    Delegates: Data access to LLMFailureDriver

    PIN-196 Invariants Enforced:
    - Invariant 2: Failure first, always (persisted before classification)
    - Invariant 3: No silent healing (no retry/fallback/suppression)
    - Invariant 4: Evidence is mandatory (failure without evidence is invalid)
    - Invariant 5: Isolation holds under failure (tenant boundaries enforced)
    """

    def __init__(
        self,
        driver: LLMFailureDriver,
        uuid_fn: UuidFn = generate_uuid,
        clock_fn: ClockFn = utc_now,
    ):
        """Constructor requires explicit DI.

        Args:
            driver: LLMFailureDriver for data access
            uuid_fn: UUID generator (for testing)
            clock_fn: Clock function (for testing)
        """
        self._driver = driver
        self._uuid_fn = uuid_fn
        self._clock_fn = clock_fn

    async def persist_failure_and_mark_run(
        self,
        failure: LLMFailureFact,
        auto_action: str = "mark_failed",
    ) -> LLMFailureResult:
        """Persist failure fact to DB, then mark run as FAILED.

        DECISION: Order of operations (PIN-196 Critical):
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

        # STEP 1: DECISION - Persist failure fact FIRST (Invariant 2)
        await self._driver.insert_failure(
            failure_id=failure.id,
            run_id=failure.run_id,
            tenant_id=failure.tenant_id,
            failure_type=failure.failure_type,
            error_code=failure.error_code,
            error_message=failure.error_message,
            model=failure.model,
            request_id=failure.request_id,
            duration_ms=failure.duration_ms,
            metadata=failure.metadata,
            created_at=now,
        )
        failure.persisted = True

        # STEP 2: DECISION - Capture evidence (Invariant 4: Mandatory)
        evidence_id = await self._capture_evidence(failure, now)

        # STEP 3: Mark run as FAILED
        error_message = f"{failure.error_code}: {failure.error_message}"
        run_marked = await self._driver.mark_run_failed(
            run_id=failure.run_id,
            tenant_id=failure.tenant_id,
            error=error_message,
            completed_at=now,
        )

        # STEP 4: DECISION - Verification mode contamination check
        if VERIFICATION_MODE:
            await self._verify_no_contamination(failure)

        await self._driver.commit()

        return LLMFailureResult(
            failure_id=failure.id,
            evidence_id=evidence_id,
            run_marked_failed=run_marked,
            timestamp=now,
        )

    async def _capture_evidence(
        self,
        failure: LLMFailureFact,
        timestamp: datetime,
    ) -> str:
        """Capture evidence for the failure (mandatory per Invariant 4).

        DECISION: Evidence structure for S4 compliance.
        """
        evidence_id = self._uuid_fn()

        # DECISION: Evidence data structure
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

        await self._driver.insert_evidence(
            evidence_id=evidence_id,
            failure_id=failure.id,
            evidence_type="llm_failure_capture",
            evidence_data=evidence_data,
            is_immutable=True,
            created_at=timestamp,
        )

        return evidence_id

    async def _verify_no_contamination(self, failure: LLMFailureFact) -> None:
        """Verify no downstream artifacts were created (AC-4).

        DECISION: Only runs in VERIFICATION_MODE.
        Raises RuntimeError if contamination detected.
        """
        # DECISION: Check for cost records contamination
        cost_count = await self._driver.count_cost_records_for_run(failure.run_id)
        if cost_count > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Cost record created for failed run {failure.run_id}"
            )

        # DECISION: Check for advisories contamination
        anomaly_count = await self._driver.count_anomalies_for_run(failure.run_id)
        if anomaly_count > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Advisory created for failed run {failure.run_id}"
            )

        # DECISION: Check for non-failure incidents contamination
        incident_count = await self._driver.count_non_failure_incidents_for_run(failure.run_id)
        if incident_count > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Non-failure incident created for failed run {failure.run_id}"
            )

    async def get_failure_by_run_id(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[LLMFailureFact]:
        """Retrieve failure fact by run ID (with tenant isolation).

        Returns None if no failure exists (not an error condition).
        """
        row = await self._driver.fetch_failure_by_run(run_id, tenant_id)

        if not row:
            return None

        return LLMFailureFact(
            id=row.id,
            run_id=row.run_id,
            tenant_id=row.tenant_id,
            failure_type=row.failure_type,
            error_code=row.error_code,
            error_message=row.error_message,
            model=row.model,
            request_id=row.request_id,
            duration_ms=row.duration_ms,
            metadata=row.metadata,
            timestamp=row.timestamp,
            persisted=True,
        )


# Backward compatibility aliases
LLMFailureService = LLMFailureEngine

__all__ = [
    "LLMFailureFact",
    "LLMFailureResult",
    "LLMFailureEngine",
    "LLMFailureService",
]
