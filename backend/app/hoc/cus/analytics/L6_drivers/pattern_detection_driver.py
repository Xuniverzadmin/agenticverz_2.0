# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: worker_runs, pattern_feedback
#   Writes: pattern_feedback
# Role: Pattern detection data access operations
# Callers: pattern_detection.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, Phase-3B SQLAlchemy Extraction
#
# ============================================================================
# L6 DRIVER INVARIANT — PATTERN DETECTION
# ============================================================================
# This driver handles PERSISTENCE only:
# - Query worker_runs for failure/cost patterns
# - Insert pattern_feedback records
# - Query pattern_feedback summaries
#
# NO BUSINESS LOGIC. Decisions happen in L5 engine.
# ============================================================================

"""
Pattern Detection Driver (L6 Data Access)

Handles all database operations for pattern detection:
- Fetching failed runs for pattern analysis
- Fetching completed runs for cost spike detection
- Inserting pattern feedback records
- Querying feedback summaries

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import PatternFeedback
from app.models.tenant import WorkerRun


class PatternDetectionDriver:
    """
    L6 Driver for pattern detection data operations.

    All methods are pure DB operations - no business logic.
    Business decisions (threshold checks, pattern grouping) stay in L5.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session."""
        self._session = session

    async def fetch_failed_runs(
        self,
        window_start: datetime,
        tenant_id: Optional[UUID] = None,
    ) -> list[WorkerRun]:
        """
        Fetch failed runs within a time window.

        Args:
            window_start: Start of the time window
            tenant_id: Optional tenant filter

        Returns:
            List of failed WorkerRun records with errors
        """
        query = (
            select(WorkerRun)
            .where(WorkerRun.status == "failed")
            .where(WorkerRun.created_at >= window_start)
            .where(WorkerRun.error.isnot(None))
        )

        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def fetch_completed_runs_with_costs(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> list[WorkerRun]:
        """
        Fetch completed runs that have cost data.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            List of completed WorkerRun records with costs, ordered by created_at desc
        """
        query = (
            select(WorkerRun)
            .where(WorkerRun.status == "completed")
            .where(WorkerRun.cost_cents.isnot(None))
            .where(WorkerRun.cost_cents > 0)
            .order_by(WorkerRun.created_at.desc())
        )

        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def insert_feedback(
        self,
        tenant_id: UUID,
        pattern_type: str,
        severity: str,
        description: str,
        signature: str,
        provenance: list[str],
        occurrence_count: int,
        time_window_minutes: int,
        threshold_used: str,
        extra_data: Optional[dict[str, Any]],
        detected_at: datetime,
        created_at: datetime,
    ) -> PatternFeedback:
        """
        Insert a pattern feedback record.

        Args:
            tenant_id: Tenant identifier
            pattern_type: Type of pattern (failure_pattern, cost_spike)
            severity: Severity level
            description: Human-readable description
            signature: Pattern signature for deduplication
            provenance: List of run IDs that triggered this pattern
            occurrence_count: Number of occurrences
            time_window_minutes: Time window used for detection
            threshold_used: Description of threshold used
            extra_data: Additional metadata
            detected_at: When pattern was detected
            created_at: Record creation time

        Returns:
            Created PatternFeedback record
        """
        record = PatternFeedback(
            tenant_id=tenant_id,
            pattern_type=pattern_type,
            severity=severity,
            description=description,
            signature=signature,
            provenance=provenance,
            occurrence_count=occurrence_count,
            time_window_minutes=time_window_minutes,
            threshold_used=threshold_used,
            extra_data=extra_data,
            detected_at=detected_at,
            created_at=created_at,
        )

        self._session.add(record)
        await self._session.flush()

        return record

    async def fetch_feedback_records(
        self,
        tenant_id: Optional[UUID] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> list[PatternFeedback]:
        """
        Fetch pattern feedback records.

        Args:
            tenant_id: Optional tenant filter
            acknowledged: Optional acknowledgment status filter
            limit: Maximum records to return

        Returns:
            List of PatternFeedback records ordered by detected_at desc
        """
        query = select(PatternFeedback).order_by(PatternFeedback.detected_at.desc())

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)
        if acknowledged is not None:
            query = query.where(PatternFeedback.acknowledged == acknowledged)

        query = query.limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # commit() method removed — L6 DOES NOT COMMIT


def get_pattern_detection_driver(session: AsyncSession) -> PatternDetectionDriver:
    """Get a PatternDetectionDriver instance."""
    return PatternDetectionDriver(session)
