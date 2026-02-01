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
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
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
# Endpoints (GAP-123)
# =============================================================================


@router.get("", response_model=Dict[str, Any])
async def list_controls(
    control_type: Optional[str] = Query(None, description="Filter by type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    List controls (GAP-123).

    Returns all controls for the tenant.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_controls",
                "control_type": control_type,
                "state": state,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    controls = op.data

    return wrap_dict({
        "controls": [c.to_dict() for c in controls],
        "total": len(controls),
        "limit": limit,
        "offset": offset,
    })


@router.get("/status", response_model=Dict[str, Any])
async def get_status(
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    Get overall control status.

    Returns summary including killswitch and maintenance mode state.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_status"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    status = op.data

    return wrap_dict(status.to_dict())


@router.get("/{control_id}", response_model=Dict[str, Any])
async def get_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.read")),
):
    """
    Get a specific control.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_control", "control_id": control_id},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    control = op.data

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.put("/{control_id}", response_model=Dict[str, Any])
async def update_control(
    control_id: str,
    request: UpdateControlRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.write")),
):
    """
    Update a control.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "update_control",
                "control_id": control_id,
                "conditions": request.conditions,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    control = op.data

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.post("/{control_id}/enable", response_model=Dict[str, Any])
async def enable_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.admin")),
):
    """
    Enable a control.

    **Requires admin permissions.**
    """
    actor = ctx.user_id or "system"
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "enable_control",
                "control_id": control_id,
                "actor": actor,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    control = op.data

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())


@router.post("/{control_id}/disable", response_model=Dict[str, Any])
async def disable_control(
    control_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("controls.admin")),
):
    """
    Disable a control.

    **Requires admin permissions.**
    """
    actor = ctx.user_id or "system"
    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "disable_control",
                "control_id": control_id,
                "actor": actor,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    control = op.data

    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    return wrap_dict(control.to_dict())
