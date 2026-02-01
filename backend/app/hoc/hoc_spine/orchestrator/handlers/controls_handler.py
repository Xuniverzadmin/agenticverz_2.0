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

Routes controls domain operations to L5 engines.
Registers two operations:
  - controls.query → ControlsFacade (6 async endpoints)
  - controls.thresholds → ThresholdEngine (constants + validation, 2 endpoints)
"""

from app.hoc.hoc_spine.orchestrator.operation_registry import (
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


def register(registry: OperationRegistry) -> None:
    """Register controls operations with the registry."""
    registry.register("controls.query", ControlsQueryHandler())
    registry.register("controls.thresholds", ControlsThresholdHandler())
    registry.register("controls.overrides", ControlsOverrideHandler())
