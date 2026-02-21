# capability_id: CAP-012
# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: MCP Servers API - customer endpoints for MCP server lifecycle management
# Callers: Customer Console frontend, SDK (aos_sdk)
# Allowed Imports: L4 (hoc_spine orchestrator)
# Forbidden Imports: L1, L5, L6
# Reference: PIN-516 (MCP Customer Integration), Phase 3
# artifact_class: CODE

"""
MCP Servers API (L2)

Customer-facing endpoints for MCP server lifecycle management.
Enables customers to register MCP servers, discover tools, and monitor health.

Endpoints:
- POST   /integrations/mcp-servers              → Register a new MCP server
- GET    /integrations/mcp-servers              → List MCP servers for tenant
- GET    /integrations/mcp-servers/{server_id}  → Get server details
- POST   /integrations/mcp-servers/{server_id}/discover → Discover tools
- GET    /integrations/mcp-servers/{server_id}/health   → Health check
- DELETE /integrations/mcp-servers/{server_id}  → Soft-delete server
- GET    /integrations/mcp-servers/{server_id}/tools    → List server tools
- GET    /integrations/mcp-servers/{server_id}/invocations → List invocations
"""

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)

logger = logging.getLogger("nova.api.mcp_servers")


# =============================================================================
# Request/Response Models
# =============================================================================


class McpServerRegisterRequest(BaseModel):
    """Request body for registering a new MCP server."""
    name: str = Field(..., min_length=1, max_length=128, description="Display name")
    url: str = Field(..., min_length=1, max_length=512, description="Server URL/endpoint")
    description: Optional[str] = Field(None, max_length=1024, description="Optional description")
    transport: str = Field("stdio", pattern="^(stdio|http|sse)$", description="Transport type")
    credential_id: Optional[str] = Field(None, max_length=64, description="Vault credential reference")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class McpServerResponse(BaseModel):
    """Response for a single MCP server."""
    server_id: str
    name: str
    url: str
    description: Optional[str] = None
    transport: str
    status: str
    credential_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class McpServerSummary(BaseModel):
    """Summary view of an MCP server for list endpoint."""
    server_id: str
    name: str
    url: str
    status: str
    transport: str
    created_at: Optional[str] = None


class McpServerListResponse(BaseModel):
    """Response for listing MCP servers."""
    servers: List[McpServerSummary]
    total: int


class McpRegistrationResponse(BaseModel):
    """Response for server registration."""
    server_id: str
    status: str
    tools_discovered: int
    error: Optional[str] = None


class McpDiscoveryResponse(BaseModel):
    """Response for tool discovery."""
    server_id: str
    tools_discovered: int
    tools: List[Dict[str, Any]]
    error: Optional[str] = None


class McpHealthResponse(BaseModel):
    """Response for health check."""
    server_id: str
    healthy: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class McpDeleteResponse(BaseModel):
    """Response for server deletion."""
    deleted: bool


class McpToolResponse(BaseModel):
    """Response for a single tool."""
    tool_id: str
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    risk_level: str
    is_active: bool


class McpToolListResponse(BaseModel):
    """Response for listing tools."""
    tools: List[McpToolResponse]
    total: int


class McpInvocationSummary(BaseModel):
    """Summary of a tool invocation."""
    invocation_id: str
    tool_id: str
    run_id: Optional[str] = None
    status: str
    latency_ms: Optional[float] = None
    invoked_at: Optional[str] = None


class McpInvocationListResponse(BaseModel):
    """Response for listing invocations."""
    invocations: List[McpInvocationSummary]
    total: int


class McpInvokeRequest(BaseModel):
    """Request body for invoking an MCP tool."""
    input: Dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")
    run_id: Optional[str] = Field(None, description="Optional run ID for context")
    step_index: Optional[int] = Field(None, description="Optional step index in run")
    actor_id: Optional[str] = Field(None, description="Optional actor ID")
    actor_type: str = Field("machine", description="Actor type (human, machine, system)")
    trace_id: Optional[str] = Field(None, description="Optional trace ID for correlation")


class McpInvokeResponse(BaseModel):
    """Response for tool invocation."""
    invocation_id: str
    tool_id: str
    server_id: str
    status: str  # success, failure, blocked, timeout
    output: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    policy_decision: str
    policy_id: Optional[str] = None
    incident_id: Optional[str] = None


# =============================================================================
# Router
# =============================================================================

router = APIRouter(
    prefix="/integrations/mcp-servers",
    tags=["mcp-servers"],
)


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# POST / - Register MCP Server
# =============================================================================


@router.post(
    "",
    response_model=McpRegistrationResponse,
    summary="Register a new MCP server",
    description="""
    Register a new MCP server for the tenant. The server will be validated
    and tools will be discovered automatically if the server is reachable.
    """,
)
async def register_mcp_server(
    request: Request,
    body: McpServerRegisterRequest,
    session = Depends(get_session_dep),
) -> McpRegistrationResponse:
    """Register a new MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "register_server",
                    "name": body.name,
                    "url": body.url,
                    "description": body.description,
                    "transport": body.transport,
                    "credential_id": body.credential_id,
                    "metadata": body.metadata,
                },
            ),
        )
        if not op.success:
            logger.warning(f"[MCP] register_server failed: {op.error}")
            raise HTTPException(
                status_code=400 if op.error_code == "VALIDATION_ERROR" else 500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpRegistrationResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] register_server exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# GET / - List MCP Servers
# =============================================================================


@router.get(
    "",
    response_model=McpServerListResponse,
    summary="List MCP servers for tenant",
    description="""
    List all MCP servers registered by the tenant.
    Optionally include disabled servers.
    """,
)
async def list_mcp_servers(
    request: Request,
    include_disabled: Annotated[
        bool,
        Query(description="Include disabled servers"),
    ] = False,
    session = Depends(get_session_dep),
) -> McpServerListResponse:
    """List MCP servers. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_servers",
                    "include_disabled": include_disabled,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpServerListResponse(
            servers=[McpServerSummary(**s) for s in op.data["servers"]],
            total=op.data["total"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] list_servers exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# GET /{server_id} - Get MCP Server Details
# =============================================================================


@router.get(
    "/{server_id}",
    response_model=McpServerResponse,
    summary="Get MCP server details",
    description="Get detailed information about a specific MCP server.",
)
async def get_mcp_server(
    request: Request,
    server_id: str,
    session = Depends(get_session_dep),
) -> McpServerResponse:
    """Get MCP server details. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_server",
                    "server_id": server_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpServerResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] get_server exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# POST /{server_id}/discover - Discover Tools
# =============================================================================


@router.post(
    "/{server_id}/discover",
    response_model=McpDiscoveryResponse,
    summary="Discover tools from MCP server",
    description="""
    Connect to the MCP server and discover available tools.
    Updates the stored tool list with new tools and marks removed tools as inactive.
    """,
)
async def discover_mcp_tools(
    request: Request,
    server_id: str,
    session = Depends(get_session_dep),
) -> McpDiscoveryResponse:
    """Discover tools from MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "discover_tools",
                    "server_id": server_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpDiscoveryResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] discover_tools exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# GET /{server_id}/health - Health Check
# =============================================================================


@router.get(
    "/{server_id}/health",
    response_model=McpHealthResponse,
    summary="Check MCP server health",
    description="Ping the MCP server to check if it's healthy and reachable.",
)
async def check_mcp_health(
    request: Request,
    server_id: str,
    session = Depends(get_session_dep),
) -> McpHealthResponse:
    """Health check MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "health_check",
                    "server_id": server_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpHealthResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] health_check exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# DELETE /{server_id} - Delete MCP Server
# =============================================================================


@router.delete(
    "/{server_id}",
    response_model=McpDeleteResponse,
    summary="Delete MCP server",
    description="""
    Soft-delete an MCP server. The server and its tools are marked as disabled
    but retained for audit trail. Invocation history is preserved.
    """,
)
async def delete_mcp_server(
    request: Request,
    server_id: str,
    session = Depends(get_session_dep),
) -> McpDeleteResponse:
    """Delete MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "delete_server",
                    "server_id": server_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpDeleteResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] delete_server exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# GET /{server_id}/tools - List Server Tools
# =============================================================================


@router.get(
    "/{server_id}/tools",
    response_model=McpToolListResponse,
    summary="List tools for MCP server",
    description="List all tools discovered from an MCP server.",
)
async def list_mcp_tools(
    request: Request,
    server_id: str,
    session = Depends(get_session_dep),
) -> McpToolListResponse:
    """List tools for MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_tools",
                    "server_id": server_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpToolListResponse(
            tools=[McpToolResponse(**t) for t in op.data["tools"]],
            total=op.data["total"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] list_tools exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# GET /{server_id}/invocations - List Invocations
# =============================================================================


@router.get(
    "/{server_id}/invocations",
    response_model=McpInvocationListResponse,
    summary="List tool invocations for MCP server",
    description="List recent tool invocations for monitoring and audit.",
)
async def list_mcp_invocations(
    request: Request,
    server_id: str,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
    session = Depends(get_session_dep),
) -> McpInvocationListResponse:
    """List invocations for MCP server. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_invocations",
                    "server_id": server_id,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": "Server not found"},
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpInvocationListResponse(
            invocations=[McpInvocationSummary(**inv) for inv in op.data["invocations"]],
            total=op.data["total"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] list_invocations exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )


# =============================================================================
# POST /{server_id}/tools/{tool_id}/invoke - Invoke Tool (Phase 4)
# =============================================================================


@router.post(
    "/{server_id}/tools/{tool_id}/invoke",
    response_model=McpInvokeResponse,
    summary="Invoke an MCP tool (governed)",
    description="""
    Invoke an MCP tool with full governance:
    - Policy validation before execution
    - Audit trail emission for compliance
    - Incident creation on failures
    - Invocation recording for analytics

    Returns the invocation result with output or error details.
    """,
)
async def invoke_mcp_tool(
    request: Request,
    server_id: str,
    tool_id: str,
    body: McpInvokeRequest,
    session = Depends(get_session_dep),
) -> McpInvokeResponse:
    """Invoke an MCP tool with governance. Tenant-scoped."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "integrations.mcp_servers",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "invoke_tool",
                    "server_id": server_id,
                    "tool_id": tool_id,
                    "input": body.input,
                    "run_id": body.run_id,
                    "step_index": body.step_index,
                    "actor_id": body.actor_id,
                    "actor_type": body.actor_type,
                    "trace_id": body.trace_id,
                },
            ),
        )
        if not op.success:
            if op.error_code == "NOT_FOUND":
                raise HTTPException(
                    status_code=404,
                    detail={"error": "not_found", "message": op.error or "Resource not found"},
                )
            if op.error_code == "POLICY_DENIED":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "policy_denied",
                        "message": op.error or "Policy denied tool invocation",
                    },
                )
            raise HTTPException(
                status_code=500,
                detail={"error": op.error_code, "message": op.error},
            )
        return McpInvokeResponse(**op.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MCP] invoke_tool exception: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)},
        )
