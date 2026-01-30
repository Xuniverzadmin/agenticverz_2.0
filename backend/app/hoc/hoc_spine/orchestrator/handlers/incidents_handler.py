# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Incidents domain handler — routes incidents operations to L5 facade via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.incidents.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Incidents Handler (L4 Orchestrator)

Routes incidents domain operations to the L5 IncidentsFacade.
Registered as "incidents.query" in the OperationRegistry.
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class IncidentsQueryHandler:
    """
    Handler for incidents.query operations.

    Dispatches to IncidentsFacade methods (list_active_incidents,
    list_resolved_incidents, list_historical_incidents, detect_patterns,
    analyze_recurrence, get_incident_learnings, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.incidents.L5_engines.incidents_facade import (
            get_incidents_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_incidents_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


def register(registry: OperationRegistry) -> None:
    """Register incidents operations with the registry."""
    registry.register("incidents.query", IncidentsQueryHandler())
