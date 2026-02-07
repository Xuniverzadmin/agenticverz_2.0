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

    # =========================================================================
    # PB-S4 API Endpoints Support (PIN-513 L2 Purity)
    # =========================================================================

    async def list_proposals_paginated(
        self,
        *,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        proposal_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Fetch paginated proposals with count and aggregation.

        Returns dict with:
            - total: int (total count with filters)
            - items: list[dict] (paginated results)
            - by_status: dict[str, int] (aggregation)
            - by_type: dict[str, int] (aggregation)
        """
        # Build base filter conditions
        conditions = []
        if tenant_id:
            conditions.append(PolicyProposal.tenant_id == tenant_id)
        if status:
            conditions.append(PolicyProposal.status == status)
        if proposal_type:
            conditions.append(PolicyProposal.proposal_type == proposal_type)

        where_clause = and_(*conditions) if conditions else True

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(PolicyProposal)
            .where(where_clause)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated items
        stmt = (
            select(PolicyProposal)
            .where(where_clause)
            .order_by(PolicyProposal.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        proposals = result.scalars().all()

        # Build items and aggregations
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        items = []

        for prop in proposals:
            # Aggregation
            by_status[prop.status] = by_status.get(prop.status, 0) + 1
            by_type[prop.proposal_type] = by_type.get(prop.proposal_type, 0) + 1

            feedback_ids = prop.triggering_feedback_ids or []
            feedback_count = len(feedback_ids) if isinstance(feedback_ids, list) else 0

            items.append(
                {
                    "id": str(prop.id),
                    "tenant_id": prop.tenant_id,
                    "proposal_name": prop.proposal_name,
                    "proposal_type": prop.proposal_type,
                    "status": prop.status,
                    "rationale": prop.rationale,
                    "created_at": prop.created_at,
                    "reviewed_at": prop.reviewed_at,
                    "reviewed_by": prop.reviewed_by,
                    "effective_from": prop.effective_from,
                    "provenance_count": feedback_count,
                }
            )

        return {
            "total": total,
            "items": items,
            "by_status": by_status,
            "by_type": by_type,
        }

    async def get_proposal_stats(
        self,
        *,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get aggregated statistics for proposals.

        Returns dict with:
            - total: int
            - by_status: dict[str, int]
            - by_type: dict[str, int]
            - reviewed: int
            - pending: int
            - approval_rate_percent: float
        """
        # Build filter
        conditions = []
        if tenant_id:
            conditions.append(PolicyProposal.tenant_id == tenant_id)
        where_clause = and_(*conditions) if conditions else True

        # Fetch all matching proposals for aggregation
        stmt = select(
            PolicyProposal.status,
            PolicyProposal.proposal_type,
        ).where(where_clause)
        result = await self._session.execute(stmt)
        records = result.all()

        # Aggregate
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for row in records:
            status_val, type_val = row
            by_status[status_val] = by_status.get(status_val, 0) + 1
            by_type[type_val] = by_type.get(type_val, 0) + 1

        total = len(records)
        approved = by_status.get("approved", 0)
        rejected = by_status.get("rejected", 0)
        reviewed = approved + rejected
        pending = by_status.get("draft", 0)
        approval_rate = (approved / reviewed * 100) if reviewed > 0 else 0

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "reviewed": reviewed,
            "pending": pending,
            "approval_rate_percent": round(approval_rate, 1),
        }

    async def get_proposal_detail(
        self,
        proposal_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get full proposal detail by ID.

        Returns None if not found.
        """
        result = await self._session.execute(
            select(PolicyProposal).where(PolicyProposal.id == proposal_id)
        )
        prop = result.scalar_one_or_none()

        if not prop:
            return None

        feedback_ids = prop.triggering_feedback_ids or []

        return {
            "id": str(prop.id),
            "tenant_id": prop.tenant_id,
            "proposal_name": prop.proposal_name,
            "proposal_type": prop.proposal_type,
            "status": prop.status,
            "rationale": prop.rationale,
            "proposed_rule": prop.proposed_rule or {},
            "triggering_feedback_ids": feedback_ids,
            "created_at": prop.created_at,
            "reviewed_at": prop.reviewed_at,
            "reviewed_by": prop.reviewed_by,
            "review_notes": prop.review_notes,
            "effective_from": prop.effective_from,
        }

    async def list_proposal_versions(
        self,
        proposal_id: str,
    ) -> list[dict[str, Any]]:
        """
        List all versions for a proposal.

        Returns list of version dicts, ordered by version DESC.
        """
        from app.models.policy import PolicyVersion

        result = await self._session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.proposal_id == proposal_id)
            .order_by(PolicyVersion.version.desc())
        )
        versions = result.scalars().all()

        return [
            {
                "id": str(v.id),
                "proposal_id": str(v.proposal_id),
                "version": v.version,
                "rule_snapshot": v.rule_snapshot or {},
                "created_at": v.created_at,
                "created_by": v.created_by,
                "change_reason": v.change_reason,
            }
            for v in versions
        ]


def get_proposals_read_driver(session: AsyncSession) -> ProposalsReadDriver:
    """Factory function for ProposalsReadDriver."""
    return ProposalsReadDriver(session)


__all__ = [
    "ProposalsReadDriver",
    "get_proposals_read_driver",
]
