# Layer: TEST
# AUDIENCE: INTERNAL
# Role: TEN-DELTA-04 — Property-based tests for tenant lifecycle state machine
# artifact_class: TEST
"""
TEN-DELTA-04: Property-based tests for tenant lifecycle state transitions.

All tests are self-contained with inline enums and transition maps. No
production code is imported.
"""

import enum
from collections import deque
from typing import Dict, FrozenSet, List, Set, Tuple

import pytest
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Tenant lifecycle state machine
# ---------------------------------------------------------------------------


class TenantState(enum.Enum):
    CREATING = "CREATING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


TENANT_VALID_TRANSITIONS: Dict[TenantState, FrozenSet[TenantState]] = {
    TenantState.CREATING: frozenset({TenantState.ACTIVE}),
    TenantState.ACTIVE: frozenset({TenantState.SUSPENDED, TenantState.DELETED}),
    TenantState.SUSPENDED: frozenset({TenantState.ACTIVE, TenantState.DELETED}),
    TenantState.DELETED: frozenset(),  # terminal state
}

TENANT_TERMINAL_STATES: FrozenSet[TenantState] = frozenset({TenantState.DELETED})


def attempt_tenant_transition(
    current: TenantState, target: TenantState
) -> bool:
    """Return True if the transition is allowed, False otherwise."""
    return target in TENANT_VALID_TRANSITIONS.get(current, frozenset())


def apply_tenant_transitions(
    initial: TenantState, transitions: List[TenantState]
) -> Tuple[TenantState, List[TenantState]]:
    """
    Apply a sequence of state transitions. Returns (final_state, rejected_list)
    where rejected_list contains the targets that were blocked.
    """
    current = initial
    rejected: List[TenantState] = []
    for target in transitions:
        if attempt_tenant_transition(current, target):
            current = target
        else:
            rejected.append(target)
    return current, rejected


def is_reachable(
    start: TenantState,
    goal: TenantState,
    transitions: Dict[TenantState, FrozenSet[TenantState]],
) -> bool:
    """BFS to determine if goal is reachable from start."""
    visited: Set[TenantState] = set()
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

tenant_state_st = st.sampled_from(list(TenantState))


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestTenantLifecycleStateMachine:
    """Property-based tests for the tenant lifecycle state machine."""

    @given(current=tenant_state_st, target=tenant_state_st)
    @settings(max_examples=200)
    def test_no_forbidden_transitions(
        self, current: TenantState, target: TenantState
    ) -> None:
        """
        Given random state pairs, only valid transitions succeed.
        Any transition not in TENANT_VALID_TRANSITIONS must be rejected.
        """
        allowed = attempt_tenant_transition(current, target)
        is_valid = target in TENANT_VALID_TRANSITIONS.get(current, frozenset())
        assert allowed == is_valid, (
            f"Transition {current.value} -> {target.value}: "
            f"got {allowed}, expected {is_valid}"
        )

    @given(current=tenant_state_st)
    @settings(max_examples=200)
    def test_deleted_is_terminal(self, current: TenantState) -> None:
        """DELETED has no valid outgoing transitions (terminal state)."""
        outgoing = TENANT_VALID_TRANSITIONS.get(TenantState.DELETED, frozenset())
        assert len(outgoing) == 0, (
            f"Terminal state DELETED should have 0 outgoing transitions, "
            f"found {len(outgoing)}"
        )

    def test_creating_only_leads_to_active(self) -> None:
        """CREATING can only transition to ACTIVE."""
        outgoing = TENANT_VALID_TRANSITIONS[TenantState.CREATING]
        assert outgoing == frozenset({TenantState.ACTIVE}), (
            f"CREATING should only allow transition to ACTIVE, found {outgoing}"
        )

    @given(current=tenant_state_st)
    @settings(max_examples=50)
    def test_no_self_transitions(self, current: TenantState) -> None:
        """Self-transitions (state→state) are never valid."""
        assert attempt_tenant_transition(current, current) is False, (
            f"Self-transition for {current.value} should be forbidden"
        )

    @given(
        current=st.sampled_from(
            [s for s in TenantState if s != TenantState.DELETED]
        )
    )
    @settings(max_examples=200)
    def test_deleted_reachable_from_any_non_terminal(
        self, current: TenantState
    ) -> None:
        """From any non-terminal state, DELETED must be reachable."""
        reachable = is_reachable(
            current,
            TenantState.DELETED,
            TENANT_VALID_TRANSITIONS,
        )
        assert reachable, (
            f"DELETED is not reachable from {current.value}"
        )

    def test_transition_map_completeness(self) -> None:
        """Every TenantState must have an entry in the transition map."""
        for state in TenantState:
            assert state in TENANT_VALID_TRANSITIONS, (
                f"TenantState.{state.name} missing from transition map"
            )

    @given(
        st.lists(
            tenant_state_st,
            min_size=0,
            max_size=30,
        )
    )
    @settings(max_examples=200)
    def test_final_state_always_valid(
        self, transitions: List[TenantState]
    ) -> None:
        """
        After applying any sequence of transitions from CREATING, the final
        state must be a valid TenantState.
        """
        final, _ = apply_tenant_transitions(TenantState.CREATING, transitions)
        assert final in set(TenantState)

    @given(
        st.lists(
            tenant_state_st,
            min_size=0,
            max_size=30,
        )
    )
    @settings(max_examples=200)
    def test_transition_sequence_idempotent(
        self, transitions: List[TenantState]
    ) -> None:
        """Applying the same transition sequence twice yields the same result."""
        final_1, rejected_1 = apply_tenant_transitions(
            TenantState.CREATING, transitions
        )
        final_2, rejected_2 = apply_tenant_transitions(
            TenantState.CREATING, transitions
        )
        assert final_1 == final_2
        assert rejected_1 == rejected_2

    def test_active_suspend_reactivate_cycle(self) -> None:
        """Concrete: ACTIVE ↔ SUSPENDED cycling is allowed."""
        transitions = [
            TenantState.ACTIVE,
            TenantState.SUSPENDED,
            TenantState.ACTIVE,
            TenantState.SUSPENDED,
        ]
        final, rejected = apply_tenant_transitions(TenantState.CREATING, transitions)
        assert final == TenantState.SUSPENDED
        assert rejected == []

    def test_deleted_blocks_all_further(self) -> None:
        """Concrete: once DELETED, all further transitions are rejected."""
        transitions = [
            TenantState.ACTIVE,
            TenantState.DELETED,
            TenantState.ACTIVE,
            TenantState.SUSPENDED,
            TenantState.CREATING,
        ]
        final, rejected = apply_tenant_transitions(TenantState.CREATING, transitions)
        assert final == TenantState.DELETED
        assert rejected == [
            TenantState.ACTIVE,
            TenantState.SUSPENDED,
            TenantState.CREATING,
        ]

    def test_creating_cannot_be_deleted_directly(self) -> None:
        """CREATING cannot transition directly to DELETED (must go through ACTIVE)."""
        assert attempt_tenant_transition(
            TenantState.CREATING, TenantState.DELETED
        ) is False
