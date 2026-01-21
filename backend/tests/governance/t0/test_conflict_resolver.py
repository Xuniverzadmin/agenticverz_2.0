# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-068 (Policy Conflict Resolution)
"""
Unit tests for GAP-068: Policy Conflict Resolution.

Tests that the conflict resolver correctly applies INV-005 determinism:
- Most restrictive action wins
- policy_id as deterministic tiebreaker
"""

import pytest
from app.policy.conflict_resolver import (
    resolve_policy_conflict,
    PolicyAction,
    ResolvedAction,
    ConflictResolutionStrategy,
    ActionSeverity,
)


class TestPolicyConflictResolver:
    """Test suite for conflict resolution."""

    def test_single_action_returns_that_action(self):
        """Single policy action should return itself."""
        actions = [
            PolicyAction(
                policy_id="pol-001",
                policy_name="Test Policy",
                action="STOP",
                precedence=10,
                reason="Test"
            )
        ]
        result = resolve_policy_conflict(actions)

        assert result.winning_action == "STOP"
        assert result.winning_policy_id == "pol-001"
        assert result.conflict_detected is False

    def test_most_restrictive_action_wins(self):
        """Most restrictive action (KILL > STOP > WARN > ALLOW) should win."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="Allow Policy",
                action="ALLOW", precedence=10, reason="Allow"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="Warn Policy",
                action="WARN", precedence=10, reason="Warn"
            ),
            PolicyAction(
                policy_id="pol-003", policy_name="Stop Policy",
                action="STOP", precedence=10, reason="Stop"
            ),
        ]
        result = resolve_policy_conflict(actions)

        assert result.winning_action == "STOP"
        assert result.winning_policy_id == "pol-003"
        assert result.conflict_detected is True

    def test_higher_precedence_wins(self):
        """Higher precedence (lower number) should win."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="Low Priority",
                action="WARN", precedence=50, reason="Low prec"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="High Priority",
                action="WARN", precedence=10, reason="High prec"
            ),
        ]
        result = resolve_policy_conflict(actions)

        # Higher precedence = lower number wins
        assert result.winning_policy_id == "pol-002"

    def test_deterministic_tiebreaker_by_policy_id(self):
        """Same action and precedence should use policy_id as tiebreaker."""
        actions = [
            PolicyAction(
                policy_id="pol-beta", policy_name="Beta Policy",
                action="STOP", precedence=10, reason="Beta"
            ),
            PolicyAction(
                policy_id="pol-alpha", policy_name="Alpha Policy",
                action="STOP", precedence=10, reason="Alpha"
            ),
        ]
        result = resolve_policy_conflict(actions)

        # Alphabetically first policy_id wins (deterministic - INV-005)
        assert result.winning_policy_id == "pol-alpha"

    def test_empty_actions_returns_continue(self):
        """Empty actions list should return CONTINUE (default)."""
        result = resolve_policy_conflict([])

        assert result.winning_action == "CONTINUE"
        assert result.winning_policy_id is None
        assert result.conflict_detected is False

    def test_kill_action_is_most_restrictive(self):
        """KILL action should be treated as most restrictive."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="Warn Policy",
                action="WARN", precedence=10, reason="Warn"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="Kill Policy",
                action="KILL", precedence=10, reason="Kill"
            ),
        ]
        result = resolve_policy_conflict(actions)

        assert result.winning_action == "KILL"
        assert result.winning_policy_id == "pol-002"

    def test_resolution_tracks_all_triggered(self):
        """Resolution should track all triggered policies."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="Policy 1",
                action="WARN", precedence=10, reason="Warn"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="Policy 2",
                action="STOP", precedence=10, reason="Stop"
            ),
        ]
        result = resolve_policy_conflict(actions)

        assert len(result.all_triggered) == 2
        assert result.all_triggered[0].policy_id in ("pol-001", "pol-002")


class TestPolicyAction:
    """Test suite for PolicyAction dataclass."""

    def test_policy_action_creation(self):
        """PolicyAction should be creatable with required fields."""
        action = PolicyAction(
            policy_id="pol-001",
            policy_name="Test Policy",
            action="STOP",
            precedence=10,
            reason="Test reason",
        )

        assert action.policy_id == "pol-001"
        assert action.policy_name == "Test Policy"
        assert action.action == "STOP"
        assert action.precedence == 10
        assert action.reason == "Test reason"


class TestResolvedAction:
    """Test suite for ResolvedAction dataclass."""

    def test_resolved_action_creation(self):
        """ResolvedAction should be creatable."""
        result = ResolvedAction(
            winning_action="STOP",
            winning_policy_id="pol-001",
            resolution_reason="single_policy",
            all_triggered=[],
            conflict_detected=False,
        )

        assert result.winning_action == "STOP"
        assert result.winning_policy_id == "pol-001"
        assert result.conflict_detected is False


class TestActionSeverity:
    """Test action severity ordering."""

    def test_severity_ordering(self):
        """Actions should have correct severity ordering."""
        assert ActionSeverity.CONTINUE < ActionSeverity.WARN
        assert ActionSeverity.WARN < ActionSeverity.PAUSE
        assert ActionSeverity.PAUSE < ActionSeverity.STOP
        assert ActionSeverity.STOP < ActionSeverity.KILL

    def test_aliases_equal(self):
        """Action aliases should have equal severity."""
        assert ActionSeverity.ALLOW == ActionSeverity.CONTINUE
        assert ActionSeverity.BLOCK == ActionSeverity.STOP
        assert ActionSeverity.ABORT == ActionSeverity.KILL


class TestConflictResolutionStrategy:
    """Test different resolution strategies."""

    def test_severity_first_strategy(self):
        """SEVERITY_FIRST should prioritize restrictive actions."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="High Priority Allow",
                action="ALLOW", precedence=1, reason="High prec allow"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="Low Priority Stop",
                action="STOP", precedence=100, reason="Low prec stop"
            ),
        ]
        result = resolve_policy_conflict(
            actions,
            strategy=ConflictResolutionStrategy.SEVERITY_FIRST
        )

        # SEVERITY_FIRST: STOP wins over ALLOW despite precedence
        assert result.winning_action == "STOP"

    def test_precedence_first_strategy(self):
        """PRECEDENCE_FIRST should prioritize higher precedence."""
        actions = [
            PolicyAction(
                policy_id="pol-001", policy_name="High Priority Allow",
                action="ALLOW", precedence=1, reason="High prec allow"
            ),
            PolicyAction(
                policy_id="pol-002", policy_name="Low Priority Stop",
                action="STOP", precedence=100, reason="Low prec stop"
            ),
        ]
        result = resolve_policy_conflict(
            actions,
            strategy=ConflictResolutionStrategy.PRECEDENCE_FIRST
        )

        # PRECEDENCE_FIRST: Higher precedence (1) wins over lower (100)
        assert result.winning_policy_id == "pol-001"
