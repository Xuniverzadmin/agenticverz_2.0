# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: engine-call
#   Execution: async
# Role: Data access for LLM failure persistence
# Callers: LLMFailureEngine (L4)
# Allowed Imports: sqlalchemy, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""LLM Failure Driver

L6 driver for LLM failure data access.

Pure persistence - no business logic.
Executes writes as directed by engine.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class FailureRow:
    """Immutable failure data from database."""

    id: str
    run_id: str
    tenant_id: str
    failure_type: str
    error_code: str
    error_message: str
    model: str
    request_id: Optional[str]
    duration_ms: Optional[int]
    metadata: Dict[str, Any]
    timestamp: datetime


class LLMFailureDriver:
    """L6 driver for LLM failure data access.

    Pure persistence - no business logic.
    Executes writes as directed by engine.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

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
        """Insert failure record.

        Args:
            failure_id: Unique failure ID
            run_id: Associated run ID
            tenant_id: Tenant ID
            failure_type: Type (timeout, exception, invalid_output)
            error_code: Error code
            error_message: Error message
            model: Model name
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
        """Insert evidence record.

        Args:
            evidence_id: Unique evidence ID
            failure_id: Associated failure ID
            evidence_type: Type of evidence
            evidence_data: Evidence data
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

    async def mark_run_failed(
        self,
        run_id: str,
        tenant_id: str,
        error: str,
        completed_at: datetime,
    ) -> bool:
        """Mark run as failed.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID
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

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    async def fetch_failure_by_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[FailureRow]:
        """Fetch failure by run ID.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for isolation

        Returns:
            FailureRow if found, None otherwise
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

        return FailureRow(
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
        )

    # =========================================================================
    # VERIFICATION QUERIES (for contamination checks)
    # =========================================================================

    async def count_cost_records_for_run(self, run_id: str) -> int:
        """Count cost records for a run (contamination check).

        Args:
            run_id: Run ID

        Returns:
            Count of cost records
        """
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_records
                WHERE request_id = :run_id OR request_id LIKE :pattern
            """
            ),
            {"run_id": run_id, "pattern": f"%{run_id}%"},
        )
        return result.scalar() or 0

    async def count_anomalies_for_run(self, run_id: str) -> int:
        """Count anomalies for a run (contamination check).

        Args:
            run_id: Run ID

        Returns:
            Count of anomalies
        """
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_anomalies
                WHERE metadata->>'run_id' = :run_id
            """
            ),
            {"run_id": run_id},
        )
        return result.scalar() or 0

    async def count_non_failure_incidents_for_run(self, run_id: str) -> int:
        """Count non-failure incidents for a run (contamination check).

        Args:
            run_id: Run ID

        Returns:
            Count of non-failure incidents
        """
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_value LIKE :pattern
                AND trigger_type != 'llm_failure'
            """
            ),
            {"pattern": f"%run_id={run_id}%"},
        )
        return result.scalar() or 0

    # =========================================================================
    # TRANSACTION OPERATIONS
    # =========================================================================

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()


# Factory function
def get_llm_failure_driver(session: AsyncSession) -> LLMFailureDriver:
    """Get driver instance.

    Args:
        session: Async database session

    Returns:
        LLMFailureDriver instance
    """
    return LLMFailureDriver(session)
