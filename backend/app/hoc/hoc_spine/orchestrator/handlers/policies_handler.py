# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Policies domain handler — routes policies operations to L5 engines via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.policies.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.5
# artifact_class: CODE

"""
Policies Handler (L4 Orchestrator)

Routes policies domain operations to L5 engines.
Registers nine operations:
  - policies.query → PoliciesFacade (15+ async methods)
  - policies.enforcement → CusEnforcementService (3 methods)
  - policies.governance → GovernanceFacade (7+ sync methods)
  - policies.lessons → LessonsLearnedEngine (async methods)
  - policies.policy_facade → PolicyDriver (37+ async methods)
  - policies.limits → PolicyLimitsService (create, update, delete)
  - policies.rules → PolicyRulesService (create, update)
  - policies.rate_limits → LimitsFacade (6 async methods)
  - policies.simulate → LimitsSimulationService (simulate)
"""

import asyncio

from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class PoliciesQueryHandler:
    """
    Handler for policies.query operations.

    Dispatches to PoliciesFacade methods (list_policy_rules, get_policy_rule_detail,
    list_limits, get_limit_detail, list_lessons, get_lesson_stats, etc.).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policies_facade import get_policies_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        facade = get_policies_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown facade method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class PoliciesEnforcementHandler:
    """
    Handler for policies.enforcement operations.

    Dispatches to CusEnforcementService methods (evaluate, get_enforcement_status,
    evaluate_batch).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.cus_enforcement_service import (
            get_cus_enforcement_service,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = get_cus_enforcement_service()
        method = getattr(service, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown enforcement method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id
        data = await method(**kwargs)
        return OperationResult.ok(data)


class PoliciesGovernanceHandler:
    """
    Handler for policies.governance operations.

    Dispatches to GovernanceFacade methods. Note: facade methods are SYNC.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.governance_facade import (
            get_governance_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        facade = get_governance_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown governance method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        # GovernanceFacade methods are sync
        if asyncio.iscoroutinefunction(method):
            data = await method(**kwargs)
        else:
            data = method(**kwargs)
        return OperationResult.ok(data)


class PoliciesLessonsHandler:
    """
    Handler for policies.lessons operations.

    Dispatches to LessonsLearnedEngine methods.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        engine = get_lessons_learned_engine()
        method = getattr(engine, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown lessons method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        if asyncio.iscoroutinefunction(method):
            data = await method(**kwargs)
        else:
            data = method(**kwargs)
        return OperationResult.ok(data)


class PoliciesPolicyFacadeHandler:
    """
    Handler for policies.policy_facade operations.

    Dispatches to PolicyDriver (policy_driver.py) methods.
    37+ call sites in policy_layer.py.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policy_driver import get_policy_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        facade = get_policy_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown policy_facade method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        if asyncio.iscoroutinefunction(method):
            data = await method(**kwargs)
        else:
            data = method(**kwargs)
        return OperationResult.ok(data)


class PoliciesLimitsHandler:
    """
    Handler for policies.limits operations.

    Dispatches to PolicyLimitsService (create, update, delete).
    Error classes (LimitNotFoundError, etc.) are translated to OperationResult.fail.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policy_limits_engine import (
            ImmutableFieldError,
            LimitNotFoundError,
            LimitValidationError,
            PolicyLimitsService,
            PolicyLimitsServiceError,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = PolicyLimitsService(ctx.session)
        method = getattr(service, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown limits method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except LimitNotFoundError as e:
            return OperationResult.fail(str(e), "LIMIT_NOT_FOUND")
        except ImmutableFieldError as e:
            return OperationResult.fail(str(e), "IMMUTABLE_FIELD")
        except LimitValidationError as e:
            return OperationResult.fail(str(e), "VALIDATION_ERROR")
        except PolicyLimitsServiceError as e:
            return OperationResult.fail(str(e), "SERVICE_ERROR")


class PoliciesRulesHandler:
    """
    Handler for policies.rules operations.

    Dispatches to PolicyRulesService (create, update).
    Error classes translated to OperationResult.fail.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policy_rules_engine import (
            PolicyRulesService,
            PolicyRulesServiceError,
            RuleNotFoundError,
            RuleValidationError,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = PolicyRulesService(ctx.session)
        method = getattr(service, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown rules method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except RuleNotFoundError as e:
            return OperationResult.fail(str(e), "RULE_NOT_FOUND")
        except RuleValidationError as e:
            return OperationResult.fail(str(e), "VALIDATION_ERROR")
        except PolicyRulesServiceError as e:
            return OperationResult.fail(str(e), "SERVICE_ERROR")


class PoliciesRateLimitsHandler:
    """
    Handler for policies.rate_limits operations.

    Dispatches to LimitsFacade methods (list_limits, get_limit, update_limit,
    get_usage, check_limit, reset_usage).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.limits_facade import get_limits_facade

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        facade = get_limits_facade()
        method = getattr(facade, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown rate_limits method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        if asyncio.iscoroutinefunction(method):
            data = await method(**kwargs)
        else:
            data = method(**kwargs)
        return OperationResult.ok(data)


class PoliciesSimulateHandler:
    """
    Handler for policies.simulate operations.

    Dispatches to LimitsSimulationService (simulate).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.limits_simulation_service import (
            LimitsSimulationService,
            LimitsSimulationServiceError,
            TenantNotFoundError,
            get_limits_simulation_service,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = get_limits_simulation_service(ctx.session)
        method = getattr(service, method_name, None)
        if method is None:
            return OperationResult.fail(f"Unknown simulate method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except TenantNotFoundError as e:
            return OperationResult.fail(str(e), "TENANT_NOT_FOUND")
        except LimitsSimulationServiceError as e:
            return OperationResult.fail(str(e), "SIMULATION_ERROR")


def register(registry: OperationRegistry) -> None:
    """Register policies domain handlers."""
    registry.register("policies.query", PoliciesQueryHandler())
    registry.register("policies.enforcement", PoliciesEnforcementHandler())
    registry.register("policies.governance", PoliciesGovernanceHandler())
    registry.register("policies.lessons", PoliciesLessonsHandler())
    registry.register("policies.policy_facade", PoliciesPolicyFacadeHandler())
    registry.register("policies.limits", PoliciesLimitsHandler())
    registry.register("policies.rules", PoliciesRulesHandler())
    registry.register("policies.rate_limits", PoliciesRateLimitsHandler())
    registry.register("policies.simulate", PoliciesSimulateHandler())
