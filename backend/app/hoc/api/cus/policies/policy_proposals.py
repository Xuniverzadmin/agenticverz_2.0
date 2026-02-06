# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Policy Proposals API (PB-S4)
# Callers: Customer Console
# Allowed Imports: L4 (registry dispatch only)
# Forbidden Imports: L1, sqlalchemy, session.execute
# Reference: PB-S4, PIN-373, PIN-513 (L2 Purity)
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

PIN-513 L2 Purity:
- All DB operations routed through L4 registry → L5 engine → L6 driver
- Zero session.execute() calls in L2
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.auth.role_guard import require_role
from app.auth.tenant_roles import TenantRole
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_async_session_context,
    get_operation_registry,
)
from app.schemas.response import wrap_dict
# NOTE: PolicyApprovalRequest and review_policy_proposal now routed through L4 handler

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
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "policies.proposals_query",
            OperationContext(
                session=session,
                tenant_id=tenant_id or "",
                params={
                    "method": "list_proposals_paginated",
                    "tenant_id": tenant_id,
                    "status": status,
                    "proposal_type": proposal_type,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        data = result.data
        records = data["items"]

        items = [
            ProposalSummaryResponse(
                id=r["id"],
                tenant_id=r["tenant_id"],
                proposal_name=r["proposal_name"],
                proposal_type=r["proposal_type"],
                status=r["status"],
                rationale=r["rationale"][:200] if r["rationale"] else "",
                created_at=r["created_at"].isoformat() if r["created_at"] else None,
                reviewed_at=r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
                reviewed_by=r["reviewed_by"],
                effective_from=r["effective_from"].isoformat() if r["effective_from"] else None,
                provenance_count=r["provenance_count"],
            )
            for r in records
        ]

        return ProposalListResponse(
            total=data["total"],
            limit=limit,
            offset=offset,
            by_status=data["by_status"],
            by_type=data["by_type"],
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
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "policies.proposals_query",
            OperationContext(
                session=session,
                tenant_id=tenant_id or "",
                params={
                    "method": "get_proposal_stats",
                    "tenant_id": tenant_id,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        data = result.data
        return wrap_dict({
            "total": data["total"],
            "by_status": data["by_status"],
            "by_type": data["by_type"],
            "reviewed": data["reviewed"],
            "pending": data["pending"],
            "approval_rate_percent": data["approval_rate_percent"],
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

    async with get_async_session_context() as session:
        registry = get_operation_registry()

        # Get proposal detail
        result = await registry.execute(
            "policies.proposals_query",
            OperationContext(
                session=session,
                tenant_id="",
                params={
                    "method": "get_proposal_detail",
                    "proposal_id": str(proposal_uuid),
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        record = result.data
        if not record:
            raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

        # Get versions
        versions_result = await registry.execute(
            "policies.proposals_query",
            OperationContext(
                session=session,
                tenant_id="",
                params={
                    "method": "list_proposal_versions",
                    "proposal_id": str(proposal_uuid),
                },
            ),
        )

        if not versions_result.success:
            raise HTTPException(status_code=500, detail=versions_result.error)

        versions = versions_result.data or []

        return ProposalDetailResponse(
            id=record["id"],
            tenant_id=record["tenant_id"],
            proposal_name=record["proposal_name"],
            proposal_type=record["proposal_type"],
            status=record["status"],
            rationale=record["rationale"],
            proposed_rule=record["proposed_rule"] or {},
            triggering_feedback_ids=record["triggering_feedback_ids"] or [],
            created_at=record["created_at"].isoformat() if record["created_at"] else None,
            reviewed_at=record["reviewed_at"].isoformat() if record["reviewed_at"] else None,
            reviewed_by=record["reviewed_by"],
            review_notes=record["review_notes"],
            effective_from=record["effective_from"].isoformat() if record["effective_from"] else None,
            versions=[
                {
                    "id": v["id"],
                    "version": v["version"],
                    "rule_snapshot": v["rule_snapshot"] or {},
                    "created_at": v["created_at"].isoformat() if v["created_at"] else None,
                    "created_by": v["created_by"],
                    "change_reason": v["change_reason"],
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

    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "policies.proposals_query",
            OperationContext(
                session=session,
                tenant_id="",
                params={
                    "method": "list_proposal_versions",
                    "proposal_id": str(proposal_uuid),
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        versions = result.data or []

        return [
            VersionResponse(
                id=v["id"],
                proposal_id=v["proposal_id"],
                version=v["version"],
                rule_snapshot=v["rule_snapshot"] or {},
                created_at=v["created_at"].isoformat() if v["created_at"] else None,
                created_by=v["created_by"],
                change_reason=v["change_reason"],
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
        async with get_async_session_context() as session:
            # Route through L4 handler which owns transaction boundary (PIN-L2-PURITY)
            registry = get_operation_registry()
            result = await registry.execute(
                "policies.approval",
                OperationContext(
                    session=session,
                    tenant_id="",
                    params={
                        "method": "review_proposal",
                        "proposal_id": proposal_id,
                        "action": "approve",
                        "reviewed_by": request.reviewed_by,
                        "review_notes": request.review_notes,
                    },
                ),
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            data = result.data

            logger.info(
                "proposal_approved_via_api",
                extra={
                    "proposal_id": proposal_id,
                    "reviewed_by": request.reviewed_by,
                    "client_host": http_request.client.host if http_request.client else None,
                },
            )

            return ApprovalResponse(
                proposal_id=data["id"],
                status=data["status"],
                reviewed_by=data["reviewed_by"] or "",
                reviewed_at=data["reviewed_at"],
                message="Proposal approved successfully",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
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
        async with get_async_session_context() as session:
            # Route through L4 handler which owns transaction boundary (PIN-L2-PURITY)
            registry = get_operation_registry()
            result = await registry.execute(
                "policies.approval",
                OperationContext(
                    session=session,
                    tenant_id="",
                    params={
                        "method": "review_proposal",
                        "proposal_id": proposal_id,
                        "action": "reject",
                        "reviewed_by": request.reviewed_by,
                        "review_notes": request.review_notes,
                    },
                ),
            )

            if not result.success:
                raise HTTPException(status_code=500, detail=result.error)

            data = result.data

            logger.info(
                "proposal_rejected_via_api",
                extra={
                    "proposal_id": proposal_id,
                    "reviewed_by": request.reviewed_by,
                    "reason": request.review_notes,
                    "client_host": http_request.client.host if http_request.client else None,
                },
            )

            return ApprovalResponse(
                proposal_id=data["id"],
                status=data["status"],
                reviewed_by=data["reviewed_by"] or "",
                reviewed_at=data["reviewed_at"],
                message="Proposal rejected",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error rejecting proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
