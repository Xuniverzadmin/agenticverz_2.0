# Workflow Engine Metrics (M4 Hardening)
"""
Prometheus metrics for workflow engine observability.

Provides:
1. Error code counters by spec_id and tenant
2. Checkpoint operation metrics
3. Golden replay verification metrics
4. Step execution timing

Design Principles:
- Low cardinality: Hash tenant_ids, limit label values
- Actionable: Every metric should enable an alert or dashboard
- Deterministic: Same errors produce same metric labels
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = None

logger = logging.getLogger("nova.workflow.metrics")


def _hash_tenant(tenant_id: str, length: int = 8) -> str:
    """
    Hash tenant_id for metrics (privacy + cardinality control).

    Args:
        tenant_id: Raw tenant identifier
        length: Length of hash prefix to use

    Returns:
        Hashed tenant identifier
    """
    if not tenant_id:
        return "unknown"
    return hashlib.sha256(tenant_id.encode()).hexdigest()[:length]


# ============== Workflow Failure Metrics ==============

if PROMETHEUS_AVAILABLE:
    # Error code counter - tracks failures by error code, spec_id, and tenant
    workflow_failures_total = Counter(
        "workflow_failures_total",
        "Total workflow failures by error code",
        ["error_code", "spec_id", "tenant_hash"],
    )

    # Step failure counter - more granular than workflow failures
    workflow_step_failures_total = Counter(
        "workflow_step_failures_total",
        "Total step failures by error code and skill",
        ["error_code", "skill_id", "spec_id"],
    )

    # Checkpoint operation metrics
    workflow_checkpoint_operations_total = Counter(
        "workflow_checkpoint_operations_total",
        "Total checkpoint operations",
        ["operation", "status"],  # operation: save/load, status: success/failure
    )

    workflow_checkpoint_duration_seconds = Histogram(
        "workflow_checkpoint_duration_seconds",
        "Checkpoint operation duration in seconds",
        ["operation"],
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    )

    # Golden replay metrics
    workflow_replay_verifications_total = Counter(
        "workflow_replay_verifications_total",
        "Total golden replay verifications",
        ["status"],  # status: passed/failed
    )

    workflow_replay_failures_total = Counter(
        "workflow_replay_failures_total",
        "Golden replay verification failures",
        ["failure_type", "spec_id"],  # failure_type: hash_mismatch, event_count, etc.
    )

    # Step execution metrics
    workflow_step_duration_seconds = Histogram(
        "workflow_step_duration_seconds",
        "Step execution duration in seconds",
        ["skill_id", "status"],  # status: success/failure
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Active workflows gauge
    workflow_active_runs = Gauge(
        "workflow_active_runs",
        "Number of currently running workflows",
        ["spec_id"],
    )

    # Budget metrics
    workflow_budget_usage_cents = Histogram(
        "workflow_budget_usage_cents",
        "Budget usage per workflow in cents",
        ["spec_id"],
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000],
    )

    # ============== Capability Violation Metrics (M5 Prep) ==============

    # Capability violation counter - tracks policy denials
    capability_violations_total = Counter(
        "nova_capability_violations_total",
        "Total capability violations by type and skill",
        ["violation_type", "skill_id", "tenant_hash"],
        # violation_type: network, filesystem, budget, rate_limit, permission
    )

    # Policy decision counter - tracks all policy evaluations
    policy_decisions_total = Counter(
        "nova_policy_decisions_total",
        "Total policy decisions by result and policy type",
        ["decision", "policy_type"],
        # decision: allow, deny, escalate
        # policy_type: budget, rate_limit, capability, permission
    )

    # Resource budget rejections
    resource_budget_rejections_total = Counter(
        "nova_resource_budget_rejections_total",
        "Resource requests rejected due to budget constraints",
        ["resource_type", "skill_id"],
        # resource_type: cost, tokens, api_calls
    )

    # Fallback activations counter
    fallback_activations_total = Counter(
        "nova_fallback_activations_total",
        "Fallback strategies activated after primary failure",
        ["fallback_type", "original_skill_id"],
        # fallback_type: cache, retry, alternative_skill, degraded
    )

    # Auto-recovery attempts
    auto_recovery_attempts_total = Counter(
        "nova_auto_recovery_attempts_total",
        "Automatic recovery attempts by outcome",
        ["recovery_type", "outcome"],
        # recovery_type: retry, checkpoint_restore, circuit_breaker
        # outcome: success, failure
    )

    # Cost simulation vs actual drift
    cost_simulation_drift_cents = Histogram(
        "nova_cost_simulation_drift_cents",
        "Difference between simulated and actual cost in cents",
        ["skill_id"],
        buckets=[-100, -50, -25, -10, -5, 0, 5, 10, 25, 50, 100],
    )

    # ============== M5 GA Additional Metrics ==============

    # Emergency stop gauge - alerts monitor this for workflow engine halt
    policy_emergency_stop_enabled = Gauge(
        "nova_policy_emergency_stop_enabled",
        "Whether emergency stop is enabled (1=enabled, 0=disabled)",
    )

    # Budget breach counter by type
    budget_breach_total = Counter(
        "nova_budget_breach_total",
        "Total budget breaches by type",
        ["breach_type"],
        # breach_type: workflow_ceiling, step_ceiling, agent_budget
    )

    # Approval workflow metrics
    approval_requests_pending = Gauge(
        "nova_approval_requests_pending",
        "Number of pending approval requests",
    )

    approval_requests_total = Counter(
        "nova_approval_requests_total",
        "Total approval requests created",
        ["policy_type"],
    )

    approval_escalations_total = Counter(
        "nova_approval_escalations_total",
        "Total approval requests escalated",
    )

    approval_actions_total = Counter(
        "nova_approval_actions_total",
        "Total approval actions taken",
        ["result"],  # result: approved, rejected, expired
    )

    # Webhook delivery metrics
    webhook_fallback_writes_total = Counter(
        "nova_webhook_fallback_writes_total",
        "Webhook callbacks that failed and were written to fallback storage",
    )

    # Feature flag metrics
    feature_flag_drift_detected = Gauge(
        "nova_feature_flag_drift_detected",
        "Whether feature flag file/DB drift is detected (1=drift, 0=no drift)",
    )

    feature_flag_enabled = Gauge(
        "nova_feature_flag_enabled",
        "Feature flag enabled status",
        ["flag"],
    )

    m5_signoff_present = Gauge(
        "nova_m5_signoff_present",
        "Whether M5 GA signoff is present (1=present, 0=missing)",
    )

    # Cost tracking totals
    cost_actual_cents_total = Counter(
        "nova_cost_actual_cents_total",
        "Total actual cost incurred in cents",
        ["skill_id"],
    )

    cost_simulated_cents_total = Counter(
        "nova_cost_simulated_cents_total",
        "Total simulated cost in cents",
        ["skill_id"],
    )

else:
    # Stub implementations when Prometheus not available
    class StubCounter:
        def labels(self, **kwargs):
            return self

        def inc(self, amount=1):
            pass

    class StubHistogram:
        def labels(self, **kwargs):
            return self

        def observe(self, value):
            pass

    class StubGauge:
        def labels(self, **kwargs):
            return self

        def set(self, value):
            pass

        def inc(self, amount=1):
            pass

        def dec(self, amount=1):
            pass

    workflow_failures_total = StubCounter()
    workflow_step_failures_total = StubCounter()
    workflow_checkpoint_operations_total = StubCounter()
    workflow_checkpoint_duration_seconds = StubHistogram()
    workflow_replay_verifications_total = StubCounter()
    workflow_replay_failures_total = StubCounter()
    workflow_step_duration_seconds = StubHistogram()
    workflow_active_runs = StubGauge()
    workflow_budget_usage_cents = StubHistogram()
    # M5 capability metrics stubs
    capability_violations_total = StubCounter()
    policy_decisions_total = StubCounter()
    resource_budget_rejections_total = StubCounter()
    fallback_activations_total = StubCounter()
    auto_recovery_attempts_total = StubCounter()
    cost_simulation_drift_cents = StubHistogram()
    # M5 GA additional metrics stubs
    policy_emergency_stop_enabled = StubGauge()
    budget_breach_total = StubCounter()
    approval_requests_pending = StubGauge()
    approval_requests_total = StubCounter()
    approval_escalations_total = StubCounter()
    approval_actions_total = StubCounter()
    webhook_fallback_writes_total = StubCounter()
    feature_flag_drift_detected = StubGauge()
    feature_flag_enabled = StubGauge()
    m5_signoff_present = StubGauge()
    cost_actual_cents_total = StubCounter()
    cost_simulated_cents_total = StubCounter()


# ============== Metric Recording Functions ==============


def record_workflow_failure(
    error_code: str,
    spec_id: str,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Record a workflow failure.

    Args:
        error_code: WorkflowErrorCode value (e.g., "TIMEOUT", "BUDGET_EXCEEDED")
        spec_id: Workflow specification ID
        tenant_id: Tenant identifier (will be hashed)
    """
    tenant_hash = _hash_tenant(tenant_id) if tenant_id else "unknown"
    workflow_failures_total.labels(
        error_code=error_code,
        spec_id=spec_id,
        tenant_hash=tenant_hash,
    ).inc()

    logger.debug("workflow_failure_recorded", extra={"error_code": error_code, "spec_id": spec_id})


def record_step_failure(
    error_code: str,
    skill_id: str,
    spec_id: str,
) -> None:
    """
    Record a step failure.

    Args:
        error_code: WorkflowErrorCode value
        skill_id: Skill that failed
        spec_id: Workflow specification ID
    """
    workflow_step_failures_total.labels(
        error_code=error_code,
        skill_id=skill_id,
        spec_id=spec_id,
    ).inc()


def record_checkpoint_operation(
    operation: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """
    Record a checkpoint operation.

    Args:
        operation: "save" or "load"
        success: Whether operation succeeded
        duration_seconds: Operation duration
    """
    status = "success" if success else "failure"
    workflow_checkpoint_operations_total.labels(
        operation=operation,
        status=status,
    ).inc()
    workflow_checkpoint_duration_seconds.labels(operation=operation).observe(duration_seconds)


def record_replay_verification(
    passed: bool,
    failure_type: Optional[str] = None,
    spec_id: Optional[str] = None,
) -> None:
    """
    Record a golden replay verification result.

    Args:
        passed: Whether verification passed
        failure_type: Type of failure if not passed
        spec_id: Workflow specification ID
    """
    status = "passed" if passed else "failed"
    workflow_replay_verifications_total.labels(status=status).inc()

    if not passed and failure_type:
        workflow_replay_failures_total.labels(
            failure_type=failure_type,
            spec_id=spec_id or "unknown",
        ).inc()


def record_step_duration(
    skill_id: str,
    duration_seconds: float,
    success: bool,
) -> None:
    """
    Record step execution duration.

    Args:
        skill_id: Skill that was executed
        duration_seconds: Execution duration
        success: Whether step succeeded
    """
    status = "success" if success else "failure"
    workflow_step_duration_seconds.labels(
        skill_id=skill_id,
        status=status,
    ).observe(duration_seconds)


def record_workflow_start(spec_id: str) -> None:
    """Record that a workflow run started."""
    workflow_active_runs.labels(spec_id=spec_id).inc()


def record_workflow_end(spec_id: str, total_cost_cents: int) -> None:
    """Record that a workflow run ended."""
    workflow_active_runs.labels(spec_id=spec_id).dec()
    workflow_budget_usage_cents.labels(spec_id=spec_id).observe(total_cost_cents)


# ============== Capability & Policy Metric Recording Functions (M5) ==============


def record_capability_violation(
    violation_type: str,
    skill_id: str,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Record a capability violation (policy denial).

    Args:
        violation_type: Type of violation (network, filesystem, budget, rate_limit, permission)
        skill_id: Skill that triggered the violation
        tenant_id: Tenant identifier (will be hashed)
    """
    tenant_hash = _hash_tenant(tenant_id) if tenant_id else "unknown"
    capability_violations_total.labels(
        violation_type=violation_type,
        skill_id=skill_id,
        tenant_hash=tenant_hash,
    ).inc()

    logger.info("capability_violation_recorded", extra={"violation_type": violation_type, "skill_id": skill_id})


def record_policy_decision(
    decision: str,
    policy_type: str,
) -> None:
    """
    Record a policy evaluation result.

    Args:
        decision: Result (allow, deny, escalate)
        policy_type: Type of policy (budget, rate_limit, capability, permission)
    """
    policy_decisions_total.labels(
        decision=decision,
        policy_type=policy_type,
    ).inc()


def record_budget_rejection(
    resource_type: str,
    skill_id: str,
) -> None:
    """
    Record a resource request rejected due to budget constraints.

    Args:
        resource_type: Type of resource (cost, tokens, api_calls)
        skill_id: Skill that was rejected
    """
    resource_budget_rejections_total.labels(
        resource_type=resource_type,
        skill_id=skill_id,
    ).inc()


def record_fallback_activation(
    fallback_type: str,
    original_skill_id: str,
) -> None:
    """
    Record a fallback strategy activation.

    Args:
        fallback_type: Type of fallback (cache, retry, alternative_skill, degraded)
        original_skill_id: Original skill that failed
    """
    fallback_activations_total.labels(
        fallback_type=fallback_type,
        original_skill_id=original_skill_id,
    ).inc()


def record_auto_recovery(
    recovery_type: str,
    success: bool,
) -> None:
    """
    Record an automatic recovery attempt.

    Args:
        recovery_type: Type of recovery (retry, checkpoint_restore, circuit_breaker)
        success: Whether recovery succeeded
    """
    outcome = "success" if success else "failure"
    auto_recovery_attempts_total.labels(
        recovery_type=recovery_type,
        outcome=outcome,
    ).inc()


def record_cost_simulation_drift(
    skill_id: str,
    simulated_cents: int,
    actual_cents: int,
) -> None:
    """
    Record the difference between simulated and actual cost.

    Args:
        skill_id: Skill that was executed
        simulated_cents: Pre-execution cost estimate
        actual_cents: Actual cost incurred
    """
    drift = actual_cents - simulated_cents
    cost_simulation_drift_cents.labels(skill_id=skill_id).observe(drift)
    # Also record totals for ratio alerts
    cost_simulated_cents_total.labels(skill_id=skill_id).inc(simulated_cents)
    cost_actual_cents_total.labels(skill_id=skill_id).inc(actual_cents)


# ============== M5 GA Additional Metric Recording Functions ==============


def set_emergency_stop(enabled: bool) -> None:
    """Set the emergency stop gauge (0=disabled, 1=enabled)."""
    policy_emergency_stop_enabled.set(1 if enabled else 0)


def record_budget_breach(breach_type: str) -> None:
    """
    Record a budget breach.

    Args:
        breach_type: Type of breach (workflow_ceiling, step_ceiling, agent_budget)
    """
    budget_breach_total.labels(breach_type=breach_type).inc()


def set_approval_requests_pending(count: int) -> None:
    """Set the number of pending approval requests."""
    approval_requests_pending.set(count)


def record_approval_request_created(policy_type: str) -> None:
    """Record that an approval request was created."""
    approval_requests_total.labels(policy_type=policy_type).inc()


def record_approval_escalation() -> None:
    """Record that an approval request was escalated."""
    approval_escalations_total.inc()


def record_approval_action(result: str) -> None:
    """
    Record an approval action result.

    Args:
        result: Result of the action (approved, rejected, expired)
    """
    approval_actions_total.labels(result=result).inc()


def record_webhook_fallback() -> None:
    """Record that a webhook callback failed and was written to fallback."""
    webhook_fallback_writes_total.inc()


def set_feature_flag_drift(detected: bool) -> None:
    """Set whether feature flag drift is detected (0=no drift, 1=drift)."""
    feature_flag_drift_detected.set(1 if detected else 0)


def set_feature_flag(flag: str, enabled: bool) -> None:
    """Set a feature flag status."""
    feature_flag_enabled.labels(flag=flag).set(1 if enabled else 0)


def set_m5_signoff_present(present: bool) -> None:
    """Set whether M5 signoff is present (0=missing, 1=present)."""
    m5_signoff_present.set(1 if present else 0)


def check_m5_signoff() -> bool:
    """
    Check if M5 signoff file exists and update the metric.

    Returns:
        True if signoff is present
    """
    import os

    signoff_path = os.getenv("M5_SIGNOFF_PATH", "/root/agenticverz2.0/.m5_signoff")
    # Also check legacy path
    legacy_path = "/root/agenticverz2.0/.m4_signoff"

    present = os.path.exists(signoff_path) or os.path.exists(legacy_path)
    set_m5_signoff_present(present)
    return present
