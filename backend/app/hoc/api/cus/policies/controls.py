# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified CONTROLS facade - L2 API for control operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-123 (Controls API)
# GOVERNANCE NOTE:
# This is the ONE facade for CONTROLS domain.
# All control flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Controls API (L2)

Provides control operations:
- GET /api/v1/controls (list controls)
- GET /api/v1/controls/status (overall status)
- GET /api/v1/controls/{id} (get control)
- PUT /api/v1/controls/{id} (update control)
- POST /api/v1/controls/{id}/enable (enable control)
- POST /api/v1/controls/{id}/disable (disable control)

This is the ONLY facade for control operations.
All controls APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (migrated to HOC per SWEEP-19)
from app.hoc.cus.controls.L5_engines.controls_facade import (
    ControlsFacade,
    get_controls_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/controls", tags=["Controls"])


# =============================================================================
# Request/Response Models
# =============================================================================


class UpdateControlRequest(BaseModel):
    """Request to update a control."""
    conditions: Optional[Dict[str, Any]] = Field(None, description="Trigger conditions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> ControlsFacade:
    """Get the controls facade."""
    return get_controls_facade()


# =============================================================================
# Endpoints (GAP-123)
# =============================================================================


@router.get("", response_model=Dict[str, Any])
async def list_controls(
    control_type: Optional[str] = Query(None, description="Filter by type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    List controls (GAP-123).

    Returns all controls for the tenant.
    """
    controls = await facade.list_controls(
        tenant_id=ctx.tenant_id,
        control_type=control_type,
        state=state,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "controls": [c.to_dict() for c in controls],
        "total": len(controls),
        "limit": limit,
        "offset": offset,
    })


@router.get("/status", response_model=Dict[str, Any])
async def get_status(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    Get overall control status.

    Returns summary including killswitch and maintenance mode state.
    """
    status = await facade.get_status(tenant_id=ctx.tenant_id)

    return wrap_dict(status.to_dict())


@router.get("/{control_id}", response_model=Dict[str, Any])
async def get_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    Get a specific control.
    """
    control = await facade.get_control(
        control_id=control_id,
        tenant_id=ctx.tenant_id,
    )

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.put("/{control_id}", response_model=Dict[str, Any])
async def update_control(
    control_id: str,
    request: UpdateControlRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.write")),
):
    """
    Update a control.
    """
    control = await facade.update_control(
        control_id=control_id,
        tenant_id=ctx.tenant_id,
        conditions=request.conditions,
        metadata=request.metadata,
    )

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.post("/{control_id}/enable", response_model=Dict[str, Any])
async def enable_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.admin")),
):
    """
    Enable a control.

    **Requires admin permissions.**
    """
    actor = ctx.user_id or "system"
    control = await facade.enable_control(
        control_id=control_id,
        tenant_id=ctx.tenant_id,
        actor=actor,
    )

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.post("/{control_id}/disable", response_model=Dict[str, Any])
async def disable_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ControlsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("controls.admin")),
):
    """
    Disable a control.

    **Requires admin permissions.**
    """
    actor = ctx.user_id or "system"
    control = await facade.disable_control(
        control_id=control_id,
        tenant_id=ctx.tenant_id,
        actor=actor,
    )

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())
