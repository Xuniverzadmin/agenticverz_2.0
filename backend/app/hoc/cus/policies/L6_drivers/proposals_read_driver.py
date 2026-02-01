# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_proposals
#   Writes: none
# Role: Read operations for policy proposals (list view)
# Callers: L5 policies_proposals_query_engine
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Proposals Read Driver (L6)

Pure data access layer for policy proposals read operations (list view).
This driver is for the "Proposals" tab in the policies domain.

Note: This is separate from policy_proposal_read_driver.py which handles
the proposal lifecycle engine operations.

All SQLAlchemy queries live here. No business logic.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.models.policy import PolicyProposal


class ProposalsReadDriver:
    """Read operations for policy proposals (list view)."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_proposals(
        self,
        tenant_id: str,
        *,
        status: str = "draft",
        proposal_type: Optional[str] = None,
        days_old: Optional[int] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Fetch policy proposals with filters and pagination.

        Returns (items, pending_count).
        """
        now = datetime.now(timezone.utc)

        # Build query
        stmt = select(PolicyProposal).where(
            and_(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == status,
            )
        )

        if not include_synthetic:
            stmt = stmt.where(
                (PolicyProposal.is_synthetic == False)  # noqa: E712
                | (PolicyProposal.is_synthetic.is_(None))
            )

        if proposal_type:
            stmt = stmt.where(PolicyProposal.proposal_type == proposal_type)

        if days_old:
            cutoff = now - timedelta(days=days_old)
            stmt = stmt.where(PolicyProposal.created_at <= cutoff)

        # Count pending (for badge)
        count_stmt = (
            select(func.count())
            .select_from(PolicyProposal)
            .where(
                and_(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "draft",
                    (PolicyProposal.is_synthetic == False)  # noqa: E712
                    | (PolicyProposal.is_synthetic.is_(None)),
                )
            )
        )
        count_result = await self._session.execute(count_stmt)
        pending_count = count_result.scalar() or 0

        stmt = stmt.order_by(PolicyProposal.created_at.desc()).limit(limit).offset(
            offset
        )
        result = await self._session.execute(stmt)
        proposals = result.scalars().all()

        items = []
        for prop in proposals:
            created = prop.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_pending = (now - created).days

            feedback_ids = prop.triggering_feedback_ids or []
            feedback_count = len(feedback_ids) if isinstance(feedback_ids, list) else 0

            items.append(
                {
                    "id": str(prop.id),
                    "proposal_name": prop.proposal_name,
                    "proposal_type": prop.proposal_type,
                    "rationale": prop.rationale,
                    "proposed_rule": prop.proposed_rule or {},
                    "status": prop.status,
                    "created_at": prop.created_at,
                    "triggering_feedback_count": feedback_count,
                    "days_pending": days_pending,
                }
            )

        return items, pending_count

    async def fetch_proposal_by_id(
        self,
        tenant_id: str,
        proposal_id: str,
    ) -> Optional[dict]:
        """Fetch a single proposal by ID. Returns None if not found."""
        result = await self._session.execute(
            select(PolicyProposal).where(
                and_(
                    PolicyProposal.id == proposal_id,
                    PolicyProposal.tenant_id == tenant_id,
                )
            )
        )
        prop = result.scalar_one_or_none()

        if not prop:
            return None

        now = datetime.now(timezone.utc)
        created = prop.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_pending = (now - created).days

        feedback_ids = prop.triggering_feedback_ids or []
        feedback_count = len(feedback_ids) if isinstance(feedback_ids, list) else 0

        return {
            "id": str(prop.id),
            "proposal_name": prop.proposal_name,
            "proposal_type": prop.proposal_type,
            "rationale": prop.rationale,
            "proposed_rule": prop.proposed_rule or {},
            "status": prop.status,
            "created_at": prop.created_at,
            "reviewed_at": prop.reviewed_at,
            "reviewed_by": prop.reviewed_by,
            "review_notes": prop.review_notes,
            "effective_from": prop.effective_from,
            "triggering_feedback_count": feedback_count,
            "triggering_feedback_ids": feedback_ids,
            "days_pending": days_pending,
        }

    async def count_draft_proposals(
        self,
        tenant_id: str,
    ) -> int:
        """Count draft proposals (for badge display)."""
        result = await self._session.execute(
            select(func.count())
            .select_from(PolicyProposal)
            .where(
                and_(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "draft",
                    (PolicyProposal.is_synthetic == False)  # noqa: E712
                    | (PolicyProposal.is_synthetic.is_(None)),
                )
            )
        )
        return result.scalar() or 0


def get_proposals_read_driver(session: AsyncSession) -> ProposalsReadDriver:
    """Factory function for ProposalsReadDriver."""
    return ProposalsReadDriver(session)


__all__ = [
    "ProposalsReadDriver",
    "get_proposals_read_driver",
]
