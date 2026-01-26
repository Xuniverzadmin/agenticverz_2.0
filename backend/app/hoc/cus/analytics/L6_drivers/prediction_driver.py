# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: PatternFeedback, PredictionEvent, WorkerRun
#   Writes: PredictionEvent
# Database:
#   Scope: domain (analytics)
#   Models: PatternFeedback, PredictionEvent, WorkerRun
# Role: Data access for prediction operations
# Callers: prediction.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5, httpx
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, Phase-2.5A Analytics Extraction
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for prediction management.
# NO business logic - only DB operations.
# NO prediction math, thresholding, or confidence calculations.
# Business logic (prediction scoring, thresholds) stays in L4 engine.
#
# ============================================================================
# L6 DRIVER INVENTORY — PREDICTION DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose                    | Status
# ----------------------------------- | -------------------------- | ------
# fetch_failure_patterns              | Get failure feedback       | [DONE]
# fetch_failed_runs                   | Get failed worker runs     | [DONE]
# fetch_run_totals                    | Get run counts by worker   | [DONE]
# fetch_cost_runs                     | Get runs with cost data    | [DONE]
# fetch_predictions                   | Get prediction events      | [DONE]
# insert_prediction                   | Create prediction event    | [DONE]
# commit                              | Commit transaction         | [DONE]
# ============================================================================

"""
Prediction Driver (L6)

Pure database operations for prediction management.
All business logic stays in L4 engine.

Operations:
- Read failure patterns from feedback
- Read failed runs and totals
- Read cost data for projections
- Read prediction events
- Insert new prediction events

NO business logic:
- NO prediction math (L4)
- NO confidence calculations (L4)
- NO threshold comparisons (L4)

Reference: Phase-2.5A Analytics Extraction
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import PatternFeedback
from app.models.prediction import PredictionEvent
from app.models.tenant import WorkerRun


class PredictionDriver:
    """
    L6 driver for prediction data access.

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    async def fetch_failure_patterns(
        self,
        tenant_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[PatternFeedback]:
        """
        Fetch failure pattern feedback records.

        Args:
            tenant_id: Optional tenant filter
            limit: Maximum records to fetch

        Returns:
            List of pattern feedback records
        """
        query = (
            select(PatternFeedback)
            .where(PatternFeedback.pattern_type == "failure_pattern")
            .order_by(PatternFeedback.detected_at.desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == str(tenant_id))

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def fetch_failed_runs(
        self,
        since: datetime,
        tenant_id: Optional[UUID] = None,
        worker_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[WorkerRun]:
        """
        Fetch failed worker runs.

        Args:
            since: Fetch runs created after this timestamp
            tenant_id: Optional tenant filter
            worker_id: Optional worker filter
            limit: Maximum records to fetch

        Returns:
            List of failed worker runs
        """
        query = (
            select(WorkerRun)
            .where(WorkerRun.status == "failed")
            .where(WorkerRun.created_at >= since)
            .order_by(WorkerRun.created_at.desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)
        if worker_id:
            query = query.where(WorkerRun.worker_id == worker_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def fetch_run_totals(
        self,
        since: datetime,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, int]:
        """
        Fetch total run counts grouped by worker.

        Args:
            since: Count runs created after this timestamp
            tenant_id: Optional tenant filter

        Returns:
            Dictionary mapping worker_id to total run count
        """
        query = (
            select(WorkerRun.worker_id, func.count().label("total"))
            .where(WorkerRun.created_at >= since)
            .group_by(WorkerRun.worker_id)
        )

        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)

        result = await self._session.execute(query)
        return {str(row.worker_id): row.total for row in result}

    async def fetch_cost_runs(
        self,
        since: datetime,
        tenant_id: Optional[UUID] = None,
        worker_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[WorkerRun]:
        """
        Fetch completed runs with cost data.

        Args:
            since: Fetch runs created after this timestamp
            tenant_id: Optional tenant filter
            worker_id: Optional worker filter
            limit: Maximum records to fetch

        Returns:
            List of completed runs with cost data
        """
        query = (
            select(WorkerRun)
            .where(WorkerRun.status == "completed")
            .where(WorkerRun.cost_cents.isnot(None))
            .where(WorkerRun.cost_cents > 0)
            .where(WorkerRun.created_at >= since)
            .order_by(WorkerRun.created_at.desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)
        if worker_id:
            query = query.where(WorkerRun.worker_id == worker_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def fetch_predictions(
        self,
        tenant_id: Optional[UUID] = None,
        prediction_type: Optional[str] = None,
        valid_after: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[PredictionEvent]:
        """
        Fetch prediction events.

        Args:
            tenant_id: Optional tenant filter
            prediction_type: Optional type filter
            valid_after: Only include predictions valid after this time
            limit: Maximum records to fetch

        Returns:
            List of prediction events
        """
        query = select(PredictionEvent).order_by(PredictionEvent.created_at.desc())

        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == str(tenant_id))
        if prediction_type:
            query = query.where(PredictionEvent.prediction_type == prediction_type)
        if valid_after:
            query = query.where(
                (PredictionEvent.valid_until.is_(None))
                | (PredictionEvent.valid_until > valid_after)
            )

        query = query.limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # INSERT OPERATIONS
    # =========================================================================

    async def insert_prediction(
        self,
        tenant_id: str,
        prediction_type: str,
        subject_type: str,
        subject_id: str,
        confidence_score: float,
        prediction_value: Dict[str, Any],
        contributing_factors: List[Dict[str, Any]],
        valid_until: datetime,
        created_at: datetime,
        notes: Optional[str] = None,
    ) -> PredictionEvent:
        """
        Insert a new prediction event.

        Args:
            tenant_id: Tenant ID
            prediction_type: Type of prediction
            subject_type: Subject type (e.g., 'worker')
            subject_id: Subject identifier
            confidence_score: Prediction confidence (0.0-1.0)
            prediction_value: Prediction data
            contributing_factors: Factors used for prediction
            valid_until: Prediction validity timestamp
            created_at: Creation timestamp
            notes: Optional notes

        Returns:
            Created prediction event
        """
        record = PredictionEvent(
            tenant_id=tenant_id,
            prediction_type=prediction_type,
            subject_type=subject_type,
            subject_id=subject_id,
            confidence_score=confidence_score,
            prediction_value=prediction_value,
            contributing_factors=contributing_factors,
            valid_until=valid_until,
            created_at=created_at,
            is_advisory=True,  # ALWAYS TRUE - enforced at driver level
            notes=notes,
        )

        self._session.add(record)
        await self._session.flush()

        return record

    # TRANSACTION HELPERS section removed — L6 DOES NOT COMMIT


def get_prediction_driver(session: AsyncSession) -> PredictionDriver:
    """Factory function to get PredictionDriver instance."""
    return PredictionDriver(session)


__all__ = [
    "PredictionDriver",
    "get_prediction_driver",
]
