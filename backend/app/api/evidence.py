# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified EVIDENCE facade - L2 API for evidence chain and export
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-104 (Evidence Chain API), GAP-105 (Evidence Export API)
# GOVERNANCE NOTE:
# This is the ONE facade for EVIDENCE domain.
# All evidence chain and export flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Evidence API (L2)

Provides evidence chain and export operations:
- GET /api/v1/evidence/chains (list chains)
- POST /api/v1/evidence/chains (create chain)
- GET /api/v1/evidence/chains/{id} (get chain)
- POST /api/v1/evidence/chains/{id}/evidence (add evidence)
- GET /api/v1/evidence/chains/{id}/verify (verify chain)
- POST /api/v1/evidence/export (create export)
- GET /api/v1/evidence/exports (list exports)
- GET /api/v1/evidence/exports/{id} (get export)

This is the ONLY facade for evidence operations.
All evidence APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.hoc.cus.logs.L5_engines.evidence_facade import (
    EvidenceFacade,
    get_evidence_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/evidence", tags=["Evidence"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateChainRequest(BaseModel):
    """Request to create evidence chain."""
    run_id: Optional[str] = Field(None, description="Associated run ID")
    initial_evidence: Optional[Dict[str, Any]] = Field(
        None,
        description="Initial evidence data",
    )


class AddEvidenceRequest(BaseModel):
    """Request to add evidence to chain."""
    evidence_type: str = Field(
        ...,
        description="Evidence type: execution, retrieval, policy, cost, incident",
    )
    data: Dict[str, Any] = Field(..., description="Evidence data")


class CreateExportRequest(BaseModel):
    """Request to create evidence export."""
    chain_id: str = Field(..., description="Chain ID to export")
    format: str = Field("json", description="Export format: json, csv, pdf")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> EvidenceFacade:
    """Get the evidence facade."""
    return get_evidence_facade()


# =============================================================================
# Chain Endpoints (GAP-104)
# =============================================================================


@router.get("/chains", response_model=Dict[str, Any])
async def list_chains(
    run_id: Optional[str] = Query(None, description="Filter by run"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.read")),
):
    """
    List evidence chains.

    Returns evidence chains for the tenant.
    """
    chains = await facade.list_chains(
        tenant_id=ctx.tenant_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "chains": [c.to_dict() for c in chains],
        "total": len(chains),
        "limit": limit,
        "offset": offset,
    })


@router.post("/chains", response_model=Dict[str, Any])
async def create_chain(
    request: CreateChainRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.write")),
):
    """
    Create an evidence chain (GAP-104).

    **Tier: REACT ($9)** - Evidence chain creation.

    Creates a new evidence chain, optionally with initial evidence.
    """
    chain = await facade.create_chain(
        tenant_id=ctx.tenant_id,
        run_id=request.run_id,
        initial_evidence=request.initial_evidence,
    )

    return wrap_dict(chain.to_dict())


@router.get("/chains/{chain_id}", response_model=Dict[str, Any])
async def get_chain(
    chain_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.read")),
):
    """
    Get a specific evidence chain.
    """
    chain = await facade.get_chain(
        chain_id=chain_id,
        tenant_id=ctx.tenant_id,
    )

    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    return wrap_dict(chain.to_dict())


@router.post("/chains/{chain_id}/evidence", response_model=Dict[str, Any])
async def add_evidence(
    chain_id: str,
    request: AddEvidenceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.write")),
):
    """
    Add evidence to a chain.

    Evidence types:
    - execution: Run execution evidence
    - retrieval: Data retrieval evidence
    - policy: Policy decision evidence
    - cost: Cost event evidence
    - incident: Incident evidence
    """
    chain = await facade.add_evidence(
        chain_id=chain_id,
        tenant_id=ctx.tenant_id,
        evidence_type=request.evidence_type,
        data=request.data,
    )

    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    return wrap_dict(chain.to_dict())


@router.get("/chains/{chain_id}/verify", response_model=Dict[str, Any])
async def verify_chain(
    chain_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.verify")),
):
    """
    Verify chain integrity.

    Verifies that all links in the chain have valid hashes
    and proper linkage.
    """
    result = await facade.verify_chain(
        chain_id=chain_id,
        tenant_id=ctx.tenant_id,
    )

    return wrap_dict(result.to_dict())


# =============================================================================
# Export Endpoints (GAP-105)
# =============================================================================


@router.post("/export", response_model=Dict[str, Any])
async def create_export(
    request: CreateExportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.export")),
):
    """
    Create evidence export (GAP-105).

    **Tier: PREVENT ($199)** - Evidence export.

    Export formats:
    - json: JSON format with full chain data
    - csv: CSV format for spreadsheet import
    - pdf: PDF format for compliance reports
    """
    export = await facade.create_export(
        tenant_id=ctx.tenant_id,
        chain_id=request.chain_id,
        format=request.format,
    )

    return wrap_dict(export.to_dict())


@router.get("/exports", response_model=Dict[str, Any])
async def list_exports(
    chain_id: Optional[str] = Query(None, description="Filter by chain"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.read")),
):
    """
    List evidence exports.
    """
    exports = await facade.list_exports(
        tenant_id=ctx.tenant_id,
        chain_id=chain_id,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "exports": [e.to_dict() for e in exports],
        "total": len(exports),
        "limit": limit,
        "offset": offset,
    })


@router.get("/exports/{export_id}", response_model=Dict[str, Any])
async def get_export(
    export_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: EvidenceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("evidence.read")),
):
    """
    Get export status.
    """
    export = await facade.get_export(
        export_id=export_id,
        tenant_id=ctx.tenant_id,
    )

    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    return wrap_dict(export.to_dict())
