# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified MONITORS facade - L2 API for monitoring operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-120 (Health Check API), GAP-121 (Monitor Configuration API)
# GOVERNANCE NOTE:
# This is the ONE facade for MONITORS domain.
# All monitoring flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Monitors API (L2)

Provides monitoring operations:
- POST /api/v1/monitors (create monitor)
- GET /api/v1/monitors (list monitors)
- GET /api/v1/monitors/{id} (get monitor)
- PUT /api/v1/monitors/{id} (update monitor)
- DELETE /api/v1/monitors/{id} (delete monitor)
- POST /api/v1/monitors/{id}/check (run health check)
- GET /api/v1/monitors/{id}/history (check history)
- GET /api/v1/monitors/status (overall status)

This is the ONLY facade for monitoring operations.
All monitor APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.services.monitors_facade import (
    MonitorsFacade,
    get_monitors_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/monitors", tags=["Monitors"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateMonitorRequest(BaseModel):
    """Request to create a monitor."""
    name: str = Field(..., description="Monitor name")
    monitor_type: str = Field(..., description="Type: http, tcp, dns, heartbeat, custom")
    target: Dict[str, Any] = Field(..., description="Target configuration")
    interval_seconds: int = Field(60, description="Check interval in seconds")
    timeout_seconds: int = Field(10, description="Timeout in seconds")
    retries: int = Field(3, description="Retry count on failure")
    enabled: bool = Field(True, description="Whether monitor is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateMonitorRequest(BaseModel):
    """Request to update a monitor."""
    name: Optional[str] = Field(None, description="Monitor name")
    target: Optional[Dict[str, Any]] = Field(None, description="Target configuration")
    interval_seconds: Optional[int] = Field(None, description="Check interval")
    timeout_seconds: Optional[int] = Field(None, description="Timeout")
    retries: Optional[int] = Field(None, description="Retry count")
    enabled: Optional[bool] = Field(None, description="Whether active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> MonitorsFacade:
    """Get the monitors facade."""
    return get_monitors_facade()


# =============================================================================
# Endpoints (GAP-120, GAP-121)
# =============================================================================


@router.post("", response_model=Dict[str, Any])
async def create_monitor(
    request: CreateMonitorRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.write")),
):
    """
    Create a monitor (GAP-121).

    **Tier: REACT ($9)** - Monitor configuration.

    Monitor types:
    - http: HTTP endpoint monitoring
    - tcp: TCP port monitoring
    - dns: DNS resolution monitoring
    - heartbeat: Passive heartbeat monitoring
    - custom: Custom check implementation
    """
    monitor = await facade.create_monitor(
        tenant_id=ctx.tenant_id,
        name=request.name,
        monitor_type=request.monitor_type,
        target=request.target,
        interval_seconds=request.interval_seconds,
        timeout_seconds=request.timeout_seconds,
        retries=request.retries,
        enabled=request.enabled,
        metadata=request.metadata,
    )

    return wrap_dict(monitor.to_dict())


@router.get("", response_model=Dict[str, Any])
async def list_monitors(
    monitor_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled_only: bool = Query(False, description="Only enabled monitors"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.read")),
):
    """
    List monitors.
    """
    monitors = await facade.list_monitors(
        tenant_id=ctx.tenant_id,
        monitor_type=monitor_type,
        status=status,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "monitors": [m.to_dict() for m in monitors],
        "total": len(monitors),
        "limit": limit,
        "offset": offset,
    })


@router.get("/status", response_model=Dict[str, Any])
async def get_status(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.read")),
):
    """
    Get overall monitoring status (GAP-120).

    Returns aggregate health status across all monitors.
    """
    summary = await facade.get_status_summary(tenant_id=ctx.tenant_id)

    return wrap_dict(summary.to_dict())


@router.get("/{monitor_id}", response_model=Dict[str, Any])
async def get_monitor(
    monitor_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.read")),
):
    """
    Get a specific monitor.
    """
    monitor = await facade.get_monitor(
        monitor_id=monitor_id,
        tenant_id=ctx.tenant_id,
    )

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return wrap_dict(monitor.to_dict())


@router.put("/{monitor_id}", response_model=Dict[str, Any])
async def update_monitor(
    monitor_id: str,
    request: UpdateMonitorRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.write")),
):
    """
    Update a monitor.
    """
    monitor = await facade.update_monitor(
        monitor_id=monitor_id,
        tenant_id=ctx.tenant_id,
        name=request.name,
        target=request.target,
        interval_seconds=request.interval_seconds,
        timeout_seconds=request.timeout_seconds,
        retries=request.retries,
        enabled=request.enabled,
        metadata=request.metadata,
    )

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return wrap_dict(monitor.to_dict())


@router.delete("/{monitor_id}", response_model=Dict[str, Any])
async def delete_monitor(
    monitor_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.write")),
):
    """
    Delete a monitor.
    """
    success = await facade.delete_monitor(
        monitor_id=monitor_id,
        tenant_id=ctx.tenant_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return wrap_dict({"success": True, "monitor_id": monitor_id})


@router.post("/{monitor_id}/check", response_model=Dict[str, Any])
async def run_check(
    monitor_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.check")),
):
    """
    Run a health check (GAP-120).

    Manually triggers a health check for the monitor.
    """
    result = await facade.run_check(
        monitor_id=monitor_id,
        tenant_id=ctx.tenant_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return wrap_dict(result.to_dict())


@router.get("/{monitor_id}/history", response_model=Dict[str, Any])
async def get_history(
    monitor_id: str,
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: MonitorsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("monitors.read")),
):
    """
    Get health check history.
    """
    history = await facade.get_check_history(
        monitor_id=monitor_id,
        tenant_id=ctx.tenant_id,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "checks": [h.to_dict() for h in history],
        "total": len(history),
        "limit": limit,
        "offset": offset,
    })
