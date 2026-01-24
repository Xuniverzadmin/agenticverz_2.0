# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified RETRIEVAL facade - L2 API for mediated data access
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-094 (Mediated Data Retrieval API)
# GOVERNANCE NOTE:
# This is the ONE facade for RETRIEVAL domain.
# All data access flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Retrieval API (L2)

Provides mediated data retrieval operations:
- POST /api/v1/retrieval/access (mediated data access)
- GET /api/v1/retrieval/planes (list available planes)
- POST /api/v1/retrieval/planes (register plane)
- GET /api/v1/retrieval/planes/{id} (get plane)
- GET /api/v1/retrieval/evidence (list evidence records)
- GET /api/v1/retrieval/evidence/{id} (get evidence)

This is the ONLY facade for mediated data retrieval.
All data access from LLM-controlled code MUST flow through this router.

INVARIANT: Deny-by-default. All access blocked unless explicitly allowed by policy.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.services.retrieval.facade import (
    RetrievalFacade,
    get_retrieval_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


# =============================================================================
# Request/Response Models
# =============================================================================


class AccessDataRequest(BaseModel):
    """Request for mediated data access."""
    run_id: str = Field(..., description="Run context for this access")
    plane_id: str = Field(..., description="Knowledge plane to access")
    action: str = Field(..., description="Action: query, retrieve, search, list")
    payload: Dict[str, Any] = Field(..., description="Action-specific payload")


class RegisterPlaneRequest(BaseModel):
    """Request to register a knowledge plane."""
    name: str = Field(..., description="Plane name")
    connector_type: str = Field(..., description="Connector type (http, sql, vector)")
    connector_id: str = Field(..., description="Associated connector ID")
    capabilities: Optional[List[str]] = Field(None, description="Plane capabilities")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> RetrievalFacade:
    """Get the retrieval facade."""
    return get_retrieval_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/access", response_model=Dict[str, Any])
async def access_data(
    request: AccessDataRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.access")),
):
    """
    Mediated data access (GAP-094).

    **Tier: REACT ($9)** - Mediated data access.

    All data access from LLM-controlled code MUST go through this endpoint.
    Implements deny-by-default policy enforcement.

    INVARIANT: Access is BLOCKED unless explicitly allowed by policy.
    """
    result = await facade.access_data(
        tenant_id=ctx.tenant_id,
        run_id=request.run_id,
        plane_id=request.plane_id,
        action=request.action,
        payload=request.payload,
    )

    if not result.success:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {result.error}",
        )

    return wrap_dict(result.to_dict())


@router.get("/planes", response_model=Dict[str, Any])
async def list_planes(
    connector_type: Optional[str] = Query(None, description="Filter by connector type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.read")),
):
    """
    List available knowledge planes.

    Returns all registered knowledge planes for the tenant.
    """
    planes = await facade.list_planes(
        tenant_id=ctx.tenant_id,
        connector_type=connector_type,
        status=status,
    )

    return wrap_dict({
        "planes": [p.to_dict() for p in planes],
        "total": len(planes),
    })


@router.post("/planes", response_model=Dict[str, Any])
async def register_plane(
    request: RegisterPlaneRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.write")),
):
    """
    Register a knowledge plane.

    Registers a new knowledge plane that maps to a connector
    for mediated data access.
    """
    plane = await facade.register_plane(
        tenant_id=ctx.tenant_id,
        name=request.name,
        connector_type=request.connector_type,
        connector_id=request.connector_id,
        capabilities=request.capabilities,
    )

    return wrap_dict(plane.to_dict())


@router.get("/planes/{plane_id}", response_model=Dict[str, Any])
async def get_plane(
    plane_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.read")),
):
    """
    Get a specific knowledge plane.
    """
    plane = await facade.get_plane(
        plane_id=plane_id,
        tenant_id=ctx.tenant_id,
    )

    if not plane:
        raise HTTPException(status_code=404, detail="Plane not found")

    return wrap_dict(plane.to_dict())


@router.get("/evidence", response_model=Dict[str, Any])
async def list_evidence(
    run_id: Optional[str] = Query(None, description="Filter by run"),
    plane_id: Optional[str] = Query(None, description="Filter by plane"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.evidence")),
):
    """
    List retrieval evidence records.

    Returns evidence of data accesses for audit and compliance.
    """
    evidence = await facade.list_evidence(
        tenant_id=ctx.tenant_id,
        run_id=run_id,
        plane_id=plane_id,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "evidence": [e.to_dict() for e in evidence],
        "total": len(evidence),
        "limit": limit,
        "offset": offset,
    })


@router.get("/evidence/{evidence_id}", response_model=Dict[str, Any])
async def get_evidence(
    evidence_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.evidence")),
):
    """
    Get a specific evidence record.
    """
    evidence = await facade.get_evidence(
        evidence_id=evidence_id,
        tenant_id=ctx.tenant_id,
    )

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return wrap_dict(evidence.to_dict())
