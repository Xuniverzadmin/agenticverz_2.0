# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | test-runner
#   Execution: sync
# Role: Safety regression tests for PIN-332 Invocation Safety Closure
# Callers: CI, pytest
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-332

"""
Invocation Safety Regression Tests - PIN-332

Tests for CLI and SDK safety boundary enforcement.

Coverage:
- Identity checks (ID-001 to ID-003)
- Ownership checks (OWN-001 to OWN-003)
- Input trust checks (INPUT-001 to INPUT-003)
- Integrity checks (INT-001 to INT-003)
- Rate limit checks (RATE-001 to RATE-003)
- Metrics and audit emission
"""

from app.auth.invocation_safety import (
    CLISafetyHook,
    InvocationSafetyContext,
    InvocationSafetyResult,
    SafetyCheckResult,
    SafetyCheckTimer,
    SafetyFlag,
    SDKSafetyHook,
    Severity,
    check_agent_ownership,
    check_budget_validation,
    check_idempotency_key,
    check_identity_resolved,
    check_impersonation_declared,
    check_impersonation_reason,
    check_plan_immutability,
    check_plan_injection,
    check_rate_limit,
    check_run_ownership,
    check_tenant_scoping,
    check_trace_hash_completeness,
    compute_plan_hash,
    emit_safety_audit_event,
    emit_safety_metrics,
    run_safety_checks,
)

# =============================================================================
# IDENTITY CHECKS (ID-001 to ID-003)
# =============================================================================


class TestIdentityChecks:
    """Tests for identity-related safety checks."""

    def test_id_001_identity_resolved_with_caller(self):
        """ID-001: Caller identity must be resolved - PASS case."""
        ctx = InvocationSafetyContext(caller_id="user_123")
        result = check_identity_resolved(ctx)
        assert result.passed is True
        assert result.flag is None

    def test_id_001_identity_unresolved(self):
        """ID-001: Caller identity must be resolved - FAIL case."""
        ctx = InvocationSafetyContext(caller_id=None)
        result = check_identity_resolved(ctx)
        assert result.passed is False
        assert result.flag == SafetyFlag.IDENTITY_UNRESOLVED
        assert result.severity == Severity.WARNING
        assert "identity" in result.message.lower()

    def test_id_002_impersonation_declared_no_impersonation(self):
        """ID-002: Impersonation must be declared - no impersonation case."""
        ctx = InvocationSafetyContext(caller_id="user_123")
        result = check_impersonation_declared(ctx)
        assert result.passed is True

    def test_id_002_impersonation_declared_with_reason(self):
        """ID-002: Impersonation must be declared - proper declaration."""
        ctx = InvocationSafetyContext(
            caller_id="admin_1",
            impersonated_subject="user_456",
            impersonation_reason="Customer support request",
        )
        result = check_impersonation_declared(ctx)
        assert result.passed is True

    def test_id_002_impersonation_without_declaration(self):
        """ID-002: Impersonation must be declared - missing declaration."""
        ctx = InvocationSafetyContext(
            caller_id="admin_1",
            impersonated_subject="user_456",
            impersonation_reason=None,  # Missing
        )
        result = check_impersonation_declared(ctx)
        assert result.passed is False
        assert result.flag == SafetyFlag.IMPERSONATION_MISSING

    def test_id_003_impersonation_reason_provided(self):
        """ID-003: Impersonation must have reason code - PASS case."""
        ctx = InvocationSafetyContext(
            impersonated_subject="user_456",
            impersonation_reason="debugging_issue_12345",
        )
        result = check_impersonation_reason(ctx)
        assert result.passed is True

    def test_id_003_impersonation_reason_missing(self):
        """ID-003: Impersonation must have reason code - FAIL case."""
        ctx = InvocationSafetyContext(
            impersonated_subject="user_456",
            impersonation_reason=None,
        )
        result = check_impersonation_reason(ctx)
        assert result.passed is False
        assert result.flag == SafetyFlag.IMPERSONATION_REASON_MISSING


# =============================================================================
# OWNERSHIP CHECKS (OWN-001 to OWN-003)
# =============================================================================


class TestOwnershipChecks:
    """Tests for ownership-related safety checks."""

    def test_own_001_agent_same_tenant(self):
        """OWN-001: Agent must belong to caller's tenant - same tenant."""
        ctx = InvocationSafetyContext(
            agent_id="agent_123",
            tenant_id="tenant_A",
        )
        result = check_agent_ownership(ctx, agent_tenant_id="tenant_A")
        assert result.passed is True

    def test_own_001_agent_different_tenant(self):
        """OWN-001: Agent must belong to caller's tenant - cross-tenant."""
        ctx = InvocationSafetyContext(
            agent_id="agent_123",
            tenant_id="tenant_A",
        )
        result = check_agent_ownership(ctx, agent_tenant_id="tenant_B")
        assert result.passed is False
        assert result.flag == SafetyFlag.OWNERSHIP_VIOLATION
        assert "tenant" in result.message.lower()

    def test_own_002_run_same_tenant(self):
        """OWN-002: Run must belong to caller's tenant - same tenant."""
        ctx = InvocationSafetyContext(
            run_id="run_456",
            tenant_id="tenant_A",
        )
        result = check_run_ownership(ctx, run_tenant_id="tenant_A")
        assert result.passed is True

    def test_own_002_run_different_tenant(self):
        """OWN-002: Run must belong to caller's tenant - cross-tenant."""
        ctx = InvocationSafetyContext(
            run_id="run_456",
            tenant_id="tenant_A",
        )
        result = check_run_ownership(ctx, run_tenant_id="tenant_B")
        assert result.passed is False
        assert result.flag == SafetyFlag.OWNERSHIP_VIOLATION

    def test_own_003_tenant_scoping_present(self):
        """OWN-003: Query results must be tenant-scoped - tenant present."""
        ctx = InvocationSafetyContext(tenant_id="tenant_A")
        result = check_tenant_scoping(ctx)
        assert result.passed is True

    def test_own_003_tenant_scoping_missing(self):
        """OWN-003: Query results must be tenant-scoped - tenant missing."""
        ctx = InvocationSafetyContext(tenant_id=None)
        result = check_tenant_scoping(ctx)
        assert result.passed is False
        assert result.flag == SafetyFlag.TENANT_SCOPE_MISSING


# =============================================================================
# INPUT TRUST CHECKS (INPUT-001 to INPUT-003)
# =============================================================================


class TestInputTrustChecks:
    """Tests for input trust safety checks."""

    def test_input_001_budget_within_limit(self):
        """INPUT-001: Client budget within tenant limit."""
        ctx = InvocationSafetyContext(
            budget_cents=5000,
            tenant_budget_limit=10000,
        )
        result = check_budget_validation(ctx)
        assert result.passed is True
        assert result.flag is None

    def test_input_001_budget_exceeds_limit(self):
        """INPUT-001: Client budget exceeds limit - override applied."""
        ctx = InvocationSafetyContext(
            budget_cents=15000,
            tenant_budget_limit=10000,
        )
        result = check_budget_validation(ctx)
        # Passes but with INFO flag (override applied, not blocked)
        assert result.passed is True
        assert result.flag == SafetyFlag.BUDGET_OVERRIDE_APPLIED
        assert result.action_taken == "budget_overridden"
        assert result.severity == Severity.INFO

    def test_input_002_plan_immutable(self):
        """INPUT-002: Plan must be immutable - no mutation."""
        plan = {"steps": [{"skill": "search"}]}
        ctx = InvocationSafetyContext(plan_hash=compute_plan_hash(plan))
        result = check_plan_immutability(ctx, current_plan=plan)
        assert result.passed is True

    def test_input_002_plan_mutated(self):
        """INPUT-002: Plan must be immutable - mutation detected."""
        original_plan = {"steps": [{"skill": "search"}]}
        mutated_plan = {"steps": [{"skill": "search"}, {"skill": "execute"}]}
        ctx = InvocationSafetyContext(plan_hash=compute_plan_hash(original_plan))
        result = check_plan_immutability(ctx, current_plan=mutated_plan)
        assert result.passed is False
        assert result.flag == SafetyFlag.PLAN_MUTATION_ATTEMPT

    def test_input_003_plan_no_injection_clean(self):
        """INPUT-003: Plan cannot override security fields - clean plan."""
        plan = {"steps": [{"skill": "search", "params": {"query": "test"}}]}
        result = check_plan_injection(plan)
        assert result.passed is True

    def test_input_003_plan_injection_tenant_id(self):
        """INPUT-003: Plan cannot override security fields - tenant_id injection."""
        plan = {"steps": [], "tenant_id": "evil_tenant"}
        result = check_plan_injection(plan)
        assert result.passed is False
        assert result.flag == SafetyFlag.PLAN_INJECTION_BLOCKED
        assert result.severity == Severity.ERROR  # This one blocks
        assert result.should_block is True

    def test_input_003_plan_injection_caller_id(self):
        """INPUT-003: Plan cannot override security fields - caller_id injection."""
        plan = {"steps": [], "caller_id": "admin_impersonation"}
        result = check_plan_injection(plan)
        assert result.passed is False
        assert result.flag == SafetyFlag.PLAN_INJECTION_BLOCKED
        assert result.should_block is True

    def test_input_003_plan_injection_owner_id(self):
        """INPUT-003: Plan cannot override security fields - owner_id injection."""
        plan = {"steps": [], "owner_id": "hijacked_owner"}
        result = check_plan_injection(plan)
        assert result.passed is False
        assert result.flag == SafetyFlag.PLAN_INJECTION_BLOCKED

    def test_input_003_plan_injection_admin(self):
        """INPUT-003: Plan cannot override security fields - admin injection."""
        plan = {"steps": [], "admin": True}
        result = check_plan_injection(plan)
        assert result.passed is False
        assert result.flag == SafetyFlag.PLAN_INJECTION_BLOCKED


# =============================================================================
# INTEGRITY CHECKS (INT-001 to INT-003)
# =============================================================================


class TestIntegrityChecks:
    """Tests for integrity-related safety checks."""

    def test_int_001_trace_hash_complete(self):
        """INT-001: Trace hash includes all required fields."""
        required = ["timestamp", "step_id", "caller_id", "outcome"]
        actual = ["timestamp", "step_id", "caller_id", "outcome", "skill_id"]
        result = check_trace_hash_completeness("hash123", required, actual)
        assert result.passed is True

    def test_int_001_trace_hash_missing_fields(self):
        """INT-001: Trace hash missing audit-critical fields."""
        required = ["timestamp", "step_id", "caller_id", "outcome"]
        actual = ["timestamp", "step_id"]  # Missing caller_id, outcome
        result = check_trace_hash_completeness("hash123", required, actual)
        assert result.passed is False
        assert result.flag == SafetyFlag.INTEGRITY_MISMATCH
        assert "caller_id" in result.message or "outcome" in result.message

    def test_int_003_idempotency_key_tenant_scoped(self):
        """INT-003: Idempotency key is tenant-scoped."""
        key = "tenant_A:run_123:step_0:skill_search:abc123"
        result = check_idempotency_key(key, tenant_id="tenant_A")
        assert result.passed is True

    def test_int_003_idempotency_key_not_tenant_scoped(self):
        """INT-003: Idempotency key is NOT tenant-scoped."""
        key = "run_123:step_0:skill_search:abc123"  # Missing tenant prefix
        result = check_idempotency_key(key, tenant_id="tenant_A")
        assert result.passed is False
        assert result.flag == SafetyFlag.IDEMPOTENCY_COLLISION_RISK


# =============================================================================
# RATE LIMIT CHECKS (RATE-001 to RATE-003)
# =============================================================================


class TestRateLimitChecks:
    """Tests for rate limit safety checks."""

    def test_rate_within_limit(self):
        """Rate count within limit."""
        ctx = InvocationSafetyContext(rate_count=30)
        result = check_rate_limit(ctx, limit=60)
        assert result.passed is True

    def test_rate_exceeds_limit(self):
        """Rate count exceeds limit."""
        ctx = InvocationSafetyContext(rate_count=100)
        result = check_rate_limit(ctx, limit=60)
        assert result.passed is False
        assert result.flag == SafetyFlag.RATE_THRESHOLD_EXCEEDED
        assert "100" in result.message
        assert "60" in result.message


# =============================================================================
# SAFETY CHECK AGGREGATOR
# =============================================================================


class TestSafetyCheckAggregator:
    """Tests for run_safety_checks aggregator."""

    def test_all_checks_pass(self):
        """All checks pass - result is passed."""
        ctx = InvocationSafetyContext(caller_id="user_123", tenant_id="tenant_A")
        checks = [
            lambda: SafetyCheckResult(passed=True),
            lambda: SafetyCheckResult(passed=True),
        ]
        result = run_safety_checks(ctx, checks)
        assert result.passed is True
        assert result.blocked is False
        assert len(result.flags) == 0

    def test_warning_check_fails(self):
        """Warning-level check fails - result passes but has flags."""
        ctx = InvocationSafetyContext()
        checks = [
            lambda: SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.IDENTITY_UNRESOLVED,
                severity=Severity.WARNING,
                message="Identity unresolved",
            ),
        ]
        result = run_safety_checks(ctx, checks)
        assert result.passed is True  # Warning doesn't block
        assert result.blocked is False
        assert SafetyFlag.IDENTITY_UNRESOLVED in result.flags
        assert "Identity unresolved" in result.warnings

    def test_error_check_fails_blocks(self):
        """Error-level check fails - result is blocked."""
        ctx = InvocationSafetyContext()
        checks = [
            lambda: SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.PLAN_INJECTION_BLOCKED,
                severity=Severity.ERROR,
                message="Plan injection detected",
            ),
        ]
        result = run_safety_checks(ctx, checks)
        assert result.passed is False
        assert result.blocked is True
        assert result.block_reason == "Plan injection detected"

    def test_info_flags_collected(self):
        """Info-level flags are collected even on pass."""
        ctx = InvocationSafetyContext()
        checks = [
            lambda: SafetyCheckResult(
                passed=True,
                flag=SafetyFlag.BUDGET_OVERRIDE_APPLIED,
                severity=Severity.INFO,
                message="Budget was overridden",
            ),
        ]
        result = run_safety_checks(ctx, checks)
        assert result.passed is True
        assert SafetyFlag.BUDGET_OVERRIDE_APPLIED in result.flags

    def test_exception_handling(self):
        """Check exceptions are caught and logged."""
        ctx = InvocationSafetyContext()

        def failing_check():
            raise ValueError("Unexpected error")

        checks = [failing_check]
        result = run_safety_checks(ctx, checks)
        # Should not crash, should log warning
        assert result.passed is True
        assert "error" in result.warnings[0].lower()


# =============================================================================
# CLI SAFETY HOOK
# =============================================================================


class TestCLISafetyHook:
    """Tests for CLI safety hook."""

    def test_check_simulate_clean(self):
        """CLI simulate check - clean plan."""
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="user_123",
            tenant_id="tenant_A",
            tenant_budget_limit=10000,
        )
        result = hook.check_simulate(ctx, plan_data={"steps": []}, budget_cents=5000)
        assert result.blocked is False

    def test_check_simulate_plan_injection(self):
        """CLI simulate check - plan injection blocked."""
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="user_123",
            tenant_id="tenant_A",
        )
        result = hook.check_simulate(ctx, plan_data={"steps": [], "tenant_id": "evil"}, budget_cents=1000)
        assert result.blocked is True
        assert SafetyFlag.PLAN_INJECTION_BLOCKED in result.flags

    def test_check_query_clean(self):
        """CLI query check - valid query."""
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="user_123",
            tenant_id="tenant_A",
        )
        result = hook.check_query(ctx, query_type="runs")
        assert result.blocked is False

    def test_check_query_missing_tenant(self):
        """CLI query check - missing tenant scope."""
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="user_123",
            tenant_id=None,  # Missing
        )
        result = hook.check_query(ctx, query_type="runs")
        assert result.blocked is False  # Warning only
        assert SafetyFlag.TENANT_SCOPE_MISSING in result.flags

    def test_check_quickstart_diagnostic(self):
        """CLI quickstart is diagnostic-only."""
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext()
        result = hook.check_quickstart(ctx)
        assert result.blocked is False
        assert SafetyFlag.DIAGNOSTIC_INVOCATION in result.flags

    def test_rate_limiting_tracked(self):
        """CLI rate limiting is tracked per tenant/operation."""
        import time

        hook = CLISafetyHook()

        # First call should pass
        ctx1 = InvocationSafetyContext(caller_id="user_123", tenant_id="tenant_A")
        result1 = hook.check_query(ctx1, query_type="runs")
        assert result1.blocked is False

        # Simulate many calls (manually set rate count high with recent window start)
        hook._rate_counts["tenant_A:query"] = (200, time.time())  # 200 calls in current window
        ctx2 = InvocationSafetyContext(caller_id="user_123", tenant_id="tenant_A")
        result2 = hook.check_query(ctx2, query_type="runs")
        # Rate limit exceeded flag should be present
        assert SafetyFlag.RATE_THRESHOLD_EXCEEDED in result2.flags


# =============================================================================
# SDK SAFETY HOOK
# =============================================================================


class TestSDKSafetyHook:
    """Tests for SDK safety hook."""

    def test_check_simulate_clean(self):
        """SDK simulate check - clean plan."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            tenant_budget_limit=10000,
        )
        result = hook.check_simulate(ctx, plan_data={"steps": []}, budget_cents=5000)
        assert result.blocked is False

    def test_check_simulate_budget_override(self):
        """SDK simulate check - budget override applied."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            tenant_budget_limit=10000,
        )
        result = hook.check_simulate(ctx, plan_data={"steps": []}, budget_cents=20000)
        assert result.blocked is False
        assert SafetyFlag.BUDGET_OVERRIDE_APPLIED in result.flags

    def test_check_create_run_clean(self):
        """SDK create_run check - clean plan."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(caller_id="service_123")
        result = hook.check_create_run(ctx, plan_data={"steps": []})
        assert result.blocked is False

    def test_check_create_run_injection(self):
        """SDK create_run check - plan injection blocked."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(caller_id="service_123")
        result = hook.check_create_run(ctx, plan_data={"caller_id": "hacked"})
        assert result.blocked is True
        assert SafetyFlag.PLAN_INJECTION_BLOCKED in result.flags

    def test_check_poll_run_ownership(self):
        """SDK poll_run check - ownership violation."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            run_id="run_456",
        )
        result = hook.check_poll_run(ctx, run_tenant_id="tenant_B")
        assert result.blocked is False  # Warning only
        assert SafetyFlag.OWNERSHIP_VIOLATION in result.flags

    def test_check_recall_ownership(self):
        """SDK recall check - ownership violation."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            agent_id="agent_789",
        )
        result = hook.check_recall(ctx, agent_tenant_id="tenant_B")
        assert result.blocked is False  # Warning only
        assert SafetyFlag.OWNERSHIP_VIOLATION in result.flags

    def test_check_post_goal_force_skill(self):
        """SDK post_goal check - force_skill triggers impersonation warning."""
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(caller_id="service_123")
        result = hook.check_post_goal(ctx, force_skill="search")
        # force_skill without reason triggers impersonation warning
        assert SafetyFlag.IMPERSONATION_MISSING in result.flags

    def test_poll_rate_limiting(self):
        """SDK poll_run rate limiting is enforced."""
        import time

        hook = SDKSafetyHook()

        # Simulate high rate count with recent window start
        hook._rate_counts["tenant_A:poll"] = (100, time.time())

        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            run_id="run_456",
        )
        result = hook.check_poll_run(ctx, run_tenant_id="tenant_A")
        assert SafetyFlag.RATE_THRESHOLD_EXCEEDED in result.flags


# =============================================================================
# METRICS AND AUDIT
# =============================================================================


class TestMetricsAndAudit:
    """Tests for metrics and audit functions."""

    def test_emit_safety_metrics_no_crash(self):
        """emit_safety_metrics does not crash."""
        result = InvocationSafetyResult(
            passed=True,
            flags=[SafetyFlag.BUDGET_OVERRIDE_APPLIED],
            warnings=["Budget overridden"],
            blocked=False,
        )
        # Should not raise
        emit_safety_metrics("CAP-020", "simulate", result, duration_seconds=0.01)

    def test_emit_safety_metrics_blocked(self):
        """emit_safety_metrics handles blocked results."""
        result = InvocationSafetyResult(
            passed=False,
            flags=[SafetyFlag.PLAN_INJECTION_BLOCKED],
            warnings=["Plan injection detected"],
            blocked=True,
            block_reason="Plan injection detected",
        )
        # Should not raise
        emit_safety_metrics("CAP-021", "create_run", result, duration_seconds=0.005)

    def test_emit_safety_audit_event_no_crash(self):
        """emit_safety_audit_event does not crash."""
        result = InvocationSafetyResult(
            passed=False,
            flags=[SafetyFlag.OWNERSHIP_VIOLATION],
            warnings=["Cross-tenant access"],
            blocked=False,
        )
        # Should not raise
        emit_safety_audit_event(
            capability="CAP-021",
            operation="poll_run",
            tenant_id="tenant_A",
            caller_id="service_123",
            result=result,
            context={"run_id": "run_456"},
        )

    def test_safety_check_timer(self):
        """SafetyCheckTimer measures duration."""
        import time

        with SafetyCheckTimer("CAP-020", "simulate") as timer:
            time.sleep(0.01)  # 10ms

        assert timer.duration > 0.005  # At least 5ms
        assert timer.duration < 0.5  # Less than 500ms

        # emit should not crash
        result = InvocationSafetyResult(passed=True, flags=[], warnings=[], blocked=False)
        timer.emit(result)


# =============================================================================
# PLAN HASH COMPUTATION
# =============================================================================


class TestPlanHashComputation:
    """Tests for deterministic plan hash computation."""

    def test_plan_hash_deterministic(self):
        """Plan hash is deterministic for same input."""
        plan = {"steps": [{"skill": "search", "params": {"query": "test"}}]}
        hash1 = compute_plan_hash(plan)
        hash2 = compute_plan_hash(plan)
        assert hash1 == hash2

    def test_plan_hash_different_plans(self):
        """Different plans produce different hashes."""
        plan1 = {"steps": [{"skill": "search"}]}
        plan2 = {"steps": [{"skill": "execute"}]}
        hash1 = compute_plan_hash(plan1)
        hash2 = compute_plan_hash(plan2)
        assert hash1 != hash2

    def test_plan_hash_key_order_independent(self):
        """Plan hash is independent of key order."""
        plan1 = {"a": 1, "b": 2}
        plan2 = {"b": 2, "a": 1}
        hash1 = compute_plan_hash(plan1)
        hash2 = compute_plan_hash(plan2)
        assert hash1 == hash2

    def test_plan_hash_none_handling(self):
        """Plan hash handles None gracefully."""
        hash1 = compute_plan_hash(None)
        hash2 = compute_plan_hash(None)
        # None returns empty string (fast path)
        assert hash1 == ""
        assert hash1 == hash2
        # Empty dict produces a real hash
        hash3 = compute_plan_hash({})
        assert hash3 != ""  # Computed hash


# =============================================================================
# INVOCATION SAFETY RESULT TO ENVELOPE
# =============================================================================


class TestInvocationSafetyResultToEnvelope:
    """Tests for converting result to envelope extension."""

    def test_to_envelope_extension_passed(self):
        """Convert passed result to envelope extension."""
        result = InvocationSafetyResult(
            passed=True,
            flags=[SafetyFlag.BUDGET_OVERRIDE_APPLIED],
            warnings=["Budget was overridden"],
            blocked=False,
        )
        ext = result.to_envelope_extension()
        assert ext["invocation_safety"]["checked"] is True
        assert ext["invocation_safety"]["passed"] is True
        assert ext["invocation_safety"]["blocked"] is False
        assert "budget_override_applied" in ext["invocation_safety"]["flags"]

    def test_to_envelope_extension_blocked(self):
        """Convert blocked result to envelope extension."""
        result = InvocationSafetyResult(
            passed=False,
            flags=[SafetyFlag.PLAN_INJECTION_BLOCKED],
            warnings=["Injection attempt"],
            blocked=True,
            block_reason="tenant_id injection",
        )
        ext = result.to_envelope_extension()
        assert ext["invocation_safety"]["checked"] is True
        assert ext["invocation_safety"]["passed"] is False
        assert ext["invocation_safety"]["blocked"] is True
        assert ext["invocation_safety"]["block_reason"] == "tenant_id injection"


# =============================================================================
# REGRESSION: SPECIFIC SCENARIOS
# =============================================================================


class TestRegressionScenarios:
    """Regression tests for specific safety scenarios."""

    def test_regression_cross_tenant_run_access(self):
        """
        Regression: Cross-tenant run access must be flagged.

        Scenario: Service A (tenant_A) tries to poll a run from tenant_B.
        Expected: OWNERSHIP_VIOLATION flag, not blocked (v1: OBSERVE_WARN).
        """
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_A",
            tenant_id="tenant_A",
            run_id="run_from_tenant_B",
        )
        result = hook.check_poll_run(ctx, run_tenant_id="tenant_B")

        assert result.blocked is False, "v1 should not block, only warn"
        assert SafetyFlag.OWNERSHIP_VIOLATION in result.flags

    def test_regression_plan_injection_always_blocks(self):
        """
        Regression: Plan injection MUST always block.

        Scenario: Plan contains tenant_id override attempt.
        Expected: Blocked with ERROR severity.
        """
        hook = CLISafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="user_123",
            tenant_id="tenant_A",
        )
        result = hook.check_simulate(
            ctx,
            plan_data={"tenant_id": "tenant_B"},
            budget_cents=1000,
        )

        assert result.blocked is True, "Plan injection must always block"
        assert SafetyFlag.PLAN_INJECTION_BLOCKED in result.flags

    def test_regression_budget_never_exceeds_tenant_limit(self):
        """
        Regression: Budget must never exceed tenant limit.

        Scenario: Client requests 50000 cents, tenant limit is 10000.
        Expected: BUDGET_OVERRIDE_APPLIED flag, effective budget capped.
        """
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            tenant_budget_limit=10000,
        )
        result = hook.check_simulate(
            ctx,
            plan_data={"steps": []},
            budget_cents=50000,
        )

        assert result.blocked is False
        assert SafetyFlag.BUDGET_OVERRIDE_APPLIED in result.flags

    def test_regression_polling_rate_limit_enforced(self):
        """
        Regression: Polling rate limit must be enforced.

        Scenario: 100 poll calls in 60 seconds, limit is 60.
        Expected: RATE_THRESHOLD_EXCEEDED flag.
        """
        import time

        hook = SDKSafetyHook()

        # Simulate 100 calls already made in current window
        hook._rate_counts["tenant_A:poll"] = (100, time.time())

        ctx = InvocationSafetyContext(
            caller_id="service_123",
            tenant_id="tenant_A",
            run_id="run_456",
        )
        result = hook.check_poll_run(ctx, run_tenant_id="tenant_A")

        assert SafetyFlag.RATE_THRESHOLD_EXCEEDED in result.flags

    def test_regression_identity_required_for_all_operations(self):
        """
        Regression: Identity must be resolved for all operations.

        Scenario: SDK call without caller_id.
        Expected: IDENTITY_UNRESOLVED flag.
        """
        hook = SDKSafetyHook()
        ctx = InvocationSafetyContext(
            caller_id=None,  # Missing identity
            tenant_id="tenant_A",
        )
        result = hook.check_create_run(ctx, plan_data={"steps": []})

        assert SafetyFlag.IDENTITY_UNRESOLVED in result.flags
