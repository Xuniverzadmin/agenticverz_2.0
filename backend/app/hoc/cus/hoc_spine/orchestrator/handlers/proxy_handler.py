# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: sync
# Role: Proxy domain handler — routes proxy operations to L6 driver via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.integrations.L6_drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), L2→L6 elimination
# artifact_class: CODE

"""
Proxy Handler (L4 Orchestrator)

Routes proxy domain operations to L6 proxy_driver.
Registers operations:
  - proxy.get_api_key_by_hash → ProxyDriver.get_api_key_by_hash()
  - proxy.get_tenant_by_id → ProxyDriver.get_tenant_by_id()
  - proxy.record_api_key_usage → ProxyDriver.record_api_key_usage()
  - proxy.get_killswitch_state → ProxyDriver.get_killswitch_state()
  - proxy.get_enabled_guardrails → ProxyDriver.get_enabled_guardrails()
  - proxy.log_proxy_call → ProxyDriver.log_proxy_call()
  - proxy.get_latency_stats → ProxyDriver.get_latency_stats()
  - proxy.get_blocked_call_count → ProxyDriver.get_blocked_call_count()
  - proxy.get_last_incident → ProxyDriver.get_last_incident()
  - proxy.get_api_key_id_and_tenant → ProxyDriver.get_api_key_id_and_tenant()
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class ProxyHandler:
    """
    Handler for proxy.* operations.

    Dispatches to ProxyDriver methods for all proxy-related DB operations.
    Note: Uses sync session — driver is synchronous.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.integrations.L6_drivers.proxy_driver import get_proxy_driver

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
            driver = get_proxy_driver(sync_session)

            if method_name == "get_api_key_by_hash":
                key_hash = ctx.params.get("key_hash")
                if not key_hash:
                    return OperationResult.fail("Missing 'key_hash'", "MISSING_PARAM")
                result = driver.get_api_key_by_hash(key_hash)
                return OperationResult.ok(result)

            elif method_name == "get_api_key_id_and_tenant":
                key_hash = ctx.params.get("key_hash")
                if not key_hash:
                    return OperationResult.fail("Missing 'key_hash'", "MISSING_PARAM")
                result = driver.get_api_key_id_and_tenant(key_hash)
                return OperationResult.ok(result)

            elif method_name == "get_tenant_by_id":
                tenant_id = ctx.params.get("lookup_tenant_id")
                if not tenant_id:
                    return OperationResult.fail("Missing 'lookup_tenant_id'", "MISSING_PARAM")
                result = driver.get_tenant_by_id(tenant_id)
                return OperationResult.ok(result)

            elif method_name == "record_api_key_usage":
                key_id = ctx.params.get("key_id")
                now = ctx.params.get("now")
                if not key_id or now is None:
                    return OperationResult.fail("Missing 'key_id' or 'now'", "MISSING_PARAM")
                driver.record_api_key_usage(key_id, now)
                # L4 owns transaction boundary
                ctx.session.commit()
                return OperationResult.ok({"recorded": True})

            elif method_name == "get_killswitch_state":
                entity_type = ctx.params.get("entity_type")
                entity_id = ctx.params.get("entity_id")
                if not entity_type or not entity_id:
                    return OperationResult.fail(
                        "Missing 'entity_type' or 'entity_id'", "MISSING_PARAM"
                    )
                result = driver.get_killswitch_state(entity_type, entity_id)
                return OperationResult.ok(result)

            elif method_name == "get_enabled_guardrails":
                result = driver.get_enabled_guardrails()
                return OperationResult.ok(result)

            elif method_name == "log_proxy_call":
                # Extract all required params for proxy call logging
                call_data = ctx.params.get("call_data", {})
                driver.log_proxy_call(**call_data)
                # L4 owns transaction boundary
                ctx.session.commit()
                return OperationResult.ok({"logged": True})

            elif method_name == "get_latency_stats":
                since = ctx.params.get("since")
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                limit = ctx.params.get("limit", 1000)
                if since is None:
                    return OperationResult.fail("Missing 'since'", "MISSING_PARAM")
                result = driver.get_latency_stats(since, lookup_tenant_id, limit)
                return OperationResult.ok(result)

            elif method_name == "get_blocked_call_count":
                since = ctx.params.get("since")
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                if since is None:
                    return OperationResult.fail("Missing 'since'", "MISSING_PARAM")
                result = driver.get_blocked_call_count(since, lookup_tenant_id)
                return OperationResult.ok(result)

            elif method_name == "get_last_incident":
                lookup_tenant_id = ctx.params.get("lookup_tenant_id")
                result = driver.get_last_incident(lookup_tenant_id)
                return OperationResult.ok(result)

            else:
                return OperationResult.fail(
                    f"Unknown proxy method: {method_name}", "UNKNOWN_METHOD"
                )

        except Exception as e:
            return OperationResult.fail(str(e), "PROXY_DRIVER_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register proxy operations with the registry."""
    registry.register("proxy.ops", ProxyHandler())
