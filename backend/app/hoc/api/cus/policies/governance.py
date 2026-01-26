# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Unified GOVERNANCE facade - L2 API for governance control operations
# Callers: Ops Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-090, GAP-091, GAP-092, GAP-095
# GOVERNANCE NOTE:
# This is the ONE facade for GOVERNANCE domain.
# All governance control data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Governance API (L2)

Provides governance control operations:
- POST /api/v1/governance/kill-switch (GAP-090)
- POST /api/v1/governance/mode (GAP-091)
- POST /api/v1/governance/resolve-conflict (GAP-092)
- GET /api/v1/governance/boot-status (GAP-095)
- GET /api/v1/governance/state

This is the ONLY facade for governance control operations.
All governance APIs flow through this router.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine import (migrated to HOC per SWEEP-03)
from app.hoc.cus.policies.L5_engines.governance_facade import (
    GovernanceFacade,
    GovernanceMode,
    get_governance_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/governance", tags=["Governance"])


# =============================================================================
# Request/Response Models
# =============================================================================


class KillSwitchRequest(BaseModel):
    """Request to toggle kill switch."""
    enabled: bool = Field(..., description="True to enable kill switch (disable governance)")
    reason: str = Field(..., description="Reason for the operation")


class ModeRequest(BaseModel):
    """Request to set governance mode."""
    mode: str = Field(..., description="Target mode: NORMAL, DEGRADED, or KILL")
    reason: str = Field(..., description="Reason for mode change")


class ConflictResolutionRequest(BaseModel):
    """Request to resolve a policy conflict."""
    conflict_id: str = Field(..., description="ID of the conflict to resolve")
    resolution: str = Field(..., description="Resolution strategy")
    notes: Optional[str] = Field(None, description="Optional resolution notes")


class GovernanceStateResponse(BaseModel):
    """Governance state response."""
    mode: str
    active: bool
    degraded_mode: bool
    last_changed: Optional[str]
    last_change_reason: Optional[str]
    last_change_actor: Optional[str]


class KillSwitchResponse(BaseModel):
    """Kill switch operation response."""
    success: bool
    previous_mode: str
    current_mode: str
    timestamp: str
    actor: str
    reason: Optional[str]
    error: Optional[str]


class BootStatusResponse(BaseModel):
    """Boot status response."""
    healthy: bool
    components: Dict[str, Any]
    boot_time: Optional[str]
    uptime_seconds: Optional[int]


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> GovernanceFacade:
    """Get the governance facade."""
    return get_governance_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/state", response_model=Dict[str, Any])
async def get_governance_state(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
):
    """
    Get current governance state.

    Returns the current governance mode, whether enforcement is active,
    and details about the last state change.
    """
    state = facade.get_governance_state()
    return wrap_dict(state.to_dict())


@router.post("/kill-switch", response_model=Dict[str, Any])
async def toggle_kill_switch(
    request: KillSwitchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("governance.kill_switch")),
):
    """
    Toggle the governance kill switch (GAP-090).

    **Tier: REACT ($9)** - Emergency governance control.

    WARNING: Enabling the kill switch disables ALL governance enforcement.
    This is an emergency operation for incident response only.

    - enabled=true: Disable governance (emergency kill switch ON)
    - enabled=false: Re-enable governance (kill switch OFF)
    """
    actor = ctx.user_id or "system"

    if request.enabled:
        result = facade.enable_kill_switch(
            reason=request.reason,
            actor=actor,
        )
    else:
        result = facade.disable_kill_switch(actor=actor)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Kill switch operation failed: {result.error}",
        )

    return wrap_dict(result.to_dict())


@router.post("/mode", response_model=Dict[str, Any])
async def set_governance_mode(
    request: ModeRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("governance.mode")),
):
    """
    Set governance mode (GAP-091).

    **Tier: REACT ($9)** - Emergency governance control.

    Modes:
    - NORMAL: Full governance enforcement
    - DEGRADED: Limited enforcement, new runs blocked
    - KILL: All governance disabled (emergency)
    """
    try:
        mode = GovernanceMode(request.mode.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Valid modes: NORMAL, DEGRADED, KILL",
        )

    actor = ctx.user_id or "system"

    result = facade.set_mode(
        mode=mode,
        reason=request.reason,
        actor=actor,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Mode change failed: {result.error}",
        )

    return wrap_dict(result.to_dict())


@router.post("/resolve-conflict", response_model=Dict[str, Any])
async def resolve_conflict(
    request: ConflictResolutionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("governance.resolve_conflict")),
):
    """
    Manually resolve a policy conflict (GAP-092).

    **Tier: PREVENT ($199)** - Policy management.

    Resolution strategies:
    - accept_first: Accept the first policy in the conflict
    - accept_second: Accept the second policy in the conflict
    - merge: Attempt to merge conflicting policies
    - defer: Defer resolution to later
    """
    actor = ctx.user_id or "system"

    result = facade.resolve_conflict(
        conflict_id=request.conflict_id,
        resolution=request.resolution,
        actor=actor,
        notes=request.notes,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Conflict resolution failed: {result.error}",
        )

    return wrap_dict(result.to_dict())


@router.get("/conflicts", response_model=Dict[str, Any])
async def list_conflicts(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="Filter by status"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("governance.read")),
):
    """
    List policy conflicts.

    Returns pending and resolved policy conflicts.
    """
    conflicts = facade.list_conflicts(
        tenant_id=tenant_id,
        status=status,
    )

    return wrap_dict({
        "conflicts": conflicts,
        "total": len(conflicts),
    })


@router.get("/boot-status", response_model=Dict[str, Any])
async def get_boot_status(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: GovernanceFacade = Depends(get_facade),
):
    """
    Get SPINE component health status (GAP-095).

    Returns health status of core governance components:
    - governance: Kill switch state
    - policy_engine: Policy evaluation engine
    - audit_store: Audit event storage
    - policy_facade: Policy facade availability
    """
    status = facade.get_boot_status()
    return wrap_dict(status.to_dict())
