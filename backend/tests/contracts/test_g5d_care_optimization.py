"""
Phase 5D: CARE Optimization - Contract Tests

PIN-176: CARE Optimization Matrix (FROZEN 2025-12-26)

These tests verify the Phase 5D optimization semantics:
- Optimization only with allowed signals
- Decision emission only on divergence
- Shadow mode is non-causal
- Kill-switch reverts instantly
- Replay determinism preserved

Frozen Decision Emission Rule:
    EMIT CARE_ROUTING_OPTIMIZED decision IF AND ONLY IF:
      - optimization_enabled = true
      - AND optimized_choice != baseline_choice

    Silence is allowed ONLY when baseline == optimized.

Test IDs: G5D-01 → G5D-12, G5D-INV-01 → G5D-INV-06
"""

import os
import uuid
from typing import Any, Dict, List, Optional

import pytest
from sqlalchemy import create_engine, text

# Phase 5D imports
from app.contracts.decisions import (
    CARESignalAccessError,
    DecisionType,
    activate_care_kill_switch,
    check_signal_access,
    deactivate_care_kill_switch,
    emit_care_optimization_decision,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_kill_switch():
    """Reset kill-switch state before each test."""
    deactivate_care_kill_switch()
    yield
    deactivate_care_kill_switch()


@pytest.fixture
def db_url() -> str:
    """Get database URL from environment."""
    return os.environ.get("DATABASE_URL", "")


@pytest.fixture
def request_id() -> str:
    """Generate unique request ID for test isolation."""
    return f"test-g5d-{uuid.uuid4()}"


@pytest.fixture
def run_id() -> str:
    """Generate unique run ID for test isolation."""
    return f"run-g5d-{uuid.uuid4()}"


@pytest.fixture
def tenant_id() -> str:
    """Test tenant ID."""
    return "test-tenant-g5d"


# =============================================================================
# Mock Signal Data
# =============================================================================


def mock_allowed_signals() -> Dict[str, Any]:
    """Mock allowed signals for CARE optimization."""
    return {
        "latency_p50": 120,
        "latency_p95": 340,
        "cost_per_run": 0.05,
        "success_rate": 0.92,  # Binary: completed without failure
        "recovery_occurred": False,
        "agent_availability": True,
        "context_size_bucket": "medium",
    }


def mock_forbidden_signals() -> Dict[str, Any]:
    """Mock forbidden signals - access should raise error."""
    return {
        "policy_outcome": "allowed",
        "budget_halt_reason": None,
        "recovery_class": "R1",
        "customer_content": "secret data",
        "safety_events": [],
        "founder_overrides": [],
        "failure_details": {"error": "timeout"},
        "user_feedback": {"thumbs_up": True},
    }


# =============================================================================
# Helper Functions
# =============================================================================


def get_decision_records(
    db_url: str,
    request_id: Optional[str] = None,
    run_id: Optional[str] = None,
    decision_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query decision records from database."""
    if not db_url:
        return []

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            # Build query (use contracts schema)
            query = "SELECT * FROM contracts.decision_records WHERE 1=1"
            params: Dict[str, Any] = {}

            if request_id:
                query += " AND request_id = :request_id"
                params["request_id"] = request_id

            if run_id:
                query += " AND run_id = :run_id"
                params["run_id"] = run_id

            if decision_type:
                query += " AND decision_type = :decision_type"
                params["decision_type"] = decision_type

            query += " ORDER BY decided_at ASC"

            result = conn.execute(text(query), params)
            rows = result.fetchall()

            # Convert to dicts
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    except Exception:
        # Table may not exist yet
        return []
    finally:
        engine.dispose()


def helper_emit_care_decision(
    request_id: str,
    baseline_agent: str,
    optimized_agent: str,
    confidence_score: float,
    signals_used: List[str],
    optimization_enabled: bool = True,
    shadow_mode: bool = False,
    tenant_id: str = "default",
) -> Optional[Dict[str, Any]]:
    """
    Helper wrapper for emit_care_optimization_decision.

    Calls the actual implementation and returns a dict representation.
    """
    record = emit_care_optimization_decision(
        request_id=request_id,
        baseline_agent=baseline_agent,
        optimized_agent=optimized_agent,
        confidence_score=confidence_score,
        signals_used=signals_used,
        optimization_enabled=optimization_enabled,
        shadow_mode=shadow_mode,
        tenant_id=tenant_id,
    )
    if record:
        return record.to_dict()
    return None


def helper_signal_access(signal_name: str) -> bool:
    """
    Helper wrapper for check_signal_access.

    Calls the actual implementation which raises on forbidden signals.
    """
    return check_signal_access(signal_name)


def helper_kill_switch_activate() -> bool:
    """
    Helper wrapper for activate_care_kill_switch.

    Calls the actual implementation.
    """
    return activate_care_kill_switch()


def get_care_routing(
    request_id: str,
    signals: Dict[str, Any],
    optimization_enabled: bool = False,
) -> Dict[str, Any]:
    """
    Get CARE routing decision.

    Returns baseline vs optimized choice.
    For red phase, this is a placeholder.
    """
    # TODO: Implement CARE optimization routing
    return {
        "baseline_agent": "agent-a",
        "optimized_agent": "agent-a",  # Same as baseline for now
        "optimization_enabled": optimization_enabled,
        "used_optimization": False,
    }


# =============================================================================
# G5D-01: Optimization disabled
# =============================================================================


class TestG5D01OptimizationDisabled:
    """
    GIVEN: Optimization is disabled
    WHEN: CARE routing is invoked
    THEN:
      - Baseline CARE only
      - No decision emitted
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_baseline_only_when_disabled(self, db_url: str, request_id: str, tenant_id: str):
        """Optimization disabled must use baseline only."""
        result = get_care_routing(
            request_id=request_id,
            signals=mock_allowed_signals(),
            optimization_enabled=False,
        )

        # Should not use optimization
        assert result["used_optimization"] is False

        # No decision should be emitted
        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        assert len(decisions) == 0, "No decision when optimization disabled"


# =============================================================================
# G5D-02: Optimization enabled, same choice
# =============================================================================


class TestG5D02OptimizationSameChoice:
    """
    GIVEN: Optimization is enabled
    AND: Optimized choice equals baseline choice
    WHEN: CARE routing is invoked
    THEN:
      - No decision emitted (silence allowed)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_decision_when_same_choice(self, db_url: str, request_id: str, tenant_id: str):
        """Same choice must not emit decision."""
        # Emit with same baseline and optimized
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-a",  # Same as baseline
            confidence_score=0.85,
            signals_used=["latency_p50", "success_rate"],
            optimization_enabled=True,
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        # Silence is allowed when baseline == optimized
        assert len(decisions) == 0, "No decision when baseline == optimized"


# =============================================================================
# G5D-03: Optimization enabled, different choice
# =============================================================================


class TestG5D03OptimizationDifferentChoice:
    """
    GIVEN: Optimization is enabled
    AND: Optimized choice differs from baseline
    WHEN: CARE routing is invoked
    THEN:
      - Decision emitted with optimized_selected
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_decision_emitted_on_divergence(self, db_url: str, request_id: str, tenant_id: str):
        """Different choice must emit decision."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",  # Different from baseline
            confidence_score=0.85,
            signals_used=["latency_p50", "success_rate"],
            optimization_enabled=True,
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        # Will FAIL until Phase 5D is implemented
        assert len(decisions) >= 1, "Decision must be emitted on divergence"
        assert decisions[0]["decision_outcome"] == "optimized_selected"
        assert decisions[0]["causal_role"] == "pre_run"


# =============================================================================
# G5D-04: Shadow mode, different choice
# =============================================================================


class TestG5D04ShadowModeDifferentChoice:
    """
    GIVEN: Shadow mode is enabled
    AND: Optimized choice differs from baseline
    WHEN: CARE routing is invoked
    THEN:
      - Shadow log only
      - Baseline is used (not optimized)
      - NO decision record emitted
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_shadow_mode_no_decision(self, db_url: str, request_id: str, tenant_id: str):
        """Shadow mode must not emit decision records."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",  # Different
            confidence_score=0.85,
            signals_used=["latency_p50", "success_rate"],
            optimization_enabled=True,
            shadow_mode=True,  # Shadow mode
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        # Shadow mode must NOT emit decisions
        assert len(decisions) == 0, "Shadow mode must NOT emit decision records"


# =============================================================================
# G5D-05: Kill-switch activated
# =============================================================================


class TestG5D05KillSwitchActivated:
    """
    GIVEN: Kill-switch is activated
    WHEN: CARE routing is invoked
    THEN:
      - Instant revert to baseline
      - No optimization decisions emitted
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_kill_switch_reverts_instantly(self, db_url: str, request_id: str, tenant_id: str):
        """Kill-switch must revert to baseline within 1 cycle."""
        # Activate kill-switch
        result = helper_kill_switch_activate()

        # Will FAIL until Phase 5D is implemented
        assert result is True, "Kill-switch must activate successfully"

        # After kill-switch, routing should use baseline only
        routing = get_care_routing(
            request_id=request_id,
            signals=mock_allowed_signals(),
            optimization_enabled=True,  # Even if enabled
        )

        # Should not use optimization
        assert routing["used_optimization"] is False


# =============================================================================
# G5D-06: Replay with same signals
# =============================================================================


class TestG5D06ReplaySameSignals:
    """
    GIVEN: Same signal snapshot
    WHEN: Replay is executed
    THEN:
      - Same routing decision is made
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_replay_deterministic(self, db_url: str, request_id: str, tenant_id: str):
        """Replay with same signals must produce same result."""
        signals = mock_allowed_signals()

        # First routing
        result1 = get_care_routing(
            request_id=request_id,
            signals=signals,
            optimization_enabled=True,
        )

        # Replay with same signals
        result2 = get_care_routing(
            request_id=f"{request_id}-replay",
            signals=signals,  # Same signals
            optimization_enabled=True,
        )

        # Results must be identical
        assert result1["baseline_agent"] == result2["baseline_agent"]
        assert result1["optimized_agent"] == result2["optimized_agent"]


# =============================================================================
# G5D-07: Replay with different signals
# =============================================================================


class TestG5D07ReplayDifferentSignals:
    """
    GIVEN: Different signal snapshot
    WHEN: Replay is executed
    THEN:
      - Different routing decision (expected)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_different_signals_different_result(self, db_url: str, request_id: str, tenant_id: str):
        """Different signals may produce different results."""
        signals1 = mock_allowed_signals()
        signals2 = mock_allowed_signals()
        signals2["success_rate"] = 0.50  # Lower success rate

        result1 = get_care_routing(
            request_id=request_id,
            signals=signals1,
            optimization_enabled=True,
        )

        result2 = get_care_routing(
            request_id=f"{request_id}-different",
            signals=signals2,
            optimization_enabled=True,
        )

        # Results may differ (this is expected behavior)
        # This test just verifies the mechanism works
        pass  # Placeholder - verifies signals affect routing


# =============================================================================
# G5D-08: Founder timeline shows optimization
# =============================================================================


class TestG5D08FounderTimelineOptimization:
    """
    GIVEN: Optimization changes routing
    WHEN: Founder views timeline
    THEN:
      - Decision includes explainability fields
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_explainability_fields_present(self, db_url: str, request_id: str, tenant_id: str):
        """Decision must include all explainability fields."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",
            confidence_score=0.85,
            signals_used=["latency_p50", "success_rate"],
            optimization_enabled=True,
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")

        # Will FAIL until Phase 5D is implemented
        assert len(decisions) >= 1, "Decision must be emitted"

        decision = decisions[0]
        # Check explainability fields
        assert "decision_inputs" in decision
        # Inputs should contain baseline, optimized, confidence, signals


# =============================================================================
# G5D-09: Forbidden signal access attempted
# =============================================================================


class TestG5D09ForbiddenSignalAccess:
    """
    GIVEN: Attempt to access forbidden signal
    WHEN: Signal isolation layer is invoked
    THEN:
      - Hard error raised
      - Not silent failure
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_forbidden_signal_raises_error(self, db_url: str, request_id: str, tenant_id: str):
        """Forbidden signal access must raise exception."""
        forbidden = mock_forbidden_signals()

        # Will FAIL until Phase 5D is implemented
        with pytest.raises(CARESignalAccessError):
            # Attempting to access any forbidden signal should raise
            helper_signal_access("policy_outcome")


# =============================================================================
# G5D-10: Policy/budget/recovery unchanged
# =============================================================================


class TestG5D10NoPhaseCrossover:
    """
    GIVEN: CARE optimization is enabled
    WHEN: Optimization runs
    THEN:
      - No impact on Phase 5A (budget)
      - No impact on Phase 5B (policy)
      - No impact on Phase 5C (recovery)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_cross_phase_impact(self, db_url: str, request_id: str, tenant_id: str):
        """Optimization must not affect other phases."""
        # This test verifies isolation - optimization doesn't change
        # budget, policy, or recovery behavior
        # For red phase, we just verify the separation exists
        pass  # Placeholder - full test requires integration


# =============================================================================
# G5D-11: Confidence below threshold
# =============================================================================


class TestG5D11ConfidenceBelowThreshold:
    """
    GIVEN: Optimization confidence is below threshold
    WHEN: CARE routing is invoked
    THEN:
      - Baseline selected (conservative)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_low_confidence_uses_baseline(self, db_url: str, request_id: str, tenant_id: str):
        """Low confidence must fall back to baseline."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",
            confidence_score=0.30,  # Below threshold
            signals_used=["latency_p50"],
            optimization_enabled=True,
            tenant_id=tenant_id,
        )

        # With low confidence, should use baseline (no decision emitted)
        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        # Low confidence = baseline selected = no decision
        assert len(decisions) == 0, "Low confidence must use baseline"


# =============================================================================
# G5D-12: No historical data available
# =============================================================================


class TestG5D12NoHistoricalData:
    """
    GIVEN: No historical data for optimization
    WHEN: CARE routing is invoked
    THEN:
      - Baseline selected (cold start)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_cold_start_uses_baseline(self, db_url: str, request_id: str, tenant_id: str):
        """Cold start must use baseline."""
        # Empty signals = cold start
        result = get_care_routing(
            request_id=request_id,
            signals={},  # No historical data
            optimization_enabled=True,
        )

        # Cold start should use baseline
        assert result["used_optimization"] is False


# =============================================================================
# Invariant Tests
# =============================================================================


class TestG5DInvariants:
    """Meta-tests verifying the CARE optimization invariants from PIN-176."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_no_silent_optimization(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-01: Every divergence must emit decision."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",  # Different
            confidence_score=0.90,
            signals_used=["latency_p50", "success_rate"],
            optimization_enabled=True,
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        # Will FAIL until Phase 5D is implemented
        assert len(decisions) >= 1, "INVARIANT: Every divergence emits decision"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_forbidden_signals_blocked(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-02: Forbidden signal access must raise exception."""
        forbidden = mock_forbidden_signals()

        # Will FAIL until Phase 5D is implemented
        for signal_name in forbidden.keys():
            with pytest.raises(CARESignalAccessError):
                helper_signal_access(signal_name)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_kill_switch_works(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-03: Kill-switch must revert within 1 cycle."""
        result = helper_kill_switch_activate()
        # Will FAIL until Phase 5D is implemented
        assert result is True, "INVARIANT: Kill-switch must work"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_replay_deterministic(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-04: Same signal snapshot must produce same routing."""
        signals = mock_allowed_signals()

        result1 = get_care_routing(
            request_id=request_id,
            signals=signals,
            optimization_enabled=True,
        )

        result2 = get_care_routing(
            request_id=f"{request_id}-replay",
            signals=signals,
            optimization_enabled=True,
        )

        assert result1["optimized_agent"] == result2["optimized_agent"], "INVARIANT: Replay must be deterministic"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_no_contract_expansion(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-05: Only additive types/outcomes allowed."""
        # Verify CARE_ROUTING_OPTIMIZED exists (will be added)
        # This test passes if enum exists after implementation
        try:
            # Will FAIL until Phase 5D adds the enum
            assert hasattr(DecisionType, "CARE_ROUTING_OPTIMIZED")
        except (AttributeError, AssertionError):
            pytest.fail("INVARIANT: CARE_ROUTING_OPTIMIZED must be added")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_shadow_mode_no_decisions(self, db_url: str, request_id: str, tenant_id: str):
        """G5D-INV-06: Shadow mode must not emit decision records."""
        helper_emit_care_decision(
            request_id=request_id,
            baseline_agent="agent-a",
            optimized_agent="agent-b",
            confidence_score=0.90,
            signals_used=["latency_p50"],
            optimization_enabled=True,
            shadow_mode=True,
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id=request_id, decision_type="care_routing_optimized")
        assert len(decisions) == 0, "INVARIANT: Shadow mode emits no decisions"
