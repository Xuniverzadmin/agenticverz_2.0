# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 limit enhancement governance requirements (GAP-009 to GAP-012)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-003: Limit Enhancement Tests (GAP-009 to GAP-012)

Tests the limit configuration and signal features:
- GAP-009: RAG access boolean limit type
- GAP-010: DB query limit (window-based)
- GAP-011: PER_SESSION vs TEMPORAL window clarity
- GAP-012: Limit separation principle (limits emit signals only)

Key Principle:
> Limits emit NEAR/BREACH signals only, actions are separate.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.policy_control_plane import (
    BreachType,
    Limit,
    LimitCategory,
    LimitConsequence,
    LimitEnforcement,
    LimitScope,
    LimitStatus,
    ResetPeriod,
)
from app.models.threshold_signal import (
    SignalType,
    ThresholdMetric,
    ThresholdSignal,
)
from app.schemas.limits.policy_limits import (
    CreatePolicyLimitRequest,
    LimitCategoryEnum,
    LimitEnforcementEnum,
    LimitScopeEnum,
    PolicyLimitResponse,
    ResetPeriodEnum,
    UpdatePolicyLimitRequest,
)


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestLimitImports:
    """Verify all limit-related imports are accessible."""

    def test_limit_model_import(self) -> None:
        """Test Limit model is importable."""
        assert Limit is not None

    def test_limit_category_import(self) -> None:
        """Test LimitCategory enum is importable."""
        assert LimitCategory is not None

    def test_limit_scope_import(self) -> None:
        """Test LimitScope enum is importable."""
        assert LimitScope is not None

    def test_limit_enforcement_import(self) -> None:
        """Test LimitEnforcement enum is importable."""
        assert LimitEnforcement is not None

    def test_threshold_signal_import(self) -> None:
        """Test ThresholdSignal model is importable."""
        assert ThresholdSignal is not None

    def test_signal_type_import(self) -> None:
        """Test SignalType enum is importable."""
        assert SignalType is not None

    def test_threshold_metric_import(self) -> None:
        """Test ThresholdMetric enum is importable."""
        assert ThresholdMetric is not None


# ===========================================================================
# GAP-009: RAG Access Boolean
# ===========================================================================


class TestGAP009RAGAccessLimit:
    """
    GAP-009: RAG Access Boolean

    CURRENT: Not supported
    REQUIRED: `rag_access: { allowed: boolean }`
    """

    def test_rag_access_metric_exists(self) -> None:
        """RAG_ACCESS is a valid ThresholdMetric."""
        assert ThresholdMetric.RAG_ACCESS is not None
        assert ThresholdMetric.RAG_ACCESS.value == "rag_access"

    def test_can_create_near_signal_for_rag_access(self) -> None:
        """Can create a NEAR signal for RAG access metric."""
        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.RAG_ACCESS,
            current_value=3,  # 3 access attempts
            threshold_value=5,  # max 5 allowed
        )
        assert signal.metric == "rag_access"
        assert signal.signal_type == SignalType.NEAR.value

    def test_can_create_breach_signal_for_rag_access(self) -> None:
        """Can create a BREACH signal for RAG access metric."""
        signal = ThresholdSignal.create_breach_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.RAG_ACCESS,
            current_value=6,  # 6 access attempts
            threshold_value=5,  # max 5 allowed
            action_taken="stop",
        )
        assert signal.metric == "rag_access"
        assert signal.signal_type == SignalType.BREACH.value

    def test_rag_access_boolean_represented_as_threshold(self) -> None:
        """RAG access boolean is represented as threshold (0 = disallowed)."""
        # For boolean disallowed: threshold = 0, any access = breach
        signal = ThresholdSignal.create_breach_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.RAG_ACCESS,
            current_value=1,  # Any access
            threshold_value=0,  # Disallowed
            action_taken="stop",
        )
        assert signal.current_value > signal.threshold_value


# ===========================================================================
# GAP-010: DB Query Limit
# ===========================================================================


class TestGAP010DBQueryLimit:
    """
    GAP-010: DB Query Limit

    CURRENT: Not supported
    REQUIRED: `db_query_limit: { max_queries, window_seconds }`

    Note: DB query limits use RATE category with window_seconds.
    """

    def test_rate_limit_category_exists(self) -> None:
        """RATE limit category exists for window-based limits."""
        assert LimitCategory.RATE is not None
        assert LimitCategory.RATE.value == "RATE"

    def test_rate_limit_requires_window_seconds(self) -> None:
        """Rate limits support window_seconds field."""
        request = CreatePolicyLimitRequest(
            name="DB Query Limit",
            limit_category=LimitCategoryEnum.RATE,
            limit_type="DB_QUERIES",
            max_value=Decimal("100"),
            window_seconds=60,  # Per minute
        )
        assert request.window_seconds == 60

    def test_can_create_db_query_rate_limit_request(self) -> None:
        """Can create a DB query rate limit request."""
        request = CreatePolicyLimitRequest(
            name="Max DB Queries",
            description="Limit DB queries per minute",
            limit_category=LimitCategoryEnum.RATE,
            limit_type="DB_QUERIES_PER_MIN",
            scope=LimitScopeEnum.AGENT,
            max_value=Decimal("50"),
            window_seconds=60,
            enforcement=LimitEnforcementEnum.BLOCK,
        )
        assert request.limit_type == "DB_QUERIES_PER_MIN"
        assert request.window_seconds == 60
        assert request.limit_category == LimitCategoryEnum.RATE

    def test_window_based_limit_patterns(self) -> None:
        """Window-based limits support various time windows."""
        windows = [30, 60, 300, 3600]  # 30s, 1m, 5m, 1h
        for window in windows:
            request = CreatePolicyLimitRequest(
                name=f"Rate limit {window}s",
                limit_category=LimitCategoryEnum.RATE,
                limit_type="REQUESTS",
                max_value=Decimal("100"),
                window_seconds=window,
            )
            assert request.window_seconds == window


# ===========================================================================
# GAP-011: PER_SESSION vs TEMPORAL Clarity
# ===========================================================================


class TestGAP011LimitWindowClarity:
    """
    GAP-011: PER_SESSION vs TEMPORAL Clarity

    CURRENT: Unclear distinction
    REQUIRED: Explicit `limit_window: PER_SESSION | TEMPORAL`

    Implementation: Uses LimitCategory to distinguish:
    - BUDGET: Per session/period (with reset_period)
    - RATE: Temporal/rolling window (with window_seconds)
    - THRESHOLD: Per-run threshold (no window)
    """

    def test_limit_category_budget_for_per_session(self) -> None:
        """BUDGET category represents per-session/period limits."""
        assert LimitCategory.BUDGET is not None
        assert LimitCategory.BUDGET.value == "BUDGET"

    def test_limit_category_rate_for_temporal(self) -> None:
        """RATE category represents temporal/rolling window limits."""
        assert LimitCategory.RATE is not None
        assert LimitCategory.RATE.value == "RATE"

    def test_limit_category_threshold_for_per_run(self) -> None:
        """THRESHOLD category represents per-run limits."""
        assert LimitCategory.THRESHOLD is not None
        assert LimitCategory.THRESHOLD.value == "THRESHOLD"

    def test_budget_limit_has_reset_period(self) -> None:
        """Budget limits have reset_period for session clarity."""
        request = CreatePolicyLimitRequest(
            name="Monthly Budget",
            limit_category=LimitCategoryEnum.BUDGET,
            limit_type="COST_USD",
            max_value=Decimal("1000"),
            reset_period=ResetPeriodEnum.MONTHLY,
        )
        assert request.reset_period == ResetPeriodEnum.MONTHLY

    def test_reset_period_values(self) -> None:
        """Reset period supports session-like values."""
        assert ResetPeriod.DAILY.value == "DAILY"
        assert ResetPeriod.WEEKLY.value == "WEEKLY"
        assert ResetPeriod.MONTHLY.value == "MONTHLY"
        assert ResetPeriod.NONE.value == "NONE"  # Per-session

    def test_rate_limit_has_window_seconds(self) -> None:
        """Rate limits have window_seconds for temporal clarity."""
        request = CreatePolicyLimitRequest(
            name="Requests Per Minute",
            limit_category=LimitCategoryEnum.RATE,
            limit_type="REQUESTS_PER_MIN",
            max_value=Decimal("60"),
            window_seconds=60,
        )
        assert request.window_seconds == 60

    def test_threshold_limit_no_window(self) -> None:
        """Threshold limits don't need window (per-run)."""
        request = CreatePolicyLimitRequest(
            name="Max Tokens Per Run",
            limit_category=LimitCategoryEnum.THRESHOLD,
            limit_type="TOKENS_PER_RUN",
            max_value=Decimal("10000"),
            # No window_seconds or reset_period needed
        )
        assert request.window_seconds is None
        assert request.reset_period is None

    def test_category_distinguishes_window_type(self) -> None:
        """Category determines whether limit is session or temporal."""
        # Session-like: BUDGET with reset period
        budget = CreatePolicyLimitRequest(
            name="Daily Budget",
            limit_category=LimitCategoryEnum.BUDGET,
            limit_type="COST_USD",
            max_value=Decimal("100"),
            reset_period=ResetPeriodEnum.DAILY,
        )
        assert budget.limit_category == LimitCategoryEnum.BUDGET

        # Temporal: RATE with rolling window
        rate = CreatePolicyLimitRequest(
            name="Rate Limit",
            limit_category=LimitCategoryEnum.RATE,
            limit_type="REQUESTS",
            max_value=Decimal("100"),
            window_seconds=60,
        )
        assert rate.limit_category == LimitCategoryEnum.RATE


# ===========================================================================
# GAP-012: Limit Separation Principle
# ===========================================================================


class TestGAP012LimitSeparationPrinciple:
    """
    GAP-012: Limit Separation Principle

    CURRENT: Limits can have actions
    REQUIRED: Limits emit NEAR/BREACH only, actions separate

    Implementation: ThresholdSignal emits NEAR/BREACH signals,
    actions are defined separately in enforcement configuration.
    """

    def test_signal_type_near_exists(self) -> None:
        """NEAR signal type exists for approaching threshold."""
        assert SignalType.NEAR is not None
        assert SignalType.NEAR.value == "near"

    def test_signal_type_breach_exists(self) -> None:
        """BREACH signal type exists for threshold exceeded."""
        assert SignalType.BREACH is not None
        assert SignalType.BREACH.value == "breach"

    def test_signal_types_are_only_near_and_breach(self) -> None:
        """Signal types are limited to NEAR and BREACH."""
        signal_values = [s.value for s in SignalType]
        assert "near" in signal_values
        assert "breach" in signal_values
        assert len(signal_values) == 2

    def test_near_signal_no_action(self) -> None:
        """NEAR signal is created without action_taken."""
        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=80,
            threshold_value=100,
        )
        assert signal.signal_type == SignalType.NEAR.value
        assert signal.action_taken is None

    def test_breach_signal_records_action_separately(self) -> None:
        """BREACH signal records action but doesn't execute it."""
        signal = ThresholdSignal.create_breach_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=120,
            threshold_value=100,
            action_taken="stop",  # Action is recorded, not executed
        )
        assert signal.signal_type == SignalType.BREACH.value
        # action_taken is a record of what was done, not the signal causing it
        assert signal.action_taken == "stop"

    def test_limit_enforcement_is_separate_from_signal(self) -> None:
        """Limit enforcement behavior is defined separately from signal."""
        # Enforcement is on the limit definition
        assert LimitEnforcement.BLOCK is not None
        assert LimitEnforcement.WARN is not None
        assert LimitEnforcement.ALERT is not None

        # These are NOT on the signal type
        enforcement_values = [e.value for e in LimitEnforcement]
        signal_values = [s.value for s in SignalType]
        # No overlap between enforcement actions and signal types
        assert not set(enforcement_values).intersection(set(signal_values))

    def test_signal_has_percentage_for_near_detection(self) -> None:
        """Signals include percentage for NEAR threshold detection."""
        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.TOKEN_USAGE,
            current_value=8000,
            threshold_value=10000,
        )
        assert signal.percentage == 80.0  # 8000/10000 * 100


# ===========================================================================
# Test: Threshold Signal Model
# ===========================================================================


class TestThresholdSignalModel:
    """Test ThresholdSignal model features."""

    def test_signal_has_required_fields(self) -> None:
        """ThresholdSignal has all required fields."""
        signal = ThresholdSignal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            signal_type="near",
            metric="cost",
            current_value=80.0,
            threshold_value=100.0,
        )
        assert signal.run_id == "RUN-001"
        assert signal.policy_id == "POL-001"
        assert signal.tenant_id == "tenant-001"

    def test_signal_acknowledgement(self) -> None:
        """Signals can be acknowledged."""
        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=90,
            threshold_value=100,
        )
        signal.acknowledge("user-123")
        assert signal.acknowledged is True
        assert signal.acknowledged_by == "user-123"
        assert signal.acknowledged_at is not None

    def test_signal_alert_marking(self) -> None:
        """Signals can be marked as alerted."""
        signal = ThresholdSignal.create_breach_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=110,
            threshold_value=100,
            action_taken="stop",
        )
        signal.mark_alert_sent(["email", "slack"])
        assert signal.alert_sent is True
        assert signal.alert_sent_at is not None
        assert "email" in signal.alert_channels
        assert "slack" in signal.alert_channels

    def test_signal_to_evidence(self) -> None:
        """Signal can be converted to evidence dict."""
        signal = ThresholdSignal.create_breach_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.TOKEN_USAGE,
            current_value=12000,
            threshold_value=10000,
            action_taken="pause",
        )
        evidence = signal.to_evidence()
        assert "signal_id" in evidence
        assert evidence["signal_type"] == "breach"
        assert evidence["metric"] == "token_usage"
        assert evidence["current_value"] == 12000
        assert evidence["threshold_value"] == 10000


# ===========================================================================
# Test: Threshold Metrics
# ===========================================================================


class TestThresholdMetrics:
    """Test ThresholdMetric enum values."""

    def test_token_usage_metric(self) -> None:
        """TOKEN_USAGE metric exists."""
        assert ThresholdMetric.TOKEN_USAGE.value == "token_usage"

    def test_cost_metric(self) -> None:
        """COST metric exists."""
        assert ThresholdMetric.COST.value == "cost"

    def test_burn_rate_metric(self) -> None:
        """BURN_RATE metric exists."""
        assert ThresholdMetric.BURN_RATE.value == "burn_rate"

    def test_rag_access_metric(self) -> None:
        """RAG_ACCESS metric exists."""
        assert ThresholdMetric.RAG_ACCESS.value == "rag_access"

    def test_step_count_metric(self) -> None:
        """STEP_COUNT metric exists."""
        assert ThresholdMetric.STEP_COUNT.value == "step_count"

    def test_latency_metric(self) -> None:
        """LATENCY metric exists."""
        assert ThresholdMetric.LATENCY.value == "latency"


# ===========================================================================
# Test: Breach Types
# ===========================================================================


class TestBreachTypes:
    """Test BreachType enum values."""

    def test_breached_type(self) -> None:
        """BREACHED type exists."""
        assert BreachType.BREACHED.value == "BREACHED"

    def test_exhausted_type(self) -> None:
        """EXHAUSTED type exists."""
        assert BreachType.EXHAUSTED.value == "EXHAUSTED"

    def test_throttled_type(self) -> None:
        """THROTTLED type exists."""
        assert BreachType.THROTTLED.value == "THROTTLED"

    def test_violated_type(self) -> None:
        """VIOLATED type exists."""
        assert BreachType.VIOLATED.value == "VIOLATED"


# ===========================================================================
# Test: Limit Scope
# ===========================================================================


class TestLimitScope:
    """Test LimitScope enum values."""

    def test_global_scope(self) -> None:
        """GLOBAL scope exists."""
        assert LimitScope.GLOBAL.value == "GLOBAL"

    def test_tenant_scope(self) -> None:
        """TENANT scope exists."""
        assert LimitScope.TENANT.value == "TENANT"

    def test_project_scope(self) -> None:
        """PROJECT scope exists."""
        assert LimitScope.PROJECT.value == "PROJECT"

    def test_agent_scope(self) -> None:
        """AGENT scope exists."""
        assert LimitScope.AGENT.value == "AGENT"

    def test_provider_scope(self) -> None:
        """PROVIDER scope exists (extends PolicyScope)."""
        assert LimitScope.PROVIDER.value == "PROVIDER"


# ===========================================================================
# Test: Limit Consequence
# ===========================================================================


class TestLimitConsequence:
    """Test LimitConsequence enum values."""

    def test_alert_consequence(self) -> None:
        """ALERT consequence exists."""
        assert LimitConsequence.ALERT.value == "ALERT"

    def test_incident_consequence(self) -> None:
        """INCIDENT consequence exists."""
        assert LimitConsequence.INCIDENT.value == "INCIDENT"

    def test_abort_consequence(self) -> None:
        """ABORT consequence exists."""
        assert LimitConsequence.ABORT.value == "ABORT"
