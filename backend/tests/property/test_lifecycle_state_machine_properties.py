# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Property-based state machine tests for onboarding/incidents lifecycle
# artifact_class: TEST
"""
BA-13: Property-based state machine tests for onboarding and incident lifecycles.

All tests are self-contained with inline enums and transition maps.  No
production code is imported.
"""

import enum
from collections import deque
from typing import Dict, FrozenSet, Set

import pytest
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Onboarding lifecycle state machine
# ---------------------------------------------------------------------------


class OnboardingState(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


ONBOARDING_VALID_TRANSITIONS: Dict[OnboardingState, FrozenSet[OnboardingState]] = {
    OnboardingState.NOT_STARTED: frozenset({OnboardingState.IN_PROGRESS}),
    OnboardingState.IN_PROGRESS: frozenset(
        {OnboardingState.COMPLETE, OnboardingState.FAILED}
    ),
    OnboardingState.COMPLETE: frozenset(),  # terminal
    OnboardingState.FAILED: frozenset(
        {OnboardingState.IN_PROGRESS}
    ),  # retry allowed
}

ONBOARDING_TERMINAL_STATES: FrozenSet[OnboardingState] = frozenset(
    {OnboardingState.COMPLETE}
)

# FAILED allows retry to IN_PROGRESS, so it is not fully terminal.
# COMPLETE is the only true terminal state.


def attempt_onboarding_transition(
    current: OnboardingState, target: OnboardingState
) -> bool:
    """Return True if the transition is allowed, False otherwise."""
    return target in ONBOARDING_VALID_TRANSITIONS.get(current, frozenset())


# ---------------------------------------------------------------------------
# Incident lifecycle state machine
# ---------------------------------------------------------------------------


class IncidentState(enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    REOPENED = "reopened"


INCIDENT_VALID_TRANSITIONS: Dict[IncidentState, FrozenSet[IncidentState]] = {
    IncidentState.OPEN: frozenset({IncidentState.INVESTIGATING}),
    IncidentState.INVESTIGATING: frozenset(
        {IncidentState.RESOLVED}
    ),
    IncidentState.RESOLVED: frozenset(
        {IncidentState.REOPENED}
    ),
    IncidentState.REOPENED: frozenset(
        {IncidentState.INVESTIGATING}
    ),
}

INCIDENT_TERMINAL_STATES: FrozenSet[IncidentState] = frozenset()
# Note: RESOLVED is not truly terminal because it can be REOPENED.
# The cycle REOPENED -> INVESTIGATING -> RESOLVED -> REOPENED is valid.
# For reachability tests we treat RESOLVED as the "goal" state.


def attempt_incident_transition(
    current: IncidentState, target: IncidentState
) -> bool:
    """Return True if the transition is allowed, False otherwise."""
    return target in INCIDENT_VALID_TRANSITIONS.get(current, frozenset())


# ---------------------------------------------------------------------------
# Reachability helper (BFS)
# ---------------------------------------------------------------------------


def is_reachable(
    start: enum.Enum,
    goal: enum.Enum,
    transitions: Dict,
) -> bool:
    """BFS to determine if `goal` is reachable from `start`."""
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
# Hypothesis strategies
# ---------------------------------------------------------------------------

onboarding_state_st = st.sampled_from(list(OnboardingState))
incident_state_st = st.sampled_from(list(IncidentState))


# ---------------------------------------------------------------------------
# Onboarding property tests
# ---------------------------------------------------------------------------


class TestOnboardingStateMachine:
    """Property-based tests for the onboarding lifecycle state machine."""

    @given(current=onboarding_state_st, target=onboarding_state_st)
    @settings(max_examples=200)
    def test_no_forbidden_transitions(
        self, current: OnboardingState, target: OnboardingState
    ) -> None:
        """
        Given random state pairs, only valid transitions succeed.
        Any transition not in ONBOARDING_VALID_TRANSITIONS must be rejected.
        """
        allowed = attempt_onboarding_transition(current, target)
        is_valid = target in ONBOARDING_VALID_TRANSITIONS.get(
            current, frozenset()
        )
        assert allowed == is_valid, (
            f"Transition {current.value} -> {target.value}: "
            f"got {allowed}, expected {is_valid}"
        )

    @given(current=onboarding_state_st)
    @settings(max_examples=200)
    def test_terminal_states_have_no_outgoing(
        self, current: OnboardingState
    ) -> None:
        """
        COMPLETE is a terminal state with no valid outgoing transitions.
        FAILED is semi-terminal: it allows retry to IN_PROGRESS only.
        """
        outgoing = ONBOARDING_VALID_TRANSITIONS.get(current, frozenset())
        if current == OnboardingState.COMPLETE:
            assert len(outgoing) == 0, (
                f"Terminal state COMPLETE should have 0 outgoing transitions, "
                f"found {len(outgoing)}"
            )
        if current == OnboardingState.FAILED:
            # FAILED allows exactly one transition: retry to IN_PROGRESS
            assert outgoing == frozenset({OnboardingState.IN_PROGRESS}), (
                f"FAILED should only allow retry to IN_PROGRESS, "
                f"found {outgoing}"
            )

    def test_initial_state_is_not_started(self) -> None:
        """The first state in any onboarding lifecycle must be NOT_STARTED."""
        initial = OnboardingState.NOT_STARTED
        # NOT_STARTED must have at least one outgoing transition
        outgoing = ONBOARDING_VALID_TRANSITIONS[initial]
        assert len(outgoing) > 0, (
            "NOT_STARTED must have at least one outgoing transition"
        )
        # No other state should be the entry point — NOT_STARTED should not
        # be reachable from any other state (it is the unique source).
        for state in OnboardingState:
            if state == initial:
                continue
            targets = ONBOARDING_VALID_TRANSITIONS.get(state, frozenset())
            assert initial not in targets, (
                f"NOT_STARTED should not be reachable from {state.value} — "
                f"it is the unique initial state"
            )

    @given(
        current=st.sampled_from(
            [
                s
                for s in OnboardingState
                if s not in {OnboardingState.COMPLETE}
            ]
        )
    )
    @settings(max_examples=200)
    def test_lifecycle_path_always_reachable(
        self, current: OnboardingState
    ) -> None:
        """
        From any non-terminal state, COMPLETE must be reachable via some
        sequence of valid transitions.
        """
        reachable = is_reachable(
            current,
            OnboardingState.COMPLETE,
            ONBOARDING_VALID_TRANSITIONS,
        )
        assert reachable, (
            f"COMPLETE is not reachable from {current.value}"
        )


# ---------------------------------------------------------------------------
# Incident property tests
# ---------------------------------------------------------------------------


class TestIncidentStateMachine:
    """Property-based tests for the incident lifecycle state machine."""

    @given(current=incident_state_st, target=incident_state_st)
    @settings(max_examples=200)
    def test_incident_no_forbidden_transitions(
        self, current: IncidentState, target: IncidentState
    ) -> None:
        """
        Given random incident state pairs, only valid transitions succeed.
        """
        allowed = attempt_incident_transition(current, target)
        is_valid = target in INCIDENT_VALID_TRANSITIONS.get(
            current, frozenset()
        )
        assert allowed == is_valid, (
            f"Incident transition {current.value} -> {target.value}: "
            f"got {allowed}, expected {is_valid}"
        )

    @given(
        data=st.data(),
    )
    @settings(max_examples=200)
    def test_resolved_cannot_go_to_open_directly(self, data: st.DataObject) -> None:
        """
        RESOLVED cannot transition directly to OPEN.  The only valid
        transition from RESOLVED is to REOPENED.
        """
        result = attempt_incident_transition(
            IncidentState.RESOLVED, IncidentState.OPEN
        )
        assert result is False, (
            "RESOLVED -> OPEN must be forbidden; "
            "must go through REOPENED first"
        )
        # Also verify the positive case: RESOLVED -> REOPENED is allowed
        assert attempt_incident_transition(
            IncidentState.RESOLVED, IncidentState.REOPENED
        ) is True, "RESOLVED -> REOPENED must be allowed"

    @given(
        current=st.sampled_from(
            [
                s
                for s in IncidentState
                # All incident states can reach RESOLVED since the graph
                # has a cycle: REOPENED -> INVESTIGATING -> RESOLVED -> REOPENED
                # So we test from every state.
            ]
        )
    )
    @settings(max_examples=200)
    def test_incident_lifecycle_path_always_reachable(
        self, current: IncidentState
    ) -> None:
        """
        From any state, RESOLVED must be reachable via some sequence of
        valid transitions.
        """
        reachable = is_reachable(
            current,
            IncidentState.RESOLVED,
            INCIDENT_VALID_TRANSITIONS,
        )
        assert reachable, (
            f"RESOLVED is not reachable from {current.value}"
        )

    def test_incident_transition_map_completeness(self) -> None:
        """
        Every IncidentState must have an entry in the transition map, even
        if its set of outgoing transitions is empty.
        """
        for state in IncidentState:
            assert state in INCIDENT_VALID_TRANSITIONS, (
                f"IncidentState.{state.name} missing from transition map"
            )

    def test_no_self_transitions(self) -> None:
        """No state should be able to transition to itself."""
        for state in IncidentState:
            assert state not in INCIDENT_VALID_TRANSITIONS[state], (
                f"IncidentState.{state.name} has a self-transition"
            )
        for state in OnboardingState:
            assert state not in ONBOARDING_VALID_TRANSITIONS[state], (
                f"OnboardingState.{state.name} has a self-transition"
            )
