# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified DETECTION facade - L2 API for anomaly detection operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-102 (Anomaly Detection API)
# GOVERNANCE NOTE:
# This is the ONE facade for DETECTION domain.
# All anomaly detection data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Detection API (L2)

Provides anomaly detection operations:
- POST /detection/run (run detection on demand)
- GET /detection/anomalies (list anomalies)
- GET /detection/anomalies/{id} (get anomaly)
- POST /detection/anomalies/{id}/resolve (resolve anomaly)
- POST /detection/anomalies/{id}/acknowledge (acknowledge anomaly)
- GET /detection/status (detection engine status)

This is the ONLY facade for anomaly detection operations.
All detection APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L4 operation registry (L2-L4-L5 architecture per PIN-491)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/detection", tags=["Detection"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RunDetectionRequest(BaseModel):
    """Request to run anomaly detection."""
    detection_type: str = Field(
        "cost",
        description="Detection type: cost, behavioral, drift",
    )


class ResolveAnomalyRequest(BaseModel):
    """Request to resolve an anomaly."""
    resolution: str = Field(
        ...,
        description="Resolution: resolved, dismissed",
    )
    notes: Optional[str] = Field(None, description="Resolution notes")


# =============================================================================
# Dependencies
# =============================================================================

# Removed: get_facade() - now using operation registry directly in endpoints


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/run", response_model=Dict[str, Any])
async def run_detection(
    request: RunDetectionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("detection.run")),
):
    """
    Run anomaly detection on demand (GAP-102).

    **Tier: REACT ($9)** - Anomaly detection.

    Detection types:
    - cost: Cost anomalies (spikes, drift, budget issues)
    - behavioral: Behavioral anomalies (pattern changes)
    - drift: Model/data drift detection

    Returns detection results including anomalies found and incidents created.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,  # DetectionFacade accepts None for session
            tenant_id=ctx.tenant_id,
            params={
                "method": "run_detection",
                "detection_type": request.detection_type,
                "session": None,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    return wrap_dict(result.to_dict())


@router.get("/anomalies", response_model=Dict[str, Any])
async def list_anomalies(
    detection_type: Optional[str] = Query(None, description="Filter by type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("detection.read")),
):
    """
    List anomalies for the tenant.

    Returns detected anomalies with optional filtering.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_anomalies",
                "detection_type": detection_type,
                "severity": severity,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    anomalies = op.data

    return wrap_dict({
        "anomalies": [a.to_dict() for a in anomalies],
        "total": len(anomalies),
        "limit": limit,
        "offset": offset,
    })


@router.get("/anomalies/{anomaly_id}", response_model=Dict[str, Any])
async def get_anomaly(
    anomaly_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("detection.read")),
):
    """
    Get a specific anomaly by ID.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_anomaly",
                "anomaly_id": anomaly_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    anomaly = op.data

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.post("/anomalies/{anomaly_id}/resolve", response_model=Dict[str, Any])
async def resolve_anomaly(
    anomaly_id: str,
    request: ResolveAnomalyRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("detection.resolve")),
):
    """
    Resolve an anomaly.

    Resolution options:
    - resolved: Anomaly has been addressed
    - dismissed: Anomaly is not actionable (false positive)
    """
    actor = ctx.user_id or "system"

    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "resolve_anomaly",
                "anomaly_id": anomaly_id,
                "resolution": request.resolution,
                "notes": request.notes,
                "actor": actor,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    anomaly = op.data

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.post("/anomalies/{anomaly_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_anomaly(
    anomaly_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("detection.acknowledge")),
):
    """
    Acknowledge an anomaly.

    Marks the anomaly as seen but not yet resolved.
    """
    actor = ctx.user_id or "system"

    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "acknowledge_anomaly",
                "anomaly_id": anomaly_id,
                "actor": actor,
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    anomaly = op.data

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.get("/status", response_model=Dict[str, Any])
async def get_detection_status(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get detection engine status.

    Returns health status of detection engines:
    - cost: Cost anomaly detector
    - behavioral: Behavioral pattern detector
    - drift: Model/data drift detector
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.detection",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_detection_status",
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    status = op.data
    return wrap_dict(status.to_dict())
