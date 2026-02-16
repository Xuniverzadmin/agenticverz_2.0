# Layer: TEST
# AUDIENCE: INTERNAL
# Role: CTRL-DELTA-04 — Property-based tests for controls state machines and threshold invariants
# artifact_class: TEST
"""
CTRL-DELTA-04: Property-based tests for killswitch state machine, threshold
validation, and override safety properties.

All tests are self-contained with inline enums and transition maps. No
production code is imported.
"""

import enum
from collections import deque
from typing import Dict, FrozenSet, List, Set, Tuple

import pytest
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Killswitch state machine
# ---------------------------------------------------------------------------


class KillswitchState(enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DECOMMISSIONED = "DECOMMISSIONED"


KILLSWITCH_VALID_TRANSITIONS: Dict[KillswitchState, FrozenSet[KillswitchState]] = {
    KillswitchState.ACTIVE: frozenset({KillswitchState.FROZEN, KillswitchState.DECOMMISSIONED}),
    KillswitchState.FROZEN: frozenset({KillswitchState.ACTIVE, KillswitchState.DECOMMISSIONED}),
    KillswitchState.DECOMMISSIONED: frozenset(),  # terminal state
}


def attempt_killswitch_transition(
    current: KillswitchState, target: KillswitchState
) -> bool:
    """Return True if the transition is allowed, False otherwise."""
    return target in KILLSWITCH_VALID_TRANSITIONS.get(current, frozenset())


def apply_killswitch_transitions(
    initial: KillswitchState, transitions: List[KillswitchState]
) -> Tuple[KillswitchState, List[KillswitchState]]:
    """Apply a sequence of transitions. Returns (final_state, rejected_list)."""
    current = initial
    rejected: List[KillswitchState] = []
    for target in transitions:
        if attempt_killswitch_transition(current, target):
            current = target
        else:
            rejected.append(target)
    return current, rejected


def is_reachable(
    start: enum.Enum,
    goal: enum.Enum,
    transitions: Dict,
) -> bool:
    """BFS to determine if goal is reachable from start."""
    visited: Set = set()
    queue: deque = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            return True
        if current in visited:
            continue
        visited.add(current)
        for nxt in transitions.get(current, frozenset()):
            if nxt not in visited:
                queue.append(nxt)
    return False


# ---------------------------------------------------------------------------
# Threshold validation helpers
# ---------------------------------------------------------------------------


def validate_control_threshold(value) -> Tuple[bool, str]:
    """Validate a control threshold value. Returns (valid, message)."""
    if value is None:
        return False, "threshold is required"
    if not isinstance(value, (int, float)):
        return False, f"threshold must be numeric, got {type(value).__name__}"
    if value != value:  # NaN check
        return False, "threshold must not be NaN"
    if value == float("inf") or value == float("-inf"):
        return False, "threshold must be finite"
    if value < 0:
        return False, f"threshold must be non-negative, got {value}"
    return True, "ok"


def validate_override_value(value) -> Tuple[bool, str]:
    """Validate an override value. Returns (valid, message)."""
    if value is None:
        return False, "override_value is required"
    if not isinstance(value, (int, float)):
        return False, f"override_value must be numeric, got {type(value).__name__}"
    if value < 0:
        return False, f"override_value must be non-negative, got {value}"
    return True, "ok"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

killswitch_state_st = st.sampled_from(list(KillswitchState))


# ---------------------------------------------------------------------------
# Property-based tests — Killswitch state machine
# ---------------------------------------------------------------------------


class TestKillswitchStateMachine:
    """Property-based tests for the killswitch lifecycle state machine."""

    @given(current=killswitch_state_st, target=killswitch_state_st)
    @settings(max_examples=200)
    def test_no_forbidden_transitions(
        self, current: KillswitchState, target: KillswitchState
    ) -> None:
        """Only valid transitions succeed."""
        allowed = attempt_killswitch_transition(current, target)
        is_valid = target in KILLSWITCH_VALID_TRANSITIONS.get(current, frozenset())
        assert allowed == is_valid

    @given(current=killswitch_state_st)
    @settings(max_examples=50)
    def test_decommissioned_is_terminal(self, current: KillswitchState) -> None:
        """DECOMMISSIONED has no valid outgoing transitions."""
        outgoing = KILLSWITCH_VALID_TRANSITIONS[KillswitchState.DECOMMISSIONED]
        assert len(outgoing) == 0

    @given(current=killswitch_state_st)
    @settings(max_examples=50)
    def test_no_self_transitions(self, current: KillswitchState) -> None:
        """Self-transitions are never valid."""
        assert attempt_killswitch_transition(current, current) is False

    @given(
        current=st.sampled_from(
            [s for s in KillswitchState if s != KillswitchState.DECOMMISSIONED]
        )
    )
    @settings(max_examples=200)
    def test_decommissioned_reachable_from_any_non_terminal(
        self, current: KillswitchState
    ) -> None:
        """From any non-terminal state, DECOMMISSIONED must be reachable."""
        reachable = is_reachable(
            current,
            KillswitchState.DECOMMISSIONED,
            KILLSWITCH_VALID_TRANSITIONS,
        )
        assert reachable

    def test_transition_map_completeness(self) -> None:
        """Every KillswitchState has an entry in the transition map."""
        for state in KillswitchState:
            assert state in KILLSWITCH_VALID_TRANSITIONS

    def test_active_frozen_cycle(self) -> None:
        """Concrete: ACTIVE ↔ FROZEN cycling is allowed."""
        transitions = [
            KillswitchState.FROZEN,
            KillswitchState.ACTIVE,
            KillswitchState.FROZEN,
            KillswitchState.ACTIVE,
        ]
        final, rejected = apply_killswitch_transitions(KillswitchState.ACTIVE, transitions)
        assert final == KillswitchState.ACTIVE
        assert rejected == []

    def test_decommissioned_blocks_all_further(self) -> None:
        """Concrete: once DECOMMISSIONED, all further transitions rejected."""
        transitions = [
            KillswitchState.DECOMMISSIONED,
            KillswitchState.ACTIVE,
            KillswitchState.FROZEN,
        ]
        final, rejected = apply_killswitch_transitions(KillswitchState.ACTIVE, transitions)
        assert final == KillswitchState.DECOMMISSIONED
        assert rejected == [KillswitchState.ACTIVE, KillswitchState.FROZEN]

    @given(
        st.lists(killswitch_state_st, min_size=0, max_size=30)
    )
    @settings(max_examples=200)
    def test_transition_sequence_idempotent(
        self, transitions: List[KillswitchState]
    ) -> None:
        """Applying the same sequence twice yields the same result."""
        final_1, rejected_1 = apply_killswitch_transitions(
            KillswitchState.ACTIVE, transitions
        )
        final_2, rejected_2 = apply_killswitch_transitions(
            KillswitchState.ACTIVE, transitions
        )
        assert final_1 == final_2
        assert rejected_1 == rejected_2


# ---------------------------------------------------------------------------
# Property-based tests — Threshold & Override validation
# ---------------------------------------------------------------------------


class TestControlThresholdProperties:
    """Property-based tests for control threshold validation."""

    @given(st.floats())
    @settings(max_examples=200)
    def test_negative_thresholds_rejected(self, value: float) -> None:
        """Any negative finite float must be rejected."""
        valid, _ = validate_control_threshold(value)
        if value < 0.0 and value == value and abs(value) != float("inf"):
            assert valid is False

    @given(
        st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_valid_thresholds_accepted(self, value: float) -> None:
        """Non-negative finite floats must be accepted."""
        valid, _ = validate_control_threshold(value)
        assert valid is True

    def test_threshold_boundary_values(self) -> None:
        """Boundary: 0.0 valid, -0.001 invalid, NaN invalid, Inf invalid."""
        assert validate_control_threshold(0.0)[0] is True
        assert validate_control_threshold(-0.001)[0] is False
        assert validate_control_threshold(float("nan"))[0] is False
        assert validate_control_threshold(float("inf"))[0] is False
        assert validate_control_threshold(None)[0] is False
        assert validate_control_threshold("high")[0] is False

    @given(
        st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_valid_overrides_accepted(self, value: float) -> None:
        """Non-negative finite floats must be valid override values."""
        valid, _ = validate_override_value(value)
        assert valid is True

    @given(st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_negative_overrides_rejected(self, value: float) -> None:
        """Negative floats must be rejected as override values."""
        valid, _ = validate_override_value(value)
        assert valid is False
