"""
PB-S4 Policy Proposals API

Exposes policy_proposals and policy_versions data with human-controlled approval.

PB-S4 Contract:
- Policies are proposed, never auto-enforced
- Human approval is mandatory
- Proposals have provenance to triggering feedback
- Rejection preserved for audit trail

O1: API endpoint exists ✓
O2: List visible with pagination ✓
O3: Detail accessible ✓
O4: Approve/Reject actions (human-controlled) ✓ (PIN-373)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select

from ..auth.gateway_middleware import get_auth_context
from ..auth.role_guard import require_role
from ..auth.tenant_roles import TenantRole
from ..db import get_async_session
from ..models.policy import PolicyApprovalRequest, PolicyProposal, PolicyVersion
from ..schemas.response import wrap_dict
from app.hoc.cus.policies.L5_engines.policy_proposal_engine import review_policy_proposal

logger = logging.getLogger("nova.api.policy_proposals")

router = APIRouter(prefix="/api/v1/policy-proposals", tags=["policy-proposals", "pb-s4"])


# =============================================================================
# Response Models
# =============================================================================


class ProposalSummaryResponse(BaseModel):
    """Summary of a policy proposal."""

    id: str
    tenant_id: str
    proposal_name: str
    proposal_type: str
    status: str
    rationale: str
    created_at: Optional[str]
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]
    effective_from: Optional[str]
    provenance_count: int


class ProposalListResponse(BaseModel):
    """Paginated list of policy proposals."""

    total: int
    limit: int
    offset: int
    by_status: dict
    by_type: dict
    items: list[ProposalSummaryResponse]


class ProposalDetailResponse(BaseModel):
    """Detailed policy proposal record."""

    id: str
    tenant_id: str
    proposal_name: str
    proposal_type: str
    status: str
    rationale: str
    proposed_rule: dict
    triggering_feedback_ids: list
    created_at: Optional[str]
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]
    review_notes: Optional[str]
    effective_from: Optional[str]
    versions: list[dict]


class VersionResponse(BaseModel):
    """Policy version record."""

    id: str
    proposal_id: str
    version: int
    rule_snapshot: dict
    created_at: Optional[str]
    created_by: Optional[str]
    change_reason: Optional[str]


# =============================================================================
# READ-ONLY Endpoints (No POST/PUT/DELETE)
# =============================================================================


@router.get("", response_model=ProposalListResponse)
async def list_proposals(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="Filter by status (draft/approved/rejected)"),
    proposal_type: Optional[str] = Query(None, description="Filter by proposal type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List policy proposals (PB-S4).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    """
    async with get_async_session() as session:
        # Build query
        query = select(PolicyProposal).order_by(PolicyProposal.created_at.desc())

        if tenant_id:
            query = query.where(PolicyProposal.tenant_id == tenant_id)
        if status:
            query = query.where(PolicyProposal.status == status)
        if proposal_type:
            query = query.where(PolicyProposal.proposal_type == proposal_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate by status and type
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for r in records:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_type[r.proposal_type] = by_type.get(r.proposal_type, 0) + 1

        items = [
            ProposalSummaryResponse(
                id=str(r.id),
                tenant_id=r.tenant_id,
                proposal_name=r.proposal_name,
                proposal_type=r.proposal_type,
                status=r.status,
                rationale=r.rationale[:200] if r.rationale else "",
                created_at=r.created_at.isoformat() if r.created_at else None,
                reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
                reviewed_by=r.reviewed_by,
                effective_from=r.effective_from.isoformat() if r.effective_from else None,
                provenance_count=len(r.triggering_feedback_ids) if r.triggering_feedback_ids else 0,
            )
            for r in records
        ]

        return ProposalListResponse(
            total=total,
            limit=limit,
            offset=offset,
            by_status=by_status,
            by_type=by_type,
            items=items,
        )


@router.get("/stats/summary")
async def get_proposal_stats(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
):
    """
    Get policy proposal statistics (PB-S4).

    READ-ONLY: This endpoint only reads aggregated data.
    No execution data is modified by this query.
    """
    async with get_async_session() as session:
        # Base query
        query = select(PolicyProposal)
        if tenant_id:
            query = query.where(PolicyProposal.tenant_id == tenant_id)

        result = await session.execute(query)
        records = result.scalars().all()

        # Aggregate stats
        total = len(records)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for r in records:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_type[r.proposal_type] = by_type.get(r.proposal_type, 0) + 1

        # Approval rate
        approved = by_status.get("approved", 0)
        rejected = by_status.get("rejected", 0)
        reviewed = approved + rejected
        approval_rate = (approved / reviewed * 100) if reviewed > 0 else 0

        return wrap_dict({
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "reviewed": reviewed,
            "pending": by_status.get("draft", 0),
            "approval_rate_percent": round(approval_rate, 1),
            "read_only": True,
            "pb_s4_compliant": True,
        })


@router.get("/{proposal_id}", response_model=ProposalDetailResponse)
async def get_proposal(
    request: Request,
    proposal_id: str,
):
    """
    Get detailed policy proposal by ID (PB-S4).

    READ-ONLY: This endpoint only reads data.
    No execution data is modified by this query.
    """
    try:
        proposal_uuid = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    async with get_async_session() as session:
        # Get proposal
        result = await session.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_uuid))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

        # Get versions
        versions_result = await session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.proposal_id == proposal_uuid)
            .order_by(PolicyVersion.version.desc())
        )
        versions = versions_result.scalars().all()

        return ProposalDetailResponse(
            id=str(record.id),
            tenant_id=record.tenant_id,
            proposal_name=record.proposal_name,
            proposal_type=record.proposal_type,
            status=record.status,
            rationale=record.rationale,
            proposed_rule=record.proposed_rule or {},
            triggering_feedback_ids=record.triggering_feedback_ids or [],
            created_at=record.created_at.isoformat() if record.created_at else None,
            reviewed_at=record.reviewed_at.isoformat() if record.reviewed_at else None,
            reviewed_by=record.reviewed_by,
            review_notes=record.review_notes,
            effective_from=record.effective_from.isoformat() if record.effective_from else None,
            versions=[
                {
                    "id": str(v.id),
                    "version": v.version,
                    "rule_snapshot": v.rule_snapshot or {},
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "created_by": v.created_by,
                    "change_reason": v.change_reason,
                }
                for v in versions
            ],
        )


@router.get("/{proposal_id}/versions", response_model=list[VersionResponse])
async def list_proposal_versions(
    request: Request,
    proposal_id: str,
):
    """
    List all versions of a policy proposal (PB-S4).

    READ-ONLY: This endpoint only reads data.
    Shows the evolution of a policy through approvals.
    """
    try:
        proposal_uuid = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    async with get_async_session() as session:
        result = await session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.proposal_id == proposal_uuid)
            .order_by(PolicyVersion.version.desc())
        )
        versions = result.scalars().all()

        return [
            VersionResponse(
                id=str(v.id),
                proposal_id=str(v.proposal_id),
                version=v.version,
                rule_snapshot=v.rule_snapshot or {},
                created_at=v.created_at.isoformat() if v.created_at else None,
                created_by=v.created_by,
                change_reason=v.change_reason,
            )
            for v in versions
        ]


# =============================================================================
# Human-Controlled Actions (PIN-373: Policy Lifecycle Completion)
# =============================================================================


class ApproveRejectRequest(BaseModel):
    """Request body for approve/reject actions."""

    reviewed_by: str
    review_notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response for approve/reject actions."""

    proposal_id: str
    status: str
    reviewed_by: str
    reviewed_at: Optional[str]
    message: str


@router.post("/{proposal_id}/approve", response_model=ApprovalResponse)
async def approve_proposal(
    http_request: Request,
    proposal_id: str,
    request: ApproveRejectRequest,
    role: TenantRole = Depends(require_role(TenantRole.MEMBER, TenantRole.ADMIN, TenantRole.OWNER)),
):
    """
    Approve a policy proposal (PIN-373).

    HUMAN ACTION: This creates a policy_rules entry when approved.
    Only draft proposals can be approved.

    PB-S4 Contract: Human approval is mandatory - system cannot auto-approve.
    """
    try:
        proposal_uuid = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    try:
        async with get_async_session() as session:
            approval_request = PolicyApprovalRequest(
                action="approve",
                reviewed_by=request.reviewed_by,
                review_notes=request.review_notes,
            )

            updated_proposal = await review_policy_proposal(
                session, proposal_uuid, approval_request
            )
            await session.commit()

            logger.info(
                "proposal_approved_via_api",
                extra={
                    "proposal_id": proposal_id,
                    "reviewed_by": request.reviewed_by,
                },
            )

            return ApprovalResponse(
                proposal_id=str(updated_proposal.id),
                status=updated_proposal.status,
                reviewed_by=updated_proposal.reviewed_by or "",
                reviewed_at=updated_proposal.reviewed_at.isoformat() if updated_proposal.reviewed_at else None,
                message="Proposal approved successfully",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error approving proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{proposal_id}/reject", response_model=ApprovalResponse)
async def reject_proposal(
    http_request: Request,
    proposal_id: str,
    request: ApproveRejectRequest,
    role: TenantRole = Depends(require_role(TenantRole.MEMBER, TenantRole.ADMIN, TenantRole.OWNER)),
):
    """
    Reject a policy proposal (PIN-373).

    HUMAN ACTION: This marks the proposal as rejected.
    Rejection is preserved for audit trail.
    Only draft proposals can be rejected.

    PB-S4 Contract: Human decision is mandatory - system cannot auto-reject.
    """
    try:
        proposal_uuid = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    try:
        async with get_async_session() as session:
            approval_request = PolicyApprovalRequest(
                action="reject",
                reviewed_by=request.reviewed_by,
                review_notes=request.review_notes,
            )

            updated_proposal = await review_policy_proposal(
                session, proposal_uuid, approval_request
            )
            await session.commit()

            logger.info(
                "proposal_rejected_via_api",
                extra={
                    "proposal_id": proposal_id,
                    "reviewed_by": request.reviewed_by,
                    "reason": request.review_notes,
                },
            )

            return ApprovalResponse(
                proposal_id=str(updated_proposal.id),
                status=updated_proposal.status,
                reviewed_by=updated_proposal.reviewed_by or "",
                reviewed_at=updated_proposal.reviewed_at.isoformat() if updated_proposal.reviewed_at else None,
                message="Proposal rejected",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error rejecting proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
