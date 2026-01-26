# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: RunFailure, FailureEvidence, WorkerRun
#   Writes: RunFailure, FailureEvidence, WorkerRun
# Database:
#   Scope: domain (incidents)
#   Models: RunFailure, FailureEvidence, WorkerRun
# Role: Data access for LLM failure operations (async)
# Callers: LLMFailureEngine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for LLM failure operations.
# NO business logic - only DB operations.
# Business logic (invariant checking, verification mode) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction from llm_failure_service.py (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — LLM FAILURE DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose
# ----------------------------------- | ----------------------------------------
# insert_failure                      | Create failure fact in run_failures
# insert_evidence                     | Create evidence record in failure_evidence
# update_run_failed                   | Mark run as failed in worker_runs
# fetch_failure_by_run_id             | Get failure by run ID
# fetch_contamination_check           | Verify no downstream contamination
# ============================================================================
# This is the SINGLE persistence authority for LLM failure writes.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
LLM Failure Driver (L6)

Pure database operations for LLM failure handling.
All business logic stays in L4 engine.

Operations:
- Create failure facts
- Create evidence records
- Mark runs as failed
- Contamination verification (read-only)

NO business logic:
- NO invariant checking (L4)
- NO verification mode decisions (L4)
- NO failure type validation (L4)

Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.drivers.llm_failure")


class LLMFailureDriver:
    """
    L6 driver for LLM failure operations (async).

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def insert_failure(
        self,
        failure_id: str,
        run_id: str,
        tenant_id: str,
        failure_type: str,
        error_code: str,
        error_message: str,
        model: str,
        request_id: Optional[str],
        duration_ms: Optional[int],
        metadata: Dict[str, Any],
        created_at: datetime,
    ) -> None:
        """
        Insert failure fact into run_failures table.

        Args:
            failure_id: Generated failure ID
            run_id: Run that failed
            tenant_id: Tenant scope
            failure_type: Type of failure (timeout, exception, invalid_output)
            error_code: Error code
            error_message: Error description
            model: LLM model used
            request_id: Optional request ID
            duration_ms: Optional duration
            metadata: Additional metadata
            created_at: Timestamp
        """
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
                "id": failure_id,
                "run_id": run_id,
                "tenant_id": tenant_id,
                "failure_type": failure_type,
                "error_code": error_code,
                "error_message": error_message,
                "model": model,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "metadata_json": json.dumps(metadata),
                "created_at": created_at,
            },
        )

    async def insert_evidence(
        self,
        evidence_id: str,
        failure_id: str,
        evidence_type: str,
        evidence_data: Dict[str, Any],
        is_immutable: bool,
        created_at: datetime,
    ) -> None:
        """
        Insert evidence record into failure_evidence table.

        Args:
            evidence_id: Generated evidence ID
            failure_id: Parent failure ID
            evidence_type: Type of evidence (e.g., llm_failure_capture)
            evidence_data: Evidence payload
            is_immutable: Whether evidence is immutable
            created_at: Timestamp
        """
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
                "failure_id": failure_id,
                "evidence_type": evidence_type,
                "evidence_data": json.dumps(evidence_data),
                "is_immutable": is_immutable,
                "created_at": created_at,
            },
        )

    async def update_run_failed(
        self,
        run_id: str,
        tenant_id: str,
        error: str,
        completed_at: datetime,
    ) -> bool:
        """
        Mark run as failed in worker_runs table.

        Args:
            run_id: Run to mark failed
            tenant_id: Tenant scope
            error: Error message
            completed_at: Completion timestamp

        Returns:
            True if run was updated, False if not found
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
                "run_id": run_id,
                "tenant_id": tenant_id,
                "error": error,
                "completed_at": completed_at,
            },
        )
        updated = result.fetchone()
        return updated is not None

    async def fetch_failure_by_run_id(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[Tuple]:
        """
        Fetch failure record by run ID.

        Args:
            run_id: Run ID to look up
            tenant_id: Tenant scope

        Returns:
            Tuple of (id, run_id, tenant_id, failure_type, error_code,
                     error_message, model, request_id, duration_ms,
                     metadata_json, created_at) or None
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
        return result.fetchone()

    async def fetch_contamination_check(
        self,
        run_id: str,
    ) -> Dict[str, int]:
        """
        Check for downstream contamination (verification mode).

        Args:
            run_id: Run ID to check

        Returns:
            Dict with counts: {cost_records, cost_anomalies, other_incidents}
        """
        # Check for cost records
        cost_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_records
                WHERE request_id = :run_id OR request_id LIKE :pattern
            """
            ),
            {"run_id": run_id, "pattern": f"%{run_id}%"},
        )
        cost_count = cost_check.scalar() or 0

        # Check for advisories
        advisory_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_anomalies
                WHERE metadata->>'run_id' = :run_id
            """
            ),
            {"run_id": run_id},
        )
        advisory_count = advisory_check.scalar() or 0

        # Check for incidents (except llm_failure type)
        incident_check = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_value LIKE :pattern
                AND trigger_type != 'llm_failure'
            """
            ),
            {"pattern": f"%run_id={run_id}%"},
        )
        incident_count = incident_check.scalar() or 0

        return {
            "cost_records": cost_count,
            "cost_anomalies": advisory_count,
            "other_incidents": incident_count,
        }

    # REMOVED: commit() helper — L6 DOES NOT COMMIT (L4 coordinator owns transaction boundary)


def get_llm_failure_driver(session: AsyncSession) -> LLMFailureDriver:
    """Factory function to get LLMFailureDriver instance."""
    return LLMFailureDriver(session)


__all__ = [
    "LLMFailureDriver",
    "get_llm_failure_driver",
]
