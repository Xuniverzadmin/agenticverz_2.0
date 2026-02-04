# Layer: L5 — Domain Engine
# Product: system-wide
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: api | cli | sdk
#   Execution: sync
# Role: Invocation Safety Layer for CAP-020 (CLI) and CAP-021 (SDK)
# Callers: CLI dispatcher, SDK wrappers
# Reference: PIN-332, PIN-522


"""
Invocation Safety Layer - PIN-332 Invocation Safety Closure

Provides safety validation for CLI and SDK invocations at the capability boundary.
Does NOT change core execution logic or authority declarations.

ENFORCEMENT MODE: OBSERVE_WARN (v1)
- Log safety check failures
- Add flags to execution envelope
- Emit metrics
- No hard blocks except plan injection

CONSTRAINTS:
- Does NOT change authority (PIN-331)
- Does NOT add RBAC per command/method
- Does NOT touch L2 core logic
- Lives ONLY at invocation boundary
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# SAFETY FLAG DEFINITIONS
# =============================================================================


class SafetyFlag(Enum):
    """Safety flags added to execution envelope on check failures."""

    # Identity
    IDENTITY_UNRESOLVED = "identity_unresolved"
    IMPERSONATION_MISSING = "impersonation_missing"
    IMPERSONATION_REASON_MISSING = "impersonation_reason_missing"

    # Ownership
    OWNERSHIP_VIOLATION = "ownership_violation"
    TENANT_SCOPE_MISSING = "tenant_scope_missing"

    # Input Trust
    BUDGET_OVERRIDE_APPLIED = "budget_override_applied"
    PLAN_MUTATION_ATTEMPT = "plan_mutation_attempt"
    PLAN_INJECTION_BLOCKED = "plan_injection_blocked"

    # Integrity
    INTEGRITY_MISMATCH = "integrity_mismatch"
    IDEMPOTENCY_COLLISION_RISK = "idempotency_collision_risk"

    # Rate
    RATE_THRESHOLD_EXCEEDED = "rate_threshold_exceeded"

    # Diagnostic
    DIAGNOSTIC_INVOCATION = "diagnostic_invocation"


class Severity(Enum):
    """Severity levels for safety flags."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# =============================================================================
# SAFETY CHECK RESULT
# =============================================================================


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""

    passed: bool
    flag: Optional[SafetyFlag] = None
    severity: Severity = Severity.WARNING
    message: str = ""
    action_taken: Optional[str] = None  # e.g., "budget_overridden"

    @property
    def should_block(self) -> bool:
        """Only ERROR severity blocks execution (v1: only plan injection)."""
        return not self.passed and self.severity == Severity.ERROR


@dataclass
class InvocationSafetyContext:
    """Context for invocation safety checks."""

    # Caller identity
    caller_id: Optional[str] = None
    tenant_id: Optional[str] = None
    impersonated_subject: Optional[str] = None
    impersonation_reason: Optional[str] = None

    # Target resources
    agent_id: Optional[str] = None
    run_id: Optional[str] = None

    # Input data
    plan_data: Optional[dict] = None
    budget_cents: Optional[int] = None
    tenant_budget_limit: int = 10000  # Default tenant limit

    # Rate tracking
    operation_type: str = ""
    rate_count: int = 0
    rate_window_seconds: int = 60

    # Computed hashes
    plan_hash: Optional[str] = None

    # Collected flags
    safety_flags: list[SafetyFlag] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Diagnostic mode
    is_diagnostic: bool = False


# =============================================================================
# SAFETY CHECKS
# =============================================================================


def check_identity_resolved(ctx: InvocationSafetyContext) -> SafetyCheckResult:
    """ID-001: Caller identity must be resolved."""
    if not ctx.caller_id:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.IDENTITY_UNRESOLVED,
            severity=Severity.WARNING,
            message="Caller identity could not be resolved",
        )
    return SafetyCheckResult(passed=True)


def check_impersonation_declared(ctx: InvocationSafetyContext) -> SafetyCheckResult:
    """ID-002: Impersonation must be explicitly declared."""
    if ctx.impersonated_subject and not ctx.impersonation_reason:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.IMPERSONATION_MISSING,
            severity=Severity.WARNING,
            message=f"Impersonation of '{ctx.impersonated_subject}' without declaration",
        )
    return SafetyCheckResult(passed=True)


def check_impersonation_reason(ctx: InvocationSafetyContext) -> SafetyCheckResult:
    """ID-003: Impersonation must have reason code."""
    if ctx.impersonated_subject and not ctx.impersonation_reason:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.IMPERSONATION_REASON_MISSING,
            severity=Severity.WARNING,
            message="Impersonation declared but reason not provided",
        )
    return SafetyCheckResult(passed=True)


def check_agent_ownership(
    ctx: InvocationSafetyContext,
    agent_tenant_id: Optional[str] = None,
) -> SafetyCheckResult:
    """OWN-001: Agent must belong to caller's tenant."""
    if ctx.agent_id and agent_tenant_id and ctx.tenant_id:
        if agent_tenant_id != ctx.tenant_id:
            return SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.OWNERSHIP_VIOLATION,
                severity=Severity.WARNING,
                message=f"Agent {ctx.agent_id} belongs to tenant {agent_tenant_id}, not {ctx.tenant_id}",
            )
    return SafetyCheckResult(passed=True)


def check_run_ownership(
    ctx: InvocationSafetyContext,
    run_tenant_id: Optional[str] = None,
) -> SafetyCheckResult:
    """OWN-002: Run must belong to caller's tenant."""
    if ctx.run_id and run_tenant_id and ctx.tenant_id:
        if run_tenant_id != ctx.tenant_id:
            return SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.OWNERSHIP_VIOLATION,
                severity=Severity.WARNING,
                message=f"Run {ctx.run_id} belongs to tenant {run_tenant_id}, not {ctx.tenant_id}",
            )
    return SafetyCheckResult(passed=True)


def check_tenant_scoping(ctx: InvocationSafetyContext) -> SafetyCheckResult:
    """OWN-003: Query results must be tenant-scoped."""
    if not ctx.tenant_id:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.TENANT_SCOPE_MISSING,
            severity=Severity.WARNING,
            message="Query not properly tenant-scoped",
        )
    return SafetyCheckResult(passed=True)


def check_budget_validation(ctx: InvocationSafetyContext) -> SafetyCheckResult:
    """INPUT-001: Client budget must not exceed tenant limits."""
    if ctx.budget_cents and ctx.budget_cents > ctx.tenant_budget_limit:
        return SafetyCheckResult(
            passed=True,  # We override, not block
            flag=SafetyFlag.BUDGET_OVERRIDE_APPLIED,
            severity=Severity.INFO,
            message=f"Budget {ctx.budget_cents} exceeds limit {ctx.tenant_budget_limit}, using limit",
            action_taken="budget_overridden",
        )
    return SafetyCheckResult(passed=True)


def compute_plan_hash(plan_data: Any) -> str:
    """Compute deterministic hash of plan data."""
    if plan_data is None:
        return ""
    canonical = json.dumps(plan_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def check_plan_immutability(
    ctx: InvocationSafetyContext,
    current_plan: Optional[dict] = None,
) -> SafetyCheckResult:
    """INPUT-002: Plan must be immutable after hash computation."""
    if ctx.plan_hash and current_plan:
        current_hash = compute_plan_hash(current_plan)
        if current_hash != ctx.plan_hash:
            return SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.PLAN_MUTATION_ATTEMPT,
                severity=Severity.WARNING,
                message="Plan was modified after initial hash computation",
            )
    return SafetyCheckResult(passed=True)


def check_plan_injection(plan_data: Optional[dict]) -> SafetyCheckResult:
    """INPUT-003: Plan cannot override security-critical fields."""
    if plan_data:
        # Check for injection of security-critical fields
        forbidden_fields = ["tenant_id", "caller_id", "owner_id", "admin"]
        for field_name in forbidden_fields:
            if field_name in plan_data:
                return SafetyCheckResult(
                    passed=False,
                    flag=SafetyFlag.PLAN_INJECTION_BLOCKED,
                    severity=Severity.ERROR,  # This one blocks
                    message=f"Plan contains forbidden field: {field_name}",
                )
    return SafetyCheckResult(passed=True)


def check_trace_hash_completeness(
    trace_hash: Optional[str],
    required_fields: list[str],
    actual_fields: list[str],
) -> SafetyCheckResult:
    """INT-001: Trace hash must include all audit-critical fields."""
    missing = set(required_fields) - set(actual_fields)
    if missing:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.INTEGRITY_MISMATCH,
            severity=Severity.WARNING,
            message=f"Trace hash missing fields: {missing}",
        )
    return SafetyCheckResult(passed=True)


def check_idempotency_key(
    idempotency_key: Optional[str],
    tenant_id: Optional[str],
) -> SafetyCheckResult:
    """INT-003: Idempotency keys must be tenant-scoped."""
    if idempotency_key and tenant_id:
        if not idempotency_key.startswith(f"{tenant_id}:"):
            return SafetyCheckResult(
                passed=False,
                flag=SafetyFlag.IDEMPOTENCY_COLLISION_RISK,
                severity=Severity.WARNING,
                message=f"Idempotency key not tenant-scoped: {idempotency_key[:20]}...",
            )
    return SafetyCheckResult(passed=True)


def check_rate_limit(
    ctx: InvocationSafetyContext,
    limit: int = 60,
) -> SafetyCheckResult:
    """RATE-001/002/003: Operation must respect rate limits."""
    if ctx.rate_count > limit:
        return SafetyCheckResult(
            passed=False,
            flag=SafetyFlag.RATE_THRESHOLD_EXCEEDED,
            severity=Severity.WARNING,
            message=f"Rate limit exceeded: {ctx.rate_count}/{limit} per {ctx.rate_window_seconds}s",
        )
    return SafetyCheckResult(passed=True)


# =============================================================================
# SAFETY CHECK AGGREGATOR
# =============================================================================


@dataclass
class InvocationSafetyResult:
    """Aggregated result of all safety checks."""

    passed: bool  # True if no ERROR severity checks failed
    flags: list[SafetyFlag]
    warnings: list[str]
    blocked: bool  # True if execution should be blocked
    block_reason: Optional[str] = None

    def to_envelope_extension(self) -> dict:
        """Convert to execution envelope extension format."""
        return {
            "invocation_safety": {
                "checked": True,
                "passed": self.passed,
                "flags": [f.value for f in self.flags],
                "warnings": self.warnings,
                "blocked": self.blocked,
                "block_reason": self.block_reason,
            }
        }


def run_safety_checks(
    ctx: InvocationSafetyContext,
    checks: list[Callable[[], SafetyCheckResult]],
) -> InvocationSafetyResult:
    """Run all safety checks and aggregate results."""
    flags: list[SafetyFlag] = []
    warnings: list[str] = []
    blocked = False
    block_reason: Optional[str] = None

    for check in checks:
        try:
            result = check()
            if not result.passed:
                if result.flag:
                    flags.append(result.flag)
                if result.message:
                    warnings.append(result.message)
                if result.should_block:
                    blocked = True
                    block_reason = result.message
            elif result.flag:
                # Info-level flags (like budget override)
                flags.append(result.flag)
                if result.message:
                    warnings.append(result.message)
        except Exception as e:
            logger.warning(f"Safety check failed with exception: {e}")
            warnings.append(f"Safety check error: {str(e)}")

    return InvocationSafetyResult(
        passed=not blocked,
        flags=flags,
        warnings=warnings,
        blocked=blocked,
        block_reason=block_reason,
    )


# =============================================================================
# CLI SAFETY HOOK
# =============================================================================


class CLISafetyHook:
    """
    Pre-invocation safety hook for CLI commands (CAP-020).

    Usage:
        hook = CLISafetyHook()
        result = hook.check_simulate(ctx, plan_data, budget)
        if result.blocked:
            print(f"Blocked: {result.block_reason}")
            return
        # Continue with execution
    """

    def __init__(self) -> None:
        self._rate_counts: dict[str, tuple[int, float]] = {}  # tenant -> (count, window_start)

    def _get_rate_count(self, tenant_id: str, operation: str) -> int:
        """Get current rate count for tenant/operation."""
        key = f"{tenant_id}:{operation}"
        if key not in self._rate_counts:
            return 0
        count, window_start = self._rate_counts[key]
        if time.time() - window_start > 60:  # Reset after 60s
            return 0
        return count

    def _increment_rate_count(self, tenant_id: str, operation: str) -> int:
        """Increment and return rate count."""
        key = f"{tenant_id}:{operation}"
        now = time.time()
        if key not in self._rate_counts:
            self._rate_counts[key] = (1, now)
            return 1
        count, window_start = self._rate_counts[key]
        if now - window_start > 60:
            self._rate_counts[key] = (1, now)
            return 1
        self._rate_counts[key] = (count + 1, window_start)
        return count + 1

    def check_simulate(
        self,
        ctx: InvocationSafetyContext,
        plan_data: Optional[dict] = None,
        budget_cents: Optional[int] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos simulate' command."""
        ctx.plan_data = plan_data
        ctx.budget_cents = budget_cents
        ctx.operation_type = "simulate"

        # Compute plan hash for mutation detection
        if plan_data:
            ctx.plan_hash = compute_plan_hash(plan_data)

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_budget_validation(ctx),
            lambda: check_plan_injection(plan_data),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("simulate", ctx, result)
        return result

    def check_query(
        self,
        ctx: InvocationSafetyContext,
        query_type: str,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos query' command."""
        ctx.operation_type = "query"

        # Rate limiting
        if ctx.tenant_id:
            ctx.rate_count = self._increment_rate_count(ctx.tenant_id, "query")

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_tenant_scoping(ctx),
            lambda: check_rate_limit(ctx, limit=120),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result(f"query:{query_type}", ctx, result)
        return result

    def check_recovery_approve(
        self,
        ctx: InvocationSafetyContext,
        approved_by: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos recovery approve/reject' command."""
        ctx.operation_type = "recovery_approve"
        ctx.impersonated_subject = approved_by

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_impersonation_declared(ctx),
            lambda: check_impersonation_reason(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("recovery_approve", ctx, result)
        return result

    def check_recovery_candidates(
        self,
        ctx: InvocationSafetyContext,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos recovery candidates' command."""
        ctx.operation_type = "recovery_candidates"

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_tenant_scoping(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("recovery_candidates", ctx, result)
        return result

    def check_capabilities(
        self,
        ctx: InvocationSafetyContext,
        agent_id: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos capabilities' command."""
        ctx.operation_type = "capabilities"
        ctx.agent_id = agent_id

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_tenant_scoping(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("capabilities", ctx, result)
        return result

    def check_quickstart(
        self,
        ctx: InvocationSafetyContext,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos quickstart' command (diagnostic-only)."""
        ctx.operation_type = "quickstart"
        ctx.is_diagnostic = True

        # Quickstart is diagnostic-only
        flags = [SafetyFlag.DIAGNOSTIC_INVOCATION]
        warnings = ["Quickstart is a diagnostic-only operation"]

        result = InvocationSafetyResult(
            passed=True,
            flags=flags,
            warnings=warnings,
            blocked=False,
        )
        self._log_result("quickstart", ctx, result)
        return result

    def check_skills(
        self,
        ctx: InvocationSafetyContext,
    ) -> InvocationSafetyResult:
        """Safety checks for 'aos skills' command."""
        ctx.operation_type = "skills"

        checks = [
            lambda: check_identity_resolved(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("skills", ctx, result)
        return result

    def _log_result(
        self,
        command: str,
        ctx: InvocationSafetyContext,
        result: InvocationSafetyResult,
        duration_seconds: float = 0.0,
    ) -> None:
        """Log safety check result and emit metrics."""
        # Emit metrics
        emit_safety_metrics("CAP-020", command, result, duration_seconds)

        # Emit audit event for non-passing results
        if result.blocked or result.flags:
            emit_safety_audit_event(
                capability="CAP-020",
                operation=command,
                tenant_id=ctx.tenant_id,
                caller_id=ctx.caller_id,
                result=result,
                context={
                    "agent_id": ctx.agent_id,
                    "run_id": ctx.run_id,
                    "is_diagnostic": ctx.is_diagnostic,
                },
            )

        # Standard logging
        if result.blocked:
            logger.warning(
                f"CLI safety BLOCKED: {command}",
                extra={
                    "command": command,
                    "tenant_id": ctx.tenant_id,
                    "flags": [f.value for f in result.flags],
                    "block_reason": result.block_reason,
                },
            )
        elif result.flags:
            logger.info(
                f"CLI safety warnings: {command}",
                extra={
                    "command": command,
                    "tenant_id": ctx.tenant_id,
                    "flags": [f.value for f in result.flags],
                    "warnings": result.warnings,
                },
            )


# =============================================================================
# SDK SAFETY HOOK
# =============================================================================


class SDKSafetyHook:
    """
    Pre-invocation safety hook for SDK methods (CAP-021).

    Usage:
        hook = SDKSafetyHook()
        result = hook.check_create_run(ctx, plan_data)
        if result.blocked:
            raise SafetyBlockedError(result.block_reason)
        # Continue with execution
    """

    def __init__(self) -> None:
        self._rate_counts: dict[str, tuple[int, float]] = {}

    def _get_rate_count(self, tenant_id: str, operation: str) -> int:
        """Get current rate count for tenant/operation."""
        key = f"{tenant_id}:{operation}"
        if key not in self._rate_counts:
            return 0
        count, window_start = self._rate_counts[key]
        if time.time() - window_start > 60:
            return 0
        return count

    def _increment_rate_count(self, tenant_id: str, operation: str) -> int:
        """Increment and return rate count."""
        key = f"{tenant_id}:{operation}"
        now = time.time()
        if key not in self._rate_counts:
            self._rate_counts[key] = (1, now)
            return 1
        count, window_start = self._rate_counts[key]
        if now - window_start > 60:
            self._rate_counts[key] = (1, now)
            return 1
        self._rate_counts[key] = (count + 1, window_start)
        return count + 1

    def check_create_agent(
        self,
        ctx: InvocationSafetyContext,
    ) -> InvocationSafetyResult:
        """Safety checks for create_agent() SDK method."""
        ctx.operation_type = "create_agent"

        checks = [
            lambda: check_identity_resolved(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("create_agent", ctx, result)
        return result

    def check_create_run(
        self,
        ctx: InvocationSafetyContext,
        plan_data: Optional[dict] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for create_run() SDK method."""
        ctx.operation_type = "create_run"
        ctx.plan_data = plan_data

        if plan_data:
            ctx.plan_hash = compute_plan_hash(plan_data)

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_plan_injection(plan_data),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("create_run", ctx, result)
        return result

    def check_post_goal(
        self,
        ctx: InvocationSafetyContext,
        force_skill: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for post_goal() SDK method."""
        ctx.operation_type = "post_goal"

        # force_skill is treated as impersonation of the planning system
        if force_skill:
            ctx.impersonated_subject = "planning_system"

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_impersonation_declared(ctx),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("post_goal", ctx, result)
        return result

    def check_simulate(
        self,
        ctx: InvocationSafetyContext,
        plan_data: Optional[dict] = None,
        budget_cents: Optional[int] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for simulate() SDK method."""
        ctx.operation_type = "simulate"
        ctx.plan_data = plan_data
        ctx.budget_cents = budget_cents

        if plan_data:
            ctx.plan_hash = compute_plan_hash(plan_data)

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_budget_validation(ctx),
            lambda: check_plan_injection(plan_data),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("simulate", ctx, result)
        return result

    def check_poll_run(
        self,
        ctx: InvocationSafetyContext,
        run_tenant_id: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for poll_run() SDK method."""
        ctx.operation_type = "poll_run"

        # Rate limiting
        if ctx.tenant_id:
            ctx.rate_count = self._increment_rate_count(ctx.tenant_id, "poll")

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_run_ownership(ctx, run_tenant_id),
            lambda: check_rate_limit(ctx, limit=60),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("poll_run", ctx, result)
        return result

    def check_get_run(
        self,
        ctx: InvocationSafetyContext,
        run_tenant_id: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for get_run() SDK method."""
        ctx.operation_type = "get_run"

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_run_ownership(ctx, run_tenant_id),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("get_run", ctx, result)
        return result

    def check_recall(
        self,
        ctx: InvocationSafetyContext,
        agent_tenant_id: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for recall() SDK method."""
        ctx.operation_type = "recall"

        checks = [
            lambda: check_identity_resolved(ctx),
            lambda: check_agent_ownership(ctx, agent_tenant_id),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("recall", ctx, result)
        return result

    def check_trace_finalize(
        self,
        ctx: InvocationSafetyContext,
        trace_hash: Optional[str] = None,
        hashed_fields: Optional[list[str]] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for Trace.finalize() SDK method."""
        ctx.operation_type = "trace_finalize"

        required_fields = ["timestamp", "step_id", "caller_id", "outcome"]
        actual_fields = hashed_fields or []

        checks = [
            lambda: check_trace_hash_completeness(trace_hash, required_fields, actual_fields),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("trace_finalize", ctx, result)
        return result

    def check_idempotency_key(
        self,
        ctx: InvocationSafetyContext,
        idempotency_key: Optional[str] = None,
    ) -> InvocationSafetyResult:
        """Safety checks for generate_idempotency_key() SDK method."""
        ctx.operation_type = "idempotency_key"

        checks = [
            lambda: check_idempotency_key(idempotency_key, ctx.tenant_id),
        ]

        result = run_safety_checks(ctx, checks)
        self._log_result("idempotency_key", ctx, result)
        return result

    def _log_result(
        self,
        method: str,
        ctx: InvocationSafetyContext,
        result: InvocationSafetyResult,
        duration_seconds: float = 0.0,
    ) -> None:
        """Log safety check result and emit metrics."""
        # Emit metrics
        emit_safety_metrics("CAP-021", method, result, duration_seconds)

        # Emit audit event for non-passing results
        if result.blocked or result.flags:
            emit_safety_audit_event(
                capability="CAP-021",
                operation=method,
                tenant_id=ctx.tenant_id,
                caller_id=ctx.caller_id,
                result=result,
                context={
                    "agent_id": ctx.agent_id,
                    "run_id": ctx.run_id,
                    "budget_cents": ctx.budget_cents,
                },
            )

        # Standard logging
        if result.blocked:
            logger.warning(
                f"SDK safety BLOCKED: {method}",
                extra={
                    "method": method,
                    "tenant_id": ctx.tenant_id,
                    "flags": [f.value for f in result.flags],
                    "block_reason": result.block_reason,
                },
            )
        elif result.flags:
            logger.info(
                f"SDK safety warnings: {method}",
                extra={
                    "method": method,
                    "tenant_id": ctx.tenant_id,
                    "flags": [f.value for f in result.flags],
                    "warnings": result.warnings,
                },
            )


# =============================================================================
# METRICS (PIN-332 Phase 4.2)
# =============================================================================

# Prometheus metrics for invocation safety
# These integrate with the existing metrics infrastructure
try:
    from prometheus_client import Counter, Histogram

    SAFETY_CHECK_TOTAL = Counter(
        "aos_invocation_safety_check_total",
        "Total invocation safety checks performed",
        ["capability", "operation", "result"],
    )

    SAFETY_FLAG_TOTAL = Counter(
        "aos_invocation_safety_flag_total",
        "Total invocation safety flags raised",
        ["capability", "operation", "flag"],
    )

    SAFETY_BLOCK_TOTAL = Counter(
        "aos_invocation_safety_block_total",
        "Total invocations blocked by safety checks",
        ["capability", "operation", "reason"],
    )

    SAFETY_CHECK_DURATION = Histogram(
        "aos_invocation_safety_check_duration_seconds",
        "Duration of invocation safety checks",
        ["capability", "operation"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    )

    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False


def emit_safety_metrics(
    capability: str,  # CAP-020 or CAP-021
    operation: str,
    result: InvocationSafetyResult,
    duration_seconds: float = 0.0,
) -> None:
    """
    Emit safety metrics to Prometheus and structured logs.

    Args:
        capability: CAP-020 (CLI) or CAP-021 (SDK)
        operation: The specific operation (simulate, query, etc.)
        result: The safety check result
        duration_seconds: How long the safety checks took
    """
    # Emit Prometheus metrics if available
    if _METRICS_AVAILABLE:
        # Check result (pass/fail/block)
        outcome = "blocked" if result.blocked else ("passed" if result.passed else "failed")
        SAFETY_CHECK_TOTAL.labels(
            capability=capability,
            operation=operation,
            result=outcome,
        ).inc()

        # Individual flags
        for flag in result.flags:
            SAFETY_FLAG_TOTAL.labels(
                capability=capability,
                operation=operation,
                flag=flag.value,
            ).inc()

        # Block events
        if result.blocked:
            SAFETY_BLOCK_TOTAL.labels(
                capability=capability,
                operation=operation,
                reason=result.block_reason or "unknown",
            ).inc()

        # Duration
        if duration_seconds > 0:
            SAFETY_CHECK_DURATION.labels(
                capability=capability,
                operation=operation,
            ).observe(duration_seconds)

    # Structured logging for audit trail
    log_extra = {
        "safety_check": True,
        "capability": capability,
        "operation": operation,
        "passed": result.passed,
        "blocked": result.blocked,
        "flags": [f.value for f in result.flags],
        "warnings": result.warnings,
        "duration_seconds": duration_seconds,
    }

    if result.blocked:
        log_extra["block_reason"] = result.block_reason
        logger.warning(f"SAFETY_BLOCK: {capability}:{operation}", extra=log_extra)
    elif result.flags:
        logger.info(f"SAFETY_WARN: {capability}:{operation}", extra=log_extra)
    else:
        logger.debug(f"SAFETY_PASS: {capability}:{operation}", extra=log_extra)


def emit_safety_audit_event(
    capability: str,
    operation: str,
    tenant_id: Optional[str],
    caller_id: Optional[str],
    result: InvocationSafetyResult,
    context: Optional[dict] = None,
) -> None:
    """
    Emit structured safety audit event for compliance logging.

    This is separate from metrics - it creates a detailed audit record
    suitable for security review and compliance reporting.

    Args:
        capability: CAP-020 (CLI) or CAP-021 (SDK)
        operation: The specific operation
        tenant_id: Tenant identifier
        caller_id: Caller identifier
        result: The safety check result
        context: Additional context data
    """
    import datetime

    audit_event = {
        "event_type": "invocation_safety_audit",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "capability": capability,
        "operation": operation,
        "tenant_id": tenant_id,
        "caller_id": caller_id,
        "result": {
            "passed": result.passed,
            "blocked": result.blocked,
            "flags": [f.value for f in result.flags],
            "warnings": result.warnings,
            "block_reason": result.block_reason,
        },
        "context": context or {},
        "pin_reference": "PIN-332",
    }

    # Log at INFO level for audit trail (these should be captured by log aggregation)
    logger.info(
        "SAFETY_AUDIT_EVENT",
        extra={"audit_event": audit_event},
    )


# =============================================================================
# SAFETY CHECK TIMING WRAPPER
# =============================================================================


class SafetyCheckTimer:
    """Context manager for timing safety checks."""

    def __init__(self, capability: str, operation: str):
        self.capability = capability
        self.operation = operation
        self.start_time: Optional[float] = None
        self.duration: float = 0.0

    def __enter__(self) -> "SafetyCheckTimer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time:
            self.duration = time.time() - self.start_time

    def emit(self, result: InvocationSafetyResult) -> None:
        """Emit metrics with recorded duration."""
        emit_safety_metrics(self.capability, self.operation, result, self.duration)


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

# Global hook instances for CLI and SDK
cli_safety_hook = CLISafetyHook()
sdk_safety_hook = SDKSafetyHook()
