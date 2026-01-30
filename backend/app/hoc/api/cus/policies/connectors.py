# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified CONNECTORS facade - L2 API for connector operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-093 (Connector Registry API)
# GOVERNANCE NOTE:
# This is the ONE facade for CONNECTORS domain.
# All connector data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Connectors API (L2)

Provides connector management operations:
- GET /api/v1/connectors (list connectors)
- POST /api/v1/connectors (register connector)
- GET /api/v1/connectors/{id} (get connector)
- PUT /api/v1/connectors/{id} (update connector)
- DELETE /api/v1/connectors/{id} (delete connector)
- POST /api/v1/connectors/{id}/test (test connector)

This is the ONLY facade for connector operations.
All connector APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L4 operation registry import
from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/connectors", tags=["Connectors"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RegisterConnectorRequest(BaseModel):
    """Request to register a new connector."""
    name: str = Field(..., description="Connector name")
    connector_type: str = Field(..., description="Connector type (http, sql, mcp, etc.)")
    endpoint: Optional[str] = Field(None, description="Connection endpoint")
    config: Optional[Dict[str, Any]] = Field(None, description="Connector configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateConnectorRequest(BaseModel):
    """Request to update a connector."""
    name: Optional[str] = Field(None, description="New connector name")
    endpoint: Optional[str] = Field(None, description="New connection endpoint")
    config: Optional[Dict[str, Any]] = Field(None, description="New configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=Dict[str, Any])
async def list_connectors(
    connector_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.read")),
):
    """
    List connectors for the tenant.

    Returns all registered connectors with optional filtering.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_connectors",
                "connector_type": connector_type,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    connectors = op.data

    return wrap_dict({
        "connectors": [c.to_dict() for c in connectors],
        "total": len(connectors),
        "limit": limit,
        "offset": offset,
    })


@router.post("", response_model=Dict[str, Any])
async def register_connector(
    request: RegisterConnectorRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.write")),
):
    """
    Register a new connector.

    Supported types:
    - http: REST/HTTP APIs
    - sql: SQL databases
    - mcp: Model Context Protocol servers
    - vector: Vector databases
    - file: File storage
    - serverless: Serverless functions
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "register_connector",
                "name": request.name,
                "connector_type": request.connector_type,
                "endpoint": request.endpoint,
                "config": request.config,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    connector = op.data

    return wrap_dict(connector.to_dict())


@router.get("/{connector_id}", response_model=Dict[str, Any])
async def get_connector(
    connector_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.read")),
):
    """
    Get a specific connector by ID.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_connector",
                "connector_id": connector_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    connector = op.data

    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    return wrap_dict(connector.to_dict())


@router.put("/{connector_id}", response_model=Dict[str, Any])
async def update_connector(
    connector_id: str,
    request: UpdateConnectorRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.write")),
):
    """
    Update a connector.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "update_connector",
                "connector_id": connector_id,
                "name": request.name,
                "endpoint": request.endpoint,
                "config": request.config,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    connector = op.data

    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    return wrap_dict(connector.to_dict())


@router.delete("/{connector_id}", response_model=Dict[str, Any])
async def delete_connector(
    connector_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.write")),
):
    """
    Delete a connector.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "delete_connector",
                "connector_id": connector_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    success = op.data

    if not success:
        raise HTTPException(status_code=404, detail="Connector not found")

    return wrap_dict({"success": True, "connector_id": connector_id})


@router.post("/{connector_id}/test", response_model=Dict[str, Any])
async def test_connector(
    connector_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("connectors.test")),
):
    """
    Test a connector connection.

    Attempts to establish a connection and returns the result.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "integrations.connectors",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "test_connector",
                "connector_id": connector_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    return wrap_dict(result.to_dict())
