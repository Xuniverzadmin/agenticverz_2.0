# Layer: L2 — API
# AUDIENCE: FOUNDER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Retrieval plane + evidence administration (founder-only)
# Callers: Founder ops tooling
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md (audience scoping)

"""
Founder-only Retrieval Administration API (L2)

This router exposes retrieval plane registry and evidence query endpoints.
These are governance/ops operations and must not be callable from CUS
surfaces.

Endpoints:
- GET /retrieval/planes
- POST /retrieval/planes
- GET /retrieval/planes/{plane_id}
- GET /retrieval/evidence
- GET /retrieval/evidence/{evidence_id}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.console_auth import verify_fops_token
from app.schemas.response import wrap_dict
from app.hoc.cus.hoc_spine.services.retrieval_facade import (
    RetrievalFacade,
    get_retrieval_facade,
)

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval", "Founder"],
    dependencies=[Depends(verify_fops_token)],
)


class RegisterPlaneRequest(BaseModel):
    """Request to register a knowledge plane (founder-only)."""

    tenant_id: str = Field(..., description="Target tenant")
    name: str = Field(..., description="Plane name")
    connector_type: str = Field(..., description="Connector type (http, sql, vector)")
    connector_id: str = Field(..., description="Associated connector ID")
    capabilities: Optional[List[str]] = Field(None, description="Plane capabilities")


def get_facade() -> RetrievalFacade:
    return get_retrieval_facade()


@router.get("/planes", response_model=Dict[str, Any])
async def list_planes(
    tenant_id: str = Query(..., description="Target tenant"),
    connector_type: Optional[str] = Query(None, description="Filter by connector type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    facade: RetrievalFacade = Depends(get_facade),
):
    planes = await facade.list_planes(
        tenant_id=tenant_id,
        connector_type=connector_type,
        status=status,
    )
    return wrap_dict({"planes": [p.to_dict() for p in planes], "total": len(planes)})


@router.post("/planes", response_model=Dict[str, Any])
async def register_plane(
    request: RegisterPlaneRequest,
    facade: RetrievalFacade = Depends(get_facade),
):
    plane = await facade.register_plane(
        tenant_id=request.tenant_id,
        name=request.name,
        connector_type=request.connector_type,
        connector_id=request.connector_id,
        capabilities=request.capabilities,
    )
    return wrap_dict(plane.to_dict())


@router.get("/planes/{plane_id}", response_model=Dict[str, Any])
async def get_plane(
    plane_id: str,
    tenant_id: str = Query(..., description="Target tenant"),
    facade: RetrievalFacade = Depends(get_facade),
):
    plane = await facade.get_plane(
        plane_id=plane_id,
        tenant_id=tenant_id,
    )
    if not plane:
        raise HTTPException(status_code=404, detail="Plane not found")
    return wrap_dict(plane.to_dict())


@router.get("/evidence", response_model=Dict[str, Any])
async def list_evidence(
    tenant_id: str = Query(..., description="Target tenant"),
    run_id: Optional[str] = Query(None, description="Filter by run"),
    plane_id: Optional[str] = Query(None, description="Filter by plane"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    facade: RetrievalFacade = Depends(get_facade),
):
    evidence = await facade.list_evidence(
        tenant_id=tenant_id,
        run_id=run_id,
        plane_id=plane_id,
        limit=limit,
        offset=offset,
    )
    return wrap_dict(
        {
            "evidence": [e.to_dict() for e in evidence],
            "total": len(evidence),
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/evidence/{evidence_id}", response_model=Dict[str, Any])
async def get_evidence(
    evidence_id: str,
    tenant_id: str = Query(..., description="Target tenant"),
    facade: RetrievalFacade = Depends(get_facade),
):
    evidence = await facade.get_evidence(
        evidence_id=evidence_id,
        tenant_id=tenant_id,
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return wrap_dict(evidence.to_dict())

