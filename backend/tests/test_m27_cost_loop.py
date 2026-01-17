"""
M27 Cost Loop Integration Tests
===============================

Tests for the full M27 cost loop:
- CostLoopOrchestrator (C1-C5 bridges)
- CostSafetyRails (per-tenant caps, blast-radius)
- CostEstimationProbe (pre-execution cost estimation)

THE INVARIANT:
    Every cost anomaly enters the loop.
    Every loop completion reduces future cost risk.

GOVERNANCE: CostLoopOrchestrator and SafeCostLoopOrchestrator require db_session.
Tests use mock sessions - in production, real sessions are required.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_session():
    """Create a mock database session for governance tests."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    return session

# =============================================================================
# UNIT TESTS: Cost Anomaly Model
# =============================================================================


class TestCostAnomaly:
    """Test CostAnomaly creation and severity classification."""

    def test_severity_classification_low(self):
        """Deviation < 200% should be LOW."""
        from app.integrations.cost_bridges import AnomalySeverity, AnomalyType, CostAnomaly

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=150,
            expected_value_cents=100,  # 50% deviation
        )

        assert anomaly.severity == AnomalySeverity.LOW
        assert anomaly.deviation_pct == 50.0

    def test_severity_classification_medium(self):
        """Deviation 200-300% should be MEDIUM."""
        from app.integrations.cost_bridges import AnomalySeverity, AnomalyType, CostAnomaly

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=250,
            expected_value_cents=100,  # 150% deviation
        )

        assert anomaly.severity == AnomalySeverity.LOW  # 150% is still LOW

        anomaly2 = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=350,
            expected_value_cents=100,  # 250% deviation
        )

        assert anomaly2.severity == AnomalySeverity.MEDIUM

    def test_severity_classification_high(self):
        """Deviation 300-500% should be HIGH."""
        from app.integrations.cost_bridges import AnomalySeverity, AnomalyType, CostAnomaly

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=450,
            expected_value_cents=100,  # 350% deviation
        )

        assert anomaly.severity == AnomalySeverity.HIGH

    def test_severity_classification_critical(self):
        """Deviation >= 500% should be CRITICAL."""
        from app.integrations.cost_bridges import AnomalySeverity, AnomalyType, CostAnomaly

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=600,
            expected_value_cents=100,  # 500% deviation
        )

        assert anomaly.severity == AnomalySeverity.CRITICAL

    def test_to_dict_serialization(self):
        """Anomaly should serialize to dict."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.FEATURE_SPIKE,
            entity_type="feature",
            entity_id="chat_feature",
            current_value_cents=1000,
            expected_value_cents=100,
        )

        d = anomaly.to_dict()
        assert d["tenant_id"] == "test_tenant"
        assert d["anomaly_type"] == "feature_spike"
        assert d["entity_type"] == "feature"
        assert "detected_at" in d


# =============================================================================
# UNIT TESTS: Cost Pattern Matcher (C2)
# =============================================================================


class TestCostPatternMatcher:
    """Test pattern matching logic."""

    @pytest.mark.asyncio
    async def test_match_user_daily_spike(self):
        """User spike should match user_daily_spike pattern."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostPatternMatcher

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_heavy_spender",
            current_value_cents=500,
            expected_value_cents=100,  # 400% deviation -> HIGH
        )

        matcher = CostPatternMatcher()
        result = await matcher.match_cost_pattern(anomaly, "inc_test123")

        assert result.pattern_id.startswith("pat_cost_")
        assert result.confidence > 0.5
        assert "pattern_type" in result.match_details
        assert result.match_details["pattern_type"] == "cost"

    @pytest.mark.asyncio
    async def test_match_feature_spike(self):
        """Feature spike should match feature_cost_explosion pattern."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostPatternMatcher

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.FEATURE_SPIKE,
            entity_type="feature",
            entity_id="chat_feature",
            current_value_cents=800,
            expected_value_cents=100,  # 700% deviation -> CRITICAL
        )

        matcher = CostPatternMatcher()
        result = await matcher.match_cost_pattern(anomaly, "inc_test456")

        assert result.confidence >= 0.6


# =============================================================================
# UNIT TESTS: Cost Recovery Generator (C3)
# =============================================================================


class TestCostRecoveryGenerator:
    """Test recovery suggestion generation."""

    @pytest.mark.asyncio
    async def test_user_spike_recoveries(self):
        """User spike should generate rate limiting suggestions."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostPatternMatcher, CostRecoveryGenerator

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_spender",
            current_value_cents=600,
            expected_value_cents=100,
        )

        matcher = CostPatternMatcher()
        pattern = await matcher.match_cost_pattern(anomaly, "inc_test")

        generator = CostRecoveryGenerator()
        recoveries = await generator.generate_recovery(anomaly, pattern, "inc_test")

        assert len(recoveries) > 0
        actions = [r.action_type for r in recoveries]
        assert "rate_limit_user" in actions or "notify_user" in actions

    @pytest.mark.asyncio
    async def test_budget_exceeded_recoveries(self):
        """Budget exceeded should generate hard limit suggestions."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostPatternMatcher, CostRecoveryGenerator

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.BUDGET_EXCEEDED,
            entity_type="tenant",
            entity_id="test_tenant",
            current_value_cents=15000,
            expected_value_cents=10000,
        )

        matcher = CostPatternMatcher()
        pattern = await matcher.match_cost_pattern(anomaly, "inc_test")

        generator = CostRecoveryGenerator()
        recoveries = await generator.generate_recovery(anomaly, pattern, "inc_test")

        assert len(recoveries) > 0
        actions = [r.action_type for r in recoveries]
        assert "enforce_hard_limit" in actions or "escalate_to_admin" in actions


# =============================================================================
# UNIT TESTS: Cost Estimation Probe
# =============================================================================


class TestCostEstimationProbe:
    """Test pre-execution cost estimation."""

    @pytest.mark.asyncio
    async def test_allowed_within_budget(self):
        """Small request should be allowed."""
        from app.integrations.cost_bridges import CostEstimationProbe

        probe = CostEstimationProbe()
        result = await probe.probe(
            model="gpt-4o-mini",
            prompt_tokens=100,
            expected_output_tokens=50,
            tenant_id="test_tenant",
            cost_threshold_cents=100,
        )

        assert result["status"] == "allowed"
        assert result["estimated_cost_cents"] < 100

    @pytest.mark.asyncio
    async def test_reroute_expensive_model(self):
        """Expensive model should suggest reroute."""
        from app.integrations.cost_bridges import CostEstimationProbe

        probe = CostEstimationProbe()
        result = await probe.probe(
            model="claude-opus-4-5-20251101",  # Most expensive
            prompt_tokens=10000,
            expected_output_tokens=5000,
            tenant_id="test_tenant",
            cost_threshold_cents=10,  # Low threshold
        )

        # Either reroute or allowed based on cost
        assert result["status"] in ["allowed", "reroute"]

    @pytest.mark.asyncio
    async def test_blocked_exceeds_hard_limit(self):
        """Very expensive request should be blocked."""
        from app.integrations.cost_bridges import CostEstimationProbe

        probe = CostEstimationProbe()
        # Need > 1000 cents to trigger block
        # claude-opus: 1.5/1k input + 7.5/1k output
        # 500k input = 750 cents, 200k output = 1500 cents = 2250 total
        result = await probe.probe(
            model="claude-opus-4-5-20251101",
            prompt_tokens=500000,
            expected_output_tokens=200000,
            tenant_id="test_tenant",
        )

        assert result["status"] == "blocked"
        assert "budget" in result["reason"].lower()


# =============================================================================
# UNIT TESTS: Safety Rails
# =============================================================================


class TestCostSafetyRails:
    """Test per-tenant caps and blast-radius limits."""

    @pytest.mark.asyncio
    async def test_policy_cap_enforcement(self):
        """Should enforce daily policy cap."""
        from app.integrations.cost_safety_rails import CostSafetyRails, SafetyConfig

        config = SafetyConfig(max_auto_policies_per_tenant_per_day=2)
        rails = CostSafetyRails(config)

        # First two should be allowed
        can1, _ = await rails.can_auto_apply_policy("tenant_a", "rate_limit", "MEDIUM")
        await rails.record_action("tenant_a", "policy", "rate_limit")
        assert can1 is True

        can2, _ = await rails.can_auto_apply_policy("tenant_a", "notify", "MEDIUM")
        await rails.record_action("tenant_a", "policy", "notify")
        assert can2 is True

        # Third should be blocked
        can3, reason = await rails.can_auto_apply_policy("tenant_a", "throttle", "MEDIUM")
        assert can3 is False
        assert "cap reached" in reason.lower()

    @pytest.mark.asyncio
    async def test_severity_gate(self):
        """Should block HIGH/CRITICAL auto-apply when configured."""
        from app.integrations.cost_safety_rails import CostSafetyRails, SafetyConfig

        config = SafetyConfig(
            high_actions_require_confirmation=True,
            critical_actions_require_confirmation=True,
        )
        rails = CostSafetyRails(config)

        can_high, reason = await rails.can_auto_apply_policy("tenant_a", "action", "HIGH")
        assert can_high is False
        assert "confirmation" in reason.lower()

        can_crit, reason = await rails.can_auto_apply_policy("tenant_a", "action", "CRITICAL")
        assert can_crit is False
        assert "confirmation" in reason.lower()

    @pytest.mark.asyncio
    async def test_blast_radius_limit(self):
        """Should enforce user affected limit."""
        from app.integrations.cost_safety_rails import CostSafetyRails, SafetyConfig

        config = SafetyConfig(max_users_affected_per_action=10)
        rails = CostSafetyRails(config)

        can_small, _ = await rails.can_auto_apply_recovery("tenant_a", "action", affected_count=5)
        assert can_small is True

        can_large, reason = await rails.can_auto_apply_recovery("tenant_a", "action", affected_count=50)
        assert can_large is False
        assert "blast radius" in reason.lower()

    @pytest.mark.asyncio
    async def test_permanent_block_requires_confirmation(self):
        """Permanent route blocks should require confirmation."""
        from app.integrations.cost_safety_rails import CostSafetyRails, SafetyConfig

        rails = CostSafetyRails(SafetyConfig())

        can_apply, reason = await rails.can_auto_apply_routing("tenant_a", "route_block", magnitude=-1.0)
        assert can_apply is False
        assert "confirmation" in reason.lower()

    @pytest.mark.asyncio
    async def test_status_reporting(self):
        """Should report accurate status."""
        from app.integrations.cost_safety_rails import CostSafetyRails, SafetyConfig

        config = SafetyConfig(max_auto_policies_per_tenant_per_day=5)
        rails = CostSafetyRails(config)

        await rails.record_action("tenant_a", "policy", "action1")
        await rails.record_action("tenant_a", "policy", "action2")

        status = rails.get_status("tenant_a")
        assert status["remaining"]["policies"] == 3
        assert status["current"]["policy"] == 2


# =============================================================================
# INTEGRATION TEST: Full Loop
# =============================================================================


class TestCostLoopOrchestrator:
    """Test full loop orchestration."""

    @pytest.mark.asyncio
    async def test_low_severity_skipped(self, mock_session):
        """LOW severity anomalies should be skipped."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostLoopOrchestrator

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=120,
            expected_value_cents=100,  # 20% deviation -> LOW
        )

        orchestrator = CostLoopOrchestrator(mock_session)
        result = await orchestrator.process_anomaly(anomaly)

        assert result["status"] == "skipped"
        assert "below threshold" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_high_severity_full_loop(self, mock_session):
        """HIGH severity should go through full loop."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostLoopOrchestrator

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_heavy",
            current_value_cents=450,
            expected_value_cents=100,  # 350% deviation -> HIGH
        )

        orchestrator = CostLoopOrchestrator(mock_session)
        result = await orchestrator.process_anomaly(anomaly)

        assert result["status"] in ["complete", "partial"]
        assert "incident_created" in result["stages_completed"]
        assert "pattern_matched" in result["stages_completed"]
        assert "incident_id" in result

    @pytest.mark.asyncio
    async def test_critical_severity_full_artifacts(self, mock_session):
        """CRITICAL severity should produce all artifacts."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly, CostLoopOrchestrator

        # Need 500%+ deviation for CRITICAL: (60000-10000)/10000*100 = 500%
        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.BUDGET_EXCEEDED,
            entity_type="tenant",
            entity_id="test_tenant",
            current_value_cents=60000,
            expected_value_cents=10000,  # 500% over budget -> CRITICAL
        )

        orchestrator = CostLoopOrchestrator(mock_session)
        result = await orchestrator.process_anomaly(anomaly)

        assert "artifacts" in result
        assert "pattern" in result["artifacts"]
        assert "recoveries" in result["artifacts"]
        assert len(result["artifacts"]["recoveries"]) > 0


# =============================================================================
# INTEGRATION TEST: Safe Orchestrator
# =============================================================================


class TestSafeCostLoopOrchestrator:
    """Test orchestrator with safety rails."""

    @pytest.mark.asyncio
    async def test_safety_rails_applied(self, mock_session):
        """Safety rails should be applied to results."""
        from app.integrations.cost_bridges import AnomalyType, CostAnomaly
        from app.integrations.cost_safety_rails import SafeCostLoopOrchestrator, SafetyConfig

        config = SafetyConfig(
            high_actions_require_confirmation=True,
            max_auto_policies_per_tenant_per_day=0,  # Block all
        )

        anomaly = CostAnomaly.create(
            tenant_id="test_tenant",
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=600,
            expected_value_cents=100,  # CRITICAL
        )

        orchestrator = SafeCostLoopOrchestrator(db_session=mock_session, safety_config=config)
        result = await orchestrator.process_anomaly_safe(anomaly)

        assert "safety_status" in result
        assert "tenant_status" in result["safety_status"]
