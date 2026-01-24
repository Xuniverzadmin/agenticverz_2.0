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
- POST /api/v1/detection/run (run detection on demand)
- GET /api/v1/detection/anomalies (list anomalies)
- GET /api/v1/detection/anomalies/{id} (get anomaly)
- POST /api/v1/detection/anomalies/{id}/resolve (resolve anomaly)
- POST /api/v1/detection/anomalies/{id}/acknowledge (acknowledge anomaly)
- GET /api/v1/detection/status (detection engine status)

This is the ONLY facade for anomaly detection operations.
All detection APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.services.detection.facade import (
    DetectionFacade,
    get_detection_facade,
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


def get_facade() -> DetectionFacade:
    """Get the detection facade."""
    return get_detection_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/run", response_model=Dict[str, Any])
async def run_detection(
    request: RunDetectionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DetectionFacade = Depends(get_facade),
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
    # Note: For cost detection, we need a database session
    # In production, this would be injected properly
    result = await facade.run_detection(
        tenant_id=ctx.tenant_id,
        detection_type=request.detection_type,
        session=None,  # Would be injected in production
    )

    return wrap_dict(result.to_dict())


@router.get("/anomalies", response_model=Dict[str, Any])
async def list_anomalies(
    detection_type: Optional[str] = Query(None, description="Filter by type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DetectionFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("detection.read")),
):
    """
    List anomalies for the tenant.

    Returns detected anomalies with optional filtering.
    """
    anomalies = await facade.list_anomalies(
        tenant_id=ctx.tenant_id,
        detection_type=detection_type,
        severity=severity,
        status=status,
        limit=limit,
        offset=offset,
    )

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
    facade: DetectionFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("detection.read")),
):
    """
    Get a specific anomaly by ID.
    """
    anomaly = await facade.get_anomaly(
        anomaly_id=anomaly_id,
        tenant_id=ctx.tenant_id,
    )

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.post("/anomalies/{anomaly_id}/resolve", response_model=Dict[str, Any])
async def resolve_anomaly(
    anomaly_id: str,
    request: ResolveAnomalyRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DetectionFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("detection.resolve")),
):
    """
    Resolve an anomaly.

    Resolution options:
    - resolved: Anomaly has been addressed
    - dismissed: Anomaly is not actionable (false positive)
    """
    actor = ctx.user_id or "system"

    anomaly = await facade.resolve_anomaly(
        anomaly_id=anomaly_id,
        tenant_id=ctx.tenant_id,
        resolution=request.resolution,
        notes=request.notes,
        actor=actor,
    )

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.post("/anomalies/{anomaly_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_anomaly(
    anomaly_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DetectionFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("detection.acknowledge")),
):
    """
    Acknowledge an anomaly.

    Marks the anomaly as seen but not yet resolved.
    """
    actor = ctx.user_id or "system"

    anomaly = await facade.acknowledge_anomaly(
        anomaly_id=anomaly_id,
        tenant_id=ctx.tenant_id,
        actor=actor,
    )

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    return wrap_dict(anomaly.to_dict())


@router.get("/status", response_model=Dict[str, Any])
async def get_detection_status(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DetectionFacade = Depends(get_facade),
):
    """
    Get detection engine status.

    Returns health status of detection engines:
    - cost: Cost anomaly detector
    - behavioral: Behavioral pattern detector
    - drift: Model/data drift detector
    """
    status = facade.get_detection_status()
    return wrap_dict(status.to_dict())
