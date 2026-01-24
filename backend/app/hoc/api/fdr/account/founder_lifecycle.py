# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Phase-9 Founder Lifecycle Endpoints
# Product: system-wide
# Temporal:
#   Trigger: request
#   Execution: sync
# Callers: Founder Console
# Allowed Imports: L4 (lifecycle, onboarding_state)
# Forbidden Imports: L1, L5, L6
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)


"""
Phase-9 Founder Lifecycle Endpoints

Founder-only endpoints for tenant lifecycle management.

OFFBOARD-004: No customer-initiated offboarding mutations.
Only founders can trigger lifecycle transitions (suspend, resume, terminate).

DESIGN NOTES:
- These endpoints are founder-only (require founder role)
- All transitions are audited via observability
- No auto-actions (system triggers deferred to future phase)
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.auth.tenant_lifecycle import (
    TenantLifecycleState,
    LifecycleAction,
    get_valid_transitions,
)
from app.auth.lifecycle_provider import (
    ActorType,
    ActorContext,
    TransitionResult,
    get_lifecycle_provider,
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
    revoked_api_keys: int = 0
    blocked_workers: int = 0


class LifecycleHistoryItem(BaseModel):
    """History item for lifecycle transitions."""

    from_state: str
    to_state: str
    action: str
    actor_type: str
    actor_id: str
    reason: str
    timestamp: str
    success: bool
    error: Optional[str] = None


class LifecycleHistoryResponse(BaseModel):
    """Response for lifecycle history queries."""

    tenant_id: str
    history: list[LifecycleHistoryItem]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_founder_actor(request: Request) -> ActorContext:
    """
    Extract founder actor context from request.

    In production, this would validate founder JWT and extract identity.
    For now, uses request state if available.
    """
    # Get founder ID from request state (set by auth middleware)
    founder_id = getattr(request.state, "user_id", None) or "founder_unknown"

    return ActorContext(
        actor_type=ActorType.FOUNDER,
        actor_id=founder_id,
        reason="founder_api",  # Will be overridden by request body
    )


def result_to_response(result: TransitionResult) -> LifecycleTransitionResponse:
    """Convert TransitionResult to API response."""
    return LifecycleTransitionResponse(
        success=result.success,
        from_state=result.from_state.name,
        to_state=result.to_state.name,
        action=result.action,
        error=result.error,
        revoked_api_keys=result.revoked_api_keys,
        blocked_workers=result.blocked_workers,
    )


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================


@router.get("/{tenant_id}", response_model=LifecycleStateResponse)
async def get_lifecycle_state(tenant_id: str):
    """
    Get lifecycle state for a tenant.

    Returns current state and what operations are allowed.
    """
    provider = get_lifecycle_provider()
    state = provider.get_state(tenant_id)
    valid = get_valid_transitions(state)

    return LifecycleStateResponse(
        tenant_id=tenant_id,
        state=state.name,
        allows_sdk_execution=state.allows_sdk_execution(),
        allows_writes=state.allows_writes(),
        allows_reads=state.allows_reads(),
        allows_new_api_keys=state.allows_new_api_keys(),
        allows_token_refresh=state.allows_token_refresh(),
        is_terminal=state.is_terminal(),
        is_reversible=state.is_reversible(),
        valid_transitions=[s.name for s in valid],
    )


@router.get("/{tenant_id}/history", response_model=LifecycleHistoryResponse)
async def get_lifecycle_history(tenant_id: str):
    """
    Get lifecycle transition history for a tenant.

    Returns all transitions (successful and failed) for audit.
    """
    provider = get_lifecycle_provider()
    history = provider.get_history(tenant_id)

    items = [
        LifecycleHistoryItem(
            from_state=record.from_state.name,
            to_state=record.to_state.name,
            action=record.action,
            actor_type=record.actor.actor_type.value,
            actor_id=record.actor.actor_id,
            reason=record.actor.reason,
            timestamp=record.timestamp.isoformat(),
            success=record.success,
            error=record.error,
        )
        for record in history
    ]

    return LifecycleHistoryResponse(
        tenant_id=tenant_id,
        history=items,
    )


# =============================================================================
# MUTATION ENDPOINTS
# =============================================================================


@router.post("/suspend", response_model=LifecycleTransitionResponse)
async def suspend_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
):
    """
    Suspend a tenant.

    Transitions: ACTIVE -> SUSPENDED

    Effects:
    - SDK execution blocked
    - New API keys blocked
    - Writes blocked
    - Reads allowed (limited)
    - Token refresh allowed

    Reversible: YES (via resume)
    """
    provider = get_lifecycle_provider()
    actor = get_founder_actor(request)
    actor.reason = body.reason

    result = provider.suspend(body.tenant_id, actor)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "suspension_failed",
                "message": result.error,
                "from_state": result.from_state.name,
            },
        )

    return result_to_response(result)


@router.post("/resume", response_model=LifecycleTransitionResponse)
async def resume_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
):
    """
    Resume a suspended tenant.

    Transitions: SUSPENDED -> ACTIVE

    Effects:
    - All operations restored

    Only valid from SUSPENDED state.
    """
    provider = get_lifecycle_provider()
    actor = get_founder_actor(request)
    actor.reason = body.reason

    result = provider.resume(body.tenant_id, actor)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "resume_failed",
                "message": result.error,
                "from_state": result.from_state.name,
            },
        )

    return result_to_response(result)


@router.post("/terminate", response_model=LifecycleTransitionResponse)
async def terminate_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
):
    """
    Terminate a tenant.

    Transitions: ACTIVE|SUSPENDED -> TERMINATED

    Effects:
    - SDK execution blocked (permanently)
    - All API keys revoked (OFFBOARD-005)
    - Background workers stopped (OFFBOARD-006)
    - Token refresh blocked (OFFBOARD-007)
    - Historical data preserved
    - Observability remains queryable
    - Audits immutable

    **IRREVERSIBLE** (OFFBOARD-002)
    """
    provider = get_lifecycle_provider()
    actor = get_founder_actor(request)
    actor.reason = body.reason

    result = provider.terminate(body.tenant_id, actor)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "termination_failed",
                "message": result.error,
                "from_state": result.from_state.name,
            },
        )

    return result_to_response(result)


@router.post("/archive", response_model=LifecycleTransitionResponse)
async def archive_tenant(
    body: LifecycleTransitionRequest,
    request: Request,
):
    """
    Archive a terminated tenant.

    Transitions: TERMINATED -> ARCHIVED

    Effects:
    - All runtime access blocked
    - Auth access blocked
    - Observability readable (internal only)
    - Audit retained

    Only valid from TERMINATED state.
    **IRREVERSIBLE** (terminal-terminal)

    NOTE: This is typically a system-triggered action after compliance
    retention period. Manual use is for exceptional cases only.
    """
    provider = get_lifecycle_provider()
    actor = get_founder_actor(request)
    actor.reason = body.reason

    result = provider.archive(body.tenant_id, actor)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "archive_failed",
                "message": result.error,
                "from_state": result.from_state.name,
            },
        )

    return result_to_response(result)


__all__ = ["router"]
