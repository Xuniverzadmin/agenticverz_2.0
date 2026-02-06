# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Controls domain handler — routes controls operations to L5 engines via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.controls.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.3
# artifact_class: CODE

"""
Controls Handler (L4 Orchestrator)

Routes controls domain operations to L5 engines and L6 drivers.
Registers operations:
  - controls.query → ControlsFacade (6 async endpoints)
  - controls.thresholds → ThresholdEngine (constants + validation, 2 endpoints)
  - controls.overrides → LimitOverrideService
  - controls.circuit_breaker → CircuitBreakerAsyncDriver
  - controls.killswitch.read → KillswitchOpsDriver (entity verification, state queries)
  - controls.killswitch.write → GuardWriteDriver (freeze/unfreeze)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class ControlsQueryHandler:
    """
    Handler for controls.query operations.

    Dispatches to ControlsFacade methods (list_controls, get_status,
    get_control, update_control, enable_control, disable_control).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L5_engines.controls_facade import get_controls_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_controls_facade()
        dispatch = {
            "list_controls": facade.list_controls,
            "get_status": facade.get_status,
            "get_control": facade.get_control,
            "update_control": facade.update_control,
            "enable_control": facade.enable_control,
            "disable_control": facade.disable_control,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class ControlsThresholdHandler:
    """
    Handler for controls.thresholds operations.

    Provides threshold engine constants and validation:
      - get_defaults → returns DEFAULT_LLM_RUN_PARAMS
      - validate_params → validates ThresholdParams
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L5_engines.threshold_engine import (
            DEFAULT_LLM_RUN_PARAMS,
            ThresholdParams,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        if method_name == "get_defaults":
            return OperationResult.ok(DEFAULT_LLM_RUN_PARAMS.copy())

        elif method_name == "validate_params":
            params = ctx.params.get("params", {})
            defaults = DEFAULT_LLM_RUN_PARAMS.copy()
            try:
                ThresholdParams(**{**defaults, **params})
                return OperationResult.ok(True)
            except Exception as e:
                return OperationResult.fail(
                    f"Invalid threshold params: {str(e)}", "VALIDATION_ERROR"
                )

        elif method_name == "get_effective_params":
            raw_params = ctx.params.get("raw_params", {})
            effective = DEFAULT_LLM_RUN_PARAMS.copy()
            for key, value in raw_params.items():
                if key in effective and value is not None:
                    effective[key] = value
            return OperationResult.ok(effective)

        else:
            return OperationResult.fail(
                f"Unknown threshold method: {method_name}", "UNKNOWN_METHOD"
            )


class ControlsOverrideHandler:
    """
    Handler for controls.overrides operations.

    Routes to LimitOverrideService (PIN-504: L2 must not import L6 directly).
    Methods: request_override, list_overrides, get_override, cancel_override.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L6_drivers.override_driver import (
            LimitOverrideService,
        )
        from app.hoc.cus.controls.L5_schemas.override_types import (
            LimitNotFoundError,
            LimitOverrideServiceError,
            OverrideNotFoundError,
            OverrideValidationError,
            StackingAbuseError,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = LimitOverrideService(ctx.session)
        dispatch = {
            "request_override": service.request_override,
            "list_overrides": service.list_overrides,
            "get_override": service.get_override,
            "cancel_override": service.cancel_override,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(f"Unknown override method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except LimitNotFoundError as e:
            return OperationResult.fail(str(e), "LIMIT_NOT_FOUND")
        except OverrideNotFoundError as e:
            return OperationResult.fail(str(e), "OVERRIDE_NOT_FOUND")
        except OverrideValidationError as e:
            return OperationResult.fail(str(e), "VALIDATION_ERROR")
        except StackingAbuseError as e:
            return OperationResult.fail(str(e), "STACKING_ABUSE")
        except LimitOverrideServiceError as e:
            return OperationResult.fail(str(e), "SERVICE_ERROR")


class CircuitBreakerHandler:
    """
    Handler for controls.circuit_breaker operations.

    Routes circuit breaker operations for CostSim V2 sandbox:
      - is_disabled: Check if circuit breaker is open
      - get_state: Get full circuit breaker state
      - reset: Reset circuit breaker (re-enable V2)
      - get_incidents: Get recent incidents

    PIN-520 Phase 3: Migrates costsim.py circuit breaker access to L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            get_circuit_breaker,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        circuit_breaker = get_circuit_breaker()

        if method_name == "is_disabled":
            is_disabled = await circuit_breaker.is_disabled()
            return OperationResult.ok({"is_disabled": is_disabled})

        elif method_name == "get_state":
            state = await circuit_breaker.get_state()
            return OperationResult.ok(state.to_dict())

        elif method_name == "reset":
            reason = ctx.params.get("reason", "Manual reset via L4")
            is_disabled = await circuit_breaker.is_disabled()
            if not is_disabled:
                state = await circuit_breaker.get_state()
                return OperationResult.ok({
                    "success": True,
                    "message": "Circuit breaker was already closed",
                    "state": state.to_dict(),
                })
            success = await circuit_breaker.reset_v2(reason=reason)
            state = await circuit_breaker.get_state()
            return OperationResult.ok({
                "success": success,
                "message": "Circuit breaker reset" if success else "Failed to reset",
                "state": state.to_dict(),
            })

        elif method_name == "get_incidents":
            include_resolved = ctx.params.get("include_resolved", False)
            limit = ctx.params.get("limit", 10)
            incidents = circuit_breaker.get_incidents(
                include_resolved=include_resolved,
                limit=limit,
            )
            return OperationResult.ok({
                "incidents": [i.to_dict() for i in incidents],
                "total": len(incidents),
            })

        else:
            return OperationResult.fail(
                f"Unknown circuit_breaker method: {method_name}", "UNKNOWN_METHOD"
            )


class KillswitchReadHandler:
    """
    Handler for controls.killswitch.read operations.

    Routes killswitch read operations to KillswitchOpsDriver (L6):
      - verify_tenant: Check if tenant exists
      - verify_api_key: Check if API key exists
      - get_state: Get killswitch state for entity
      - get_key_states: Get all key states for tenant
      - list_guardrails: Get active guardrails
      - list_incidents: List incidents for tenant
      - get_incident: Get incident detail
      - get_incident_events: Get timeline events
      - get_proxy_call: Get proxy call for replay/detail

    Eliminates session.execute() from L2 v1_killswitch.py.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.controls.L6_drivers.killswitch_ops_driver import (
            get_killswitch_ops_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for killswitch read operations", "SESSION_REQUIRED"
            )

        driver = get_killswitch_ops_driver(ctx.session)
        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "verify_tenant":
                tenant_id = kwargs.get("tenant_id")
                if not tenant_id:
                    return OperationResult.fail("Missing 'tenant_id'", "MISSING_PARAM")
                result = driver.verify_tenant_exists(tenant_id)
                if result is None:
                    return OperationResult.ok({"exists": False, "data": None})
                return OperationResult.ok({"exists": True, "data": result.model_dump()})

            elif method_name == "verify_api_key":
                key_id = kwargs.get("key_id")
                if not key_id:
                    return OperationResult.fail("Missing 'key_id'", "MISSING_PARAM")
                result = driver.verify_api_key_exists(key_id)
                if result is None:
                    return OperationResult.ok({"exists": False, "data": None})
                return OperationResult.ok({"exists": True, "data": result.model_dump()})

            elif method_name == "get_state":
                entity_type = kwargs.get("entity_type")
                entity_id = kwargs.get("entity_id")
                if not entity_type or not entity_id:
                    return OperationResult.fail(
                        "Missing 'entity_type' or 'entity_id'", "MISSING_PARAM"
                    )
                result = driver.get_killswitch_state(entity_type, entity_id)
                if result is None:
                    return OperationResult.ok(None)
                return OperationResult.ok(result.model_dump())

            elif method_name == "get_key_states":
                tenant_id = kwargs.get("tenant_id")
                if not tenant_id:
                    return OperationResult.fail("Missing 'tenant_id'", "MISSING_PARAM")
                result = driver.get_key_states_for_tenant(tenant_id)
                return OperationResult.ok(result)

            elif method_name == "list_guardrails":
                result = driver.list_active_guardrails()
                return OperationResult.ok([g.model_dump() for g in result])

            elif method_name == "list_incidents":
                tenant_id = kwargs.get("tenant_id")
                if not tenant_id:
                    return OperationResult.fail("Missing 'tenant_id'", "MISSING_PARAM")
                status = kwargs.get("status")
                limit = kwargs.get("limit", 50)
                offset = kwargs.get("offset", 0)
                result = driver.list_incidents(tenant_id, status, limit, offset)
                return OperationResult.ok([i.model_dump() for i in result])

            elif method_name == "get_incident":
                incident_id = kwargs.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                result = driver.get_incident_detail(incident_id)
                if result is None:
                    return OperationResult.ok(None)
                return OperationResult.ok(result.model_dump())

            elif method_name == "get_incident_events":
                incident_id = kwargs.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                result = driver.get_incident_events(incident_id)
                return OperationResult.ok([e.model_dump() for e in result])

            elif method_name == "get_proxy_call":
                call_id = kwargs.get("call_id")
                if not call_id:
                    return OperationResult.fail("Missing 'call_id'", "MISSING_PARAM")
                result = driver.get_proxy_call(call_id)
                if result is None:
                    return OperationResult.ok(None)
                return OperationResult.ok(result.model_dump())

            return OperationResult.fail(
                f"Unknown killswitch read method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "KILLSWITCH_READ_ERROR")


class KillswitchWriteHandler:
    """
    Handler for controls.killswitch.write operations.

    Routes killswitch write operations to GuardWriteDriver (hoc_spine L6):
      - freeze: Freeze an entity (tenant or key)
      - unfreeze: Unfreeze an entity
      - get_or_create_state: Get or create killswitch state

    Uses existing GuardWriteDriver from hoc_spine.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.guard_write_driver import (
            get_guard_write_driver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for killswitch write operations", "SESSION_REQUIRED"
            )

        driver = get_guard_write_driver(ctx.session)
        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "get_or_create_state":
                entity_type = kwargs.get("entity_type")
                entity_id = kwargs.get("entity_id")
                tenant_id = kwargs.get("tenant_id")
                if not entity_type or not entity_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'entity_type', 'entity_id', or 'tenant_id'",
                        "MISSING_PARAM",
                    )
                state, is_new = driver.get_or_create_killswitch_state(
                    entity_type, entity_id, tenant_id
                )
                return OperationResult.ok({
                    "state": {
                        "id": state.id,
                        "entity_type": state.entity_type,
                        "entity_id": state.entity_id,
                        "tenant_id": state.tenant_id,
                        "is_frozen": state.is_frozen,
                        "frozen_at": state.frozen_at.isoformat() if state.frozen_at else None,
                        "frozen_by": state.frozen_by,
                        "freeze_reason": state.freeze_reason,
                        "auto_triggered": state.auto_triggered,
                        "trigger_type": state.trigger_type,
                    },
                    "is_new": is_new,
                })

            elif method_name == "freeze":
                entity_type = kwargs.get("entity_type")
                entity_id = kwargs.get("entity_id")
                tenant_id = kwargs.get("tenant_id")
                actor = kwargs.get("actor", "system")
                reason = kwargs.get("reason", "Manual freeze")
                auto = kwargs.get("auto", False)
                trigger = kwargs.get("trigger")

                if not entity_type or not entity_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'entity_type', 'entity_id', or 'tenant_id'",
                        "MISSING_PARAM",
                    )

                # Get or create state first
                state, _ = driver.get_or_create_killswitch_state(
                    entity_type, entity_id, tenant_id
                )
                if state.is_frozen:
                    return OperationResult.fail(
                        f"{entity_type.title()} is already frozen",
                        "ALREADY_FROZEN",
                    )

                state = driver.freeze_killswitch(
                    state=state,
                    by=actor,
                    reason=reason,
                    auto=auto,
                    trigger=trigger,
                )
                return OperationResult.ok({
                    "entity_type": state.entity_type,
                    "entity_id": state.entity_id,
                    "is_frozen": True,
                    "frozen_at": state.frozen_at.isoformat() if state.frozen_at else None,
                    "frozen_by": state.frozen_by,
                    "freeze_reason": state.freeze_reason,
                    "auto_triggered": state.auto_triggered,
                    "trigger_type": state.trigger_type,
                })

            elif method_name == "unfreeze":
                entity_type = kwargs.get("entity_type")
                entity_id = kwargs.get("entity_id")
                tenant_id = kwargs.get("tenant_id")
                actor = kwargs.get("actor", "system")

                if not entity_type or not entity_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'entity_type', 'entity_id', or 'tenant_id'",
                        "MISSING_PARAM",
                    )

                # Get or create state first
                state, _ = driver.get_or_create_killswitch_state(
                    entity_type, entity_id, tenant_id
                )
                if not state.is_frozen:
                    return OperationResult.fail(
                        f"{entity_type.title()} is not frozen",
                        "NOT_FROZEN",
                    )

                state = driver.unfreeze_killswitch(state=state, by=actor)
                return OperationResult.ok({
                    "entity_type": state.entity_type,
                    "entity_id": state.entity_id,
                    "is_frozen": False,
                    "frozen_at": state.frozen_at.isoformat() if state.frozen_at else None,
                    "frozen_by": state.frozen_by,
                    "freeze_reason": state.freeze_reason,
                    "auto_triggered": state.auto_triggered,
                    "trigger_type": state.trigger_type,
                })

            return OperationResult.fail(
                f"Unknown killswitch write method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "KILLSWITCH_WRITE_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register controls operations with the registry."""
    registry.register("controls.query", ControlsQueryHandler())
    registry.register("controls.thresholds", ControlsThresholdHandler())
    registry.register("controls.overrides", ControlsOverrideHandler())
    # PIN-520 Phase 3: Circuit breaker handler for CostSim V2
    registry.register("controls.circuit_breaker", CircuitBreakerHandler())
    # Killswitch operations (v1_killswitch.py L2 refactoring)
    registry.register("controls.killswitch.read", KillswitchReadHandler())
    registry.register("controls.killswitch.write", KillswitchWriteHandler())
