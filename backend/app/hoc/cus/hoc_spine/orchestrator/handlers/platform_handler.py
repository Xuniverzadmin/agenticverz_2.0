# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: sync
# Role: Platform domain handler — routes platform health operations to L6 driver via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.agent.L6_drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), L2→L6 elimination
# artifact_class: CODE

"""
Platform Handler (L4 Orchestrator)

Routes platform domain operations to L6 platform_driver.
Registers operations:
  - platform.health → PlatformDriver (get_blca_status, get_lifecycle_coherence, etc.)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class PlatformHealthHandler:
    """
    Handler for platform.health operations.

    Dispatches to PlatformDriver methods for platform health queries.
    Note: Uses sync session — driver is synchronous.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.platform_driver import get_platform_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # Platform driver can create its own session if not provided
        sync_session = ctx.params.get("sync_session")

        try:
            driver = get_platform_driver(sync_session)

            if method_name == "get_blca_status":
                result = driver.get_blca_status()
                return OperationResult.ok({"status": result})

            elif method_name == "get_lifecycle_coherence":
                result = driver.get_lifecycle_coherence()
                return OperationResult.ok({"coherence": result})

            elif method_name == "get_blocked_scopes":
                result = driver.get_blocked_scopes()
                return OperationResult.ok({"scopes": list(result)})

            elif method_name == "get_capability_signals":
                capability_name = ctx.params.get("capability_name")
                limit = ctx.params.get("limit", 5)
                if not capability_name:
                    return OperationResult.fail("Missing 'capability_name'", "MISSING_PARAM")
                result = driver.get_capability_signals(capability_name, limit)
                return OperationResult.ok({"signals": result})

            elif method_name == "count_blocked_for_capability":
                capability_name = ctx.params.get("capability_name")
                if not capability_name:
                    return OperationResult.fail("Missing 'capability_name'", "MISSING_PARAM")
                result = driver.count_blocked_for_capability(capability_name)
                return OperationResult.ok({"count": result})

            else:
                return OperationResult.fail(
                    f"Unknown platform method: {method_name}", "UNKNOWN_METHOD"
                )

        except Exception as e:
            return OperationResult.fail(str(e), "PLATFORM_DRIVER_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register platform operations with the registry."""
    registry.register("platform.health", PlatformHealthHandler())
