# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: PatternFeedback
#   Writes: none
# Database:
#   Scope: domain (analytics)
#   Models: PatternFeedback
# Role: Data access for feedback read operations (PB-S3 compliant, READ-ONLY)
# Callers: feedback_read_engine.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Feedback Read Driver (L6)

Pure database read operations for PatternFeedback (PB-S3).

All methods are pure DB operations — no business logic.
Business decisions stay in L5 engine.

Operations:
- Fetch feedback list with filters and pagination
- Fetch single feedback by ID
- Fetch feedback stats
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import PatternFeedback


class FeedbackReadDriver:
    """
    L6 driver for feedback read operations.

    Pure database access — no business logic.
    READ-ONLY: No write operations.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_feedback_list(
        self,
        tenant_id: Optional[str] = None,
        pattern_type: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Fetch paginated feedback list with filters.

        Returns dict with 'total' count and 'records' list.
        """
        query = select(PatternFeedback).order_by(PatternFeedback.detected_at.desc())

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)
        if pattern_type:
            query = query.where(PatternFeedback.pattern_type == pattern_type)
        if severity:
            query = query.where(PatternFeedback.severity == severity)
        if acknowledged is not None:
            query = query.where(PatternFeedback.acknowledged == acknowledged)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        records = result.scalars().all()

        return {"total": total, "records": list(records)}

    async def fetch_feedback_by_id(self, feedback_id: UUID) -> Optional[PatternFeedback]:
        """Fetch a single feedback record by UUID."""
        result = await self._session.execute(
            select(PatternFeedback).where(PatternFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def fetch_feedback_stats(
        self,
        tenant_id: Optional[str] = None,
    ) -> list[PatternFeedback]:
        """
        Fetch all feedback records for stats aggregation.

        Returns list of PatternFeedback records for L5 to aggregate.
        """
        query = select(PatternFeedback)
        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == tenant_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())


def get_feedback_read_driver(session: AsyncSession) -> FeedbackReadDriver:
    """Get feedback read driver instance."""
    return FeedbackReadDriver(session)
