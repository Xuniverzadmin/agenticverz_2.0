# capability_id: CAP-009
# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified DATASOURCES facade - L2 API for data source operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-113 (Data Sources API)
# GOVERNANCE NOTE:
# This is the ONE facade for DATASOURCES domain.
# All data source flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
DataSources API (L2)

Provides data source operations:
- POST /datasources (create source)
- GET /datasources (list sources)
- GET /datasources/{id} (get source)
- PUT /datasources/{id} (update source)
- DELETE /datasources/{id} (delete source)
- POST /datasources/{id}/test (test connection)
- POST /datasources/{id}/activate (activate source)
- POST /datasources/{id}/deactivate (deactivate source)
- GET /datasources/stats (statistics)

This is the ONLY facade for data source operations.
All data source APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L4 operation registry import
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/datasources", tags=["DataSources"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateSourceRequest(BaseModel):
    """Request to create a data source."""
    name: str = Field(..., description="Source name")
    source_type: str = Field(..., description="Type: database, file, api, vector, stream, custom")
    config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    description: Optional[str] = Field(None, description="Source description")
    tags: Optional[List[str]] = Field(None, description="Tags for organization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateSourceRequest(BaseModel):
    """Request to update a data source."""
    name: Optional[str] = Field(None, description="Source name")
    description: Optional[str] = Field(None, description="Source description")
    config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Endpoints (GAP-113)
# =============================================================================


@router.post("", response_model=Dict[str, Any])
async def create_source(
    request: CreateSourceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Create a data source (GAP-113).

    **Tier: REACT ($9)** - Data source management.

    Source types:
    - database: Relational databases (PostgreSQL, MySQL, etc.)
    - file: File storage (S3, GCS, local)
    - api: REST/GraphQL APIs
    - vector: Vector databases (Pinecone, Weaviate)
    - stream: Streaming sources (Kafka, etc.)
    - custom: Custom connectors
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "register_source",
                "name": request.name,
                "source_type": request.source_type,
                "config": request.config,
                "description": request.description,
                "tags": request.tags,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    source = op.data

    return wrap_dict(source.to_dict())


@router.get("", response_model=Dict[str, Any])
async def list_sources(
    source_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    List data sources.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_sources",
                "source_type": source_type,
                "status": status,
                "tag": tag,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    sources = op.data

    return wrap_dict({
        "sources": [s.to_dict() for s in sources],
        "total": len(sources),
        "limit": limit,
        "offset": offset,
    })


@router.get("/stats", response_model=Dict[str, Any])
async def get_statistics(
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    Get data source statistics.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_statistics",
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    stats = op.data

    return wrap_dict(stats.to_dict())


@router.get("/{source_id}", response_model=Dict[str, Any])
async def get_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    Get a specific data source.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_source",
                "source_id": source_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    source = op.data

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.put("/{source_id}", response_model=Dict[str, Any])
async def update_source(
    source_id: str,
    request: UpdateSourceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Update a data source.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "update_source",
                "source_id": source_id,
                "name": request.name,
                "description": request.description,
                "config": request.config,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    source = op.data

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.delete("/{source_id}", response_model=Dict[str, Any])
async def delete_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Delete a data source.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "delete_source",
                "source_id": source_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    success = op.data

    if not success:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict({"success": True, "source_id": source_id})


@router.post("/{source_id}/test", response_model=Dict[str, Any])
async def test_connection(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.test")),
):
    """
    Test a data source connection.

    Verifies that the data source can be reached with the current configuration.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "test_connection",
                "source_id": source_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(result.to_dict())


@router.post("/{source_id}/activate", response_model=Dict[str, Any])
async def activate_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Activate a data source.

    Makes the data source available for use.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "activate_source",
                "source_id": source_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    source = op.data

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.post("/{source_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Deactivate a data source.

    Temporarily disables the data source.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.datasources",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "deactivate_source",
                "source_id": source_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    source = op.data

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())
