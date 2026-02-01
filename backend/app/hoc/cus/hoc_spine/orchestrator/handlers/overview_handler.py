# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Overview domain handler — routes overview operations to L5 facade via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.overview.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Overview Handler (L4 Orchestrator)

Routes overview domain operations to the L5 OverviewFacade.
Registered as "overview.query" in the OperationRegistry.

The handler dispatches to specific facade methods based on ctx.params["method"].
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class OverviewQueryHandler:
    """
    Handler for overview.query operations.

    Dispatches to OverviewFacade methods:
      - get_highlights
      - get_decisions
      - get_costs
      - get_decisions_count
      - get_recovery_stats
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.overview.L5_engines.overview_facade import get_overview_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_overview_facade()
        dispatch = {
            "get_highlights": facade.get_highlights,
            "get_decisions": facade.get_decisions,
            "get_costs": facade.get_costs,
            "get_decisions_count": facade.get_decisions_count,
            "get_recovery_stats": facade.get_recovery_stats,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register overview operations with the registry."""
    registry.register("overview.query", OverviewQueryHandler())
