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
- POST /api/v1/datasources (create source)
- GET /api/v1/datasources (list sources)
- GET /api/v1/datasources/{id} (get source)
- PUT /api/v1/datasources/{id} (update source)
- DELETE /api/v1/datasources/{id} (delete source)
- POST /api/v1/datasources/{id}/test (test connection)
- POST /api/v1/datasources/{id}/activate (activate source)
- POST /api/v1/datasources/{id}/deactivate (deactivate source)
- GET /api/v1/datasources/stats (statistics)

This is the ONLY facade for data source operations.
All data source APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.hoc.cus.integrations.L5_engines.datasources_facade import (
    DataSourcesFacade,
    get_datasources_facade,
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
# Dependencies
# =============================================================================


def get_facade() -> DataSourcesFacade:
    """Get the datasources facade."""
    return get_datasources_facade()


# =============================================================================
# Endpoints (GAP-113)
# =============================================================================


@router.post("", response_model=Dict[str, Any])
async def create_source(
    request: CreateSourceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
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
    source = await facade.register_source(
        tenant_id=ctx.tenant_id,
        name=request.name,
        source_type=request.source_type,
        config=request.config,
        description=request.description,
        tags=request.tags,
        metadata=request.metadata,
    )

    return wrap_dict(source.to_dict())


@router.get("", response_model=Dict[str, Any])
async def list_sources(
    source_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    List data sources.
    """
    sources = await facade.list_sources(
        tenant_id=ctx.tenant_id,
        source_type=source_type,
        status=status,
        tag=tag,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "sources": [s.to_dict() for s in sources],
        "total": len(sources),
        "limit": limit,
        "offset": offset,
    })


@router.get("/stats", response_model=Dict[str, Any])
async def get_statistics(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    Get data source statistics.
    """
    stats = await facade.get_statistics(tenant_id=ctx.tenant_id)

    return wrap_dict(stats.to_dict())


@router.get("/{source_id}", response_model=Dict[str, Any])
async def get_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.read")),
):
    """
    Get a specific data source.
    """
    source = await facade.get_source(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
    )

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.put("/{source_id}", response_model=Dict[str, Any])
async def update_source(
    source_id: str,
    request: UpdateSourceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Update a data source.
    """
    source = await facade.update_source(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
        name=request.name,
        description=request.description,
        config=request.config,
        metadata=request.metadata,
    )

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.delete("/{source_id}", response_model=Dict[str, Any])
async def delete_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Delete a data source.
    """
    success = await facade.delete_source(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict({"success": True, "source_id": source_id})


@router.post("/{source_id}/test", response_model=Dict[str, Any])
async def test_connection(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.test")),
):
    """
    Test a data source connection.

    Verifies that the data source can be reached with the current configuration.
    """
    result = await facade.test_connection(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(result.to_dict())


@router.post("/{source_id}/activate", response_model=Dict[str, Any])
async def activate_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Activate a data source.

    Makes the data source available for use.
    """
    source = await facade.activate_source(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
    )

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())


@router.post("/{source_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_source(
    source_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: DataSourcesFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("datasources.write")),
):
    """
    Deactivate a data source.

    Temporarily disables the data source.
    """
    source = await facade.deactivate_source(
        source_id=source_id,
        tenant_id=ctx.tenant_id,
    )

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return wrap_dict(source.to_dict())
