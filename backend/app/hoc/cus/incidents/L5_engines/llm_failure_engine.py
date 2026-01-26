# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: async
# Lifecycle:
#   Emits: llm_failure_recorded
#   Subscribes: none
# Data Access:
#   Reads: RunFailure (via driver)
#   Writes: RunFailure, FailureEvidence (via driver)
# Role: S4 failure truth model, fact persistence
# Callers: L5 workers (on LLM failure)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Forbidden: session.commit(), session.rollback() — L5 DOES NOT COMMIT (L4 coordinator owns)
# Reference: PIN-470, PIN-242 (Baseline Freeze), PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Renamed llm_failure_service.py → llm_failure_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-23)
# - All DB operations extracted to LLMFailureDriver
# - Engine contains ONLY decision logic
# - NO sqlalchemy/sqlmodel imports at runtime
#
# ============================================================================
# L5 ENGINE INVARIANT — LLM FAILURE DOMAIN (LOCKED)
# ============================================================================
# This file MUST NOT import sqlalchemy/sqlmodel at runtime.
# All persistence is delegated to llm_failure_driver.py.
# Business decisions ONLY.
#
# Any violation is a Phase-2.5 regression.
# ============================================================================

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
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

# L6 driver import (allowed)
from app.hoc.cus.incidents.L6_drivers.llm_failure_driver import (
    LLMFailureDriver,
    get_llm_failure_driver,
)

if TYPE_CHECKING:
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

    Note: All DB operations are delegated to LLMFailureDriver (L6).
    This engine contains only business logic decisions.
    """

    def __init__(
        self,
        session: "AsyncSession",
        uuid_fn: UuidFn = generate_uuid,
        clock_fn: ClockFn = utc_now,
        driver: Optional[LLMFailureDriver] = None,
    ):
        """
        Constructor requires explicit DI - no get_llm_failure_service() factory.

        Args:
            session: Database session (injected, not fetched)
            uuid_fn: UUID generator (for testing)
            clock_fn: Clock function (for testing)
            driver: Optional pre-configured driver (for testing)
        """
        self._session = session
        self._uuid_fn = uuid_fn
        self._clock_fn = clock_fn
        self._driver = driver or get_llm_failure_driver(session)

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

        # NO COMMIT — L4 coordinator owns transaction boundary

        return LLMFailureResult(
            failure_id=failure.id,
            evidence_id=evidence_id,
            run_marked_failed=run_marked,
            timestamp=now,
        )

    async def _persist_failure(self, failure: LLMFailureFact, timestamp: datetime) -> None:
        """
        Persist failure fact to run_failures table.

        PERSISTENCE: Delegated to driver.
        """
        if failure.id is None:
            raise ValueError("failure.id must be set before persistence")

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
            created_at=timestamp,
        )

    async def _capture_evidence(self, failure: LLMFailureFact, timestamp: datetime) -> str:
        """
        Capture evidence for the failure (mandatory per Invariant 4).

        PERSISTENCE: Delegated to driver.
        """
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

        await self._driver.insert_evidence(
            evidence_id=evidence_id,
            failure_id=failure.id,
            evidence_type="llm_failure_capture",
            evidence_data=evidence_data,
            is_immutable=True,
            created_at=timestamp,
        )

        return evidence_id

    async def _mark_run_failed(self, failure: LLMFailureFact, timestamp: datetime) -> bool:
        """
        Mark the run as FAILED.

        Critical: Sets status='failed', success=false, error populated.
        Does NOT set recoveries (no implicit retry - Invariant 3).

        PERSISTENCE: Delegated to driver.
        """
        error_message = f"{failure.error_code}: {failure.error_message}"

        return await self._driver.update_run_failed(
            run_id=failure.run_id,
            tenant_id=failure.tenant_id,
            error=error_message,
            completed_at=timestamp,
        )

    async def _verify_no_contamination(self, failure: LLMFailureFact) -> None:
        """
        Verify no downstream artifacts were created (AC-4).

        Only runs in VERIFICATION_MODE.
        Raises RuntimeError if contamination detected.

        PERSISTENCE: Delegated to driver for queries.
        BUSINESS LOGIC: Interpretation of counts stays here (L4).
        """
        counts = await self._driver.fetch_contamination_check(failure.run_id)

        if counts["cost_records"] > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Cost record created for failed run {failure.run_id}"
            )

        if counts["cost_anomalies"] > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Advisory created for failed run {failure.run_id}"
            )

        if counts["other_incidents"] > 0:
            raise RuntimeError(
                f"FAILURE_CONTAMINATION_VIOLATION: Non-failure incident created for failed run {failure.run_id}"
            )

    async def get_failure_by_run_id(self, run_id: str, tenant_id: str) -> Optional[LLMFailureFact]:
        """
        Retrieve failure fact by run ID (with tenant isolation).

        Returns None if no failure exists (not an error condition).

        PERSISTENCE: Delegated to driver.
        BUSINESS LOGIC: Fact reconstruction stays here (L4).
        """
        import json

        row = await self._driver.fetch_failure_by_run_id(run_id, tenant_id)
        if not row:
            return None

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
