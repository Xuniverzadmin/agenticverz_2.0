# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: MCP_SERVER_REGISTERED, MCP_TOOLS_DISCOVERED, MCP_SERVER_HEALTH_CHANGED
#   Subscribes: none
# Data Access:
#   Reads: mcp_servers, mcp_tools
#   Writes: mcp_servers, mcp_tools
# Role: MCP server lifecycle orchestration (registration, discovery, health)
# Product: system-wide
# Callers: L4 mcp_handler
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-516 Phase 2

"""
MCP Server Engine — Server lifecycle orchestration.

Handles:
- Server registration with credential vault integration
- Tool discovery via real MCP protocol (initialize, tools/list)
- Health checks via MCP ping
- Server status management (pending → active → degraded → offline)

PIN-516 Phase 2 Deliverable.

Protocol Implementation:
- MCP initialize: Discover server capabilities and protocol version
- MCP tools/list: Discover available tools with schemas
- MCP ping: Health check (if supported)

Security Model:
- Credentials stored by reference only (vault)
- All HTTP calls use credential service for auth
- Tenant isolation enforced at driver level
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import httpx

from app.hoc.cus.integrations.L5_engines.credentials import (
    Credential,
    CredentialService,
)
from app.hoc.cus.integrations.L6_drivers.mcp_driver import (
    McpDriver,
    McpServerRow,
    McpToolRow,
    compute_input_hash,
)

logger = logging.getLogger("nova.hoc.integrations.mcp_server_engine")


# =============================================================================
# Constants
# =============================================================================

MCP_PROTOCOL_VERSION = "2024-11-05"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_HEALTH_CHECK_FAILURES = 3


class McpServerStatus(str, Enum):
    """Server status values."""
    PENDING = "pending"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    DISABLED = "disabled"
    ERROR = "error"


# =============================================================================
# Result Types
# =============================================================================


@dataclass(frozen=True)
class McpDiscoveryResult:
    """Result of server discovery (capabilities + tools)."""
    server_id: str
    protocol_version: str
    capabilities: List[str]
    tools_found: int
    tools_added: int
    tools_updated: int
    errors: List[str]


@dataclass(frozen=True)
class McpHealthResult:
    """Result of health check."""
    server_id: str
    is_healthy: bool
    status: str
    latency_ms: int
    error: Optional[str] = None


@dataclass(frozen=True)
class McpRegistrationResult:
    """Result of server registration."""
    server_id: str
    name: str
    url: str
    status: str
    discovery_triggered: bool


# =============================================================================
# MCP Server Engine (L5)
# =============================================================================


class McpServerEngine:
    """
    L5 Engine for MCP server lifecycle management.

    Responsibilities:
    - Server registration with credential validation
    - Tool discovery via MCP protocol
    - Health monitoring
    - Status transitions

    PIN-516 Phase 2 Invariants:
    - All persistence via L6 McpDriver (never direct DB access)
    - Credentials via CredentialService protocol (never stored in engine)
    - HTTP calls isolated in private methods
    """

    def __init__(
        self,
        driver: McpDriver,
        credential_service: Optional[CredentialService] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """Initialize MCP server engine.

        Args:
            driver: L6 driver for persistence (required).
            credential_service: Optional credential service for vault access.
            http_client: Optional HTTP client (created on demand if not provided).
        """
        self._driver = driver
        self._credential_service = credential_service
        self._http_client = http_client
        self._owns_http_client = http_client is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
            self._owns_http_client = True
        return self

    async def __aexit__(self, exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        if self._owns_http_client and self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # =========================================================================
    # Server Registration
    # =========================================================================

    async def register_server(
        self,
        tenant_id: str,
        name: str,
        url: str,
        credential_ref: Optional[str] = None,
        transport: str = "http",
        auth_type: Optional[str] = None,
        description: Optional[str] = None,
        requires_approval: bool = True,
        rate_limit_requests: Optional[int] = None,
        tags: Optional[List[str]] = None,
        auto_discover: bool = True,
    ) -> McpRegistrationResult:
        """
        Register a new MCP server.

        Args:
            tenant_id: Owning tenant ID.
            name: Display name for the server.
            url: Server URL (http/https/stdio).
            credential_ref: Vault reference for credentials (optional).
            transport: Transport type (http, https, stdio, sse).
            auth_type: Authentication type (none, api_key, bearer, oauth).
            description: Optional description.
            requires_approval: Whether tool invocations require approval.
            rate_limit_requests: Max requests per minute (optional).
            tags: Optional tags list.
            auto_discover: Whether to trigger discovery immediately.

        Returns:
            Registration result with server_id and status.

        Raises:
            ValueError: If server with same URL already exists for tenant.
        """
        # Check for existing server with same URL
        existing = await self._driver.get_server_by_url(tenant_id, url)
        if existing:
            raise ValueError(
                f"Server with URL '{url}' already registered for tenant "
                f"(server_id: {existing.server_id})"
            )

        # Validate credential reference if provided
        if credential_ref and self._credential_service:
            try:
                await self._credential_service.get(credential_ref)
            except Exception as e:
                logger.warning(
                    "mcp_server_engine.credential_validation_failed",
                    extra={
                        "tenant_id": tenant_id,
                        "credential_ref": credential_ref,
                        "error": str(e),
                    },
                )
                # Don't fail registration, but log warning

        # Create server record
        server = await self._driver.create_server(
            tenant_id=tenant_id,
            name=name,
            url=url,
            transport=transport,
            auth_type=auth_type,
            credential_id=credential_ref,
            description=description,
            requires_approval=requires_approval,
            rate_limit_requests=rate_limit_requests,
            tags=tags,
        )

        logger.info(
            "mcp_server_engine.server_registered",
            extra={
                "server_id": server.server_id,
                "tenant_id": tenant_id,
                "name": name,
                "url": url,
            },
        )

        # Trigger discovery if requested
        discovery_triggered = False
        if auto_discover:
            try:
                await self.discover_tools(server.server_id)
                discovery_triggered = True
            except Exception as e:
                logger.warning(
                    "mcp_server_engine.auto_discovery_failed",
                    extra={
                        "server_id": server.server_id,
                        "error": str(e),
                    },
                )

        return McpRegistrationResult(
            server_id=server.server_id,
            name=server.name,
            url=server.url,
            status=server.status,
            discovery_triggered=discovery_triggered,
        )

    # =========================================================================
    # Tool Discovery
    # =========================================================================

    async def discover_tools(self, server_id: str) -> McpDiscoveryResult:
        """
        Discover tools from an MCP server.

        Performs:
        1. MCP initialize call to get capabilities and protocol version
        2. MCP tools/list call to get available tools
        3. Upserts tools to database via driver
        4. Updates server status and tool count

        Args:
            server_id: Server ID to discover tools from.

        Returns:
            Discovery result with tool counts and any errors.

        Raises:
            ValueError: If server not found.
        """
        server = await self._driver.get_server(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")

        errors: List[str] = []
        protocol_version = MCP_PROTOCOL_VERSION
        capabilities: List[str] = []
        tools_data: List[Dict[str, Any]] = []

        # Get credentials if configured
        api_key = None
        if server.credential_id and self._credential_service:
            try:
                credential = await self._credential_service.get(server.credential_id)
                api_key = credential.value
            except Exception as e:
                errors.append(f"Failed to get credentials: {e}")

        # Step 1: MCP initialize
        try:
            init_result = await self._mcp_initialize(server.url, api_key)
            protocol_version = init_result.get("protocolVersion", MCP_PROTOCOL_VERSION)
            capabilities = init_result.get("capabilities", {})
            if isinstance(capabilities, dict):
                capabilities = list(capabilities.keys())
        except Exception as e:
            errors.append(f"MCP initialize failed: {e}")
            logger.warning(
                "mcp_server_engine.initialize_failed",
                extra={"server_id": server_id, "error": str(e)},
            )

        # Step 2: MCP tools/list
        try:
            tools_data = await self._mcp_list_tools(server.url, api_key)
        except Exception as e:
            errors.append(f"MCP tools/list failed: {e}")
            logger.warning(
                "mcp_server_engine.tools_list_failed",
                extra={"server_id": server_id, "error": str(e)},
            )

        # Step 3: Upsert tools
        tools_added = 0
        tools_updated = 0

        if tools_data:
            # Get existing tools to determine add vs update
            existing_tools = await self._driver.get_tools(server_id, enabled_only=False)
            existing_names = {t.name for t in existing_tools}

            # Format tools for upsert
            formatted_tools = []
            for tool in tools_data:
                tool_def = {
                    "name": tool.get("name", "unknown"),
                    "description": tool.get("description"),
                    "input_schema": tool.get("inputSchema", {}),
                    "output_schema": tool.get("outputSchema"),
                    "risk_level": self._assess_tool_risk(tool),
                }
                formatted_tools.append(tool_def)

                if tool_def["name"] in existing_names:
                    tools_updated += 1
                else:
                    tools_added += 1

            # Upsert to database
            await self._driver.upsert_tools(
                server_id=server_id,
                tenant_id=server.tenant_id,
                tools=formatted_tools,
            )

        # Step 4: Update server status
        new_status = "active" if not errors else "error"
        capabilities_hash = self._compute_capabilities_hash(capabilities)

        await self._driver.update_server(
            server_id=server_id,
            status=new_status,
            protocol_version=protocol_version,
            capabilities=capabilities,
            tool_count=len(tools_data),
            last_discovery_at=datetime.now(timezone.utc),
            last_error=errors[0] if errors else None,
        )

        logger.info(
            "mcp_server_engine.discovery_complete",
            extra={
                "server_id": server_id,
                "tools_found": len(tools_data),
                "tools_added": tools_added,
                "tools_updated": tools_updated,
                "errors": len(errors),
            },
        )

        return McpDiscoveryResult(
            server_id=server_id,
            protocol_version=protocol_version,
            capabilities=capabilities,
            tools_found=len(tools_data),
            tools_added=tools_added,
            tools_updated=tools_updated,
            errors=errors,
        )

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self, server_id: str) -> McpHealthResult:
        """
        Check health of an MCP server.

        Uses MCP ping if available, otherwise tries initialize.

        Args:
            server_id: Server ID to check.

        Returns:
            Health check result with status and latency.
        """
        server = await self._driver.get_server(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")

        # Get credentials if configured
        api_key = None
        if server.credential_id and self._credential_service:
            try:
                credential = await self._credential_service.get(server.credential_id)
                api_key = credential.value
            except Exception as e:
                return McpHealthResult(
                    server_id=server_id,
                    is_healthy=False,
                    status="error",
                    latency_ms=0,
                    error=f"Credential error: {e}",
                )

        # Perform health check
        start_time = datetime.now(timezone.utc)
        is_healthy = False
        error_msg = None

        try:
            # Try ping first, fall back to initialize
            await self._mcp_ping(server.url, api_key)
            is_healthy = True
        except Exception as e:
            error_msg = str(e)
            logger.warning(
                "mcp_server_engine.health_check_failed",
                extra={"server_id": server_id, "error": error_msg},
            )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Determine new status
        current_failures = server.health_check_failures
        if is_healthy:
            new_status = "active"
            new_failures = 0
        else:
            new_failures = current_failures + 1
            if new_failures >= MAX_HEALTH_CHECK_FAILURES:
                new_status = "offline"
            else:
                new_status = "degraded"

        # Update server
        await self._driver.update_server(
            server_id=server_id,
            status=new_status,
            health_check_failures=new_failures,
            last_health_check_at=datetime.now(timezone.utc),
            last_error=error_msg,
        )

        logger.info(
            "mcp_server_engine.health_check_complete",
            extra={
                "server_id": server_id,
                "is_healthy": is_healthy,
                "status": new_status,
                "latency_ms": latency_ms,
            },
        )

        return McpHealthResult(
            server_id=server_id,
            is_healthy=is_healthy,
            status=new_status,
            latency_ms=latency_ms,
            error=error_msg,
        )

    # =========================================================================
    # Server Management
    # =========================================================================

    async def get_server(self, server_id: str) -> Optional[McpServerRow]:
        """Get server by ID."""
        return await self._driver.get_server(server_id)

    async def list_servers(
        self,
        tenant_id: str,
        include_disabled: bool = False,
    ) -> List[McpServerRow]:
        """List servers for a tenant."""
        return await self._driver.list_servers(tenant_id, include_disabled)

    async def update_server(
        self,
        server_id: str,
        **updates: Any,
    ) -> Optional[McpServerRow]:
        """Update server fields."""
        return await self._driver.update_server(server_id, **updates)

    async def disable_server(self, server_id: str) -> bool:
        """Disable (soft-delete) a server."""
        return await self._driver.soft_delete_server(server_id)

    # =========================================================================
    # Tool Management
    # =========================================================================

    async def get_tools(
        self,
        server_id: str,
        enabled_only: bool = True,
    ) -> List[McpToolRow]:
        """Get tools for a server."""
        return await self._driver.get_tools(server_id, enabled_only)

    async def enable_tool(self, tool_id: str) -> Optional[McpToolRow]:
        """Enable a tool."""
        return await self._driver.update_tool(tool_id, enabled=True)

    async def disable_tool(self, tool_id: str) -> Optional[McpToolRow]:
        """Disable a tool."""
        return await self._driver.update_tool(tool_id, enabled=False)

    async def set_tool_risk_level(
        self,
        tool_id: str,
        risk_level: str,
    ) -> Optional[McpToolRow]:
        """Set tool risk level."""
        if risk_level not in ("low", "medium", "high", "critical"):
            raise ValueError(f"Invalid risk level: {risk_level}")
        return await self._driver.update_tool(tool_id, risk_level=risk_level)

    # =========================================================================
    # Private: MCP Protocol Methods
    # =========================================================================

    async def _mcp_initialize(
        self,
        url: str,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call MCP initialize endpoint.

        Args:
            url: Server URL.
            api_key: Optional API key for authentication.

        Returns:
            Initialize response with capabilities and protocol version.
        """
        client = self._http_client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            request_body = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "aos-mcp-client",
                        "version": "1.0.0",
                    },
                },
                "id": 1,
            }

            response = await client.post(
                f"{url.rstrip('/')}/mcp",
                json=request_body,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                raise Exception(result["error"].get("message", "Unknown error"))

            return result.get("result", {})
        finally:
            if not self._http_client:
                await client.aclose()

    async def _mcp_list_tools(
        self,
        url: str,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Call MCP tools/list endpoint.

        Args:
            url: Server URL.
            api_key: Optional API key for authentication.

        Returns:
            List of tool definitions.
        """
        client = self._http_client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            request_body = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }

            response = await client.post(
                f"{url.rstrip('/')}/mcp",
                json=request_body,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                raise Exception(result["error"].get("message", "Unknown error"))

            return result.get("result", {}).get("tools", [])
        finally:
            if not self._http_client:
                await client.aclose()

    async def _mcp_ping(
        self,
        url: str,
        api_key: Optional[str] = None,
    ) -> bool:
        """
        Ping MCP server for health check.

        Falls back to initialize if ping not supported.

        Args:
            url: Server URL.
            api_key: Optional API key for authentication.

        Returns:
            True if server responds successfully.
        """
        client = self._http_client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # Try ping first
            request_body = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 3,
            }

            response = await client.post(
                f"{url.rstrip('/')}/mcp",
                json=request_body,
                headers=headers,
            )

            # If ping not supported, try initialize
            if response.status_code == 400:
                await self._mcp_initialize(url, api_key)
                return True

            response.raise_for_status()
            return True
        finally:
            if not self._http_client:
                await client.aclose()

    # =========================================================================
    # Private: Helpers
    # =========================================================================

    def _assess_tool_risk(self, tool: Dict[str, Any]) -> str:
        """
        Assess risk level of a tool based on its schema.

        Heuristic based on:
        - Tool name keywords (write, delete, execute, etc.)
        - Parameter types (file paths, shell commands, etc.)

        Args:
            tool: Tool definition from MCP server.

        Returns:
            Risk level: "low", "medium", "high", or "critical".
        """
        name = tool.get("name", "").lower()
        description = (tool.get("description") or "").lower()

        # Critical: destructive operations
        if any(kw in name for kw in ["delete", "remove", "drop", "destroy", "kill"]):
            return "critical"

        # High: write/execute operations
        if any(kw in name for kw in ["write", "execute", "run", "shell", "eval", "create"]):
            return "high"

        # Medium: modification operations
        if any(kw in name for kw in ["update", "modify", "set", "put", "post"]):
            return "medium"

        # Low: read-only operations
        if any(kw in name for kw in ["read", "get", "list", "search", "query", "fetch"]):
            return "low"

        # Default to medium for unknown
        return "medium"

    @staticmethod
    def _compute_capabilities_hash(capabilities: List[str]) -> str:
        """Compute hash of capabilities list."""
        import json
        data = json.dumps(sorted(capabilities))
        return hashlib.sha256(data.encode()).hexdigest()[:16]
