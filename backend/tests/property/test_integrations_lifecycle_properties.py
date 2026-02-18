# Layer: TEST
# AUDIENCE: INTERNAL
# Role: INT-DELTA-04 — Property-based tests for integrations lifecycle state machine and invariants
# artifact_class: TEST
"""
INT-DELTA-04: Property-based tests for integration enable/disable lifecycle
state machine, connector registration validation, and tenant-scoped query
safety properties.

All tests are self-contained with inline enums and transition maps. No
production code is imported.
"""

import enum
from collections import deque
from typing import Dict, FrozenSet, List, Set, Tuple

from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Integration lifecycle state machine
# ---------------------------------------------------------------------------


class IntegrationState(enum.Enum):
    CREATED = "created"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


INTEGRATION_VALID_TRANSITIONS: Dict[IntegrationState, FrozenSet[IntegrationState]] = {
    IntegrationState.CREATED: frozenset({IntegrationState.ENABLED, IntegrationState.ERROR}),
    IntegrationState.ENABLED: frozenset({IntegrationState.DISABLED, IntegrationState.ERROR}),
    IntegrationState.DISABLED: frozenset({IntegrationState.ENABLED, IntegrationState.ERROR}),
    IntegrationState.ERROR: frozenset({IntegrationState.DISABLED}),
}


def attempt_integration_transition(
    current: IntegrationState, target: IntegrationState
) -> bool:
    """Return True if the transition is allowed, False otherwise."""
    return target in INTEGRATION_VALID_TRANSITIONS.get(current, frozenset())


def apply_integration_transitions(
    initial: IntegrationState, transitions: List[IntegrationState]
) -> Tuple[IntegrationState, List[IntegrationState]]:
    """Apply a sequence of transitions. Returns (final_state, rejected_list)."""
    current = initial
    rejected: List[IntegrationState] = []
    for target in transitions:
        if attempt_integration_transition(current, target):
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
# Connector registration validation
# ---------------------------------------------------------------------------


KNOWN_CONNECTOR_TYPES = frozenset({"openai", "anthropic", "azure", "google", "custom"})


def validate_connector_registration(
    connector_type: str, registered: bool
) -> Tuple[bool, str]:
    """Validate connector can be enabled. Returns (valid, message)."""
    if not connector_type:
        return False, "connector_type is required"
    if not registered:
        return False, f"connector_type '{connector_type}' is not registered"
    return True, "ok"


def validate_disable_precondition(
    exists: bool, current_status: str
) -> Tuple[bool, str]:
    """Validate integration can be disabled. Returns (valid, message)."""
    if not exists:
        return False, "integration does not exist"
    if current_status == "disabled":
        return False, "integration is already disabled"
    if current_status != "enabled":
        return False, f"integration must be 'enabled' to disable, got '{current_status}'"
    return True, "ok"


def validate_query_tenant_scope(tenant_id: str) -> Tuple[bool, str]:
    """Validate query has tenant scope. Returns (valid, message)."""
    if not tenant_id:
        return False, "tenant_id is required"
    return True, "ok"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

integration_state_st = st.sampled_from(list(IntegrationState))
connector_type_st = st.sampled_from(list(KNOWN_CONNECTOR_TYPES) + ["unknown", ""])


# ---------------------------------------------------------------------------
# Property-based tests — Integration lifecycle state machine
# ---------------------------------------------------------------------------


class TestIntegrationLifecycleStateMachine:
    """Property-based tests for the integration enable/disable lifecycle."""

    @given(current=integration_state_st, target=integration_state_st)
    @settings(max_examples=200)
    def test_no_forbidden_transitions(
        self, current: IntegrationState, target: IntegrationState
    ) -> None:
        """Only valid transitions succeed."""
        allowed = attempt_integration_transition(current, target)
        is_valid = target in INTEGRATION_VALID_TRANSITIONS.get(current, frozenset())
        assert allowed == is_valid

    @given(current=integration_state_st)
    @settings(max_examples=50)
    def test_no_self_transitions(self, current: IntegrationState) -> None:
        """Self-transitions are never valid."""
        assert attempt_integration_transition(current, current) is False

    @given(current=integration_state_st)
    @settings(max_examples=50)
    def test_error_reachable_from_any_state(self, current: IntegrationState) -> None:
        """ERROR is reachable from any state (created, enabled, disabled, error)."""
        reachable = is_reachable(
            current, IntegrationState.ERROR, INTEGRATION_VALID_TRANSITIONS
        )
        assert reachable

    def test_transition_map_completeness(self) -> None:
        """Every IntegrationState has an entry in the transition map."""
        for state in IntegrationState:
            assert state in INTEGRATION_VALID_TRANSITIONS

    def test_enable_disable_cycle(self) -> None:
        """Concrete: ENABLED ↔ DISABLED cycling is allowed."""
        transitions = [
            IntegrationState.ENABLED,
            IntegrationState.DISABLED,
            IntegrationState.ENABLED,
            IntegrationState.DISABLED,
        ]
        final, rejected = apply_integration_transitions(IntegrationState.CREATED, transitions)
        assert final == IntegrationState.DISABLED
        assert rejected == []

    def test_created_cannot_directly_disable(self) -> None:
        """Concrete: CREATED → DISABLED is forbidden (must enable first)."""
        allowed = attempt_integration_transition(
            IntegrationState.CREATED, IntegrationState.DISABLED
        )
        assert allowed is False

    def test_error_recovery_requires_disable(self) -> None:
        """Concrete: ERROR can only transition to DISABLED."""
        valid_from_error = INTEGRATION_VALID_TRANSITIONS[IntegrationState.ERROR]
        assert valid_from_error == frozenset({IntegrationState.DISABLED})

    @given(
        st.lists(integration_state_st, min_size=0, max_size=30)
    )
    @settings(max_examples=200)
    def test_transition_sequence_deterministic(
        self, transitions: List[IntegrationState]
    ) -> None:
        """Applying the same sequence twice yields the same result."""
        final_1, rejected_1 = apply_integration_transitions(
            IntegrationState.CREATED, transitions
        )
        final_2, rejected_2 = apply_integration_transitions(
            IntegrationState.CREATED, transitions
        )
        assert final_1 == final_2
        assert rejected_1 == rejected_2


# ---------------------------------------------------------------------------
# Property-based tests — Connector registration & disable validation
# ---------------------------------------------------------------------------


class TestIntegrationValidationProperties:
    """Property-based tests for integration invariant validation."""

    @given(connector_type=connector_type_st, registered=st.booleans())
    @settings(max_examples=200)
    def test_unregistered_connectors_always_rejected(
        self, connector_type: str, registered: bool
    ) -> None:
        """Any unregistered connector must be rejected regardless of type."""
        valid, _ = validate_connector_registration(connector_type, registered)
        if not registered and connector_type:
            assert valid is False

    @given(connector_type=st.sampled_from(list(KNOWN_CONNECTOR_TYPES)))
    @settings(max_examples=50)
    def test_registered_known_connectors_accepted(
        self, connector_type: str
    ) -> None:
        """Known registered connectors must be accepted."""
        valid, _ = validate_connector_registration(connector_type, True)
        assert valid is True

    def test_empty_connector_type_rejected(self) -> None:
        """Empty connector_type is always rejected."""
        valid, msg = validate_connector_registration("", True)
        assert valid is False
        assert "required" in msg

    @given(
        status=st.sampled_from(["enabled", "disabled", "created", "error"])
    )
    @settings(max_examples=50)
    def test_disable_only_from_enabled(self, status: str) -> None:
        """Only 'enabled' integrations can be disabled."""
        valid, _ = validate_disable_precondition(True, status)
        if status == "enabled":
            assert valid is True
        else:
            assert valid is False

    @given(tenant_id=st.text(min_size=0, max_size=50))
    @settings(max_examples=200)
    def test_query_requires_non_empty_tenant(self, tenant_id: str) -> None:
        """Query validation rejects empty/missing tenant_id."""
        valid, _ = validate_query_tenant_scope(tenant_id)
        if tenant_id:
            assert valid is True
        else:
            assert valid is False
