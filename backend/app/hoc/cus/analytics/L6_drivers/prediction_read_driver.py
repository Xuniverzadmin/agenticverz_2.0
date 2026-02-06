# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: PredictionEvent
#   Writes: none
# Database:
#   Scope: domain (analytics)
#   Models: PredictionEvent
# Role: Data access for prediction read operations (PB-S5 compliant, READ-ONLY)
# Callers: prediction_read_engine.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Prediction Read Driver (L6)

Pure database read operations for PredictionEvent (PB-S5).

All methods are pure DB operations — no business logic.
Business decisions stay in L5 engine.

Operations:
- Fetch prediction list with filters and pagination
- Fetch single prediction by ID
- Fetch predictions by subject
- Fetch prediction stats
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionEvent


class PredictionReadDriver:
    """
    L6 driver for prediction read operations.

    Pure database access — no business logic.
    READ-ONLY: No write operations.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_prediction_list(
        self,
        tenant_id: Optional[str] = None,
        prediction_type: Optional[str] = None,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        include_expired: bool = False,
        now: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Fetch paginated prediction list with filters.

        Returns dict with 'total' count and 'records' list.
        """
        query = select(PredictionEvent).order_by(PredictionEvent.created_at.desc())

        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == tenant_id)
        if prediction_type:
            query = query.where(PredictionEvent.prediction_type == prediction_type)
        if subject_type:
            query = query.where(PredictionEvent.subject_type == subject_type)
        if subject_id:
            query = query.where(PredictionEvent.subject_id == subject_id)
        if not include_expired and now:
            query = query.where(
                (PredictionEvent.expires_at.is_(None)) | (PredictionEvent.expires_at > now)
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        records = result.scalars().all()

        return {"total": total, "records": list(records)}

    async def fetch_prediction_by_id(self, prediction_id: UUID) -> Optional[PredictionEvent]:
        """Fetch a single prediction record by UUID."""
        result = await self._session.execute(
            select(PredictionEvent).where(PredictionEvent.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def fetch_predictions_for_subject(
        self,
        subject_type: str,
        subject_id: str,
        include_expired: bool = False,
        now: Optional[datetime] = None,
        limit: int = 20,
    ) -> list[PredictionEvent]:
        """Fetch predictions for a specific subject."""
        query = (
            select(PredictionEvent)
            .where(PredictionEvent.subject_type == subject_type)
            .where(PredictionEvent.subject_id == subject_id)
            .order_by(PredictionEvent.created_at.desc())
        )

        if not include_expired and now:
            query = query.where(
                (PredictionEvent.expires_at.is_(None)) | (PredictionEvent.expires_at > now)
            )

        query = query.limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def fetch_prediction_stats(
        self,
        tenant_id: Optional[str] = None,
        include_expired: bool = False,
        now: Optional[datetime] = None,
    ) -> list[PredictionEvent]:
        """
        Fetch all prediction records for stats aggregation.

        Returns list of PredictionEvent records for L5 to aggregate.
        """
        query = select(PredictionEvent)
        if tenant_id:
            query = query.where(PredictionEvent.tenant_id == tenant_id)
        if not include_expired and now:
            query = query.where(
                (PredictionEvent.expires_at.is_(None)) | (PredictionEvent.expires_at > now)
            )

        result = await self._session.execute(query)
        return list(result.scalars().all())


def get_prediction_read_driver(session: AsyncSession) -> PredictionReadDriver:
    """Get prediction read driver instance."""
    return PredictionReadDriver(session)
