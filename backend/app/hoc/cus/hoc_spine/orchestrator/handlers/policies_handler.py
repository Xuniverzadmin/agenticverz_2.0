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

        # RecoveryMatcher uses a sync SQLModel Session.
        # First-principles pattern: ctx.session=None and params["sync_session"] holds the sync session.
        # Back-compat: accept ctx.session for older call sites.
        session = ctx.params.get("sync_session") or ctx.session
        if session is None:
            return OperationResult.fail(
                "Session required for recovery match operations", "SESSION_REQUIRED"
            )

        matcher = RecoveryMatcher(session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        kwargs.pop("sync_session", None)

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

            elif method_name == "approve_candidate_transactional":
                candidate_id = kwargs.get("candidate_id")
                approved_by = kwargs.get("approved_by")
                decision = kwargs.get("decision", "approved")
                note = kwargs.get("note", "")
                if candidate_id is None or not approved_by:
                    return OperationResult.fail(
                        "Missing 'candidate_id' or 'approved_by'", "MISSING_PARAMS"
                    )
                try:
                    data = matcher.approve_candidate(
                        candidate_id=int(candidate_id),
                        approved_by=str(approved_by),
                        decision=str(decision),
                        note=str(note or ""),
                    )
                    session.commit()
                    return OperationResult.ok(data)
                except Exception as e:
                    session.rollback()
                    raise e

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
      - upsert_candidate: Atomic upsert of recovery candidate (no commit)
      - upsert_candidate_transactional: Upsert with L4-owned commit/rollback
      - get_by_idempotency_key: Get candidate by idempotency key
      - enqueue_evaluation_transactional: DB fallback enqueue with commit
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

        # RecoveryWriteService uses a sync SQLModel Session.
        # First-principles pattern: ctx.session=None and params["sync_session"] holds the sync session.
        # Back-compat: accept ctx.session for older call sites.
        session = ctx.params.get("sync_session") or ctx.session
        if session is None:
            return OperationResult.fail(
                "Session required for recovery write operations", "SESSION_REQUIRED"
            )

        service = RecoveryWriteService(session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        kwargs.pop("sync_session", None)

        try:
            if method_name == "upsert_candidate":
                # Required params for upsert (no commit - legacy compatibility)
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

            elif method_name == "upsert_candidate_transactional":
                # L4 owns transaction boundary: upsert + commit, rollback on integrity error
                try:
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
                    session.commit()
                    return OperationResult.ok({
                        "candidate_id": result[0],
                        "is_insert": result[1],
                        "occurrence_count": result[2],
                    })
                except Exception as ie:
                    # Check if it's an integrity error (unique constraint violation)
                    if "integrity" in type(ie).__name__.lower() or "unique" in str(ie).lower():
                        session.rollback()
                        # Return the integrity error details for L2 to handle
                        return OperationResult.fail(
                            str(getattr(ie, "orig", ie)),
                            "INTEGRITY_ERROR"
                        )
                    raise

            elif method_name == "get_by_idempotency_key":
                idempotency_key = kwargs.get("idempotency_key")
                if not idempotency_key:
                    return OperationResult.fail("Missing 'idempotency_key'", "MISSING_KEY")
                result = service.get_candidate_by_idempotency_key(idempotency_key)
                if result:
                    return OperationResult.ok({"candidate_id": result[0], "failure_match_id": result[1]})
                return OperationResult.ok(None)

            elif method_name == "enqueue_evaluation_transactional":
                # L4 owns transaction boundary: enqueue + commit
                candidate_id = kwargs.get("candidate_id")
                idempotency_key = kwargs.get("idempotency_key")
                if candidate_id is None:
                    return OperationResult.fail("Missing 'candidate_id'", "MISSING_PARAM")
                try:
                    service.enqueue_evaluation_db_fallback(candidate_id, idempotency_key)
                    session.commit()
                    return OperationResult.ok({"enqueued": True})
                except Exception as e:
                    session.rollback()
                    return OperationResult.fail(str(e), "ENQUEUE_ERROR")

            elif method_name == "update_candidate_transactional":
                """
                Transactional candidate update used by L2 recovery APIs.
                L2 passes desired fields; L4 builds SQL update list and commits.
                """
                import json

                candidate_id = kwargs.get("candidate_id")
                if candidate_id is None:
                    return OperationResult.fail("Missing 'candidate_id'", "MISSING_PARAM")

                execution_status = kwargs.get("execution_status")
                selected_action_id = kwargs.get("selected_action_id")
                execution_result = kwargs.get("execution_result")
                note = kwargs.get("note")
                old_confidence = kwargs.get("old_confidence", 0.0)

                updates: list[str] = []
                params: dict[str, Any] = {"id": int(candidate_id)}

                if execution_status:
                    updates.append("execution_status = :execution_status")
                    params["execution_status"] = execution_status
                    if execution_status in ("succeeded", "failed", "rolled_back"):
                        updates.append("executed_at = now()")

                if selected_action_id is not None:
                    updates.append("selected_action_id = :selected_action_id")
                    params["selected_action_id"] = selected_action_id

                if execution_result is not None:
                    updates.append("execution_result = CAST(:execution_result AS jsonb)")
                    params["execution_result"] = json.dumps(execution_result)

                if not updates:
                    return OperationResult.fail("No updates provided", "MISSING_UPDATES")

                try:
                    service.update_recovery_candidate(int(candidate_id), updates, params)

                    # Provenance is best-effort. If table is missing, do not fail update.
                    if execution_status or note or selected_action_id is not None:
                        try:
                            event_type = (
                                "executed"
                                if execution_status == "executing"
                                else (
                                    "success"
                                    if execution_status == "succeeded"
                                    else (
                                        "failure"
                                        if execution_status == "failed"
                                        else "manual_override"
                                    )
                                )
                            )
                            service.insert_suggestion_provenance(
                                suggestion_id=int(candidate_id),
                                event_type=event_type,
                                details_json=json.dumps(
                                    {
                                        "execution_status": execution_status,
                                        "note": note,
                                    }
                                ),
                                action_id=selected_action_id,
                                confidence_before=float(old_confidence or 0.0),
                                actor="api",
                            )
                        except Exception:
                            pass

                    session.commit()
                    return OperationResult.ok(
                        {
                            "status": "updated",
                            "candidate_id": int(candidate_id),
                            "updates_applied": list(params.keys()),
                        }
                    )
                except Exception as e:
                    session.rollback()
                    return OperationResult.fail(str(e), "RECOVERY_UPDATE_ERROR")

            return OperationResult.fail(
                f"Unknown recovery write method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "RECOVERY_WRITE_ERROR")


class PoliciesGuardReadHandler:
    """
    Handler for policies.guard_read operations.

    L2 first-principles purity: Routes all guard/killswitch DB read
    operations through L4 to L6 GuardReadDriver.
    This eliminates sqlalchemy/sqlmodel imports from L2 guard files.

    Methods dispatch directly to GuardReadDriver by method name.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.guard_read_driver import GuardReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for guard read operations", "SESSION_REQUIRED"
            )

        driver = GuardReadDriver(ctx.session)
        method = getattr(driver, method_name, None)
        if method is None or not callable(method):
            return OperationResult.fail(
                f"Unknown guard_read method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            data = await method(**kwargs)
            return OperationResult.ok(data)
        except Exception as e:
            return OperationResult.fail(str(e), "GUARD_READ_ERROR")


class PoliciesSyncGuardReadHandler:
    """
    Handler for policies.sync_guard_read operations.

    L2 first-principles purity: Routes all sync guard/killswitch DB read
    operations through L4 to L6 SyncGuardReadDriver.
    This eliminates session.execute() calls from L2 guard.py.

    Uses synchronous Session (SQLModel Session via get_sync_session_dep).

    Methods dispatch directly to SyncGuardReadDriver by method name.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.guard_read_driver import SyncGuardReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for sync guard read operations", "SESSION_REQUIRED"
            )

        driver = SyncGuardReadDriver(ctx.session)
        method = getattr(driver, method_name, None)
        if method is None or not callable(method):
            return OperationResult.fail(
                f"Unknown sync_guard_read method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            # Sync driver methods are not async
            data = method(**kwargs)
            return OperationResult.ok(data)
        except Exception as e:
            return OperationResult.fail(str(e), "SYNC_GUARD_READ_ERROR")


class PoliciesCustomerVisibilityHandler:
    """
    Handler for policies.customer_visibility operations.

    Routes customer visibility DB read operations through L4 to L6 GuardReadDriver.
    Supports fetch_run_outcome and fetch_decision_summary for outcome reconciliation.

    Methods:
      - fetch_run_outcome: Get run data for outcome reconciliation
      - fetch_decision_summary: Get decision summary (effects only)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.guard_read_driver import GuardReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for customer visibility operations", "SESSION_REQUIRED"
            )

        driver = GuardReadDriver(ctx.session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "fetch_run_outcome":
                run_id = kwargs.get("run_id")
                tenant_id = kwargs.get("tenant_id")
                if not run_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'run_id' or 'tenant_id'", "MISSING_PARAMS"
                    )
                data = await driver.fetch_run_outcome(run_id, tenant_id)
                return OperationResult.ok(data)

            elif method_name == "fetch_decision_summary":
                run_id = kwargs.get("run_id")
                tenant_id = kwargs.get("tenant_id")
                if not run_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'run_id' or 'tenant_id'", "MISSING_PARAMS"
                    )
                data = await driver.fetch_decision_summary(run_id, tenant_id)
                return OperationResult.ok(data)

            return OperationResult.fail(
                f"Unknown customer_visibility method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "CUSTOMER_VISIBILITY_ERROR")


class PoliciesRecoveryReadHandler:
    """
    Handler for policies.recovery.read operations.

    L2 first-principles purity: Routes all recovery DB read
    operations through L4 to L6 RecoveryReadDriver.
    This eliminates session.execute() from L2 recovery.py.

    Methods:
      - get_candidate_detail: Get detailed candidate by ID
      - get_selected_action: Get action by ID
      - get_suggestion_inputs: Get inputs for a suggestion
      - get_suggestion_provenance: Get provenance history for a suggestion
      - candidate_exists: Check if candidate exists (returns exists, confidence)
      - list_actions: List recovery actions from catalog
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.recovery_read_driver import RecoveryReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        session = ctx.params.get("sync_session") or ctx.session
        if session is None:
            return OperationResult.fail(
                "Session required for recovery read operations", "SESSION_REQUIRED"
            )

        driver = RecoveryReadDriver(session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        kwargs.pop("sync_session", None)

        try:
            if method_name == "get_candidate_detail":
                candidate_id = kwargs.get("candidate_id")
                if candidate_id is None:
                    return OperationResult.fail("Missing 'candidate_id'", "MISSING_PARAM")
                data = driver.get_candidate_detail(candidate_id)
                return OperationResult.ok(data)

            elif method_name == "get_selected_action":
                action_id = kwargs.get("action_id")
                if action_id is None:
                    return OperationResult.fail("Missing 'action_id'", "MISSING_PARAM")
                data = driver.get_selected_action(action_id)
                return OperationResult.ok(data)

            elif method_name == "get_suggestion_inputs":
                suggestion_id = kwargs.get("suggestion_id")
                if suggestion_id is None:
                    return OperationResult.fail("Missing 'suggestion_id'", "MISSING_PARAM")
                data = driver.get_suggestion_inputs(suggestion_id)
                return OperationResult.ok(data)

            elif method_name == "get_suggestion_provenance":
                suggestion_id = kwargs.get("suggestion_id")
                if suggestion_id is None:
                    return OperationResult.fail("Missing 'suggestion_id'", "MISSING_PARAM")
                data = driver.get_suggestion_provenance(suggestion_id)
                return OperationResult.ok(data)

            elif method_name == "candidate_exists":
                candidate_id = kwargs.get("candidate_id")
                if candidate_id is None:
                    return OperationResult.fail("Missing 'candidate_id'", "MISSING_PARAM")
                exists, confidence = driver.candidate_exists(candidate_id)
                return OperationResult.ok({"exists": exists, "confidence": confidence})

            elif method_name == "list_actions":
                action_type = kwargs.get("action_type")
                active_only = kwargs.get("active_only", True)
                limit = kwargs.get("limit", 50)
                data = driver.list_actions(
                    action_type=action_type,
                    active_only=active_only,
                    limit=limit,
                )
                return OperationResult.ok({"actions": data, "total": len(data)})

            return OperationResult.fail(
                f"Unknown recovery read method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "RECOVERY_READ_ERROR")


class PoliciesReplayHandler:
    """
    Handler for policies.replay operations.

    L2 first-principles purity: Routes all replay UX DB read
    operations through L4 to L6 ReplayReadDriver.
    This eliminates session.execute() from L2 replay.py.

    Methods:
      - get_incident: Get incident by ID with tenant check
      - get_incident_no_tenant_check: Get incident by ID (caller does tenant check)
      - get_proxy_calls_in_window: Get proxy calls within time window
      - get_incident_events_in_window: Get incident events within time window
      - get_proxy_calls_for_timeline: Get all proxy calls for timeline
      - get_all_incident_events: Get all incident events
      - get_proxy_call_by_id: Get single proxy call
      - get_incident_event_by_id: Get single incident event
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.replay_read_driver import ReplayReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for replay read operations", "SESSION_REQUIRED"
            )

        driver = ReplayReadDriver(ctx.session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "get_incident":
                incident_id = kwargs.get("incident_id")
                tenant_id = kwargs.get("tenant_id")
                if not incident_id or not tenant_id:
                    return OperationResult.fail(
                        "Missing 'incident_id' or 'tenant_id'", "MISSING_PARAMS"
                    )
                data = driver.get_incident(incident_id, tenant_id)
                return OperationResult.ok(data)

            elif method_name == "get_incident_no_tenant_check":
                incident_id = kwargs.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                data = driver.get_incident_no_tenant_check(incident_id)
                return OperationResult.ok(data)

            elif method_name == "get_proxy_calls_in_window":
                call_ids = kwargs.get("call_ids", [])
                window_start = kwargs.get("window_start")
                window_end = kwargs.get("window_end")
                if window_start is None or window_end is None:
                    return OperationResult.fail(
                        "Missing 'window_start' or 'window_end'", "MISSING_PARAMS"
                    )
                data = driver.get_proxy_calls_in_window(call_ids, window_start, window_end)
                return OperationResult.ok(data)

            elif method_name == "get_incident_events_in_window":
                incident_id = kwargs.get("incident_id")
                window_start = kwargs.get("window_start")
                window_end = kwargs.get("window_end")
                if not incident_id or window_start is None or window_end is None:
                    return OperationResult.fail(
                        "Missing 'incident_id', 'window_start', or 'window_end'",
                        "MISSING_PARAMS",
                    )
                data = driver.get_incident_events_in_window(
                    incident_id, window_start, window_end
                )
                return OperationResult.ok(data)

            elif method_name == "get_proxy_calls_for_timeline":
                call_ids = kwargs.get("call_ids", [])
                limit = kwargs.get("limit", 100)
                data = driver.get_proxy_calls_for_timeline(call_ids, limit)
                return OperationResult.ok(data)

            elif method_name == "get_all_incident_events":
                incident_id = kwargs.get("incident_id")
                if not incident_id:
                    return OperationResult.fail("Missing 'incident_id'", "MISSING_PARAM")
                data = driver.get_all_incident_events(incident_id)
                return OperationResult.ok(data)

            elif method_name == "get_proxy_call_by_id":
                call_id = kwargs.get("call_id")
                if not call_id:
                    return OperationResult.fail("Missing 'call_id'", "MISSING_PARAM")
                data = driver.get_proxy_call_by_id(call_id)
                return OperationResult.ok(data)

            elif method_name == "get_incident_event_by_id":
                event_id = kwargs.get("event_id")
                incident_id = kwargs.get("incident_id")
                if not event_id or not incident_id:
                    return OperationResult.fail(
                        "Missing 'event_id' or 'incident_id'", "MISSING_PARAMS"
                    )
                data = driver.get_incident_event_by_id(event_id, incident_id)
                return OperationResult.ok(data)

            return OperationResult.fail(
                f"Unknown replay method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "REPLAY_READ_ERROR")


class RbacAuditHandler:
    """
    Handler for rbac.audit_query and rbac.audit_cleanup operations.

    L2 first-principles purity: Routes all RBAC audit DB operations
    through L4 to L6 RbacAuditDriver.
    This eliminates db.execute() and db.commit() from L2 rbac_api.py.

    Transaction boundary: L4 owns commit/rollback (not L6 driver).

    Methods:
      - query_audit_logs: Query audit entries with filters (read-only)
      - cleanup_audit_logs: Delete old audit entries (L4 commits after driver call)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.rbac_audit_driver import (
            RbacAuditDriver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        # RbacAuditDriver expects a sync session passed via params
        sync_session = ctx.params.get("sync_session")
        if sync_session is None:
            return OperationResult.fail(
                "sync_session required for RBAC audit operations", "SESSION_REQUIRED"
            )

        driver = RbacAuditDriver(sync_session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        kwargs.pop("sync_session", None)

        try:
            if method_name == "query_audit_logs":
                result = driver.query_audit_logs(**kwargs)
                return OperationResult.ok({
                    "entries": [e.model_dump() for e in result.entries],
                    "total": result.total,
                })

            elif method_name == "cleanup_audit_logs":
                retention_days = kwargs.get("retention_days")
                if retention_days is None:
                    return OperationResult.fail(
                        "Missing 'retention_days'", "MISSING_PARAM"
                    )
                result = driver.cleanup_audit_logs(retention_days=retention_days)
                # L4 owns transaction boundary — commit after successful driver call
                sync_session.commit()
                return OperationResult.ok({"deleted_count": result.deleted_count})

            return OperationResult.fail(
                f"Unknown rbac audit method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            # L4 owns transaction boundary — rollback on exception
            try:
                sync_session.rollback()
            except Exception:
                pass  # Rollback best-effort
            return OperationResult.fail(str(e), "RBAC_AUDIT_ERROR")


class PoliciesWorkersHandler:
    """
    Handler for policies.workers operations.

    L2 first-principles purity: Routes all worker DB read/write
    operations through L4 to L6 WorkersReadDriver.
    This eliminates session.execute() from L2 workers.py.

    Methods:
      - verify_run_exists: Verify worker_run exists
      - get_run: Get worker run by ID
      - list_runs: List recent worker runs
      - count_runs: Count worker runs for health check
      - get_active_tenant_budget: Get tenant's active cost budget
      - get_daily_spend: Calculate today's spend
      - get_existing_advisory: Check if advisory exists
      - count_advisories: Count advisories for run
      - get_run_for_retry: Get run from `runs` table
      - insert_retry_run: Insert new retry run
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.workers_read_driver import WorkersReadDriver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if ctx.session is None:
            return OperationResult.fail(
                "Session required for workers operations", "SESSION_REQUIRED"
            )

        driver = WorkersReadDriver(ctx.session)

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)

        try:
            if method_name == "verify_run_exists":
                run_id = kwargs.get("run_id")
                if not run_id:
                    return OperationResult.fail("Missing 'run_id'", "MISSING_PARAM")
                exists = await driver.verify_run_exists(run_id)
                return OperationResult.ok({"exists": exists})

            elif method_name == "get_run":
                run_id = kwargs.get("run_id")
                if not run_id:
                    return OperationResult.fail("Missing 'run_id'", "MISSING_PARAM")
                data = await driver.get_run(run_id)
                return OperationResult.ok(data)

            elif method_name == "list_runs":
                limit = kwargs.get("limit", 20)
                tenant_id = kwargs.get("tenant_id")
                data = await driver.list_runs(limit=limit, tenant_id=tenant_id)
                return OperationResult.ok(data)

            elif method_name == "count_runs":
                count = await driver.count_runs()
                return OperationResult.ok({"count": count})

            elif method_name == "get_active_tenant_budget":
                tenant_id = kwargs.get("tenant_id")
                budget_type = kwargs.get("budget_type", "tenant")
                if not tenant_id:
                    return OperationResult.fail("Missing 'tenant_id'", "MISSING_PARAM")
                data = await driver.get_active_tenant_budget(tenant_id, budget_type)
                return OperationResult.ok(data)

            elif method_name == "get_daily_spend":
                tenant_id = kwargs.get("tenant_id")
                today_start = kwargs.get("today_start")
                if not tenant_id or today_start is None:
                    return OperationResult.fail(
                        "Missing 'tenant_id' or 'today_start'", "MISSING_PARAMS"
                    )
                spend = await driver.get_daily_spend(tenant_id, today_start)
                return OperationResult.ok({"spend_cents": spend})

            elif method_name == "get_existing_advisory":
                run_id = kwargs.get("run_id")
                if not run_id:
                    return OperationResult.fail("Missing 'run_id'", "MISSING_PARAM")
                advisory_id = await driver.get_existing_advisory(run_id)
                return OperationResult.ok({"advisory_id": advisory_id})

            elif method_name == "count_advisories":
                tenant_id = kwargs.get("tenant_id")
                run_id = kwargs.get("run_id")
                if not tenant_id or not run_id:
                    return OperationResult.fail(
                        "Missing 'tenant_id' or 'run_id'", "MISSING_PARAMS"
                    )
                count = await driver.count_advisories(tenant_id, run_id)
                return OperationResult.ok({"count": count})

            elif method_name == "get_run_for_retry":
                run_id = kwargs.get("run_id")
                if not run_id:
                    return OperationResult.fail("Missing 'run_id'", "MISSING_PARAM")
                data = await driver.get_run_for_retry(run_id)
                return OperationResult.ok(data)

            elif method_name == "insert_retry_run":
                required = ["new_run_id", "agent_id", "goal", "parent_run_id",
                           "tenant_id", "created_at"]
                missing = [k for k in required if kwargs.get(k) is None]
                if missing:
                    return OperationResult.fail(
                        f"Missing required params: {missing}", "MISSING_PARAMS"
                    )
                try:
                    await driver.insert_retry_run(
                        new_run_id=kwargs["new_run_id"],
                        agent_id=kwargs["agent_id"],
                        goal=kwargs["goal"],
                        parent_run_id=kwargs["parent_run_id"],
                        tenant_id=kwargs["tenant_id"],
                        max_attempts=kwargs.get("max_attempts"),
                        priority=kwargs.get("priority"),
                        created_at=kwargs["created_at"],
                    )
                    # L4 owns transaction boundary: commit after successful insert
                    await ctx.session.commit()
                    return OperationResult.ok({"inserted": True})
                except Exception as e:
                    # L4 owns transaction boundary: rollback on failure
                    await ctx.session.rollback()
                    return OperationResult.fail(str(e), "INSERT_RETRY_RUN_ERROR")

            return OperationResult.fail(
                f"Unknown workers method: {method_name}", "UNKNOWN_METHOD"
            )
        except Exception as e:
            return OperationResult.fail(str(e), "WORKERS_READ_ERROR")


class PoliciesEnforcementWriteHandler:
    """
    Handler for policies.enforcement_write operations.

    L4 owns transaction boundary for enforcement record writes.
    Creates own session, calls driver, commits.

    Methods:
      - record_enforcement: Record a policy enforcement event (L4 commits)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.db import get_async_session
        from app.hoc.cus.policies.L6_drivers.policy_enforcement_write_driver import (
            PolicyEnforcementWriteDriver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail("Missing 'method' in params", "MISSING_METHOD")

        if method_name == "record_enforcement":
            tenant_id = ctx.params.get("tenant_id")
            rule_id = ctx.params.get("rule_id")
            action_taken = ctx.params.get("action_taken")
            run_id = ctx.params.get("run_id")
            incident_id = ctx.params.get("incident_id")
            details = ctx.params.get("details")

            if not tenant_id or not rule_id or not action_taken:
                return OperationResult.fail(
                    "Missing tenant_id, rule_id, or action_taken", "MISSING_PARAM"
                )

            try:
                async with get_async_session() as session:
                    driver = PolicyEnforcementWriteDriver(session)
                    enforcement_id = await driver.record_enforcement(
                        tenant_id=tenant_id,
                        rule_id=rule_id,
                        action_taken=action_taken,
                        run_id=run_id,
                        incident_id=incident_id,
                        details=details,
                    )
                    # L4 owns transaction boundary
                    await session.commit()
                    return OperationResult.ok({"enforcement_id": enforcement_id})
            except Exception as e:
                return OperationResult.fail(str(e), "ENFORCEMENT_WRITE_ERROR")

        return OperationResult.fail(
            f"Unknown enforcement_write method: {method_name}", "UNKNOWN_METHOD"
        )


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
    # L2 first-principles purity: Recovery read operations
    registry.register("policies.recovery.read", PoliciesRecoveryReadHandler())
    # L2 first-principles purity: Guard domain read operations
    registry.register("policies.guard_read", PoliciesGuardReadHandler())
    # L2 first-principles purity: Sync guard read operations (for guard.py migration)
    registry.register("policies.sync_guard_read", PoliciesSyncGuardReadHandler())
    # Customer visibility operations (outcome reconciliation)
    registry.register("policies.customer_visibility", PoliciesCustomerVisibilityHandler())
    # Replay UX read operations (H1)
    registry.register("policies.replay", PoliciesReplayHandler())
    # Workers domain read operations (L2 purity for workers.py)
    registry.register("policies.workers", PoliciesWorkersHandler())
    # Approval workflow operations (Goal B: eliminate session.execute from policy.py)
    from app.hoc.cus.hoc_spine.orchestrator.handlers.policy_approval_handler import (
        PolicyApprovalHandler,
    )
    registry.register("policies.approval", PolicyApprovalHandler())
    # RBAC audit operations (L2 purity for rbac_api.py)
    registry.register("rbac.audit", RbacAuditHandler())
    # Enforcement write operations (L4 owns commit for L6 driver purity)
    registry.register("policies.enforcement_write", PoliciesEnforcementWriteHandler())
