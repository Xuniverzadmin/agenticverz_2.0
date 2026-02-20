# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: MCP servers domain handler — routes MCP operations to L5 engine via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.integrations.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-516 (MCP Customer Integration), Phase 3+4
# artifact_class: CODE

"""
MCP Servers Handler (L4 Orchestrator)

Routes MCP server lifecycle operations to L5 engines.
Registers one operation:
  - integrations.mcp_servers → McpServerEngine, McpToolInvocationEngine

Methods:
  - register_server: Register a new MCP server
  - get_server: Get server details by ID
  - list_servers: List all servers for tenant
  - discover_tools: Discover tools from MCP server
  - health_check: Check MCP server health
  - delete_server: Soft-delete a server
  - list_tools: List tools for a server
  - get_invocations: Get invocation history
  - invoke_tool: Invoke an MCP tool (Phase 4 - governed execution)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class McpServersHandler:
    """
    Handler for integrations.mcp_servers operations.

    Dispatches to McpServerEngine methods for MCP server lifecycle management.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L5_engines.mcp_server_engine import (
            McpServerEngine,
        )
        from app.hoc.cus.integrations.L6_drivers.mcp_driver import McpDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # Initialize driver and engine
        driver = McpDriver(session=ctx.session)
        engine = McpServerEngine(driver=driver)

        # Method dispatch
        if method_name == "register_server":
            result = await engine.register_server(
                tenant_id=ctx.tenant_id,
                name=ctx.params["name"],
                url=ctx.params["url"],
                description=ctx.params.get("description"),
                transport=ctx.params.get("transport", "http"),
                auth_type=ctx.params.get("auth_type"),
                credential_ref=ctx.params.get("credential_id"),
                requires_approval=ctx.params.get("requires_approval", True),
                tags=ctx.params.get("tags"),
                auto_discover=ctx.params.get("auto_discover", True),
            )
            return OperationResult.ok({
                "server_id": result.server_id,
                "status": result.status,
                "tools_discovered": 0,  # Discovery result is separate
                "error": None,
            })

        elif method_name == "get_server":
            server = await driver.get_server(ctx.params["server_id"])
            if server is None:
                return OperationResult.fail(
                    f"Server not found: {ctx.params['server_id']}", "NOT_FOUND"
                )
            # Verify tenant ownership
            if server.tenant_id != ctx.tenant_id:
                return OperationResult.fail(
                    "Server not found", "NOT_FOUND"  # Don't leak existence
                )
            return OperationResult.ok({
                "server_id": server.server_id,
                "name": server.name,
                "url": server.url,
                "description": server.description,
                "transport": server.transport,
                "status": server.status,
                "credential_id": server.credential_id,
                "metadata": server.extra_metadata,
                "created_at": server.registered_at.isoformat() if server.registered_at else None,
                "updated_at": server.updated_at.isoformat() if server.updated_at else None,
            })

        elif method_name == "list_servers":
            include_disabled = ctx.params.get("include_disabled", False)
            servers = await driver.list_servers(
                tenant_id=ctx.tenant_id,
                include_disabled=include_disabled,
            )
            return OperationResult.ok({
                "servers": [
                    {
                        "server_id": s.server_id,
                        "name": s.name,
                        "url": s.url,
                        "status": s.status,
                        "transport": s.transport,
                        "created_at": s.registered_at.isoformat() if s.registered_at else None,
                    }
                    for s in servers
                ],
                "total": len(servers),
            })

        elif method_name == "discover_tools":
            # Verify tenant ownership first
            server = await driver.get_server(ctx.params["server_id"])
            if server is None or server.tenant_id != ctx.tenant_id:
                return OperationResult.fail("Server not found", "NOT_FOUND")
            result = await engine.discover_tools(
                server_id=ctx.params["server_id"],
            )
            # Get tools to return as list
            tools = await driver.get_tools(ctx.params["server_id"])
            return OperationResult.ok({
                "server_id": result.server_id,
                "tools_discovered": result.tools_found,
                "tools": [
                    {"name": t.name, "description": t.description, "risk_level": t.risk_level}
                    for t in tools
                ],
                "error": result.errors[0] if result.errors else None,
            })

        elif method_name == "health_check":
            # Verify tenant ownership first
            server = await driver.get_server(ctx.params["server_id"])
            if server is None or server.tenant_id != ctx.tenant_id:
                return OperationResult.fail("Server not found", "NOT_FOUND")
            result = await engine.health_check(
                server_id=ctx.params["server_id"],
            )
            return OperationResult.ok({
                "server_id": result.server_id,
                "healthy": result.is_healthy,
                "latency_ms": result.latency_ms,
                "error": result.error,
            })

        elif method_name == "delete_server":
            # Verify tenant ownership first
            server = await driver.get_server(ctx.params["server_id"])
            if server is None or server.tenant_id != ctx.tenant_id:
                return OperationResult.fail("Server not found", "NOT_FOUND")
            deleted = await driver.soft_delete_server(ctx.params["server_id"])
            if not deleted:
                return OperationResult.fail("Failed to delete server", "DELETE_FAILED")
            return OperationResult.ok({"deleted": True})

        elif method_name == "list_tools":
            # Verify tenant ownership
            server = await driver.get_server(ctx.params["server_id"])
            if server is None or server.tenant_id != ctx.tenant_id:
                return OperationResult.fail("Server not found", "NOT_FOUND")
            tools = await driver.get_tools(ctx.params["server_id"])
            return OperationResult.ok({
                "tools": [
                    {
                        "tool_id": t.tool_id,
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                        "risk_level": t.risk_level,
                        "is_active": t.enabled,
                    }
                    for t in tools
                ],
                "total": len(tools),
            })

        elif method_name == "get_invocations":
            # Verify tenant ownership
            server = await driver.get_server(ctx.params["server_id"])
            if server is None or server.tenant_id != ctx.tenant_id:
                return OperationResult.fail("Server not found", "NOT_FOUND")
            invocations = await driver.get_invocations(
                server_id=ctx.params["server_id"],
                limit=ctx.params.get("limit", 50),
                offset=ctx.params.get("offset", 0),
            )
            return OperationResult.ok({
                "invocations": [
                    {
                        "invocation_id": inv.invocation_id,
                        "tool_id": inv.tool_id,
                        "run_id": inv.run_id,
                        "status": inv.outcome,
                        "latency_ms": inv.duration_ms,
                        "invoked_at": inv.invoked_at.isoformat() if inv.invoked_at else None,
                    }
                    for inv in invocations
                ],
                "total": len(invocations),
            })

        elif method_name == "invoke_tool":
            # Phase 4: Governed tool invocation with policy, audit, incidents
            from app.hoc.cus.integrations.L5_engines.mcp_tool_invocation_engine import (
                McpToolInvocationEngine,
            )

            # Initialize invocation engine with driver
            invocation_engine = McpToolInvocationEngine(driver=driver)

            # Execute governed invocation
            result = await invocation_engine.invoke_tool(
                tenant_id=ctx.tenant_id,
                server_id=ctx.params["server_id"],
                tool_id=ctx.params["tool_id"],
                input_params=ctx.params.get("input", {}),
                run_id=ctx.params.get("run_id"),
                step_index=ctx.params.get("step_index"),
                actor_id=ctx.params.get("actor_id"),
                actor_type=ctx.params.get("actor_type", "machine"),
                trace_id=ctx.params.get("trace_id"),
            )

            return OperationResult.ok({
                "invocation_id": result.invocation_id,
                "tool_id": result.tool_id,
                "server_id": result.server_id,
                "status": result.status,
                "output": result.output,
                "error_code": result.error_code,
                "error_message": result.error_message,
                "duration_ms": result.duration_ms,
                "policy_decision": result.policy_decision,
                "policy_id": result.policy_id,
                "incident_id": result.incident_id,
            })

        else:
            return OperationResult.fail(
                f"Unknown method: {method_name}", "UNKNOWN_METHOD"
            )


def register(registry: OperationRegistry) -> None:
    """Register MCP server operations with the registry."""
    registry.register("integrations.mcp_servers", McpServersHandler())
