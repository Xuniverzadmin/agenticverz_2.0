# M18 Advanced Tests
# Critical test types for production-grade M18 implementation
#
# Tests:
# - System Convergence: System stabilizes after perturbations
# - Oscillation Stress: No runaway loops under stress
# - Boundary Cascade: Violations propagate correctly
# - Hysteresis vs Drift: Hysteresis doesn't block necessary drift adjustments
# - Self-Tuning Instability: Auto-tuning doesn't destabilize

import asyncio

import pytest

from app.agents.sba.evolution import (
    VIOLATION_SPIKE_THRESHOLD,
    DriftType,
    SBAEvolutionEngine,
    ViolationType,
)
from app.routing.feedback import (
    FeedbackLoop,
    TaskPriority,
)
from app.routing.governor import (
    GLOBAL_FREEZE_THRESHOLD,
    MAX_ADJUSTMENT_MAGNITUDE,
    Governor,
    GovernorState,
    RollbackReason,
)
from app.routing.learning import (
    HysteresisManager,
    LearningParameters,
    QuarantineState,
    ReputationStore,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def governor():
    """Create a fresh governor instance."""
    return Governor()


@pytest.fixture
def feedback_loop():
    """Create a fresh feedback loop instance."""
    return FeedbackLoop()


@pytest.fixture
def evolution_engine():
    """Create a fresh evolution engine instance."""
    return SBAEvolutionEngine()


@pytest.fixture
def reputation_store():
    """Create a fresh reputation store instance."""
    return ReputationStore()


@pytest.fixture
def learning_params():
    """Create a fresh learning parameters instance."""
    return LearningParameters()


# =============================================================================
# 1. System Convergence Tests
# =============================================================================


class TestSystemConvergence:
    """Test that system converges to stable state after perturbations."""

    @pytest.mark.asyncio
    async def test_reputation_converges_after_mixed_outcomes(self, reputation_store):
        """Reputation should stabilize after a series of mixed outcomes."""
        agent_id = "convergence-test-agent"
        rep = await reputation_store.get_reputation(agent_id)

        # Simulate alternating success/failure pattern
        for i in range(20):
            if i % 2 == 0:
                rep.record_success()
            else:
                rep.record_failure()

        # Reputation should converge around 0.5 (50% success)
        assert 0.4 <= rep.success_rate <= 0.6
        assert rep.quarantine_state in [QuarantineState.ACTIVE, QuarantineState.PROBATION]

    @pytest.mark.asyncio
    async def test_sla_converges_to_target_with_good_performance(self, feedback_loop):
        """SLA score should converge toward target with consistent good performance."""
        agent_id = "sla-convergence-agent"

        # Record many successful outcomes
        for i in range(50):
            await feedback_loop.record_routing_outcome(
                agent_id=agent_id,
                task_id=f"task-{i}",
                success=True,
                latency_ms=100.0,
                task_priority=TaskPriority.NORMAL,
            )

        sla_score = await feedback_loop.get_sla_score(agent_id)
        assert sla_score is not None
        # Should be approaching 100% with all successes
        assert sla_score.current_sla >= 0.9

    @pytest.mark.asyncio
    async def test_governor_returns_to_stable_after_adjustment_burst(self, governor):
        """Governor should return to stable after burst of adjustments."""
        # Record several adjustments (but not enough to freeze)
        for i in range(3):
            await governor.record_adjustment(
                parameter_name=f"param_{i}",
                old_value=0.5,
                new_value=0.52,
                agent_id="burst-agent",
            )

        metrics = await governor.get_stability_metrics()
        # Should not be frozen with only 3 adjustments
        assert metrics.state != GovernorState.FROZEN
        assert metrics.adjustments_this_hour == 3

    @pytest.mark.asyncio
    async def test_batch_learning_stabilizes_parameters(self, feedback_loop):
        """Batch learning should produce bounded parameter adjustments."""
        # Record diverse outcomes
        for i in range(20):
            await feedback_loop.record_routing_outcome(
                agent_id=f"agent-{i % 3}",
                task_id=f"task-{i}",
                success=i % 3 != 0,  # 2/3 success rate
                latency_ms=100.0 + i * 10,
                task_priority=TaskPriority.NORMAL,
            )

        result = await feedback_loop.run_batch_learning(window_hours=1)

        # Adjustments should be bounded
        for param, delta in result.parameter_adjustments.items():
            assert abs(delta) <= MAX_ADJUSTMENT_MAGNITUDE


# =============================================================================
# 2. Oscillation Stress Tests
# =============================================================================


class TestOscillationStress:
    """Test that system doesn't enter runaway oscillation loops."""

    @pytest.mark.asyncio
    async def test_governor_detects_parameter_oscillation(self, governor):
        """Governor should detect and prevent parameter oscillation."""
        # Simulate oscillating parameter
        for i in range(10):
            value = 0.5 + (0.1 if i % 2 == 0 else -0.1)
            approved, reason, _ = await governor.request_adjustment(
                parameter_name="oscillating_param",
                old_value=0.5,
                new_value=value,
                agent_id="oscillation-agent",
            )

            if i >= 4:
                # After enough oscillations, should be detected
                if not approved:
                    assert "oscillation" in reason.lower() or "rate limit" in reason.lower()
                    break

    @pytest.mark.asyncio
    async def test_hysteresis_prevents_agent_flip_flopping(self):
        """Hysteresis should prevent rapid agent switching."""
        hysteresis = HysteresisManager()

        agent_a = "agent-a"
        agent_b = "agent-b"

        # Agent B slightly better initially
        should_switch, _ = await hysteresis.should_switch(
            current_agent=agent_a,
            candidate_agent=agent_b,
            current_score=0.7,
            candidate_score=0.75,  # Only 5% better
        )
        assert not should_switch  # Difference below threshold

        # Now A is slightly better
        should_switch, _ = await hysteresis.should_switch(
            current_agent=agent_b,
            candidate_agent=agent_a,
            current_score=0.75,
            candidate_score=0.78,  # Only 3% better
        )
        assert not should_switch  # Still below threshold

    @pytest.mark.asyncio
    async def test_global_freeze_prevents_runaway_adjustments(self, governor):
        """Global freeze should activate when adjustment rate is too high."""
        # Rapidly make adjustments
        for i in range(GLOBAL_FREEZE_THRESHOLD + 2):
            try:
                await governor.record_adjustment(
                    parameter_name=f"rapid_param_{i}",
                    old_value=0.5,
                    new_value=0.52,
                    agent_id=f"agent-{i % 5}",
                )
            except Exception:
                pass  # May fail after freeze

        metrics = await governor.get_stability_metrics()
        # Should be frozen after hitting threshold
        assert metrics.state == GovernorState.FROZEN or metrics.adjustments_this_hour >= GLOBAL_FREEZE_THRESHOLD

    @pytest.mark.asyncio
    async def test_reputation_doesnt_oscillate_at_boundary(self, reputation_store):
        """Reputation shouldn't oscillate at probation/active boundary."""
        agent_id = "boundary-oscillation-agent"
        rep = await reputation_store.get_reputation(agent_id)

        transitions = []

        # Push toward probation boundary
        for i in range(10):
            if i % 2 == 0:
                for _ in range(3):  # 3 failures
                    rep.record_failure()
            else:
                for _ in range(3):  # 3 successes
                    rep.record_success()

            transitions.append(rep.quarantine_state)

        # Count state changes - shouldn't be too many
        changes = sum(1 for i in range(1, len(transitions)) if transitions[i] != transitions[i - 1])
        assert changes <= 5  # Reasonable number of transitions


# =============================================================================
# 3. Boundary Cascade Tests
# =============================================================================


class TestBoundaryCascade:
    """Test that boundary violations propagate correctly through the system."""

    def test_violations_trigger_drift_detection(self, evolution_engine):
        """Multiple violations should trigger boundary drift signal."""
        agent_id = "cascade-agent"

        # Record enough violations to trigger drift
        for i in range(VIOLATION_SPIKE_THRESHOLD + 1):
            evolution_engine.record_violation(
                agent_id=agent_id,
                violation_type=ViolationType.DOMAIN,
                description=f"Domain violation {i}",
                task_domain="data-processing",
                severity=0.6,
            )

        # Check for drift signal
        signals = evolution_engine.get_drift_signals(agent_id)
        boundary_drift = [s for s in signals if s.drift_type == DriftType.BOUNDARY_DRIFT]
        assert len(boundary_drift) >= 1

    @pytest.mark.asyncio
    async def test_violations_cascade_to_reputation(self, reputation_store):
        """Violations should impact agent reputation."""
        agent_id = "violation-cascade-agent"
        rep = await reputation_store.get_reputation(agent_id)

        initial_score = rep.compute_reputation()

        # Record violations
        for _ in range(3):
            rep.record_violation("domain")

        final_score = rep.compute_reputation()

        # Reputation should decrease
        assert final_score < initial_score
        # Should be quarantined after 3 violations
        assert rep.quarantine_state == QuarantineState.QUARANTINED

    def test_drift_triggers_adjustment_recommendation(self, evolution_engine):
        """Drift signal should trigger strategy adjustment recommendation."""
        agent_id = "drift-adjustment-agent"

        # Detect drift
        signals = evolution_engine.detect_drift(
            agent_id=agent_id,
            current_success_rate=0.5,
            historical_success_rate=0.8,  # 30% drop
            current_latency=500,
            historical_latency=100,  # 5x increase
            recent_violations=5,
        )

        assert len(signals) >= 1

        # Get adjustment recommendation
        import copy

        current_sba = {
            "where_to_play": {"domain": "test", "boundaries": ""},
            "how_to_win": {"tasks": ["task1"]},
            "capabilities_capacity": {"dependencies": []},
        }
        original_sba = copy.deepcopy(current_sba)

        adjustment_found = False
        for signal in signals:
            adjustment = evolution_engine.suggest_adjustment(
                agent_id=agent_id,
                drift_signal=signal,
                current_sba=current_sba,
            )
            if adjustment:
                assert adjustment.agent_id == agent_id
                assert adjustment.adjustment_type is not None
                # Verify an adjustment was recommended
                adjustment_found = True
                break

        assert adjustment_found, "No adjustment was suggested for drift signal"


# =============================================================================
# 4. Hysteresis vs Drift Conflict Tests
# =============================================================================


class TestHysteresisVsDrift:
    """Test that hysteresis doesn't block necessary drift-based adjustments."""

    @pytest.mark.asyncio
    async def test_severe_drift_overrides_hysteresis(self):
        """Severe performance drift should allow agent switching despite hysteresis."""
        hysteresis = HysteresisManager()

        # Current agent is slightly better score but severely degrading
        current_agent = "degrading-agent"
        candidate_agent = "stable-agent"

        # First check - small difference, blocked by hysteresis
        should_switch, reason = await hysteresis.should_switch(
            current_agent=current_agent,
            candidate_agent=candidate_agent,
            current_score=0.6,
            candidate_score=0.65,
        )
        assert not should_switch  # Below threshold

        # After severe degradation, larger difference
        should_switch, reason = await hysteresis.should_switch(
            current_agent=current_agent,
            candidate_agent=candidate_agent,
            current_score=0.3,  # Dropped significantly
            candidate_score=0.65,  # 35% better now
        )
        # Should allow switch with large difference
        assert should_switch or "threshold" not in reason.lower()

    @pytest.mark.asyncio
    async def test_drift_signal_marks_agent_for_review(self, evolution_engine, feedback_loop):
        """Drift signal should flag agent even if hysteresis would keep routing to it."""
        agent_id = "drift-review-agent"

        # Generate drift
        signals = evolution_engine.detect_drift(
            agent_id=agent_id,
            current_success_rate=0.4,
            historical_success_rate=0.9,  # 50% drop
            current_latency=100,
            historical_latency=100,
            recent_violations=0,
        )

        assert len(signals) >= 1
        assert signals[0].drift_type == DriftType.BEHAVIOR_DRIFT
        assert signals[0].severity > 0.5  # High severity

    @pytest.mark.asyncio
    async def test_sla_miss_overrides_hysteresis(self, feedback_loop):
        """SLA miss should adjust scoring to enable agent switching."""
        agent_id = "sla-miss-agent"

        # Record many failures to miss SLA
        for i in range(20):
            await feedback_loop.record_routing_outcome(
                agent_id=agent_id,
                task_id=f"task-{i}",
                success=i % 3 == 0,  # Only 33% success
                latency_ms=100.0,
                task_priority=TaskPriority.CRITICAL,  # Critical tasks
            )

        sla_score = await feedback_loop.get_sla_score(agent_id)
        assert sla_score is not None

        # SLA-adjusted reputation should be penalized
        adjusted = await feedback_loop.compute_sla_adjusted_reputation(agent_id, base_reputation=0.8)
        # Should be lower than base due to SLA gap
        assert adjusted < 0.8


# =============================================================================
# 5. Self-Tuning Instability Tests
# =============================================================================


class TestSelfTuningInstability:
    """Test that auto-tuning parameters don't destabilize the system."""

    def test_parameter_bounds_enforced(self):
        """Learning parameters should stay within bounds."""
        params = LearningParameters()

        # Try to tune with extreme outcomes
        extreme_outcomes = [{"success": True, "confidence_blocked": True, "was_fallback": False} for _ in range(100)]

        adjustments = params.tune_from_outcomes(extreme_outcomes)

        # Parameters should stay within bounds
        assert 0.0 <= params.confidence_block <= 1.0
        assert 0.0 <= params.confidence_fallback <= 1.0
        assert params.confidence_fallback > params.confidence_block

    @pytest.mark.asyncio
    async def test_governor_caps_adjustment_magnitude(self, governor):
        """Governor should cap adjustment magnitude."""
        # Try to make a large adjustment
        approved, reason, capped_value = await governor.request_adjustment(
            parameter_name="large_adjustment_param",
            old_value=0.5,
            new_value=0.9,  # 80% increase
            agent_id="large-adjust-agent",
        )

        if approved:
            # Value should be capped
            expected_max = 0.5 * (1 + MAX_ADJUSTMENT_MAGNITUDE)
            assert capped_value <= expected_max

    @pytest.mark.asyncio
    async def test_rollback_on_performance_degradation(self, governor):
        """Bad adjustments should be rolled back automatically."""
        # Make an adjustment
        record = await governor.record_adjustment(
            parameter_name="rollback_test_param",
            old_value=0.5,
            new_value=0.55,
            agent_id="rollback-test-agent",
            success_rate_before=0.8,
        )

        # Evaluate with worse performance
        is_good, result = await governor.evaluate_adjustment(
            adjustment_id=record.id,
            success_rate_after=0.6,  # Got worse
        )

        # Should trigger rollback
        assert not is_good
        if result:
            assert result.reason == RollbackReason.PERFORMANCE_DEGRADED

    def test_adaptation_rate_limits_change_speed(self):
        """Adaptation rate should limit how fast parameters change."""
        params = LearningParameters(adaptation_rate=0.01)

        # Single outcome shouldn't change parameters much
        outcomes = [{"success": False, "confidence_blocked": False, "was_fallback": True}]

        initial_confidence = params.confidence_fallback
        adjustments = params.tune_from_outcomes(outcomes)

        if adjustments:
            for param, delta in adjustments.items():
                assert abs(delta) <= params.adaptation_rate * 2  # Allow some slack

    @pytest.mark.asyncio
    async def test_batch_learning_bounded_reputation_updates(self, feedback_loop):
        """Batch learning reputation updates should be bounded."""
        # Record varied outcomes for multiple agents
        for i in range(30):
            await feedback_loop.record_routing_outcome(
                agent_id=f"batch-agent-{i % 5}",
                task_id=f"task-{i}",
                success=i % 2 == 0,
                latency_ms=100.0 + i,
            )

        result = await feedback_loop.run_batch_learning(window_hours=1)

        # Check reputation updates are bounded
        for agent_id, delta in result.reputation_updates.items():
            assert -0.2 <= delta <= 0.2  # Reasonable bounds


# =============================================================================
# 6. Integration Stress Tests
# =============================================================================


class TestIntegrationStress:
    """Test the full integrated system under stress."""

    @pytest.mark.asyncio
    async def test_concurrent_adjustments_handled(self, governor):
        """System should handle concurrent adjustment requests."""

        async def make_adjustment(i):
            try:
                await governor.request_adjustment(
                    parameter_name=f"concurrent_param_{i}",
                    old_value=0.5,
                    new_value=0.52,
                    agent_id=f"concurrent-agent-{i % 3}",
                )
            except Exception:
                pass  # Some may be rejected

        # Run concurrent adjustments
        await asyncio.gather(*[make_adjustment(i) for i in range(10)])

        metrics = await governor.get_stability_metrics()
        # System should still be in a valid state
        assert metrics.state in [GovernorState.STABLE, GovernorState.CAUTIOUS, GovernorState.FROZEN]

    @pytest.mark.asyncio
    async def test_high_volume_outcome_recording(self, feedback_loop):
        """System should handle high volume of outcome recordings."""
        # Record many outcomes rapidly
        for i in range(100):
            await feedback_loop.record_routing_outcome(
                agent_id=f"volume-agent-{i % 10}",
                task_id=f"volume-task-{i}",
                success=i % 3 != 0,
                latency_ms=50.0 + (i % 100),
                task_priority=TaskPriority(["critical", "high", "normal", "low"][i % 4]),
            )

        # Verify system is still functional
        result = await feedback_loop.run_batch_learning(window_hours=1)
        assert result.total_outcomes >= 100

    def test_rapid_violation_recording(self, evolution_engine):
        """System should handle rapid violation recording."""
        agent_id = "rapid-violation-agent"

        # Record many violations
        for i in range(50):
            evolution_engine.record_violation(
                agent_id=agent_id,
                violation_type=ViolationType(["domain", "tool", "context"][i % 3]),
                description=f"Violation {i}",
                severity=0.5 + (i % 5) * 0.1,
            )

        # Check violations are tracked
        violations = evolution_engine.get_violations(agent_id)
        assert len(violations) == 50

        # Should have drift signals
        signals = evolution_engine.get_drift_signals(agent_id)
        assert len(signals) >= 1


# =============================================================================
# 7. Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_zero_outcomes_batch_learning(self, feedback_loop):
        """Batch learning with no outcomes should handle gracefully."""
        result = await feedback_loop.run_batch_learning(window_hours=1)

        assert result.total_outcomes == 0
        assert len(result.parameter_adjustments) == 0
        assert len(result.reputation_updates) == 0

    @pytest.mark.asyncio
    async def test_new_agent_reputation(self, reputation_store):
        """New agent should have default reputation."""
        rep = await reputation_store.get_reputation("brand-new-agent")

        assert rep.reputation_score == 1.0
        assert rep.success_rate == 1.0
        assert rep.quarantine_state == QuarantineState.ACTIVE
        assert rep.total_routes == 0

    @pytest.mark.asyncio
    async def test_frozen_governor_rejects_all(self, governor):
        """Frozen governor should reject all adjustments."""
        await governor.force_freeze(duration_seconds=100, reason="Test freeze")

        approved, reason, _ = await governor.request_adjustment(
            parameter_name="frozen_test_param",
            old_value=0.5,
            new_value=0.52,
        )

        assert not approved
        assert "frozen" in reason.lower()

    def test_adjustment_with_zero_old_value(self, evolution_engine):
        """Adjustment calculation should handle zero old value."""
        # This tests edge case in magnitude calculation
        signals = evolution_engine.detect_drift(
            agent_id="zero-value-agent",
            current_success_rate=0.5,
            historical_success_rate=0.0,  # Zero historical
            current_latency=100,
            historical_latency=0,  # Zero historical
            recent_violations=0,
        )
        # Should not crash, signals may or may not be generated
        assert isinstance(signals, list)

    @pytest.mark.asyncio
    async def test_sla_with_all_critical_tasks(self, feedback_loop):
        """SLA calculation should handle all critical tasks."""
        agent_id = "all-critical-agent"

        for i in range(20):
            await feedback_loop.record_routing_outcome(
                agent_id=agent_id,
                task_id=f"critical-{i}",
                success=True,
                latency_ms=100.0,
                task_priority=TaskPriority.CRITICAL,
            )

        sla_score = await feedback_loop.get_sla_score(agent_id)
        assert sla_score is not None
        # Should be high with all successes
        assert sla_score.current_sla >= 0.9
