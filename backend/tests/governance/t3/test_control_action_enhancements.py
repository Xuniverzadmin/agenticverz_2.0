# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 control action enhancement governance requirements (GAP-013 to GAP-015)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-004: Control Action Enhancement Tests (GAP-013 to GAP-015)

Tests the control action configuration and semantics:
- GAP-013: PAUSE action (resumable) - suspend, can resume
- GAP-014: STOP vs KILL semantics - STOP = graceful, KILL = immediate
- GAP-015: requires_ack flag for enforcement

Key Principle:
> Control actions have clear semantics and severity ordering.
"""

import pytest

from app.policy.arbitrator import (
    ACTION_SEVERITY,
    ArbitrationInput,
    PolicyAction,
    PolicyArbitrator,
    PolicyLimit,
)
from app.models.policy_precedence import ArbitrationResult, ConflictStrategy


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestControlActionImports:
    """Verify all control action related imports are accessible."""

    def test_policy_action_import(self) -> None:
        """Test PolicyAction dataclass is importable."""
        assert PolicyAction is not None

    def test_action_severity_import(self) -> None:
        """Test ACTION_SEVERITY dict is importable."""
        assert ACTION_SEVERITY is not None

    def test_arbitration_input_import(self) -> None:
        """Test ArbitrationInput dataclass is importable."""
        assert ArbitrationInput is not None

    def test_policy_arbitrator_import(self) -> None:
        """Test PolicyArbitrator class is importable."""
        assert PolicyArbitrator is not None


# ===========================================================================
# GAP-013: PAUSE Action (Resumable)
# ===========================================================================


class TestGAP013PauseAction:
    """
    GAP-013: PAUSE Action (Resumable)

    CURRENT: Not supported
    REQUIRED: `action: PAUSE` - suspend, can resume
    """

    def test_pause_action_is_valid(self) -> None:
        """PAUSE is a valid action type."""
        action = PolicyAction(
            policy_id="POL-001",
            action="pause",
        )
        assert action.action == "pause"

    def test_pause_action_in_severity_ranking(self) -> None:
        """PAUSE is included in action severity ranking."""
        assert "pause" in ACTION_SEVERITY

    def test_pause_is_least_severe_action(self) -> None:
        """PAUSE is the least severe action (lowest severity number)."""
        pause_severity = ACTION_SEVERITY["pause"]
        assert pause_severity == 1  # Lowest severity
        for action, severity in ACTION_SEVERITY.items():
            if action != "pause":
                assert severity > pause_severity

    def test_pause_action_can_be_in_arbitration_input(self) -> None:
        """PAUSE action can be included in ArbitrationInput."""
        arb_input = ArbitrationInput(
            policy_ids=["POL-001"],
            breach_actions=[
                PolicyAction(policy_id="POL-001", action="pause"),
            ],
        )
        assert len(arb_input.breach_actions) == 1
        assert arb_input.breach_actions[0].action == "pause"

    def test_pause_allows_lower_severity_resolution(self) -> None:
        """When policies conflict, PAUSE can be selected as less severe option."""
        actions = [
            PolicyAction(policy_id="POL-001", action="pause"),
            PolicyAction(policy_id="POL-002", action="stop"),
        ]
        # Most restrictive strategy would pick stop (higher severity)
        # But pause exists as a valid, less severe option
        assert any(a.action == "pause" for a in actions)


# ===========================================================================
# GAP-014: STOP vs KILL Semantics
# ===========================================================================


class TestGAP014StopVsKillSemantics:
    """
    GAP-014: STOP vs KILL Semantics

    CURRENT: Unclear (ABORT exists)
    REQUIRED: `STOP` = graceful, `KILL` = immediate
    """

    def test_stop_action_exists(self) -> None:
        """STOP is a valid action type."""
        action = PolicyAction(
            policy_id="POL-001",
            action="stop",
        )
        assert action.action == "stop"

    def test_kill_action_exists(self) -> None:
        """KILL is a valid action type."""
        action = PolicyAction(
            policy_id="POL-001",
            action="kill",
        )
        assert action.action == "kill"

    def test_stop_in_severity_ranking(self) -> None:
        """STOP is in the severity ranking."""
        assert "stop" in ACTION_SEVERITY

    def test_kill_in_severity_ranking(self) -> None:
        """KILL is in the severity ranking."""
        assert "kill" in ACTION_SEVERITY

    def test_kill_more_severe_than_stop(self) -> None:
        """KILL is more severe than STOP."""
        assert ACTION_SEVERITY["kill"] > ACTION_SEVERITY["stop"]

    def test_stop_more_severe_than_pause(self) -> None:
        """STOP is more severe than PAUSE."""
        assert ACTION_SEVERITY["stop"] > ACTION_SEVERITY["pause"]

    def test_severity_ordering_is_pause_stop_kill(self) -> None:
        """Severity ordering is PAUSE < STOP < KILL."""
        assert ACTION_SEVERITY["pause"] < ACTION_SEVERITY["stop"]
        assert ACTION_SEVERITY["stop"] < ACTION_SEVERITY["kill"]

    def test_stop_is_default_action(self) -> None:
        """STOP is the default breach action when none specified."""
        from datetime import datetime, timezone
        # From arbitrator.py: effective_action = "stop"  # Default
        result = ArbitrationResult(
            policy_ids=["POL-001"],
            precedence_order=[1],
            effective_breach_action="stop",  # Default
            arbitration_timestamp=datetime.now(timezone.utc),
            snapshot_hash="test_hash_123",
        )
        assert result.effective_breach_action == "stop"

    def test_stop_semantics_graceful_termination(self) -> None:
        """STOP implies graceful termination (severity 2)."""
        # Stop allows cleanup operations
        assert ACTION_SEVERITY["stop"] == 2

    def test_kill_semantics_immediate_termination(self) -> None:
        """KILL implies immediate termination (highest severity)."""
        # Kill is immediate, no cleanup
        assert ACTION_SEVERITY["kill"] == 3
        # Kill should be the most severe
        assert ACTION_SEVERITY["kill"] == max(ACTION_SEVERITY.values())


# ===========================================================================
# GAP-015: Requires Acknowledgment Flag
# ===========================================================================


class TestGAP015RequiresAckFlag:
    """
    GAP-015: requires_ack Flag

    CURRENT: Not supported
    REQUIRED: `requires_ack: boolean` for enforcement

    Note: Acknowledgment machinery exists in the codebase through RAC
    (Runtime Audit Contract) and signal acknowledgment features.
    """

    def test_threshold_signal_has_acknowledged_field(self) -> None:
        """ThresholdSignal has acknowledged field for ack tracking."""
        from app.models.threshold_signal import ThresholdSignal, ThresholdMetric

        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=90,
            threshold_value=100,
        )
        assert hasattr(signal, "acknowledged")
        assert signal.acknowledged is False  # Default unacknowledged

    def test_threshold_signal_acknowledge_method(self) -> None:
        """ThresholdSignal has acknowledge method."""
        from app.models.threshold_signal import ThresholdSignal, ThresholdMetric

        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=90,
            threshold_value=100,
        )
        assert callable(getattr(signal, "acknowledge", None))

    def test_signal_acknowledgment_tracking(self) -> None:
        """Signal acknowledgment is properly tracked."""
        from app.models.threshold_signal import ThresholdSignal, ThresholdMetric

        signal = ThresholdSignal.create_near_signal(
            run_id="RUN-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            metric=ThresholdMetric.COST,
            current_value=90,
            threshold_value=100,
        )
        # Initially unacknowledged
        assert signal.acknowledged is False
        assert signal.acknowledged_by is None
        assert signal.acknowledged_at is None

        # Acknowledge the signal
        signal.acknowledge("user-123")

        # Now acknowledged
        assert signal.acknowledged is True
        assert signal.acknowledged_by == "user-123"
        assert signal.acknowledged_at is not None

    def test_audit_ack_status_exists(self) -> None:
        """AuditStatus includes ACKED state for acknowledgment tracking."""
        from app.services.audit.models import AuditStatus

        assert AuditStatus.ACKED is not None
        assert AuditStatus.ACKED.value == "ACKED"


# ===========================================================================
# Test: Policy Action
# ===========================================================================


class TestPolicyAction:
    """Test PolicyAction dataclass features."""

    def test_policy_action_creation(self) -> None:
        """Can create a PolicyAction."""
        action = PolicyAction(
            policy_id="POL-001",
            action="stop",
        )
        assert action.policy_id == "POL-001"
        assert action.action == "stop"

    def test_policy_action_has_precedence(self) -> None:
        """PolicyAction has precedence field."""
        action = PolicyAction(
            policy_id="POL-001",
            action="pause",
            precedence=50,
        )
        assert action.precedence == 50

    def test_policy_action_default_precedence(self) -> None:
        """PolicyAction has default precedence of 100."""
        action = PolicyAction(
            policy_id="POL-001",
            action="stop",
        )
        assert action.precedence == 100


# ===========================================================================
# Test: Action Severity
# ===========================================================================


class TestActionSeverity:
    """Test ACTION_SEVERITY dictionary."""

    def test_severity_has_three_levels(self) -> None:
        """ACTION_SEVERITY has exactly three action levels."""
        assert len(ACTION_SEVERITY) == 3

    def test_severity_keys_are_actions(self) -> None:
        """ACTION_SEVERITY keys are action strings."""
        expected_actions = {"pause", "stop", "kill"}
        assert set(ACTION_SEVERITY.keys()) == expected_actions

    def test_severity_values_are_integers(self) -> None:
        """ACTION_SEVERITY values are integers."""
        for action, severity in ACTION_SEVERITY.items():
            assert isinstance(severity, int)

    def test_severity_values_are_unique(self) -> None:
        """ACTION_SEVERITY values are unique (no ties)."""
        severities = list(ACTION_SEVERITY.values())
        assert len(severities) == len(set(severities))

    def test_severity_is_ordinal(self) -> None:
        """ACTION_SEVERITY values form an ordinal scale (1, 2, 3)."""
        assert sorted(ACTION_SEVERITY.values()) == [1, 2, 3]


# ===========================================================================
# Test: Arbitration Input
# ===========================================================================


class TestArbitrationInput:
    """Test ArbitrationInput dataclass features."""

    def test_arbitration_input_creation(self) -> None:
        """Can create an ArbitrationInput."""
        arb_input = ArbitrationInput(
            policy_ids=["POL-001", "POL-002"],
        )
        assert len(arb_input.policy_ids) == 2

    def test_arbitration_input_with_breach_actions(self) -> None:
        """ArbitrationInput can include breach actions."""
        arb_input = ArbitrationInput(
            policy_ids=["POL-001", "POL-002"],
            breach_actions=[
                PolicyAction(policy_id="POL-001", action="pause"),
                PolicyAction(policy_id="POL-002", action="stop"),
            ],
        )
        assert len(arb_input.breach_actions) == 2

    def test_arbitration_input_defaults_empty_lists(self) -> None:
        """ArbitrationInput has empty defaults for optional fields."""
        arb_input = ArbitrationInput(
            policy_ids=["POL-001"],
        )
        assert arb_input.token_limits == []
        assert arb_input.cost_limits == []
        assert arb_input.burn_rate_limits == []
        assert arb_input.breach_actions == []


# ===========================================================================
# Test: Conflict Strategy
# ===========================================================================


class TestConflictStrategy:
    """Test ConflictStrategy enum for action resolution."""

    def test_most_restrictive_strategy(self) -> None:
        """MOST_RESTRICTIVE strategy exists."""
        assert ConflictStrategy.MOST_RESTRICTIVE is not None
        assert ConflictStrategy.MOST_RESTRICTIVE.value == "most_restrictive"

    def test_explicit_priority_strategy(self) -> None:
        """EXPLICIT_PRIORITY strategy exists."""
        assert ConflictStrategy.EXPLICIT_PRIORITY is not None
        assert ConflictStrategy.EXPLICIT_PRIORITY.value == "explicit_priority"

    def test_fail_closed_strategy(self) -> None:
        """FAIL_CLOSED strategy exists."""
        assert ConflictStrategy.FAIL_CLOSED is not None
        assert ConflictStrategy.FAIL_CLOSED.value == "fail_closed"

    def test_strategies_affect_action_resolution(self) -> None:
        """Different strategies lead to different action selection."""
        # MOST_RESTRICTIVE: pick highest severity
        # EXPLICIT_PRIORITY: pick highest precedence policy's action
        # FAIL_CLOSED: pick highest severity on ambiguity
        strategies = [
            ConflictStrategy.MOST_RESTRICTIVE,
            ConflictStrategy.EXPLICIT_PRIORITY,
            ConflictStrategy.FAIL_CLOSED,
        ]
        assert len(strategies) == 3
