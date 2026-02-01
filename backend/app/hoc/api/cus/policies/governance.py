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
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
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



# =============================================================================
# Endpoints
# =============================================================================


@router.get("/state", response_model=Dict[str, Any])
async def get_governance_state(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get current governance state.

    Returns the current governance mode, whether enforcement is active,
    and details about the last state change.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_governance_state"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)


@router.post("/kill-switch", response_model=Dict[str, Any])
async def toggle_kill_switch(
    request: KillSwitchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
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
    method = "enable_kill_switch" if request.enabled else "disable_kill_switch"
    params = {"method": method, "actor": actor}
    if request.enabled:
        params["reason"] = request.reason

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params=params,
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)


@router.post("/mode", response_model=Dict[str, Any])
async def set_governance_mode(
    request: ModeRequest,
    ctx: TenantContext = Depends(get_tenant_context),
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
    # Validate mode string before dispatch
    valid_modes = {"NORMAL", "DEGRADED", "KILL"}
    mode_str = request.mode.upper()
    if mode_str not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Valid modes: NORMAL, DEGRADED, KILL",
        )

    actor = ctx.user_id or "system"

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "set_mode",
                "mode": mode_str,
                "reason": request.reason,
                "actor": actor,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)


@router.post("/resolve-conflict", response_model=Dict[str, Any])
async def resolve_conflict(
    request: ConflictResolutionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
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

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "resolve_conflict",
                "conflict_id": request.conflict_id,
                "resolution": request.resolution,
                "actor": actor,
                "notes": request.notes,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)


@router.get("/conflicts", response_model=Dict[str, Any])
async def list_conflicts(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    status: Optional[str] = Query(None, description="Filter by status"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("governance.read")),
):
    """
    List policy conflicts.

    Returns pending and resolved policy conflicts.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_conflicts",
                "tenant_id": tenant_id,
                "status": status,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)


@router.get("/boot-status", response_model=Dict[str, Any])
async def get_boot_status(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get SPINE component health status (GAP-095).

    Returns health status of core governance components:
    - governance: Kill switch state
    - policy_engine: Policy evaluation engine
    - audit_store: Audit event storage
    - policy_facade: Policy facade availability
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.governance",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_boot_status"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    return wrap_dict(op.data)
