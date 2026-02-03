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
Registers twelve operations:
  - policies.query → PoliciesFacade (15+ async methods)
  - policies.enforcement → CusEnforcementEngine (3 methods)
  - policies.governance → GovernanceFacade (7+ sync methods)
  - policies.lessons → LessonsLearnedEngine (async methods)
  - policies.policy_facade → PolicyDriver (37+ async methods)
  - policies.limits → PolicyLimitsService (create, update, delete)
  - policies.rules → PolicyRulesService (create, update)
  - policies.rate_limits → LimitsFacade (6 async methods)
  - policies.simulate → LimitsSimulationEngine (simulate)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
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
        dispatch = {
            "list_policy_rules": facade.list_policy_rules,
            "get_policy_rule_detail": facade.get_policy_rule_detail,
            "list_limits": facade.list_limits,
            "get_limit_detail": facade.get_limit_detail,
            "get_policy_state": facade.get_policy_state,
            "get_policy_metrics": facade.get_policy_metrics,
            "list_conflicts": facade.list_conflicts,
            "get_dependency_graph": facade.get_dependency_graph,
            "list_violations": facade.list_violations,
            "list_budgets": facade.list_budgets,
            "list_requests": facade.list_requests,
            "list_lessons": facade.list_lessons,
            "get_lesson_stats": facade.get_lesson_stats,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(f"Unknown facade method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class PoliciesEnforcementHandler:
    """
    Handler for policies.enforcement operations.

    Dispatches to CusEnforcementEngine methods (evaluate, get_enforcement_status,
    evaluate_batch).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.cus_enforcement_engine import (
            get_cus_enforcement_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = get_cus_enforcement_engine()
        dispatch = {
            "evaluate": service.evaluate,
            "get_enforcement_status": service.get_enforcement_status,
            "evaluate_batch": service.evaluate_batch,
        }
        method = dispatch.get(method_name)
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
        dispatch = {
            "enable_kill_switch": facade.enable_kill_switch,
            "disable_kill_switch": facade.disable_kill_switch,
            "set_mode": facade.set_mode,
            "get_governance_state": facade.get_governance_state,
            "resolve_conflict": facade.resolve_conflict,
            "list_conflicts": facade.list_conflicts,
            "get_boot_status": facade.get_boot_status,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(f"Unknown governance method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        data = method(**kwargs)
        return OperationResult.ok(data)


class PoliciesLessonsHandler:
    """
    Handler for policies.lessons operations.

    Dispatches to LessonsLearnedEngine methods.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.domain_bridge import get_domain_bridge

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        # PIN-508 Phase 2A: Inject capability via DomainBridge (Gap 3)
        bridge = get_domain_bridge()
        capability = bridge.lessons_capability(ctx.session)
        engine = get_lessons_learned_engine(driver=capability)
        dispatch = {
            "detect_lesson_from_failure": engine.detect_lesson_from_failure,
            "detect_lesson_from_near_threshold": engine.detect_lesson_from_near_threshold,
            "detect_lesson_from_critical_success": engine.detect_lesson_from_critical_success,
            "emit_near_threshold": engine.emit_near_threshold,
            "emit_critical_success": engine.emit_critical_success,
            "list_lessons": engine.list_lessons,
            "get_lesson": engine.get_lesson,
            "convert_lesson_to_draft": engine.convert_lesson_to_draft,
            "defer_lesson": engine.defer_lesson,
            "dismiss_lesson": engine.dismiss_lesson,
            "get_lesson_stats": engine.get_lesson_stats,
            "reactivate_deferred_lesson": engine.reactivate_deferred_lesson,
            "get_expired_deferred_lessons": engine.get_expired_deferred_lessons,
            "reactivate_expired_deferred_lessons": engine.reactivate_expired_deferred_lessons,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(f"Unknown lessons method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

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
        async_dispatch = {
            "evaluate": facade.evaluate,
            "pre_check": facade.pre_check,
            "get_state": facade.get_state,
            "reload_policies": facade.reload_policies,
            "get_violations": facade.get_violations,
            "get_violation": facade.get_violation,
            "acknowledge_violation": facade.acknowledge_violation,
            "get_risk_ceilings": facade.get_risk_ceilings,
            "get_risk_ceiling": facade.get_risk_ceiling,
            "update_risk_ceiling": facade.update_risk_ceiling,
            "reset_risk_ceiling": facade.reset_risk_ceiling,
            "get_safety_rules": facade.get_safety_rules,
            "update_safety_rule": facade.update_safety_rule,
            "get_ethical_constraints": facade.get_ethical_constraints,
            "get_active_cooldowns": facade.get_active_cooldowns,
            "clear_cooldowns": facade.clear_cooldowns,
            "get_metrics": facade.get_metrics,
            "get_policy_versions": facade.get_policy_versions,
            "get_current_version": facade.get_current_version,
            "create_policy_version": facade.create_policy_version,
            "rollback_to_version": facade.rollback_to_version,
            "get_version_provenance": facade.get_version_provenance,
            "activate_policy_version": facade.activate_policy_version,
            "get_dependency_graph": facade.get_dependency_graph,
            "get_policy_conflicts": facade.get_policy_conflicts,
            "resolve_conflict": facade.resolve_conflict,
            "validate_dependency_dag": facade.validate_dependency_dag,
            "add_dependency_with_dag_check": facade.add_dependency_with_dag_check,
            "get_temporal_policies": facade.get_temporal_policies,
            "create_temporal_policy": facade.create_temporal_policy,
            "get_temporal_utilization": facade.get_temporal_utilization,
            "prune_temporal_metrics": facade.prune_temporal_metrics,
            "get_temporal_storage_stats": facade.get_temporal_storage_stats,
            "evaluate_with_context": facade.evaluate_with_context,
        }
        sync_dispatch = {
            "get_topological_evaluation_order": facade.get_topological_evaluation_order,
        }

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        method = async_dispatch.get(method_name)
        if method:
            data = await method(**kwargs)
        elif method_name in sync_dispatch:
            data = sync_dispatch[method_name](**kwargs)
        else:
            return OperationResult.fail(f"Unknown policy_facade method: {method_name}", "UNKNOWN_METHOD")
        return OperationResult.ok(data)


class PoliciesLimitsHandler:
    """
    Handler for policies.limits operations.

    Dispatches to PolicyLimitsService (create, update, delete).
    Error classes (LimitNotFoundError, etc.) are translated to OperationResult.fail.
    Injects audit service into L5 engine (PIN-504: no cross-domain imports).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policy_limits_engine import (
            ImmutableFieldError,
            LimitNotFoundError,
            LimitValidationError,
            PolicyLimitsService,
            PolicyLimitsServiceError,
        )
        from app.hoc.cus.logs.L6_drivers.audit_ledger_service_async import (
            AuditLedgerServiceAsync,
        )
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.domain_bridge import get_domain_bridge

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        # PIN-508 Phase 2C: Inject capability via DomainBridge (Gap 3)
        bridge = get_domain_bridge()
        capability = bridge.policy_limits_capability(ctx.session)
        # L4 creates audit service and injects into L5 engine (PIN-504)
        audit = AuditLedgerServiceAsync(ctx.session)
        service = PolicyLimitsService(ctx.session, audit=audit, driver=capability)
        dispatch = {
            "create": service.create,
            "update": service.update,
            "delete": service.delete,
            "get": service.get,
        }
        method = dispatch.get(method_name)
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
    Injects audit service into L5 engine (PIN-504: no cross-domain imports).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policy_rules_engine import (
            PolicyRulesService,
            PolicyRulesServiceError,
            RuleNotFoundError,
            RuleValidationError,
        )
        from app.hoc.cus.logs.L6_drivers.audit_ledger_service_async import (
            AuditLedgerServiceAsync,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        # L4 creates audit service and injects into L5 engine (PIN-504)
        audit = AuditLedgerServiceAsync(ctx.session)
        service = PolicyRulesService(ctx.session, audit=audit)
        dispatch = {
            "create": service.create,
            "update": service.update,
            "get": service.get,
        }
        method = dispatch.get(method_name)
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
        dispatch = {
            "list_limits": facade.list_limits,
            "get_limit": facade.get_limit,
            "update_limit": facade.update_limit,
            "check_limit": facade.check_limit,
            "get_usage": facade.get_usage,
            "reset_limit": facade.reset_limit,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(f"Unknown rate_limits method: {method_name}", "UNKNOWN_METHOD")

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        data = await method(**kwargs)
        return OperationResult.ok(data)


class PoliciesSimulateHandler:
    """
    Handler for policies.simulate operations.

    Dispatches to LimitsSimulationEngine (simulate).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.limits_simulation_engine import (
            LimitsSimulationEngine,
            LimitsSimulationServiceError,
            TenantNotFoundError,
            get_limits_simulation_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        service = get_limits_simulation_engine(ctx.session)
        dispatch = {
            "simulate": service.simulate,
        }
        method = dispatch.get(method_name)
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


class PoliciesLimitsQueryHandler:
    """
    Handler for policies.limits_query operations (PIN-513 Batch 2B).

    Dispatches to LimitsQueryEngine (get_limits_query_engine).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policies_limits_query_engine import (
            get_limits_query_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        engine = get_limits_query_engine(session=ctx.session)
        method = getattr(engine, method_name, None)
        if method is None or not callable(method):
            return OperationResult.fail(
                f"Unknown limits_query method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        data = await method(**kwargs)
        return OperationResult.ok(data)


class PoliciesProposalsQueryHandler:
    """
    Handler for policies.proposals_query operations (PIN-513 Batch 2B).

    Dispatches to ProposalsQueryEngine (get_proposals_query_engine).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policies_proposals_query_engine import (
            get_proposals_query_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        engine = get_proposals_query_engine(session=ctx.session)
        method = getattr(engine, method_name, None)
        if method is None or not callable(method):
            return OperationResult.fail(
                f"Unknown proposals_query method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        data = await method(**kwargs)
        return OperationResult.ok(data)


class PoliciesRulesQueryHandler:
    """
    Handler for policies.rules_query operations (PIN-513 Batch 2B).

    Dispatches to PolicyRulesQueryEngine (get_policy_rules_query_engine).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L5_engines.policies_rules_query_engine import (
            get_policy_rules_query_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        engine = get_policy_rules_query_engine(session=ctx.session)
        method = getattr(engine, method_name, None)
        if method is None or not callable(method):
            return OperationResult.fail(
                f"Unknown rules_query method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = ctx.tenant_id

        data = await method(**kwargs)
        return OperationResult.ok(data)


class PoliciesHealthHandler:
    """
    Handler for policies.health operations (PIN-520 Phase 1).

    Reports availability of policy-related L5 engines.
    Used by workers.py health endpoint to check moat status.

    This handler absorbs the L5 import checks that were previously
    done directly in workers.py, routing them through L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        moat_status = {}

        # Check M20 Policy (DAGExecutor)
        try:
            from app.hoc.cus.policies.L5_engines.dag_executor import DAGExecutor
            DAGExecutor()
            moat_status["m20_policy"] = "available"
        except ImportError:
            moat_status["m20_policy"] = "unavailable"

        # Check M9 Failure Catalog and M10 Recovery (RecoveryEvaluationEngine)
        try:
            from app.hoc.cus.policies.L5_engines.recovery_evaluation_engine import (
                RecoveryEvaluationEngine,
            )
            RecoveryEvaluationEngine()
            moat_status["m9_failure_catalog"] = "available"
            moat_status["m10_recovery"] = "available"
        except ImportError:
            moat_status["m9_failure_catalog"] = "unavailable"
            moat_status["m10_recovery"] = "unavailable"

        return OperationResult.ok(moat_status)


class PoliciesRecoveryMatchHandler:
    """
    Handler for policies.recovery.match operations.

    PIN-520 Phase 1: Routes RecoveryMatcher through L4 registry.
    Dispatches to RecoveryMatcher methods.

    Methods:
      - suggest: Synchronous pattern matching and suggestion generation
      - suggest_hybrid: Async hybrid (embedding + LLM) suggestion
      - get_candidates: List recovery candidates
      - count_candidates: Count candidates by status
      - count_by_status: Get candidate counts grouped by status
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.recovery_matcher import RecoveryMatcher

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # RecoveryMatcher requires a session
        if ctx.session is None:
            return OperationResult.fail(
                "Session required for recovery match operations", "SESSION_REQUIRED"
            )

        matcher = RecoveryMatcher(ctx.session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "suggest":
                request = kwargs.get("request")
                if not request:
                    return OperationResult.fail("Missing 'request'", "MISSING_REQUEST")
                result = matcher.suggest(request)
                return OperationResult.ok(result.__dict__ if hasattr(result, "__dict__") else result)

            elif method_name == "suggest_hybrid":
                request = kwargs.get("request")
                if not request:
                    return OperationResult.fail("Missing 'request'", "MISSING_REQUEST")
                result = await matcher.suggest_hybrid(request)
                return OperationResult.ok(result.__dict__ if hasattr(result, "__dict__") else result)

            elif method_name == "get_candidates":
                status = kwargs.get("status", "pending")
                limit = kwargs.get("limit", 50)
                offset = kwargs.get("offset", 0)
                result = matcher.get_candidates(status=status, limit=limit, offset=offset)
                return OperationResult.ok({"candidates": result})

            elif method_name == "count_candidates":
                status = kwargs.get("status", "pending")
                count = matcher.count_candidates(status=status)
                return OperationResult.ok({"count": count})

            elif method_name == "count_by_status":
                counts = matcher.count_by_status()
                return OperationResult.ok(counts)

            return OperationResult.fail(
                f"Unknown recovery match method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "RECOVERY_MATCH_ERROR")


class PoliciesRecoveryWriteHandler:
    """
    Handler for policies.recovery.write operations.

    PIN-520 Phase 1: Routes RecoveryWriteService through L4 registry.
    Dispatches to RecoveryWriteService methods for candidate management.

    Methods:
      - upsert_candidate: Atomic upsert of recovery candidate
      - get_by_idempotency_key: Get candidate by idempotency key
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.recovery_write_driver import (
            RecoveryWriteService,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        # RecoveryWriteService needs a session
        if ctx.session is None:
            return OperationResult.fail(
                "Session required for recovery write operations", "SESSION_REQUIRED"
            )

        service = RecoveryWriteService(ctx.session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "upsert_candidate":
                # Required params for upsert
                result = service.upsert_recovery_candidate(
                    failure_match_id=kwargs.get("failure_match_id"),
                    suggestion=kwargs.get("suggestion"),
                    confidence=kwargs.get("confidence"),
                    explain_json=kwargs.get("explain_json"),
                    error_code=kwargs.get("error_code"),
                    error_signature=kwargs.get("error_signature"),
                    source=kwargs.get("source"),
                    idempotency_key=kwargs.get("idempotency_key"),
                )
                return OperationResult.ok({
                    "candidate_id": result[0],
                    "is_insert": result[1],
                    "occurrence_count": result[2],
                })

            elif method_name == "get_by_idempotency_key":
                idempotency_key = kwargs.get("idempotency_key")
                if not idempotency_key:
                    return OperationResult.fail("Missing 'idempotency_key'", "MISSING_KEY")
                result = service.get_candidate_by_idempotency_key(idempotency_key)
                if result:
                    return OperationResult.ok({"candidate_id": result[0], "status": result[1]})
                return OperationResult.ok(None)

            return OperationResult.fail(
                f"Unknown recovery write method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "RECOVERY_WRITE_ERROR")


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
    # PIN-513 Batch 2B: Query engine handlers
    registry.register("policies.limits_query", PoliciesLimitsQueryHandler())
    registry.register("policies.proposals_query", PoliciesProposalsQueryHandler())
    registry.register("policies.rules_query", PoliciesRulesQueryHandler())
    # PIN-520 Phase 1: Health handler for workers.py migration
    registry.register("policies.health", PoliciesHealthHandler())
    # PIN-520 Phase 1: Recovery handlers for recovery.py and recovery_ingest.py migration
    registry.register("policies.recovery.match", PoliciesRecoveryMatchHandler())
    registry.register("policies.recovery.write", PoliciesRecoveryWriteHandler())
