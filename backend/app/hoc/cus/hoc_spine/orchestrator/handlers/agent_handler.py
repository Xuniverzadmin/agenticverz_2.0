# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Agent domain handler — routes agent operations to L6 drivers via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.agent.L6_drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), PIN-484 (HOC Topology V2.0.0)
# artifact_class: CODE

"""
Agent Handler (L4 Orchestrator)

Routes agent domain operations to L6 drivers.
Registers operations:
  - agent.discovery_stats → DiscoveryStatsDriver
  - agent.routing → RoutingDriver (get_stats, get_decision)
  - agent.strategy → RoutingDriver (update_sba)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class AgentDiscoveryStatsHandler:
    """
    Handler for agent.discovery_stats operations.

    Dispatches to DiscoveryStatsDriver.get_stats() method.
    Note: Uses sync session — driver is synchronous.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.discovery_stats_driver import (
            get_discovery_stats_driver,
        )

        try:
            driver = get_discovery_stats_driver()
            # The session in ctx is async, but for sync drivers we need
            # a sync session. The L2 should pass a sync session via params.
            sync_session = ctx.params.get("sync_session")
            if sync_session is None:
                return OperationResult.fail(
                    "Missing 'sync_session' in params for sync driver operation",
                    "MISSING_SESSION",
                )

            stats = driver.get_stats(sync_session)
            return OperationResult.ok(stats)
        except Exception as e:
            return OperationResult.fail(str(e), "DISCOVERY_STATS_ERROR")


class AgentRoutingHandler:
    """
    Handler for agent.routing operations.

    Dispatches to RoutingDriver methods:
    - get_stats: Aggregate routing stats
    - get_decision: Single routing decision
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.routing_driver import get_routing_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_routing_driver(ctx.session)

        if method_name == "get_stats":
            hours = ctx.params.get("hours", 24)
            data = await driver.get_routing_stats(
                tenant_id=ctx.tenant_id,
                hours=hours,
            )
            return OperationResult.ok(data)

        elif method_name == "get_decision":
            request_id = ctx.params.get("request_id")
            if not request_id:
                return OperationResult.fail(
                    "Missing 'request_id'", "MISSING_PARAM"
                )
            data = await driver.get_routing_decision(
                request_id=request_id,
                tenant_id=ctx.tenant_id,
            )
            if data is None:
                return OperationResult.fail(
                    f"Decision not found: {request_id}", "NOT_FOUND"
                )
            return OperationResult.ok(data)

        return OperationResult.fail(
            f"Unknown routing method: {method_name}", "UNKNOWN_METHOD"
        )


class AgentStrategyHandler:
    """
    Handler for agent.strategy operations.

    Dispatches to RoutingDriver methods:
    - update_sba: Update agent SBA
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.routing_driver import get_routing_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_routing_driver(ctx.session)

        if method_name == "update_sba":
            agent_id = ctx.params.get("agent_id")
            sba = ctx.params.get("sba")
            if not agent_id:
                return OperationResult.fail(
                    "Missing 'agent_id'", "MISSING_PARAM"
                )
            if sba is None:
                return OperationResult.fail(
                    "Missing 'sba'", "MISSING_PARAM"
                )
            await driver.update_agent_sba(agent_id=agent_id, sba=sba)
            # L4 owns transaction boundary
            await ctx.session.commit()
            return OperationResult.ok({"updated": True})

        return OperationResult.fail(
            f"Unknown strategy method: {method_name}", "UNKNOWN_METHOD"
        )


def register(registry: OperationRegistry) -> None:
    """Register agent operations with the registry."""
    registry.register("agent.discovery_stats", AgentDiscoveryStatsHandler())
    registry.register("agent.routing", AgentRoutingHandler())
    registry.register("agent.strategy", AgentStrategyHandler())
