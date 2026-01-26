# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: pattern_feedback, policy_proposals, policy_versions
#   Writes: none
# Role: Read operations for policy proposal engine
# Callers: L5 policy_proposal_engine
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Policy Proposal Read Driver (L6)

Pure data access layer for policy proposal read operations.
No business logic - only query execution and data retrieval.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import PatternFeedback
from app.models.policy import PolicyProposal, PolicyVersion


class PolicyProposalReadDriver:
    """Read operations for policy proposals."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_unacknowledged_feedback(
        self,
        tenant_id: Optional[UUID] = None,
        feedback_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch unacknowledged pattern feedback records.

        Returns list of dicts with: id, tenant_id, pattern_type, signature
        """
        query = select(PatternFeedback).where(
            PatternFeedback.acknowledged == False  # noqa: E712
        )

        if tenant_id:
            query = query.where(PatternFeedback.tenant_id == str(tenant_id))
        if feedback_type:
            query = query.where(PatternFeedback.pattern_type == feedback_type)

        result = await self._session.execute(query)
        records = result.scalars().all()

        return [
            {
                "id": str(fb.id),
                "tenant_id": str(fb.tenant_id),
                "pattern_type": fb.pattern_type,
                "signature": fb.signature,
            }
            for fb in records
        ]

    async def fetch_proposal_by_id(
        self,
        proposal_id: UUID,
    ) -> Optional[dict]:
        """Fetch a proposal by ID. Returns None if not found."""
        result = await self._session.execute(
            select(PolicyProposal).where(PolicyProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()

        if not proposal:
            return None

        return {
            "id": str(proposal.id),
            "tenant_id": str(proposal.tenant_id),
            "proposal_name": proposal.proposal_name,
            "proposal_type": proposal.proposal_type,
            "rationale": proposal.rationale,
            "proposed_rule": proposal.proposed_rule,
            "triggering_feedback_ids": proposal.triggering_feedback_ids,
            "status": proposal.status,
            "created_at": proposal.created_at,
            "reviewed_at": proposal.reviewed_at,
            "reviewed_by": proposal.reviewed_by,
            "review_notes": proposal.review_notes,
            "effective_from": proposal.effective_from,
            "is_synthetic": getattr(proposal, "is_synthetic", False),
            "synthetic_scenario_id": getattr(proposal, "synthetic_scenario_id", None),
        }

    async def fetch_proposal_status(
        self,
        proposal_id: UUID,
    ) -> Optional[str]:
        """Fetch just the status of a proposal."""
        result = await self._session.execute(
            select(PolicyProposal.status).where(PolicyProposal.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def count_versions_for_proposal(
        self,
        proposal_id: UUID,
    ) -> int:
        """Count existing versions for a proposal."""
        result = await self._session.execute(
            select(func.count())
            .select_from(PolicyVersion)
            .where(PolicyVersion.proposal_id == proposal_id)
        )
        return result.scalar() or 0

    async def fetch_proposals(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch proposals with optional filters."""
        query = select(PolicyProposal).order_by(PolicyProposal.created_at.desc())

        if tenant_id:
            query = query.where(PolicyProposal.tenant_id == str(tenant_id))
        if status:
            query = query.where(PolicyProposal.status == status)

        query = query.limit(limit)

        result = await self._session.execute(query)
        proposals = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "tenant_id": str(p.tenant_id),
                "proposal_name": p.proposal_name,
                "proposal_type": p.proposal_type,
                "rationale": p.rationale,
                "status": p.status,
                "created_at": p.created_at,
                "reviewed_at": p.reviewed_at,
                "reviewed_by": p.reviewed_by,
                "effective_from": p.effective_from,
                "triggering_feedback_ids": p.triggering_feedback_ids,
            }
            for p in proposals
        ]

    async def check_rule_exists(
        self,
        rule_id: str,
    ) -> bool:
        """Check if a policy rule exists by ID."""
        result = await self._session.execute(
            text("SELECT id FROM policy_rules WHERE id = :rule_id"),
            {"rule_id": rule_id},
        )
        return result.scalar_one_or_none() is not None

    async def fetch_rule_by_id(
        self,
        rule_id: str,
        tenant_id: str,
    ) -> Optional[dict]:
        """Fetch a policy rule by ID with tenant check."""
        result = await self._session.execute(
            text("""
                SELECT id, name FROM policy_rules
                WHERE id = :rule_id AND tenant_id = :tenant_id
            """),
            {"rule_id": rule_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {"id": row[0], "name": row[1]}


def get_policy_proposal_read_driver(session: AsyncSession) -> PolicyProposalReadDriver:
    """Factory function for PolicyProposalReadDriver."""
    return PolicyProposalReadDriver(session)


__all__ = [
    "PolicyProposalReadDriver",
    "get_policy_proposal_read_driver",
]
