# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Audit entry for an agent_invoke call.
# M12.1 Invoke Audit Service
# Audit trail for agent_invoke calls
#
# Based on: PIN-063-m12.1-stabilization.md

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("nova.agents.invoke_audit")


@dataclass
class InvokeAuditEntry:
    """Audit entry for an agent_invoke call."""

    id: UUID
    invoke_id: str
    caller_instance_id: str
    target_instance_id: str
    job_id: Optional[UUID]
    request_payload: Any
    response_payload: Optional[Any]
    status: str  # pending, completed, timeout, failed
    credits_charged: Optional[Decimal]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]


class InvokeAuditService:
    """
    Audit trail service for agent_invoke calls.

    Provides:
    - Start/complete/fail logging for invoke calls
    - Query by invoke_id, caller, target, job
    - Duration and credit tracking
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for InvokeAuditService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)

    def start_invoke(
        self,
        invoke_id: str,
        caller_instance_id: str,
        target_instance_id: str,
        request_payload: Any,
        job_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Record the start of an invoke call.

        Args:
            invoke_id: Correlation ID for the invoke
            caller_instance_id: Who is calling
            target_instance_id: Who is being called
            request_payload: Request data
            job_id: Optional job context

        Returns:
            Audit entry UUID
        """
        entry_id = uuid4()

        with self.Session() as session:
            try:
                session.execute(
                    text(
                        """
                        INSERT INTO agents.invoke_audit (
                            id, invoke_id, caller_instance_id, target_instance_id,
                            job_id, request_payload, status, started_at
                        ) VALUES (
                            :id, :invoke_id, :caller, :target,
                            CAST(:job_id AS UUID), CAST(:payload AS JSONB),
                            'pending', now()
                        )
                    """
                    ),
                    {
                        "id": str(entry_id),
                        "invoke_id": invoke_id,
                        "caller": caller_instance_id,
                        "target": target_instance_id,
                        "job_id": str(job_id) if job_id else None,
                        "payload": json.dumps(request_payload)
                        if not isinstance(request_payload, str)
                        else request_payload,
                    },
                )
                session.commit()

                logger.debug(
                    "invoke_started",
                    extra={
                        "invoke_id": invoke_id,
                        "caller": caller_instance_id,
                        "target": target_instance_id,
                    },
                )

                return entry_id

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log invoke start: {e}")
                # Don't fail the invoke - audit is best-effort
                return entry_id

    def complete_invoke(
        self,
        invoke_id: str,
        response_payload: Any,
        credits_charged: Optional[Decimal] = None,
    ) -> bool:
        """
        Record successful completion of an invoke call.

        Args:
            invoke_id: Correlation ID
            response_payload: Response data
            credits_charged: Credits charged for this invoke

        Returns:
            True if updated
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        UPDATE agents.invoke_audit
                        SET status = 'completed',
                            response_payload = CAST(:payload AS JSONB),
                            credits_charged = :credits,
                            completed_at = now(),
                            duration_ms = EXTRACT(MILLISECONDS FROM (now() - started_at))::INTEGER
                        WHERE invoke_id = :invoke_id AND status = 'pending'
                        RETURNING id
                    """
                    ),
                    {
                        "invoke_id": invoke_id,
                        "payload": json.dumps(response_payload)
                        if not isinstance(response_payload, str)
                        else response_payload,
                        "credits": float(credits_charged) if credits_charged else None,
                    },
                )
                row = result.fetchone()
                session.commit()

                if row:
                    logger.debug(f"invoke_completed: {invoke_id}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log invoke completion: {e}")
                return False

    def fail_invoke(
        self,
        invoke_id: str,
        error_message: str,
        status: str = "failed",  # failed, timeout
    ) -> bool:
        """
        Record failed invoke call.

        Args:
            invoke_id: Correlation ID
            error_message: Error description
            status: 'failed' or 'timeout'

        Returns:
            True if updated
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        UPDATE agents.invoke_audit
                        SET status = :status,
                            error_message = :error,
                            completed_at = now(),
                            duration_ms = EXTRACT(MILLISECONDS FROM (now() - started_at))::INTEGER
                        WHERE invoke_id = :invoke_id AND status = 'pending'
                        RETURNING id
                    """
                    ),
                    {
                        "invoke_id": invoke_id,
                        "status": status,
                        "error": error_message[:1000] if error_message else None,
                    },
                )
                row = result.fetchone()
                session.commit()

                if row:
                    logger.warning(f"invoke_{status}: {invoke_id} - {error_message[:100]}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log invoke failure: {e}")
                return False

    def get_by_invoke_id(self, invoke_id: str) -> Optional[InvokeAuditEntry]:
        """Get audit entry by invoke ID."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, invoke_id, caller_instance_id, target_instance_id,
                        job_id, request_payload, response_payload, status,
                        credits_charged, started_at, completed_at,
                        duration_ms, error_message
                    FROM agents.invoke_audit
                    WHERE invoke_id = :invoke_id
                """
                ),
                {"invoke_id": invoke_id},
            )
            row = result.fetchone()

            if not row:
                return None

            return self._row_to_entry(row)

    def list_by_job(
        self,
        job_id: UUID,
        limit: int = 100,
    ) -> List[InvokeAuditEntry]:
        """List invoke audit entries for a job."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, invoke_id, caller_instance_id, target_instance_id,
                        job_id, request_payload, response_payload, status,
                        credits_charged, started_at, completed_at,
                        duration_ms, error_message
                    FROM agents.invoke_audit
                    WHERE job_id = :job_id
                    ORDER BY started_at DESC
                    LIMIT :limit
                """
                ),
                {"job_id": str(job_id), "limit": limit},
            )

            return [self._row_to_entry(row) for row in result]

    def list_by_caller(
        self,
        caller_instance_id: str,
        limit: int = 100,
    ) -> List[InvokeAuditEntry]:
        """List invoke audit entries by caller."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, invoke_id, caller_instance_id, target_instance_id,
                        job_id, request_payload, response_payload, status,
                        credits_charged, started_at, completed_at,
                        duration_ms, error_message
                    FROM agents.invoke_audit
                    WHERE caller_instance_id = :caller
                    ORDER BY started_at DESC
                    LIMIT :limit
                """
                ),
                {"caller": caller_instance_id, "limit": limit},
            )

            return [self._row_to_entry(row) for row in result]

    def get_stats(
        self,
        since_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get invoke statistics."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        status,
                        COUNT(*) as count,
                        AVG(duration_ms) as avg_duration_ms,
                        SUM(credits_charged) as total_credits
                    FROM agents.invoke_audit
                    WHERE started_at > now() - make_interval(hours => :hours)
                    GROUP BY status
                """
                ),
                {"hours": since_hours},
            )

            stats = {
                "since_hours": since_hours,
                "by_status": {},
                "total": 0,
                "total_credits": Decimal("0"),
            }

            for row in result:
                status, count, avg_duration, credits = row
                stats["by_status"][status] = {
                    "count": count,
                    "avg_duration_ms": round(avg_duration, 2) if avg_duration else None,
                    "total_credits": float(credits) if credits else 0,
                }
                stats["total"] += count
                if credits:
                    stats["total_credits"] += Decimal(str(credits))

            return stats

    def _row_to_entry(self, row) -> InvokeAuditEntry:
        """Convert DB row to InvokeAuditEntry."""
        return InvokeAuditEntry(
            id=UUID(str(row[0])),
            invoke_id=row[1],
            caller_instance_id=row[2],
            target_instance_id=row[3],
            job_id=UUID(str(row[4])) if row[4] else None,
            request_payload=row[5],
            response_payload=row[6],
            status=row[7],
            credits_charged=Decimal(str(row[8])) if row[8] else None,
            started_at=row[9],
            completed_at=row[10],
            duration_ms=row[11],
            error_message=row[12],
        )


# Singleton instance
_service: Optional[InvokeAuditService] = None


def get_invoke_audit_service() -> InvokeAuditService:
    """Get singleton invoke audit service instance."""
    global _service
    if _service is None:
        _service = InvokeAuditService()
    return _service
