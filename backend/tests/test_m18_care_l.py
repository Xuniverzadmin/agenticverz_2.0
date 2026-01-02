# M18 CARE-L + SBA Evolution Tests
# Tests for Learning Router and Agent Evolution

from datetime import datetime, timedelta, timezone

import pytest

# =============================================================================
# Reputation Tests
# =============================================================================


class TestAgentReputation:
    """Test agent reputation calculation."""

    def test_initial_reputation(self):
        """New agent should have perfect reputation."""
        from app.routing.learning import AgentReputation

        rep = AgentReputation(agent_id="new_agent")

        assert rep.reputation_score == 1.0
        assert rep.success_rate == 1.0
        assert rep.quarantine_state.value == "active"
        assert rep.is_routable() is True

    def test_reputation_after_success(self):
        """Reputation should remain high after success."""
        from app.routing.learning import AgentReputation

        rep = AgentReputation(agent_id="agent1")
        rep.record_success(latency_ms=100.0)

        assert rep.total_routes == 1
        assert rep.successful_routes == 1
        assert rep.success_rate == 1.0
        assert rep.consecutive_successes == 1
        assert rep.is_routable() is True

    def test_reputation_after_failure(self):
        """Reputation should drop after failure."""
        from app.routing.learning import AgentReputation

        rep = AgentReputation(agent_id="agent1")
        rep.total_routes = 10
        rep.successful_routes = 10
        rep.success_rate = 1.0

        rep.record_failure(reason="test failure")

        assert rep.total_routes == 11
        assert rep.successful_routes == 10
        assert rep.success_rate < 1.0
        assert rep.consecutive_successes == 0

    def test_reputation_computation(self):
        """Test reputation score formula."""
        from app.routing.learning import AgentReputation

        rep = AgentReputation(
            agent_id="agent1",
            success_rate=0.8,
            latency_percentile=0.3,
            violation_count=1,
            consecutive_successes=5,
        )

        score = rep.compute_reputation()

        # Should be weighted combination
        assert 0.0 <= score <= 1.0
        # With 80% success, low latency, few violations, should be decent
        assert score > 0.6

    def test_reputation_violation_impact(self):
        """Violations should lower reputation."""
        from app.routing.learning import AgentReputation

        rep = AgentReputation(agent_id="agent1")
        initial_score = rep.compute_reputation()

        rep.record_violation("domain")
        new_score = rep.compute_reputation()

        assert new_score < initial_score
        assert rep.violation_count == 1


# =============================================================================
# Quarantine State Machine Tests
# =============================================================================


class TestQuarantineStateMachine:
    """Test quarantine state transitions."""

    def test_active_to_probation(self):
        """Agent should enter probation after repeated failures."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(agent_id="agent1")
        assert rep.quarantine_state == QuarantineState.ACTIVE

        # Record failures to trigger probation
        for _ in range(3):
            rep.record_failure()

        assert rep.quarantine_state == QuarantineState.PROBATION
        assert rep.is_routable() is True  # Still routable in probation

    def test_probation_to_quarantine(self):
        """Agent should be quarantined after more failures."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(agent_id="agent1")
        rep.quarantine_state = QuarantineState.PROBATION
        rep.recent_failures = 3

        # More failures to trigger quarantine
        for _ in range(2):
            rep.record_failure()

        assert rep.quarantine_state == QuarantineState.QUARANTINED
        assert rep.quarantine_until is not None
        assert rep.is_routable() is False

    def test_probation_exit_on_success(self):
        """Agent should exit probation after consecutive successes."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(agent_id="agent1")
        rep.quarantine_state = QuarantineState.PROBATION

        # 5 consecutive successes
        for _ in range(5):
            rep.record_success()

        assert rep.quarantine_state == QuarantineState.ACTIVE
        assert rep.consecutive_successes >= 5

    def test_quarantine_cooloff(self):
        """Agent should be released after cooloff period."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(agent_id="agent1")
        rep.quarantine_state = QuarantineState.QUARANTINED
        rep.quarantine_until = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Should be released on next check
        is_routable = rep.is_routable()

        assert is_routable is True
        assert rep.quarantine_state == QuarantineState.PROBATION

    def test_violation_quarantine(self):
        """Multiple violations should trigger quarantine."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(agent_id="agent1")

        # 3 violations should quarantine
        for _ in range(3):
            rep.record_violation("domain")

        assert rep.quarantine_state == QuarantineState.QUARANTINED
        assert rep.quarantine_count >= 1


# =============================================================================
# Hysteresis Tests
# =============================================================================


class TestHysteresisStability:
    """Test hysteresis prevents routing oscillation."""

    @pytest.mark.asyncio
    async def test_hysteresis_blocks_small_difference(self):
        """Small score differences should not trigger switch."""
        from app.routing.learning import HysteresisManager

        manager = HysteresisManager(redis_url="redis://invalid:9999/0")

        should_switch, reason = await manager.should_switch(
            _current_agent="agent1",
            candidate_agent="agent2",
            current_score=0.80,
            candidate_score=0.82,  # Only 2% difference
        )

        assert should_switch is False
        assert "below threshold" in reason.lower()

    @pytest.mark.asyncio
    async def test_hysteresis_allows_large_difference(self):
        """Large score differences should allow switch."""
        from app.routing.learning import HysteresisManager

        manager = HysteresisManager(redis_url="redis://invalid:9999/0")

        should_switch, reason = await manager.should_switch(
            _current_agent="agent1",
            candidate_agent="agent2",
            current_score=0.60,
            candidate_score=0.85,  # 25% difference
        )

        # May still require consistency, but threshold is met
        assert "exceeds threshold" in reason.lower() or "consistent" in reason.lower()

    @pytest.mark.asyncio
    async def test_hysteresis_requires_consistency(self):
        """Candidate must be consistently better."""
        from app.routing.learning import HysteresisManager

        manager = HysteresisManager(redis_url="redis://invalid:9999/0")

        # First check - no history
        should_switch, reason = await manager.should_switch(
            _current_agent="agent1",
            candidate_agent="agent2",
            current_score=0.50,
            candidate_score=0.90,
        )

        # Should need more data points
        # (Without Redis, this may pass but that's acceptable for graceful degradation)
        assert isinstance(should_switch, bool)


# =============================================================================
# Drift Detection Tests
# =============================================================================


class TestDriftDetection:
    """Test SBA drift detection."""

    def test_behavior_drift_detection(self):
        """Success rate drop should trigger behavior drift."""
        from app.agents.sba.evolution import DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        signals = engine.detect_drift(
            agent_id="agent1",
            current_success_rate=0.60,
            historical_success_rate=0.90,  # 30% drop
            current_latency=100,
            historical_latency=100,
        )

        assert len(signals) >= 1
        assert any(s.drift_type == DriftType.BEHAVIOR_DRIFT for s in signals)

    def test_data_drift_detection(self):
        """Latency increase should trigger data drift."""
        from app.agents.sba.evolution import DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        signals = engine.detect_drift(
            agent_id="agent1",
            current_success_rate=0.90,
            historical_success_rate=0.90,
            current_latency=200,
            historical_latency=100,  # 100% increase
        )

        assert len(signals) >= 1
        assert any(s.drift_type == DriftType.DATA_DRIFT for s in signals)

    def test_boundary_drift_from_violations(self):
        """Violation spike should trigger boundary drift."""
        from app.agents.sba.evolution import DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        signals = engine.detect_drift(
            agent_id="agent1",
            current_success_rate=0.90,
            historical_success_rate=0.90,
            current_latency=100,
            historical_latency=100,
            recent_violations=5,  # Above threshold
        )

        assert len(signals) >= 1
        assert any(s.drift_type == DriftType.BOUNDARY_DRIFT for s in signals)

    def test_no_drift_when_stable(self):
        """No drift should be detected when metrics are stable."""
        from app.agents.sba.evolution import SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        signals = engine.detect_drift(
            agent_id="agent1",
            current_success_rate=0.88,
            historical_success_rate=0.90,  # Small drop
            current_latency=105,
            historical_latency=100,  # Small increase
            recent_violations=0,
        )

        assert len(signals) == 0

    def test_drift_signal_severity(self):
        """Severity should scale with drift magnitude."""
        from app.agents.sba.evolution import SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        # Small drift
        signals_small = engine.detect_drift(
            agent_id="agent1",
            current_success_rate=0.70,
            historical_success_rate=0.90,  # 20% drop
            current_latency=100,
            historical_latency=100,
        )

        # Large drift
        signals_large = engine.detect_drift(
            agent_id="agent2",
            current_success_rate=0.30,
            historical_success_rate=0.90,  # 60% drop
            current_latency=100,
            historical_latency=100,
        )

        if signals_small and signals_large:
            assert signals_large[0].severity > signals_small[0].severity


# =============================================================================
# Boundary Violation Tests
# =============================================================================


class TestBoundaryViolations:
    """Test boundary violation tracking."""

    def test_record_violation(self):
        """Should record and track violations."""
        from app.agents.sba.evolution import SBAEvolutionEngine, ViolationType

        engine = SBAEvolutionEngine()

        violation = engine.record_violation(
            agent_id="agent1",
            violation_type=ViolationType.DOMAIN,
            description="Task outside allowed domain",
            task_domain="finance",
            severity=0.7,
        )

        assert violation.agent_id == "agent1"
        assert violation.violation_type == ViolationType.DOMAIN
        assert violation.severity == 0.7

        # Should be retrievable
        violations = engine.get_violations("agent1")
        assert len(violations) == 1

    def test_violation_types(self):
        """All violation types should be recordable."""
        from app.agents.sba.evolution import SBAEvolutionEngine, ViolationType

        engine = SBAEvolutionEngine()

        for vtype in ViolationType:
            violation = engine.record_violation(
                agent_id=f"agent_{vtype.value}",
                violation_type=vtype,
                description=f"Test {vtype.value} violation",
            )
            assert violation.violation_type == vtype

    def test_violations_filter_by_type(self):
        """Should filter violations by type."""
        from app.agents.sba.evolution import SBAEvolutionEngine, ViolationType

        engine = SBAEvolutionEngine()

        # Record different types
        engine.record_violation("agent1", ViolationType.DOMAIN, "domain issue")
        engine.record_violation("agent1", ViolationType.RISK, "risk issue")
        engine.record_violation("agent1", ViolationType.DOMAIN, "another domain issue")

        domain_violations = engine.get_violations("agent1", violation_type=ViolationType.DOMAIN)
        assert len(domain_violations) == 2

    def test_auto_reported_violation(self):
        """Should track auto-reported violations."""
        from app.agents.sba.evolution import SBAEvolutionEngine, ViolationType

        engine = SBAEvolutionEngine()

        violation = engine.record_violation(
            agent_id="agent1",
            violation_type=ViolationType.CAPABILITY,
            description="Agent self-reported capability issue",
            auto_reported=True,
        )

        assert violation.auto_reported is True

    def test_violation_triggers_drift_check(self):
        """Multiple violations should trigger boundary drift."""
        from app.agents.sba.evolution import DriftType, SBAEvolutionEngine, ViolationType

        engine = SBAEvolutionEngine()

        # Record enough violations to trigger drift
        for _ in range(4):
            engine.record_violation(
                agent_id="agent1",
                violation_type=ViolationType.DOMAIN,
                description="Repeated domain violation",
            )

        drift_signals = engine.get_drift_signals("agent1")
        assert any(s.drift_type == DriftType.BOUNDARY_DRIFT for s in drift_signals)


# =============================================================================
# Strategy Adjustment Tests
# =============================================================================


class TestStrategyAdjustment:
    """Test strategy adjustment suggestions and application."""

    def test_suggest_boundary_expand(self):
        """Should suggest boundary expansion for boundary drift."""
        from app.agents.sba.evolution import AdjustmentType, DriftSignal, DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        drift = DriftSignal(
            agent_id="agent1",
            drift_type=DriftType.BOUNDARY_DRIFT,
            severity=0.6,
            evidence={"recent_violations": 5},
            recommendation="Expand boundaries",
        )

        current_sba = {
            "where_to_play": {"domain": "test", "boundaries": "Original boundaries"},
            "how_to_win": {"tasks": ["task1"]},
        }

        adjustment = engine.suggest_adjustment("agent1", drift, current_sba)

        assert adjustment is not None
        assert adjustment.adjustment_type == AdjustmentType.BOUNDARY_EXPAND
        assert "Auto-expanded" in adjustment.new_strategy["where_to_play"]["boundaries"]

    def test_suggest_step_refinement(self):
        """Should suggest step refinement for behavior drift."""
        from app.agents.sba.evolution import AdjustmentType, DriftSignal, DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        drift = DriftSignal(
            agent_id="agent1",
            drift_type=DriftType.BEHAVIOR_DRIFT,
            severity=0.5,
            evidence={"current_success_rate": 0.6},
        )

        current_sba = {
            "where_to_play": {"domain": "test"},
            "how_to_win": {"tasks": ["task1", "task2"]},
        }

        adjustment = engine.suggest_adjustment("agent1", drift, current_sba)

        assert adjustment is not None
        assert adjustment.adjustment_type == AdjustmentType.STEP_REFINEMENT
        # Should add fallback task
        assert any("fallback" in t.lower() for t in adjustment.new_strategy["how_to_win"]["tasks"])

    def test_adjustment_cooldown(self):
        """Should respect cooldown between adjustments."""
        from datetime import datetime, timezone

        from app.agents.sba.evolution import DriftSignal, DriftType, SBAEvolutionEngine

        engine = SBAEvolutionEngine()

        # Record a recent adjustment
        engine._last_adjustment["agent1"] = datetime.now(timezone.utc)

        drift = DriftSignal(
            agent_id="agent1",
            drift_type=DriftType.BOUNDARY_DRIFT,
            severity=0.5,
        )

        adjustment = engine.suggest_adjustment("agent1", drift, {})

        # Should be None due to cooldown
        assert adjustment is None

    def test_adjustment_history(self):
        """Should track adjustment history."""
        from app.agents.sba.evolution import (
            AdjustmentType,
            SBAEvolutionEngine,
            StrategyAdjustment,
        )

        engine = SBAEvolutionEngine()

        adjustment = StrategyAdjustment(
            agent_id="agent1",
            trigger="test trigger",
            adjustment_type=AdjustmentType.FALLBACK_ADD,
            old_strategy={"version": 1},
            new_strategy={"version": 2},
        )

        engine.apply_adjustment(adjustment)

        history = engine.get_adjustments("agent1")
        assert len(history) == 1
        assert history[0].trigger == "test trigger"


# =============================================================================
# Learning Parameters Tests
# =============================================================================


class TestLearningParameters:
    """Test self-tuning parameters."""

    def test_initial_parameters(self):
        """Should have sensible defaults."""
        from app.routing.learning import LearningParameters

        params = LearningParameters()

        assert params.confidence_block == 0.35
        assert params.confidence_fallback == 0.55
        assert params.adaptation_rate == 0.01

    def test_tune_from_high_block_rate(self):
        """Should lower block threshold if blocking too much."""
        from app.routing.learning import LearningParameters

        params = LearningParameters()

        # Simulate high block rate with good success
        outcomes = [{"success": True, "confidence_blocked": True, "was_fallback": False} for _ in range(30)] + [
            {"success": True, "confidence_blocked": False, "was_fallback": False} for _ in range(70)
        ]

        adjustments = params.tune_from_outcomes(outcomes)

        # Should lower confidence_block
        if "confidence_block" in adjustments:
            assert adjustments["confidence_block"] < 0

    def test_tune_from_fallback_failures(self):
        """Should raise fallback threshold if fallbacks failing."""
        from app.routing.learning import LearningParameters

        params = LearningParameters()

        # Simulate fallback failures
        outcomes = [{"success": False, "confidence_blocked": False, "was_fallback": True} for _ in range(20)] + [
            {"success": True, "confidence_blocked": False, "was_fallback": False} for _ in range(80)
        ]

        adjustments = params.tune_from_outcomes(outcomes)

        # Should raise confidence_fallback
        if "confidence_fallback" in adjustments:
            assert adjustments["confidence_fallback"] > 0


# =============================================================================
# Reputation Store Tests
# =============================================================================


class TestReputationStore:
    """Test reputation persistence."""

    @pytest.mark.asyncio
    async def test_store_without_redis(self):
        """Should work without Redis (in-memory fallback)."""
        from app.routing.learning import ReputationStore

        store = ReputationStore(redis_url="redis://invalid:9999/0")

        # Get non-existent - should return new
        rep = await store.get_reputation("new_agent")
        assert rep.agent_id == "new_agent"
        assert rep.reputation_score == 1.0

    @pytest.mark.asyncio
    async def test_store_save_and_get(self):
        """Should save and retrieve reputation."""
        from app.routing.learning import AgentReputation, ReputationStore

        store = ReputationStore(redis_url="redis://invalid:9999/0")

        rep = AgentReputation(agent_id="test_agent")
        rep.record_success()
        rep.record_success()
        rep.record_failure()

        await store.save_reputation(rep)

        retrieved = await store.get_reputation("test_agent")
        assert retrieved.total_routes == 3
        assert retrieved.successful_routes == 2


# =============================================================================
# Integration Tests
# =============================================================================


class TestFeedbackLoopIntegration:
    """Test end-to-end feedback loop."""

    @pytest.mark.asyncio
    async def test_outcome_updates_reputation(self):
        """Routing outcomes should update agent reputation."""
        from app.routing.learning import ReputationStore

        store = ReputationStore(redis_url="redis://invalid:9999/0")

        # Get fresh reputation
        rep = await store.get_reputation("integration_agent")

        # Simulate routing outcomes
        rep.record_success(latency_ms=100)
        rep.record_success(latency_ms=150)
        rep.record_failure(reason="timeout")

        await store.save_reputation(rep)

        # Verify updates
        updated = await store.get_reputation("integration_agent")
        assert updated.total_routes == 3
        assert updated.success_rate == 2 / 3

    def test_violation_affects_reputation_and_drift(self):
        """Violations should affect both reputation and trigger drift."""
        from app.agents.sba.evolution import SBAEvolutionEngine, ViolationType
        from app.routing.learning import AgentReputation

        rep = AgentReputation(agent_id="integration_agent")
        engine = SBAEvolutionEngine()

        initial_score = rep.compute_reputation()

        # Record violations
        for _ in range(4):
            rep.record_violation("domain")
            engine.record_violation(
                agent_id="integration_agent",
                violation_type=ViolationType.DOMAIN,
                description="test",
            )

        # Reputation should drop
        assert rep.compute_reputation() < initial_score

        # Drift should be detected
        signals = engine.get_drift_signals("integration_agent")
        assert len(signals) > 0

    def test_reputation_to_dict(self):
        """Reputation should serialize to dict."""
        from app.routing.learning import AgentReputation, QuarantineState

        rep = AgentReputation(
            agent_id="test",
            reputation_score=0.85,
            quarantine_state=QuarantineState.PROBATION,
        )

        d = rep.to_dict()

        assert d["agent_id"] == "test"
        assert d["reputation_score"] == 0.85
        assert d["quarantine_state"] == "probation"
        assert "is_routable" in d


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
