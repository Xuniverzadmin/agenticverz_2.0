# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified ALERTS facade - L2 API for alert operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-110 (Alert Configuration), GAP-111 (Alert History), GAP-124 (Alert Routing)
# GOVERNANCE NOTE:
# This is the ONE facade for ALERTS domain.
# All alert flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Alerts API (L2)

Provides alert operations:
- POST /api/v1/alerts/rules (create rule)
- GET /api/v1/alerts/rules (list rules)
- GET /api/v1/alerts/rules/{id} (get rule)
- PUT /api/v1/alerts/rules/{id} (update rule)
- DELETE /api/v1/alerts/rules/{id} (delete rule)
- GET /api/v1/alerts/history (alert history)
- GET /api/v1/alerts/history/{id} (get event)
- POST /api/v1/alerts/history/{id}/acknowledge (acknowledge)
- POST /api/v1/alerts/history/{id}/resolve (resolve)
- POST /api/v1/alerts/routes (create route)
- GET /api/v1/alerts/routes (list routes)
- DELETE /api/v1/alerts/routes/{id} (delete route)

This is the ONLY facade for alert operations.
All alert APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (migrated to HOC per SWEEP-18)
from app.hoc.cus.general.L5_engines.alerts_facade import (
    AlertsFacade,
    get_alerts_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateRuleRequest(BaseModel):
    """Request to create alert rule."""
    name: str = Field(..., description="Rule name")
    condition: Dict[str, Any] = Field(..., description="Alert condition")
    severity: str = Field("warning", description="Severity: info, warning, error, critical")
    description: Optional[str] = Field(None, description="Rule description")
    channels: Optional[List[str]] = Field(None, description="Notification channels")
    enabled: bool = Field(True, description="Whether rule is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateRuleRequest(BaseModel):
    """Request to update alert rule."""
    name: Optional[str] = Field(None, description="Rule name")
    condition: Optional[Dict[str, Any]] = Field(None, description="Alert condition")
    severity: Optional[str] = Field(None, description="Severity")
    description: Optional[str] = Field(None, description="Rule description")
    channels: Optional[List[str]] = Field(None, description="Notification channels")
    enabled: Optional[bool] = Field(None, description="Whether rule is active")


class CreateRouteRequest(BaseModel):
    """Request to create alert route."""
    name: str = Field(..., description="Route name")
    match_labels: Dict[str, str] = Field(..., description="Labels to match")
    channel: str = Field(..., description="Target notification channel")
    priority_override: Optional[str] = Field(None, description="Priority override")
    enabled: bool = Field(True, description="Whether route is active")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> AlertsFacade:
    """Get the alerts facade."""
    return get_alerts_facade()


# =============================================================================
# Rule Endpoints (GAP-110)
# =============================================================================


@router.post("/rules", response_model=Dict[str, Any])
async def create_rule(
    request: CreateRuleRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.write")),
):
    """
    Create an alert rule (GAP-110).

    **Tier: REACT ($9)** - Alert configuration.

    Condition example:
    ```json
    {
        "metric": "cost_daily",
        "operator": "gt",
        "threshold": 1000
    }
    ```
    """
    rule = await facade.create_rule(
        tenant_id=ctx.tenant_id,
        name=request.name,
        condition=request.condition,
        severity=request.severity,
        description=request.description,
        channels=request.channels,
        enabled=request.enabled,
        metadata=request.metadata,
    )

    return wrap_dict(rule.to_dict())


@router.get("/rules", response_model=Dict[str, Any])
async def list_rules(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    enabled_only: bool = Query(False, description="Only enabled rules"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    List alert rules.
    """
    rules = await facade.list_rules(
        tenant_id=ctx.tenant_id,
        severity=severity,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "rules": [r.to_dict() for r in rules],
        "total": len(rules),
        "limit": limit,
        "offset": offset,
    })


@router.get("/rules/{rule_id}", response_model=Dict[str, Any])
async def get_rule(
    rule_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    Get a specific alert rule.
    """
    rule = await facade.get_rule(
        rule_id=rule_id,
        tenant_id=ctx.tenant_id,
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return wrap_dict(rule.to_dict())


@router.put("/rules/{rule_id}", response_model=Dict[str, Any])
async def update_rule(
    rule_id: str,
    request: UpdateRuleRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.write")),
):
    """
    Update an alert rule.
    """
    rule = await facade.update_rule(
        rule_id=rule_id,
        tenant_id=ctx.tenant_id,
        name=request.name,
        condition=request.condition,
        severity=request.severity,
        description=request.description,
        channels=request.channels,
        enabled=request.enabled,
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return wrap_dict(rule.to_dict())


@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_rule(
    rule_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.write")),
):
    """
    Delete an alert rule.
    """
    success = await facade.delete_rule(
        rule_id=rule_id,
        tenant_id=ctx.tenant_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")

    return wrap_dict({"success": True, "rule_id": rule_id})


# =============================================================================
# History Endpoints (GAP-111)
# =============================================================================


@router.get("/history", response_model=Dict[str, Any])
async def list_history(
    rule_id: Optional[str] = Query(None, description="Filter by rule"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    List alert history (GAP-111).

    Returns triggered alert events with status.
    """
    events = await facade.list_history(
        tenant_id=ctx.tenant_id,
        rule_id=rule_id,
        severity=severity,
        status=status,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "events": [e.to_dict() for e in events],
        "total": len(events),
        "limit": limit,
        "offset": offset,
    })


@router.get("/history/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    Get a specific alert event.
    """
    event = await facade.get_event(
        event_id=event_id,
        tenant_id=ctx.tenant_id,
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return wrap_dict(event.to_dict())


@router.post("/history/{event_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_event(
    event_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.acknowledge")),
):
    """
    Acknowledge an alert event.
    """
    actor = ctx.user_id or "system"

    event = await facade.acknowledge_event(
        event_id=event_id,
        tenant_id=ctx.tenant_id,
        actor=actor,
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return wrap_dict(event.to_dict())


@router.post("/history/{event_id}/resolve", response_model=Dict[str, Any])
async def resolve_event(
    event_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.resolve")),
):
    """
    Resolve an alert event.
    """
    actor = ctx.user_id or "system"

    event = await facade.resolve_event(
        event_id=event_id,
        tenant_id=ctx.tenant_id,
        actor=actor,
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return wrap_dict(event.to_dict())


# =============================================================================
# Routing Endpoints (GAP-124)
# =============================================================================


@router.post("/routes", response_model=Dict[str, Any])
async def create_route(
    request: CreateRouteRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.routes")),
):
    """
    Create an alert route (GAP-124).

    **Tier: PREVENT ($199)** - Alert routing configuration.

    Routes determine where alerts are sent based on labels.
    """
    route = await facade.create_route(
        tenant_id=ctx.tenant_id,
        name=request.name,
        match_labels=request.match_labels,
        channel=request.channel,
        priority_override=request.priority_override,
        enabled=request.enabled,
    )

    return wrap_dict(route.to_dict())


@router.get("/routes", response_model=Dict[str, Any])
async def list_routes(
    enabled_only: bool = Query(False, description="Only enabled routes"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    List alert routes.
    """
    routes = await facade.list_routes(
        tenant_id=ctx.tenant_id,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "routes": [r.to_dict() for r in routes],
        "total": len(routes),
        "limit": limit,
        "offset": offset,
    })


@router.get("/routes/{route_id}", response_model=Dict[str, Any])
async def get_route(
    route_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.read")),
):
    """
    Get a specific alert route.
    """
    route = await facade.get_route(
        route_id=route_id,
        tenant_id=ctx.tenant_id,
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    return wrap_dict(route.to_dict())


@router.delete("/routes/{route_id}", response_model=Dict[str, Any])
async def delete_route(
    route_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: AlertsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("alerts.routes")),
):
    """
    Delete an alert route.
    """
    success = await facade.delete_route(
        route_id=route_id,
        tenant_id=ctx.tenant_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Route not found")

    return wrap_dict({"success": True, "route_id": route_id})
