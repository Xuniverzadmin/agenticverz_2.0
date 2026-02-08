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
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)
from app.schemas.response import wrap_dict
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/planes", response_model=Dict[str, Any])
async def list_planes(
    tenant_id: str = Query(..., description="Target tenant"),
    connector_type: Optional[str] = Query(None, description="Filter by connector type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_session_dep),
):
    # Phase 3: planes are served from the persisted SSOT (knowledge_plane_registry),
    # not RetrievalFacade's in-memory demo registry.
    #
    # NOTE: `status` filter is accepted for API compatibility but not yet applied
    # until lifecycle state wiring is unified (Phase 4).
    _ = status
    registry = get_operation_registry()
    result = await registry.execute(
        "knowledge.planes.list",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"plane_type": connector_type},
        ),
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return wrap_dict(result.data)


@router.post("/planes", response_model=Dict[str, Any])
async def register_plane(
    request: RegisterPlaneRequest,
    session: AsyncSession = Depends(get_session_dep),
):
    registry = get_operation_registry()
    result = await registry.execute(
        "knowledge.planes.register",
        OperationContext(
            session=session,
            tenant_id=request.tenant_id,
            params={
                "plane_type": request.connector_type,
                "plane_name": request.name,
                "connector_type": request.connector_type,
                "connector_id": request.connector_id,
                "config": {"capabilities": request.capabilities or []},
                "created_by": "founder",
            },
        ),
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return wrap_dict(result.data)


@router.get("/planes/{plane_id}", response_model=Dict[str, Any])
async def get_plane(
    plane_id: str,
    tenant_id: str = Query(..., description="Target tenant"),
    session: AsyncSession = Depends(get_session_dep),
):
    registry = get_operation_registry()
    result = await registry.execute(
        "knowledge.planes.get",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"plane_id": plane_id},
        ),
    )
    if not result.success:
        raise HTTPException(status_code=404, detail="Plane not found")
    return wrap_dict(result.data)


@router.get("/evidence", response_model=Dict[str, Any])
async def list_evidence(
    tenant_id: str = Query(..., description="Target tenant"),
    run_id: Optional[str] = Query(None, description="Filter by run"),
    plane_id: Optional[str] = Query(None, description="Filter by plane"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_session_dep),
):
    registry = get_operation_registry()
    result = await registry.execute(
        "knowledge.evidence.list",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "run_id": run_id,
                "plane_id": plane_id,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return wrap_dict(result.data)


@router.get("/evidence/{evidence_id}", response_model=Dict[str, Any])
async def get_evidence(
    evidence_id: str,
    tenant_id: str = Query(..., description="Target tenant"),
    session: AsyncSession = Depends(get_session_dep),
):
    registry = get_operation_registry()
    result = await registry.execute(
        "knowledge.evidence.get",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"evidence_id": evidence_id},
        ),
    )
    if not result.success:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return wrap_dict(result.data)
