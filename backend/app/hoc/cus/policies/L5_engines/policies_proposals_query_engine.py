# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_proposals (via driver)
#   Writes: none
# Role: Proposals query engine - read-only operations for policy proposals list
# Callers: L2 policies API
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Proposals Query Engine (L5)

Read-only query operations for policy proposals (list view).
Provides list, get detail, and draft counts.

Note: This engine is for the "Proposals" tab UI.
For proposal lifecycle operations (create, approve, reject),
see policy_proposal_engine.py.

Invariant: This engine is READ-ONLY. No writes. No state mutation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.hoc.cus.policies.L6_drivers.proposals_read_driver import (
    ProposalsReadDriver,
    get_proposals_read_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class PolicyRequestResult:
    """Pending policy request summary (ACT-O3)."""

    id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict[str, Any]
    status: str
    created_at: datetime
    triggering_feedback_count: int
    days_pending: int


@dataclass
class PolicyRequestsListResult:
    """Policy requests list response."""

    items: list[PolicyRequestResult]
    total: int
    pending_count: int
    filters_applied: dict[str, Any]


@dataclass
class PolicyRequestDetailResult:
    """Policy request detail response."""

    id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict[str, Any]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    review_notes: Optional[str]
    effective_from: Optional[datetime]
    triggering_feedback_count: int
    triggering_feedback_ids: list[str]
    days_pending: int


# =============================================================================
# Query Engine
# =============================================================================


class ProposalsQueryEngine:
    """
    L5 Query Engine for policy proposals.

    Provides read-only operations:
    - List proposals with filters
    - Get proposal detail
    - Count draft proposals

    All data access is delegated to L6 driver.
    """

    def __init__(self, driver: ProposalsReadDriver):
        self._driver = driver

    async def list_policy_requests(
        self,
        tenant_id: str,
        *,
        status: str = "draft",
        proposal_type: Optional[str] = None,
        days_old: Optional[int] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> PolicyRequestsListResult:
        """List pending policy requests."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id, "status": status}

        if proposal_type:
            filters_applied["proposal_type"] = proposal_type
        if days_old:
            filters_applied["days_old"] = days_old
        if include_synthetic:
            filters_applied["include_synthetic"] = True

        # Fetch from driver
        rows, pending_count = await self._driver.fetch_proposals(
            tenant_id=tenant_id,
            status=status,
            proposal_type=proposal_type,
            days_old=days_old,
            include_synthetic=include_synthetic,
            limit=limit,
            offset=offset,
        )

        # Transform to result objects
        items = [
            PolicyRequestResult(
                id=row["id"],
                proposal_name=row["proposal_name"],
                proposal_type=row["proposal_type"],
                rationale=row["rationale"],
                proposed_rule=row["proposed_rule"],
                status=row["status"],
                created_at=row["created_at"],
                triggering_feedback_count=row["triggering_feedback_count"],
                days_pending=row["days_pending"],
            )
            for row in rows
        ]

        return PolicyRequestsListResult(
            items=items,
            total=len(items),
            pending_count=pending_count,
            filters_applied=filters_applied,
        )

    async def get_policy_request_detail(
        self,
        tenant_id: str,
        proposal_id: str,
    ) -> Optional[PolicyRequestDetailResult]:
        """Get policy request detail. Tenant isolation enforced."""
        row = await self._driver.fetch_proposal_by_id(tenant_id, proposal_id)

        if not row:
            return None

        return PolicyRequestDetailResult(
            id=row["id"],
            proposal_name=row["proposal_name"],
            proposal_type=row["proposal_type"],
            rationale=row["rationale"],
            proposed_rule=row["proposed_rule"],
            status=row["status"],
            created_at=row["created_at"],
            reviewed_at=row["reviewed_at"],
            reviewed_by=row["reviewed_by"],
            review_notes=row["review_notes"],
            effective_from=row["effective_from"],
            triggering_feedback_count=row["triggering_feedback_count"],
            triggering_feedback_ids=row["triggering_feedback_ids"],
            days_pending=row["days_pending"],
        )

    async def count_drafts(
        self,
        tenant_id: str,
    ) -> int:
        """Count draft proposals for badge display."""
        return await self._driver.count_draft_proposals(tenant_id)


# =============================================================================
# Factory
# =============================================================================


def get_proposals_query_engine(session: "AsyncSession") -> ProposalsQueryEngine:
    """Get a ProposalsQueryEngine instance."""
    return ProposalsQueryEngine(
        driver=get_proposals_read_driver(session),
    )


__all__ = [
    # Engine
    "ProposalsQueryEngine",
    "get_proposals_query_engine",
    # Result types
    "PolicyRequestResult",
    "PolicyRequestsListResult",
    "PolicyRequestDetailResult",
]
