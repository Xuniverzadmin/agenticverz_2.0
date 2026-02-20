# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: sync
# Role: Killswitch domain handler — routes killswitch operations to L6 drivers via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.controls.L6_drivers, hoc_spine/drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), L2→L6 elimination
# artifact_class: CODE

"""
Killswitch Handler (L4 Orchestrator)

Routes killswitch domain operations to L6 drivers:
  - killswitch.read → KillswitchOpsDriver (read operations)
  - killswitch.write → GuardWriteDriver (write operations)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class KillswitchReadHandler:
    """
    Handler for killswitch.read operations.

    Dispatches to KillswitchOpsDriver methods for read operations.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L6_drivers.killswitch_ops_driver import (
            get_killswitch_ops_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        sync_session = ctx.params.get("sync_session")
        if sync_session is None:
            return OperationResult.fail(
                "Missing 'sync_session' in params for sync driver operation",
                "MISSING_SESSION",
            )

        try:
            driver = get_killswitch_ops_driver(sync_session)

            if method_name == "verify_tenant_exists":
                tenant_id = ctx.params.get("lookup_tenant_id")
                if not tenant_id:
                    return OperationResult.fail("Missing 'lookup_tenant_id'", "MISSING_PARAM")
                result = driver.verify_tenant_exists(tenant_id)
                return OperationResult.ok(result)

            elif method_name == "verify_api_key_exists":
                key_id = ctx.params.get("key_id")
                if not key_id:
                    return OperationResult.fail("Missing 'key_id'", "MISSING_PARAM")
                result = driver.verify_api_key_exists(key_id)
                return OperationResult.ok(result)

            elif method_name == "get_killswitch_state":
                entity_type = ctx.params.get("entity_type")
                entity_id = ctx.params.get("entity_id")
                if not entity_type or not entity_id:
                    return OperationResult.fail(
                        "Missing 'entity_type' or 'entity_id'", "MISSING_PARAM"
                    )
                result = driver.get_killswitch_state(entity_type, entity_id)
                return OperationResult.ok(result)

            elif method_name == "get_key_states_for_tenant":
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                if not lookup_tenant_id:
                    return OperationResult.fail("Missing 'lookup_tenant_id'", "MISSING_PARAM")
                result = driver.get_key_states_for_tenant(lookup_tenant_id)
                return OperationResult.ok(result)

            elif method_name == "list_active_guardrails":
                result = driver.list_active_guardrails()
                return OperationResult.ok(result)

            elif method_name == "list_incidents":
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                status = ctx.params.get("status")
                limit = ctx.params.get("limit", 50)
                offset = ctx.params.get("offset", 0)
                if not lookup_tenant_id:
                    return OperationResult.fail("Missing 'lookup_tenant_id'", "MISSING_PARAM")
                result = driver.list_incidents(lookup_tenant_id, status, limit, offset)
                return OperationResult.ok(result)

            elif method_name == "get_incident_detail":
                incident_id = ctx.params.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                result = driver.get_incident_detail(incident_id)
                return OperationResult.ok(result)

            elif method_name == "get_incident_events":
                incident_id = ctx.params.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                result = driver.get_incident_events(incident_id)
                return OperationResult.ok(result)

            elif method_name == "get_proxy_call":
                call_id = ctx.params.get("call_id")
                if not call_id:
                    return OperationResult.fail("Missing 'call_id'", "MISSING_PARAM")
                result = driver.get_proxy_call(call_id)
                return OperationResult.ok(result)

            else:
                return OperationResult.fail(
                    f"Unknown killswitch read method: {method_name}", "UNKNOWN_METHOD"
                )

        except Exception as e:
            return OperationResult.fail(str(e), "KILLSWITCH_READ_ERROR")


class KillswitchWriteHandler:
    """
    Handler for killswitch.write operations.

    Dispatches to GuardWriteDriver methods for write operations.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.guard_write_driver import (
            get_guard_write_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        sync_session = ctx.params.get("sync_session")
        if sync_session is None:
            return OperationResult.fail(
                "Missing 'sync_session' in params for sync driver operation",
                "MISSING_SESSION",
            )

        try:
            driver = get_guard_write_driver(sync_session)

            if method_name == "get_or_create_killswitch_state":
                entity_type = ctx.params.get("entity_type")
                entity_id = ctx.params.get("entity_id")
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                if not entity_type or not entity_id or not lookup_tenant_id:
                    return OperationResult.fail(
                        "Missing 'entity_type', 'entity_id', or 'lookup_tenant_id'",
                        "MISSING_PARAM",
                    )
                state, is_new = driver.get_or_create_killswitch_state(
                    entity_type, entity_id, lookup_tenant_id
                )
                return OperationResult.ok({"state": state, "is_new": is_new})

            elif method_name == "freeze_killswitch":
                state = ctx.params.get("state")
                by = ctx.params.get("by")
                reason = ctx.params.get("reason")
                auto = ctx.params.get("auto", False)
                trigger = ctx.params.get("trigger")
                if not state or not by or not reason:
                    return OperationResult.fail(
                        "Missing 'state', 'by', or 'reason'", "MISSING_PARAM"
                    )
                result = driver.freeze_killswitch(state, by, reason, auto, trigger)
                return OperationResult.ok(result)

            elif method_name == "unfreeze_killswitch":
                state = ctx.params.get("state")
                by = ctx.params.get("by")
                if not state or not by:
                    return OperationResult.fail("Missing 'state' or 'by'", "MISSING_PARAM")
                result = driver.unfreeze_killswitch(state, by)
                return OperationResult.ok(result)

            else:
                return OperationResult.fail(
                    f"Unknown killswitch write method: {method_name}", "UNKNOWN_METHOD"
                )

        except Exception as e:
            return OperationResult.fail(str(e), "KILLSWITCH_WRITE_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register killswitch operations with the registry."""
    registry.register("killswitch.read", KillswitchReadHandler())
    registry.register("killswitch.write", KillswitchWriteHandler())
