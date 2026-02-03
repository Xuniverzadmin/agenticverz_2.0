# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: MCP Server Persistence Driver
# Reference: PIN-516 Phase 1
"""MCP Driver - Pure persistence layer for MCP servers and tools.

L6 driver for MCP server data access.

Pure persistence - no business logic, no protocol calls.
All methods accept primitive parameters and return raw facts.

PIN-516 Invariants:
- INV-2: Pure CRUD only (no HTTP, no MCP protocol, no health checks)
- INV-3: Credentials stored by reference only
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_models import (
    McpServer,
    McpTool,
    McpToolInvocation,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Transfer Objects (Frozen Dataclasses)
# =============================================================================


@dataclass(frozen=True)
class McpServerRow:
    """Immutable DTO for MCP server database row."""

    id: int
    server_id: str
    tenant_id: str
    name: str
    url: str
    description: Optional[str]
    transport: str
    auth_type: Optional[str]
    credential_id: Optional[str]
    status: str
    protocol_version: Optional[str]
    capabilities: List[str]
    tool_count: int
    resource_count: int
    requires_approval: bool
    rate_limit_requests: Optional[int]
    rate_limit_window_seconds: Optional[int]
    health_check_failures: int
    last_health_check_at: Optional[datetime]
    last_discovery_at: Optional[datetime]
    last_error: Optional[str]
    tags: List[str]
    extra_metadata: Optional[Dict[str, Any]]
    registered_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class McpToolRow:
    """Immutable DTO for MCP tool database row."""

    id: int
    tool_id: str
    server_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    risk_level: str
    enabled: bool
    requires_policy: bool
    policy_id: Optional[str]
    invocation_count: int
    failure_count: int
    last_invoked_at: Optional[datetime]
    discovered_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class McpInvocationRow:
    """Immutable DTO for MCP tool invocation database row."""

    id: int
    invocation_id: str
    tool_id: Optional[str]
    server_id: str
    tenant_id: str
    run_id: Optional[str]
    step_index: Optional[int]
    actor_id: Optional[str]
    actor_type: str
    tool_name: str
    input_hash: str
    input_preview: Optional[str]
    policy_id: Optional[str]
    policy_snapshot_id: Optional[str]
    policy_decision: str
    policy_reason: Optional[str]
    outcome: str
    output_hash: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[int]
    invoked_at: datetime
    completed_at: Optional[datetime]
    recorded_at: datetime


# =============================================================================
# MCP Driver (L6 - Pure CRUD)
# =============================================================================


class McpDriver:
    """L6 driver for MCP persistence.

    Pure CRUD operations only. No protocol logic.

    PIN-516 INV-2 Enforcement:
    - NO HTTP calls
    - NO MCP protocol logic
    - NO health checks
    - NO JSON-RPC parsing
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session.

        Args:
            session: SQLAlchemy async session for DB operations.
        """
        self._session = session

    # =========================================================================
    # Server Operations
    # =========================================================================

    async def create_server(
        self,
        tenant_id: str,
        name: str,
        url: str,
        transport: str = "http",
        auth_type: Optional[str] = None,
        credential_id: Optional[str] = None,
        description: Optional[str] = None,
        requires_approval: bool = True,
        rate_limit_requests: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> McpServerRow:
        """Create a new MCP server record.

        Args:
            tenant_id: Owning tenant ID.
            name: Server display name.
            url: Server URL.
            transport: Transport type (http, https, stdio, sse, websocket).
            auth_type: Authentication type (none, api_key, oauth, bearer, basic).
            credential_id: Vault reference for credentials (NEVER plaintext).
            description: Optional description.
            requires_approval: Whether tool invocations require approval.
            rate_limit_requests: Max requests per minute (optional).
            tags: Optional tags list.
            metadata: Optional metadata dict.

        Returns:
            Created server as frozen DTO.
        """
        server_id = f"mcp_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        server = McpServer(
            server_id=server_id,
            tenant_id=tenant_id,
            name=name,
            url=url,
            description=description,
            transport=transport,
            auth_type=auth_type,
            credential_id=credential_id,
            status="pending",
            capabilities=[],
            tool_count=0,
            resource_count=0,
            requires_approval=requires_approval,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window_seconds=60 if rate_limit_requests else None,
            health_check_failures=0,
            tags=tags or [],
            extra_metadata=metadata,
            registered_at=now,
            updated_at=now,
        )

        self._session.add(server)
        await self._session.flush()
        await self._session.refresh(server)

        return self._server_to_row(server)

    async def get_server(self, server_id: str) -> Optional[McpServerRow]:
        """Get server by ID.

        Args:
            server_id: Server ID to fetch.

        Returns:
            Server row or None if not found.
        """
        stmt = select(McpServer).where(McpServer.server_id == server_id)
        result = await self._session.execute(stmt)
        server = result.scalar_one_or_none()
        return self._server_to_row(server) if server else None

    async def get_server_by_url(
        self, tenant_id: str, url: str
    ) -> Optional[McpServerRow]:
        """Get server by tenant and URL.

        Args:
            tenant_id: Tenant ID.
            url: Server URL.

        Returns:
            Server row or None if not found.
        """
        stmt = select(McpServer).where(
            and_(
                McpServer.tenant_id == tenant_id,
                McpServer.url == url,
            )
        )
        result = await self._session.execute(stmt)
        server = result.scalar_one_or_none()
        return self._server_to_row(server) if server else None

    async def list_servers(
        self,
        tenant_id: str,
        include_disabled: bool = False,
    ) -> List[McpServerRow]:
        """List servers for a tenant.

        Args:
            tenant_id: Tenant ID.
            include_disabled: Include disabled/deleted servers.

        Returns:
            List of server rows.
        """
        stmt = select(McpServer).where(McpServer.tenant_id == tenant_id)

        if not include_disabled:
            stmt = stmt.where(McpServer.status != "disabled")

        stmt = stmt.order_by(McpServer.registered_at.desc())
        result = await self._session.execute(stmt)
        servers = result.scalars().all()

        return [self._server_to_row(s) for s in servers]

    async def update_server(
        self,
        server_id: str,
        **updates: Any,
    ) -> Optional[McpServerRow]:
        """Update server fields.

        Args:
            server_id: Server ID to update.
            **updates: Fields to update.

        Returns:
            Updated server row or None if not found.
        """
        # Add updated_at
        updates["updated_at"] = datetime.now(timezone.utc)

        stmt = (
            update(McpServer)
            .where(McpServer.server_id == server_id)
            .values(**updates)
            .returning(McpServer)
        )
        result = await self._session.execute(stmt)
        server = result.scalar_one_or_none()

        return self._server_to_row(server) if server else None

    async def soft_delete_server(self, server_id: str) -> bool:
        """Soft-delete a server by setting status to 'disabled'.

        Args:
            server_id: Server ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        result = await self.update_server(
            server_id,
            status="disabled",
        )
        return result is not None

    # =========================================================================
    # Tool Operations
    # =========================================================================

    async def upsert_tools(
        self,
        server_id: str,
        tenant_id: str,
        tools: List[Dict[str, Any]],
    ) -> List[McpToolRow]:
        """Upsert tools for a server.

        Tools are matched by (server_id, name). New tools are created,
        existing tools are updated.

        Args:
            server_id: Server ID.
            tenant_id: Tenant ID.
            tools: List of tool definitions with name, description, input_schema, etc.

        Returns:
            List of upserted tool rows.
        """
        now = datetime.now(timezone.utc)
        result_rows = []

        for tool_data in tools:
            name = tool_data["name"]
            # Note: tool_hash could be used for drift detection in Phase 2

            # Check if tool exists
            stmt = select(McpTool).where(
                and_(
                    McpTool.server_id == server_id,
                    McpTool.name == name,
                )
            )
            existing = await self._session.execute(stmt)
            existing_tool = existing.scalar_one_or_none()

            if existing_tool:
                # Update existing tool
                existing_tool.description = tool_data.get("description")
                existing_tool.input_schema = tool_data.get("input_schema", {})
                existing_tool.output_schema = tool_data.get("output_schema")
                existing_tool.risk_level = tool_data.get("risk_level", "medium")
                existing_tool.updated_at = now
                await self._session.flush()
                result_rows.append(self._tool_to_row(existing_tool))
            else:
                # Create new tool
                tool_id = f"tool_{uuid4().hex[:16]}"
                new_tool = McpTool(
                    tool_id=tool_id,
                    server_id=server_id,
                    tenant_id=tenant_id,
                    name=name,
                    description=tool_data.get("description"),
                    input_schema=tool_data.get("input_schema", {}),
                    output_schema=tool_data.get("output_schema"),
                    risk_level=tool_data.get("risk_level", "medium"),
                    enabled=True,
                    requires_policy=True,
                    invocation_count=0,
                    failure_count=0,
                    discovered_at=now,
                    updated_at=now,
                )
                self._session.add(new_tool)
                await self._session.flush()
                await self._session.refresh(new_tool)
                result_rows.append(self._tool_to_row(new_tool))

        return result_rows

    async def get_tools(
        self,
        server_id: str,
        enabled_only: bool = True,
    ) -> List[McpToolRow]:
        """Get tools for a server.

        Args:
            server_id: Server ID.
            enabled_only: Only return enabled tools.

        Returns:
            List of tool rows.
        """
        stmt = select(McpTool).where(McpTool.server_id == server_id)

        if enabled_only:
            stmt = stmt.where(McpTool.enabled == True)  # noqa: E712

        stmt = stmt.order_by(McpTool.name)
        result = await self._session.execute(stmt)
        tools = result.scalars().all()

        return [self._tool_to_row(t) for t in tools]

    async def get_tool(self, tool_id: str) -> Optional[McpToolRow]:
        """Get tool by ID.

        Args:
            tool_id: Tool ID.

        Returns:
            Tool row or None if not found.
        """
        stmt = select(McpTool).where(McpTool.tool_id == tool_id)
        result = await self._session.execute(stmt)
        tool = result.scalar_one_or_none()
        return self._tool_to_row(tool) if tool else None

    async def update_tool(
        self,
        tool_id: str,
        **updates: Any,
    ) -> Optional[McpToolRow]:
        """Update tool fields.

        Args:
            tool_id: Tool ID to update.
            **updates: Fields to update.

        Returns:
            Updated tool row or None if not found.
        """
        updates["updated_at"] = datetime.now(timezone.utc)

        stmt = (
            update(McpTool)
            .where(McpTool.tool_id == tool_id)
            .values(**updates)
            .returning(McpTool)
        )
        result = await self._session.execute(stmt)
        tool = result.scalar_one_or_none()

        return self._tool_to_row(tool) if tool else None

    # =========================================================================
    # Invocation Operations (Append-Only)
    # =========================================================================

    async def record_invocation(
        self,
        tool_id: Optional[str],
        server_id: str,
        tenant_id: str,
        tool_name: str,
        input_hash: str,
        outcome: str,
        invoked_at: datetime,
        run_id: Optional[str] = None,
        step_index: Optional[int] = None,
        actor_id: Optional[str] = None,
        actor_type: str = "machine",
        input_preview: Optional[str] = None,
        policy_id: Optional[str] = None,
        policy_snapshot_id: Optional[str] = None,
        policy_decision: str = "allowed",
        policy_reason: Optional[str] = None,
        output_hash: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        completed_at: Optional[datetime] = None,
    ) -> McpInvocationRow:
        """Record a tool invocation (append-only).

        Args:
            tool_id: Tool ID (may be None if tool was deleted).
            server_id: Server ID.
            tenant_id: Tenant ID.
            tool_name: Tool name for audit (preserved even if tool deleted).
            input_hash: SHA256 of input parameters.
            outcome: Outcome (success, failure, timeout, blocked).
            invoked_at: When invocation started.
            run_id: Optional run ID context.
            step_index: Optional step index in run.
            actor_id: Optional actor ID.
            actor_type: Actor type (human, machine, system).
            input_preview: Optional truncated input for debugging.
            policy_id: Policy ID that was checked.
            policy_snapshot_id: Policy snapshot ID.
            policy_decision: Policy decision (allowed, blocked, flagged).
            policy_reason: Reason for policy decision.
            output_hash: SHA256 of output (if success).
            error_code: Error code (if failure).
            error_message: Error message (if failure).
            duration_ms: Duration in milliseconds.
            completed_at: When invocation completed.

        Returns:
            Created invocation row.
        """
        invocation_id = f"inv_{uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        invocation = McpToolInvocation(
            invocation_id=invocation_id,
            tool_id=tool_id,
            server_id=server_id,
            tenant_id=tenant_id,
            run_id=run_id,
            step_index=step_index,
            actor_id=actor_id,
            actor_type=actor_type,
            tool_name=tool_name,
            input_hash=input_hash,
            input_preview=input_preview,
            policy_id=policy_id,
            policy_snapshot_id=policy_snapshot_id,
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            outcome=outcome,
            output_hash=output_hash,
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
            invoked_at=invoked_at,
            completed_at=completed_at,
            recorded_at=now,
        )

        self._session.add(invocation)
        await self._session.flush()
        await self._session.refresh(invocation)

        return self._invocation_to_row(invocation)

    async def get_invocations(
        self,
        server_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[McpInvocationRow]:
        """Get invocations for a server.

        Args:
            server_id: Server ID.
            limit: Max rows to return.
            offset: Rows to skip.

        Returns:
            List of invocation rows (newest first).
        """
        stmt = (
            select(McpToolInvocation)
            .where(McpToolInvocation.server_id == server_id)
            .order_by(McpToolInvocation.invoked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        invocations = result.scalars().all()

        return [self._invocation_to_row(i) for i in invocations]

    async def get_invocation(
        self, invocation_id: str
    ) -> Optional[McpInvocationRow]:
        """Get invocation by ID.

        Args:
            invocation_id: Invocation ID.

        Returns:
            Invocation row or None if not found.
        """
        stmt = select(McpToolInvocation).where(
            McpToolInvocation.invocation_id == invocation_id
        )
        result = await self._session.execute(stmt)
        invocation = result.scalar_one_or_none()
        return self._invocation_to_row(invocation) if invocation else None

    async def get_invocations_by_tenant(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[McpInvocationRow]:
        """Get invocations for a tenant.

        Args:
            tenant_id: Tenant ID.
            limit: Max rows to return.
            offset: Rows to skip.

        Returns:
            List of invocation rows (newest first).
        """
        stmt = (
            select(McpToolInvocation)
            .where(McpToolInvocation.tenant_id == tenant_id)
            .order_by(McpToolInvocation.invoked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        invocations = result.scalars().all()

        return [self._invocation_to_row(i) for i in invocations]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _server_to_row(self, server: McpServer) -> McpServerRow:
        """Convert ORM model to frozen DTO."""
        return McpServerRow(
            id=server.id,
            server_id=server.server_id,
            tenant_id=server.tenant_id,
            name=server.name,
            url=server.url,
            description=server.description,
            transport=server.transport,
            auth_type=server.auth_type,
            credential_id=server.credential_id,
            status=server.status,
            protocol_version=server.protocol_version,
            capabilities=server.capabilities or [],
            tool_count=server.tool_count,
            resource_count=server.resource_count,
            requires_approval=server.requires_approval,
            rate_limit_requests=server.rate_limit_requests,
            rate_limit_window_seconds=server.rate_limit_window_seconds,
            health_check_failures=server.health_check_failures,
            last_health_check_at=server.last_health_check_at,
            last_discovery_at=server.last_discovery_at,
            last_error=server.last_error,
            tags=server.tags or [],
            extra_metadata=server.extra_metadata,
            registered_at=server.registered_at,
            updated_at=server.updated_at,
        )

    def _tool_to_row(self, tool: McpTool) -> McpToolRow:
        """Convert ORM model to frozen DTO."""
        return McpToolRow(
            id=tool.id,
            tool_id=tool.tool_id,
            server_id=tool.server_id,
            tenant_id=tool.tenant_id,
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema or {},
            output_schema=tool.output_schema,
            risk_level=tool.risk_level,
            enabled=tool.enabled,
            requires_policy=tool.requires_policy,
            policy_id=tool.policy_id,
            invocation_count=tool.invocation_count,
            failure_count=tool.failure_count,
            last_invoked_at=tool.last_invoked_at,
            discovered_at=tool.discovered_at,
            updated_at=tool.updated_at,
        )

    def _invocation_to_row(self, inv: McpToolInvocation) -> McpInvocationRow:
        """Convert ORM model to frozen DTO."""
        return McpInvocationRow(
            id=inv.id,
            invocation_id=inv.invocation_id,
            tool_id=inv.tool_id,
            server_id=inv.server_id,
            tenant_id=inv.tenant_id,
            run_id=inv.run_id,
            step_index=inv.step_index,
            actor_id=inv.actor_id,
            actor_type=inv.actor_type,
            tool_name=inv.tool_name,
            input_hash=inv.input_hash,
            input_preview=inv.input_preview,
            policy_id=inv.policy_id,
            policy_snapshot_id=inv.policy_snapshot_id,
            policy_decision=inv.policy_decision,
            policy_reason=inv.policy_reason,
            outcome=inv.outcome,
            output_hash=inv.output_hash,
            error_code=inv.error_code,
            error_message=inv.error_message,
            duration_ms=inv.duration_ms,
            invoked_at=inv.invoked_at,
            completed_at=inv.completed_at,
            recorded_at=inv.recorded_at,
        )

    @staticmethod
    def _compute_tool_hash(name: str, input_schema: Dict[str, Any]) -> str:
        """Compute hash for tool identity (name + schema)."""
        import json

        data = json.dumps({"name": name, "schema": input_schema}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


# =============================================================================
# Utility Functions
# =============================================================================


def compute_input_hash(params: Dict[str, Any]) -> str:
    """Compute SHA256 hash of input parameters.

    Args:
        params: Input parameters dict.

    Returns:
        Hex-encoded SHA256 hash.
    """
    import json

    data = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()


def compute_output_hash(output: Any) -> str:
    """Compute SHA256 hash of output.

    Args:
        output: Output value (any JSON-serializable type).

    Returns:
        Hex-encoded SHA256 hash.
    """
    import json

    data = json.dumps(output, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()
