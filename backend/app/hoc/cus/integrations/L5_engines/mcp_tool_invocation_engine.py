# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: MCP_TOOL_INVOKED, MCP_TOOL_ALLOWED, MCP_TOOL_DENIED, MCP_TOOL_FAILED
#   Subscribes: none
# Data Access:
#   Reads: mcp_servers, mcp_tools, policies
#   Writes: mcp_tool_invocations, incidents (via engine)
# Role: MCP tool invocation orchestration with policy, audit, and incident integration
# Product: system-wide
# Callers: L4 mcp_handler
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-516 Phase 4

"""
MCP Tool Invocation Engine — Governed tool execution.

Orchestrates MCP tool invocations with full monitoring integration:
- Policy validation before execution
- Audit trail emission for compliance
- Actual tool execution via JSON-RPC
- Incident creation on failures

PIN-516 Phase 4 Deliverable.

Monitoring Integration:
- Policy: Validates tool calls against tenant policies
- Audit: Emits compliance-grade events via MCPAuditEmitter
- Incidents: Creates incidents for failed invocations
- Activity: Records invocations for analytics

Security Model:
- All invocations are recorded (append-only)
- Policy decisions are captured in audit trail
- Failures trigger incident creation
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

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
    compute_output_hash,
)

# PIN-521: Use Protocol for cross-domain dependency injection (no direct L5→L5 import)
from app.hoc.cus.hoc_spine.schemas.protocols import MCPAuditEmitterPort

logger = logging.getLogger("nova.hoc.integrations.mcp_tool_invocation_engine")


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TIMEOUT_SECONDS = 30
MCP_PROTOCOL_VERSION = "2024-11-05"


# =============================================================================
# Protocols
# =============================================================================


@runtime_checkable
class McpPolicyChecker(Protocol):
    """Protocol for MCP tool invocation policy checking."""

    async def check_tool_invocation(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        tool_risk_level: str,
        input_params: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> "PolicyCheckResult":
        """
        Check if tool invocation is allowed by policy.

        Returns:
            PolicyCheckResult with allowed, policy_id, and deny_reason
        """
        ...


@dataclass(frozen=True)
class PolicyCheckResult:
    """Result of policy check for tool invocation."""

    allowed: bool
    policy_id: Optional[str] = None
    deny_reason: Optional[str] = None


# =============================================================================
# Result Types
# =============================================================================


@dataclass(frozen=True)
class McpInvocationResult:
    """Result of MCP tool invocation."""

    invocation_id: str
    tool_id: str
    server_id: str
    status: str  # success, failure, blocked, timeout
    output: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    policy_decision: str = "allowed"  # allowed, blocked, flagged
    policy_id: Optional[str] = None
    incident_id: Optional[str] = None  # If incident was created


# =============================================================================
# Default Policy Checker (Permissive)
# =============================================================================


class DefaultMcpPolicyChecker:
    """
    Default policy checker that allows all invocations.

    Production deployments should inject a real policy checker
    that validates against tenant policies.
    """

    async def check_tool_invocation(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        tool_risk_level: str,
        input_params: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> PolicyCheckResult:
        """Allow all invocations (default behavior)."""
        # In production, this would check against policies:
        # - Tool is enabled
        # - Server is active
        # - Risk level is acceptable
        # - Input parameters are within bounds
        # - Rate limits are not exceeded
        return PolicyCheckResult(allowed=True)


# =============================================================================
# MCP Tool Invocation Engine (L5)
# =============================================================================


class McpToolInvocationEngine:
    """
    L5 Engine for governed MCP tool invocations.

    Responsibilities:
    - Policy validation before execution
    - Audit trail emission
    - Tool execution via JSON-RPC
    - Incident creation on failure
    - Invocation recording for analytics

    PIN-516 Phase 4 Invariants:
    - All invocations recorded (append-only via driver)
    - Policy decisions captured in audit trail
    - Failures trigger incident creation
    - No direct DB access (via L6 driver)
    """

    def __init__(
        self,
        driver: McpDriver,
        audit_emitter: Optional[MCPAuditEmitterPort] = None,
        policy_checker: Optional[McpPolicyChecker] = None,
        credential_service: Optional[CredentialService] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        incident_creator: Optional[Any] = None,  # IncidentEngine protocol
    ):
        """
        Initialize tool invocation engine.

        Args:
            driver: L6 driver for persistence.
            audit_emitter: Optional audit emitter (defaults to singleton).
                           PIN-521: Must be injected, lazy loads if None.
            policy_checker: Optional policy checker (defaults to permissive).
            credential_service: Optional credential service for vault access.
            http_client: Optional HTTP client for MCP calls.
            incident_creator: Optional incident creator for failures.
        """
        self._driver = driver
        self._audit_emitter = audit_emitter or self._get_default_audit_emitter()
        self._policy_checker = policy_checker or DefaultMcpPolicyChecker()
        self._credential_service = credential_service
        self._http_client = http_client
        self._incident_creator = incident_creator
        self._owns_http_client = http_client is None

    @staticmethod
    def _get_default_audit_emitter() -> MCPAuditEmitterPort:
        """Lazy-load default audit emitter (PIN-521: avoids top-level cross-domain import)."""
        from app.hoc.cus.logs.L5_engines.audit_evidence import get_mcp_audit_emitter

        return get_mcp_audit_emitter()

    async def __aenter__(self):
        """Async context manager entry."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
            self._owns_http_client = True
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        if self._owns_http_client and self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # =========================================================================
    # Tool Invocation (Main Entry Point)
    # =========================================================================

    async def invoke_tool(
        self,
        tenant_id: str,
        server_id: str,
        tool_id: str,
        input_params: Dict[str, Any],
        run_id: Optional[str] = None,
        step_index: Optional[int] = None,
        actor_id: Optional[str] = None,
        actor_type: str = "machine",
        trace_id: Optional[str] = None,
    ) -> McpInvocationResult:
        """
        Invoke an MCP tool with full governance.

        Orchestration flow:
        1. Validate server and tool exist
        2. Emit audit: TOOL_INVOCATION_REQUESTED
        3. Check policy
        4. Emit audit: TOOL_INVOCATION_ALLOWED or TOOL_INVOCATION_DENIED
        5. If denied, record invocation as blocked, return
        6. Emit audit: TOOL_INVOCATION_STARTED
        7. Execute tool via MCP JSON-RPC
        8. Emit audit: TOOL_INVOCATION_COMPLETED or TOOL_INVOCATION_FAILED
        9. Record invocation
        10. If failed, create incident
        11. Return result

        Args:
            tenant_id: Tenant ID.
            server_id: MCP server ID.
            tool_id: Tool ID to invoke.
            input_params: Parameters to pass to tool.
            run_id: Optional run context.
            step_index: Optional step index in run.
            actor_id: Optional actor ID.
            actor_type: Actor type (human, machine, system).
            trace_id: Optional trace ID for correlation.

        Returns:
            McpInvocationResult with status and output.
        """
        invoked_at = datetime.now(timezone.utc)
        input_hash = compute_input_hash(input_params)

        # Step 1: Validate server and tool
        server = await self._driver.get_server(server_id)
        if server is None:
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name="unknown",
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="SERVER_NOT_FOUND",
                error_message=f"Server not found: {server_id}",
            )

        if server.tenant_id != tenant_id:
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name="unknown",
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="ACCESS_DENIED",
                error_message="Server does not belong to tenant",
            )

        if server.status != "active":
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name="unknown",
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="SERVER_NOT_ACTIVE",
                error_message=f"Server status is {server.status}, not active",
            )

        tool = await self._driver.get_tool(tool_id)
        if tool is None:
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name="unknown",
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="TOOL_NOT_FOUND",
                error_message=f"Tool not found: {tool_id}",
            )

        if tool.server_id != server_id:
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name=tool.name,
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="TOOL_SERVER_MISMATCH",
                error_message="Tool does not belong to specified server",
            )

        if not tool.enabled:
            return await self._record_error(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_id=tool_id,
                tool_name=tool.name,
                input_hash=input_hash,
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                error_code="TOOL_DISABLED",
                error_message=f"Tool '{tool.name}' is disabled",
            )

        # Step 2: Emit audit - TOOL_INVOCATION_REQUESTED
        await self._audit_emitter.emit_tool_requested(
            tenant_id=tenant_id,
            server_id=server_id,
            tool_name=tool.name,
            run_id=run_id or "standalone",
            input_params=input_params,
            trace_id=trace_id,
        )

        # Step 3: Check policy
        policy_result = await self._policy_checker.check_tool_invocation(
            tenant_id=tenant_id,
            server_id=server_id,
            tool_name=tool.name,
            tool_risk_level=tool.risk_level,
            input_params=input_params,
            run_id=run_id,
        )

        # Step 4: Emit audit - ALLOWED or DENIED
        if not policy_result.allowed:
            await self._audit_emitter.emit_tool_denied(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_name=tool.name,
                run_id=run_id or "standalone",
                deny_reason=policy_result.deny_reason or "Policy denied",
                policy_id=policy_result.policy_id,
                trace_id=trace_id,
            )

            # Record blocked invocation
            invocation = await self._driver.record_invocation(
                tool_id=tool_id,
                server_id=server_id,
                tenant_id=tenant_id,
                tool_name=tool.name,
                input_hash=input_hash,
                outcome="blocked",
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                policy_id=policy_result.policy_id,
                policy_decision="blocked",
                policy_reason=policy_result.deny_reason,
                completed_at=datetime.now(timezone.utc),
            )

            return McpInvocationResult(
                invocation_id=invocation.invocation_id,
                tool_id=tool_id,
                server_id=server_id,
                status="blocked",
                error_code="POLICY_DENIED",
                error_message=policy_result.deny_reason or "Policy denied invocation",
                policy_decision="blocked",
                policy_id=policy_result.policy_id,
            )

        # Policy allowed
        await self._audit_emitter.emit_tool_allowed(
            tenant_id=tenant_id,
            server_id=server_id,
            tool_name=tool.name,
            run_id=run_id or "standalone",
            policy_id=policy_result.policy_id,
            trace_id=trace_id,
        )

        # Step 6: Emit audit - TOOL_INVOCATION_STARTED
        await self._audit_emitter.emit_tool_started(
            tenant_id=tenant_id,
            server_id=server_id,
            tool_name=tool.name,
            run_id=run_id or "standalone",
            trace_id=trace_id,
        )

        # Step 7: Execute tool
        start_time = datetime.now(timezone.utc)
        try:
            output = await self._execute_tool(
                server=server,
                tool=tool,
                input_params=input_params,
            )
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Step 8: Emit audit - TOOL_INVOCATION_COMPLETED
            await self._audit_emitter.emit_tool_completed(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_name=tool.name,
                run_id=run_id or "standalone",
                output=output,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )

            # Step 9: Record successful invocation
            invocation = await self._driver.record_invocation(
                tool_id=tool_id,
                server_id=server_id,
                tenant_id=tenant_id,
                tool_name=tool.name,
                input_hash=input_hash,
                outcome="success",
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                policy_id=policy_result.policy_id,
                policy_decision="allowed",
                output_hash=compute_output_hash(output) if output else None,
                duration_ms=duration_ms,
                completed_at=end_time,
            )

            # Update tool invocation count
            await self._driver.update_tool(
                tool_id,
                invocation_count=tool.invocation_count + 1,
                last_invoked_at=end_time,
            )

            return McpInvocationResult(
                invocation_id=invocation.invocation_id,
                tool_id=tool_id,
                server_id=server_id,
                status="success",
                output=output,
                duration_ms=duration_ms,
                policy_decision="allowed",
                policy_id=policy_result.policy_id,
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            error_message = str(e)
            error_code = type(e).__name__

            # Step 8: Emit audit - TOOL_INVOCATION_FAILED
            await self._audit_emitter.emit_tool_failed(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_name=tool.name,
                run_id=run_id or "standalone",
                error_message=error_message,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )

            # Step 9: Record failed invocation
            invocation = await self._driver.record_invocation(
                tool_id=tool_id,
                server_id=server_id,
                tenant_id=tenant_id,
                tool_name=tool.name,
                input_hash=input_hash,
                outcome="failure",
                invoked_at=invoked_at,
                run_id=run_id,
                step_index=step_index,
                actor_id=actor_id,
                actor_type=actor_type,
                policy_id=policy_result.policy_id,
                policy_decision="allowed",
                error_code=error_code,
                error_message=error_message,
                duration_ms=duration_ms,
                completed_at=end_time,
            )

            # Update tool failure count
            await self._driver.update_tool(
                tool_id,
                failure_count=tool.failure_count + 1,
                last_invoked_at=end_time,
            )

            # Step 10: Create incident
            incident_id = await self._create_incident(
                tenant_id=tenant_id,
                server_id=server_id,
                tool_name=tool.name,
                run_id=run_id,
                error_code=error_code,
                error_message=error_message,
            )

            logger.warning(
                "mcp_tool_invocation.failed",
                extra={
                    "invocation_id": invocation.invocation_id,
                    "tool_id": tool_id,
                    "server_id": server_id,
                    "tenant_id": tenant_id,
                    "error_code": error_code,
                    "incident_id": incident_id,
                },
            )

            return McpInvocationResult(
                invocation_id=invocation.invocation_id,
                tool_id=tool_id,
                server_id=server_id,
                status="failure",
                error_code=error_code,
                error_message=error_message,
                duration_ms=duration_ms,
                policy_decision="allowed",
                policy_id=policy_result.policy_id,
                incident_id=incident_id,
            )

    # =========================================================================
    # Private: Error Recording
    # =========================================================================

    async def _record_error(
        self,
        tenant_id: str,
        server_id: str,
        tool_id: str,
        tool_name: str,
        input_hash: str,
        invoked_at: datetime,
        run_id: Optional[str],
        step_index: Optional[int],
        actor_id: Optional[str],
        actor_type: str,
        error_code: str,
        error_message: str,
    ) -> McpInvocationResult:
        """Record a pre-execution error."""
        invocation = await self._driver.record_invocation(
            tool_id=tool_id if tool_id != "unknown" else None,
            server_id=server_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            input_hash=input_hash,
            outcome="failure",
            invoked_at=invoked_at,
            run_id=run_id,
            step_index=step_index,
            actor_id=actor_id,
            actor_type=actor_type,
            policy_decision="error",
            error_code=error_code,
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
        )

        return McpInvocationResult(
            invocation_id=invocation.invocation_id,
            tool_id=tool_id,
            server_id=server_id,
            status="failure",
            error_code=error_code,
            error_message=error_message,
            policy_decision="error",
        )

    # =========================================================================
    # Private: Tool Execution
    # =========================================================================

    async def _execute_tool(
        self,
        server: McpServerRow,
        tool: McpToolRow,
        input_params: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Execute MCP tool via JSON-RPC.

        Args:
            server: Server row with URL and credentials.
            tool: Tool row with name and schema.
            input_params: Input parameters.

        Returns:
            Tool output or None.

        Raises:
            Exception on execution failure.
        """
        # Get credentials if configured
        api_key = None
        if server.credential_id and self._credential_service:
            try:
                credential = await self._credential_service.get(server.credential_id)
                api_key = credential.value
            except Exception as e:
                raise Exception(f"Failed to get credentials: {e}")

        # Execute via JSON-RPC
        client = self._http_client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            request_body = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool.name,
                    "arguments": input_params,
                },
                "id": 1,
            }

            response = await client.post(
                f"{server.url.rstrip('/')}/mcp",
                json=request_body,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                error = result["error"]
                raise Exception(error.get("message", "Unknown MCP error"))

            return result.get("result")
        finally:
            if not self._http_client:
                await client.aclose()

    # =========================================================================
    # Private: Incident Creation
    # =========================================================================

    async def _create_incident(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: Optional[str],
        error_code: str,
        error_message: str,
    ) -> Optional[str]:
        """
        Create incident for failed tool invocation.

        Args:
            tenant_id: Tenant ID.
            server_id: Server ID.
            tool_name: Tool name.
            run_id: Run ID (if available).
            error_code: Error code.
            error_message: Error message.

        Returns:
            Incident ID if created, None if not (no incident creator or suppressed).
        """
        if self._incident_creator is None:
            logger.debug(
                "mcp_tool_invocation.no_incident_creator",
                extra={
                    "server_id": server_id,
                    "tool_name": tool_name,
                },
            )
            return None

        try:
            # Try to call create_incident_for_failed_run if available
            if hasattr(self._incident_creator, "create_incident_for_failed_run"):
                incident_id = self._incident_creator.create_incident_for_failed_run(
                    run_id=run_id or f"mcp-{server_id}-{tool_name}",
                    tenant_id=tenant_id,
                    error_code=f"MCP_{error_code}",
                    error_message=f"MCP tool '{tool_name}' failed: {error_message}",
                    agent_id=server_id,
                )
                return incident_id
        except Exception as e:
            logger.error(
                "mcp_tool_invocation.incident_creation_failed",
                extra={
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "error": str(e),
                },
            )

        return None
