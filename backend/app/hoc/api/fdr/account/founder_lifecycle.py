# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Phase-9 Founder Lifecycle Endpoints
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: async
# Callers: Founder Console
# Allowed Imports: L4 (operation_registry, lifecycle)
# Forbidden Imports: L1, L5, L6
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)


"""
Phase-9 Founder Lifecycle Endpoints

Founder-only endpoints for tenant lifecycle management.
Routes through L4 operation registry (account.lifecycle.query/transition).

OFFBOARD-004: No customer-initiated offboarding mutations.
Only founders can trigger lifecycle transitions (suspend, resume, terminate).
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)

router = APIRouter(prefix="/fdr/lifecycle", tags=["founder", "lifecycle"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================


class LifecycleTransitionRequest(BaseModel):
    """Request body for lifecycle transitions."""

    tenant_id: str
    reason: str


class LifecycleStateResponse(BaseModel):
    """Response for lifecycle state queries."""

    tenant_id: str
    state: str
    allows_sdk_execution: bool
    allows_writes: bool
    allows_reads: bool
    allows_new_api_keys: bool
    allows_token_refresh: bool
    is_terminal: bool
    is_reversible: bool
    valid_transitions: list[str]


class LifecycleTransitionResponse(BaseModel):
    """Response for lifecycle transitions."""

    success: bool
    from_state: str
    to_state: str
    action: str
    error: Optional[str] = None


class LifecycleHistoryResponse(BaseModel):
    """Response for lifecycle history queries."""

    tenant_id: str
    history: list[dict]


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================


@router.get("/{tenant_id}", response_model=LifecycleStateResponse)
async def get_lifecycle_state(
    tenant_id: str,
    session: Session = Depends(get_sync_session_dep),
):
    """
    Get lifecycle state for a tenant.

    Returns current state and what operations are allowed.
    """
    registry = get_operation_registry()
    result = await registry.execute(
        "account.lifecycle.query",
        OperationContext(
            session=None,
            tenant_id=tenant_id,
            params={"sync_session": session},
        ),
    )

    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)

    data = result.data
    return LifecycleStateResponse(
        tenant_id=tenant_id,
        state=data["status"].upper(),
        allows_sdk_execution=data["allows_sdk"],
        allows_writes=data["allows_writes"],
        allows_reads=data["allows_reads"],
        allows_new_api_keys=data["allows_api_keys"],
        allows_token_refresh=data["allows_token_refresh"],
        is_terminal=data["is_terminal"],
        is_reversible=data["is_reversible"],
        valid_transitions=[s.upper() for s in data["valid_transitions"]],
    )


@router.get("/{tenant_id}/history", response_model=LifecycleHistoryResponse)
async def get_lifecycle_history(tenant_id: str):
    """
    Get lifecycle transition history for a tenant.

    Returns empty list — in-memory history removed.
    Transition audit records are in the audit log table.
    """
    return LifecycleHistoryResponse(
        tenant_id=tenant_id,
        history=[],
    )


# =============================================================================
# MUTATION ENDPOINTS
# =============================================================================


async def _do_transition(
    action: str,
    body: LifecycleTransitionRequest,
    request: Request,
    session: Session,
    error_label: str,
) -> LifecycleTransitionResponse:
    """Execute a lifecycle transition via L4 registry."""
    founder_id = getattr(request.state, "user_id", None) or "founder_unknown"

    registry = get_operation_registry()
    result = await registry.execute(
        "account.lifecycle.transition",
        OperationContext(
            session=None,
            tenant_id=body.tenant_id,
            params={
                "sync_session": session,
                "action": action,
                "reason": body.reason,
                "actor_id": founder_id,
                "actor_type": "FOUNDER",
            },
        ),
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail={"error": error_label, "message": result.error},
        )

    data = result.data
    if not data["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_label,
                "message": data["error"],
                "from_state": data["from_status"].upper(),
            },
        )

    return LifecycleTransitionResponse(
        success=True,
        from_state=data["from_status"].upper(),
        to_state=data["to_status"].upper(),
        action=data["action"],
    )


@router.post("/suspend", response_model=LifecycleTransitionResponse)
async def suspend_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
    session: Session = Depends(get_sync_session_dep),
):
    """Suspend a tenant. Transitions: ACTIVE -> SUSPENDED. Reversible."""
    return await _do_transition("suspend", body, request, session, "suspension_failed")


@router.post("/resume", response_model=LifecycleTransitionResponse)
async def resume_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
    session: Session = Depends(get_sync_session_dep),
):
    """Resume a suspended tenant. Transitions: SUSPENDED -> ACTIVE."""
    return await _do_transition("resume", body, request, session, "resume_failed")


@router.post("/terminate", response_model=LifecycleTransitionResponse)
async def terminate_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
    session: Session = Depends(get_sync_session_dep),
):
    """Terminate a tenant. IRREVERSIBLE (OFFBOARD-002)."""
    return await _do_transition("terminate", body, request, session, "termination_failed")


@router.post("/archive", response_model=LifecycleTransitionResponse)
async def archive_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
    session: Session = Depends(get_sync_session_dep),
):
    """Archive a terminated tenant. IRREVERSIBLE (terminal-terminal)."""
    return await _do_transition("archive", body, request, session, "archive_failed")


__all__ = ["router"]
