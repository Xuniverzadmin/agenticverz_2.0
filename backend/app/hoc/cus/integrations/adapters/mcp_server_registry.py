# Layer: L3 — cus/integrations/adapters
# AUDIENCE: CUSTOMER
# PHASE: W0
# Product: system-wide
# Wiring Type: registry
# Parent Gap: GAP-063 (MCPConnector)
# Temporal:
#   Trigger: api (MCP server management)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: mcp_servers (SQL)
#   Writes: mcp_servers (SQL)
# Database:
#   Scope: integrations
#   Models: mcp_servers (via SQL)
# Role: Registry for external MCP servers — relocated from hoc_spine/mcp/ (orphaned, zero callers)
# Callers: L2 API routes, skill execution
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L4, L5
# Reference: PIN-470, GAP-141, HOC_integrations_analysis_v1.md, HOC_LAYER_TOPOLOGY_V2.0.0.md
# Relocated: 2026-01-29 from backend/app/hoc/cus/hoc_spine/mcp/server_registry.py

"""
Module: server_registry
Purpose: Registry for external MCP servers.

Provides:
    - MCP server registration
    - Server capability discovery
    - Health monitoring
    - Tenant-scoped access control

Database Table: mcp_servers (requires GAP-170 migration)

MCP Protocol Reference: https://modelcontextprotocol.io/specification

Acceptance Criteria:
    - AC-141-01: Servers can be registered
    - AC-141-02: Tool discovery via MCP protocol
    - AC-141-03: Health monitoring
    - AC-141-04: Tenant isolation
    - AC-141-05: Status tracking
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.mcp.server_registry")


class MCPServerStatus(str, Enum):
    """Status of an MCP server."""

    PENDING = "pending"  # Registered but not validated
    ACTIVE = "active"  # Healthy and operational
    DEGRADED = "degraded"  # Partially operational
    OFFLINE = "offline"  # Not responding
    SUSPENDED = "suspended"  # Administratively suspended


class MCPCapability(str, Enum):
    """Standard MCP capabilities."""

    TOOLS = "tools"  # Server provides tools
    RESOURCES = "resources"  # Server provides resources
    PROMPTS = "prompts"  # Server provides prompts
    SAMPLING = "sampling"  # Server can sample from models


@dataclass
class MCPTool:
    """
    Tool exposed by MCP server.

    Represents a tool that can be invoked via MCP protocol.
    """

    tool_id: str
    server_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    requires_policy: bool = True  # Whether policy check is required
    is_dangerous: bool = False  # Whether tool can have side effects
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_id": self.tool_id,
            "server_id": self.server_id,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "requires_policy": self.requires_policy,
            "is_dangerous": self.is_dangerous,
            "metadata": self.metadata,
        }


@dataclass
class MCPServer:
    """
    Registered MCP server.

    Represents an external MCP server that has been registered
    with the system for tool invocation.
    """

    server_id: str
    tenant_id: str
    name: str
    url: str
    status: MCPServerStatus
    capabilities: List[str]
    registered_at: datetime
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    metadata: Optional[Dict[str, Any]] = None
    tools: List[MCPTool] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "server_id": self.server_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "url": self.url,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "registered_at": self.registered_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_failures": self.health_check_failures,
            "tool_count": len(self.tools),
            "metadata": self.metadata,
        }


@dataclass
class MCPRegistrationResult:
    """Result of MCP server registration."""

    success: bool
    server: Optional[MCPServer] = None
    error: Optional[str] = None
    tool_count: int = 0


class MCPServerRegistry:
    """
    Registry for MCP servers and their tools.

    GAP-141: Provides registration API for external MCP servers.
    GAP-142: Tool→Policy mapping (separate module).
    GAP-143: Audit evidence emission (separate module).

    This registry:
    1. Manages MCP server registrations
    2. Discovers server capabilities and tools
    3. Monitors server health
    4. Enforces tenant isolation
    """

    # Health check constants
    HEALTH_CHECK_TIMEOUT_SECONDS = 10
    MAX_HEALTH_CHECK_FAILURES = 3

    def __init__(self):
        """Initialize registry with in-memory storage."""
        self._servers: Dict[str, MCPServer] = {}
        self._servers_by_tenant: Dict[str, List[str]] = {}

    async def register_server(
        self,
        tenant_id: str,
        name: str,
        url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MCPRegistrationResult:
        """
        Register a new MCP server.

        Discovers tools via MCP protocol and registers them.

        Args:
            tenant_id: Tenant registering the server
            name: Human-readable server name
            url: MCP server URL
            capabilities: Optional list of capabilities (discovered if not provided)
            metadata: Optional metadata

        Returns:
            MCPRegistrationResult with registration outcome
        """
        server_id = str(uuid.uuid4())

        logger.info(
            "mcp_registry.registering",
            extra={
                "tenant_id": tenant_id,
                "name": name,
                "url": url,
            },
        )

        try:
            # Discover capabilities via MCP handshake
            discovered_capabilities = await self._discover_capabilities(url)

            # Create server record
            server = MCPServer(
                server_id=server_id,
                tenant_id=tenant_id,
                name=name,
                url=url,
                status=MCPServerStatus.PENDING,
                capabilities=capabilities or discovered_capabilities,
                registered_at=datetime.now(timezone.utc),
                metadata=metadata,
            )

            # Discover and register tools
            if MCPCapability.TOOLS.value in server.capabilities:
                tools = await self._discover_tools(server_id, url)
                server.tools = tools

            # Store server
            self._servers[server_id] = server
            if tenant_id not in self._servers_by_tenant:
                self._servers_by_tenant[tenant_id] = []
            self._servers_by_tenant[tenant_id].append(server_id)

            # Perform initial health check
            is_healthy = await self._health_check(server_id)
            if is_healthy:
                server.status = MCPServerStatus.ACTIVE

            logger.info(
                "mcp_registry.registered",
                extra={
                    "server_id": server_id,
                    "tenant_id": tenant_id,
                    "name": name,
                    "status": server.status.value,
                    "tool_count": len(server.tools),
                },
            )

            return MCPRegistrationResult(
                success=True,
                server=server,
                tool_count=len(server.tools),
            )

        except Exception as e:
            logger.error(
                "mcp_registry.registration_failed",
                extra={
                    "tenant_id": tenant_id,
                    "name": name,
                    "url": url,
                    "error": str(e),
                },
            )
            return MCPRegistrationResult(
                success=False,
                error=str(e),
            )

    async def unregister_server(
        self,
        server_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Unregister an MCP server.

        Args:
            server_id: Server to unregister
            tenant_id: Tenant making the request (for authorization)

        Returns:
            True if unregistered, False if not found or unauthorized
        """
        server = self._servers.get(server_id)
        if server is None:
            return False

        # Verify tenant ownership
        if server.tenant_id != tenant_id:
            logger.warning(
                "mcp_registry.unauthorized_unregister",
                extra={
                    "server_id": server_id,
                    "requesting_tenant": tenant_id,
                    "owning_tenant": server.tenant_id,
                },
            )
            return False

        # Remove from storage
        del self._servers[server_id]
        if tenant_id in self._servers_by_tenant:
            self._servers_by_tenant[tenant_id] = [
                sid for sid in self._servers_by_tenant[tenant_id]
                if sid != server_id
            ]

        logger.info(
            "mcp_registry.unregistered",
            extra={"server_id": server_id, "tenant_id": tenant_id},
        )

        return True

    async def get_server(
        self,
        server_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[MCPServer]:
        """
        Get server by ID.

        Args:
            server_id: Server identifier
            tenant_id: Optional tenant filter (for access control)

        Returns:
            MCPServer if found and accessible, None otherwise
        """
        server = self._servers.get(server_id)
        if server is None:
            return None

        # Check tenant access if specified
        if tenant_id is not None and server.tenant_id != tenant_id:
            return None

        return server

    async def list_servers(
        self,
        tenant_id: str,
        status: Optional[MCPServerStatus] = None,
    ) -> List[MCPServer]:
        """
        List servers for tenant.

        Args:
            tenant_id: Tenant identifier
            status: Optional status filter

        Returns:
            List of servers matching criteria
        """
        server_ids = self._servers_by_tenant.get(tenant_id, [])
        servers = [self._servers[sid] for sid in server_ids if sid in self._servers]

        if status is not None:
            servers = [s for s in servers if s.status == status]

        return servers

    async def get_tools(
        self,
        server_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[MCPTool]:
        """
        Get tools for server.

        Args:
            server_id: Server identifier
            tenant_id: Optional tenant filter (for access control)

        Returns:
            List of tools, empty if server not found
        """
        server = await self.get_server(server_id, tenant_id)
        if server is None:
            return []
        return server.tools

    async def get_tool(
        self,
        server_id: str,
        tool_name: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[MCPTool]:
        """
        Get a specific tool by name.

        Args:
            server_id: Server identifier
            tool_name: Tool name
            tenant_id: Optional tenant filter

        Returns:
            MCPTool if found, None otherwise
        """
        tools = await self.get_tools(server_id, tenant_id)
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    async def refresh_tools(self, server_id: str) -> List[MCPTool]:
        """
        Refresh tool list from server.

        Args:
            server_id: Server to refresh

        Returns:
            Updated list of tools
        """
        server = self._servers.get(server_id)
        if server is None:
            return []

        tools = await self._discover_tools(server_id, server.url)
        server.tools = tools

        logger.info(
            "mcp_registry.tools_refreshed",
            extra={"server_id": server_id, "tool_count": len(tools)},
        )

        return tools

    async def check_health(self, server_id: str) -> bool:
        """
        Check server health.

        Args:
            server_id: Server to check

        Returns:
            True if healthy, False otherwise
        """
        return await self._health_check(server_id)

    async def _discover_capabilities(self, url: str) -> List[str]:
        """
        Discover server capabilities via MCP protocol.

        TODO: Implement actual MCP initialize/list_capabilities call
        """
        # Default capabilities for now
        logger.debug(
            "mcp_registry.discovering_capabilities",
            extra={"url": url},
        )
        return [MCPCapability.TOOLS.value, MCPCapability.RESOURCES.value]

    async def _discover_tools(
        self,
        server_id: str,
        url: str,
    ) -> List[MCPTool]:
        """
        Discover tools exposed by server.

        TODO: Implement actual MCP tools/list call
        """
        logger.debug(
            "mcp_registry.discovering_tools",
            extra={"server_id": server_id, "url": url},
        )

        # Return empty for now - actual implementation would call MCP protocol
        return []

    async def _health_check(self, server_id: str) -> bool:
        """
        Check server health and update status.

        Args:
            server_id: Server to check

        Returns:
            True if healthy, False otherwise
        """
        server = self._servers.get(server_id)
        if server is None:
            return False

        logger.debug(
            "mcp_registry.health_check",
            extra={"server_id": server_id, "url": server.url},
        )

        try:
            # TODO: Implement actual MCP ping/health check
            # For now, assume healthy
            is_healthy = True

            if is_healthy:
                server.status = MCPServerStatus.ACTIVE
                server.health_check_failures = 0
            else:
                server.health_check_failures += 1
                if server.health_check_failures >= self.MAX_HEALTH_CHECK_FAILURES:
                    server.status = MCPServerStatus.OFFLINE
                else:
                    server.status = MCPServerStatus.DEGRADED

            server.last_health_check = datetime.now(timezone.utc)
            return is_healthy

        except Exception as e:
            logger.warning(
                "mcp_registry.health_check_failed",
                extra={"server_id": server_id, "error": str(e)},
            )
            server.health_check_failures += 1
            if server.health_check_failures >= self.MAX_HEALTH_CHECK_FAILURES:
                server.status = MCPServerStatus.OFFLINE
            else:
                server.status = MCPServerStatus.DEGRADED
            server.last_health_check = datetime.now(timezone.utc)
            return False


# =========================
# Singleton Management
# =========================

_mcp_registry: Optional[MCPServerRegistry] = None


def get_mcp_registry() -> MCPServerRegistry:
    """
    Get or create the singleton MCPServerRegistry.

    Returns:
        MCPServerRegistry instance
    """
    global _mcp_registry

    if _mcp_registry is None:
        _mcp_registry = MCPServerRegistry()
        logger.info("mcp_registry.created")

    return _mcp_registry


def configure_mcp_registry() -> MCPServerRegistry:
    """
    Configure the singleton MCPServerRegistry.

    Returns:
        Configured MCPServerRegistry
    """
    global _mcp_registry

    _mcp_registry = MCPServerRegistry()

    logger.info("mcp_registry.configured")

    return _mcp_registry


def reset_mcp_registry() -> None:
    """Reset the singleton (for testing)."""
    global _mcp_registry
    _mcp_registry = None
