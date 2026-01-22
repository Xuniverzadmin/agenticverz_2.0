# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: T4 State Machine Invariants Tests (GAP-089)
# Callers: pytest, CI
# Allowed Imports: L4 (models)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-089, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.2

"""
T4 State Machine Invariants Tests (GAP-089)

These tests verify the knowledge plane lifecycle state machine enforces:
1. Every valid transition is allowed
2. Every invalid transition is rejected
3. FAILED and PURGED are terminal (no exits)
4. State category helpers work correctly
5. Capability helpers respect state boundaries

Test Count Target: ~80 tests

INVARIANTS UNDER TEST:
- LIFECYCLE-001: States are ordered (draft < active < purged)
- LIFECYCLE-002: Cannot skip states (must complete verification before ingestion)
- LIFECYCLE-003: PURGED is irreversible
- LIFECYCLE-004: ACTIVE requires policy binding (tested in policy gate tests)
- LIFECYCLE-005: Every transition emits audit event (tested in audit tests)
- LIFECYCLE-006: Offboarding requires dependency checks (tested in policy gate tests)
"""

import pytest
from typing import Set

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
    TransitionResult,
    VALID_TRANSITIONS,
    ACTION_TRANSITIONS,
    ILLEGAL_TRANSITIONS,
    is_valid_transition,
    get_valid_transitions,
    validate_transition,
    get_action_for_transition,
    get_transition_for_action,
    get_next_onboarding_state,
    get_next_offboarding_state,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def all_states() -> list[KnowledgePlaneLifecycleState]:
    """Return all lifecycle states."""
    return list(KnowledgePlaneLifecycleState)


@pytest.fixture
def onboarding_states() -> list[KnowledgePlaneLifecycleState]:
    """Return onboarding states in order."""
    return [
        KnowledgePlaneLifecycleState.DRAFT,
        KnowledgePlaneLifecycleState.PENDING_VERIFY,
        KnowledgePlaneLifecycleState.VERIFIED,
        KnowledgePlaneLifecycleState.INGESTING,
        KnowledgePlaneLifecycleState.INDEXED,
        KnowledgePlaneLifecycleState.CLASSIFIED,
        KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
    ]


@pytest.fixture
def offboarding_states() -> list[KnowledgePlaneLifecycleState]:
    """Return offboarding states in order."""
    return [
        KnowledgePlaneLifecycleState.ACTIVE,
        KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
        KnowledgePlaneLifecycleState.DEACTIVATED,
        KnowledgePlaneLifecycleState.ARCHIVED,
        KnowledgePlaneLifecycleState.PURGED,
    ]


@pytest.fixture
def terminal_states() -> list[KnowledgePlaneLifecycleState]:
    """Return terminal states (no valid exits)."""
    return [
        KnowledgePlaneLifecycleState.PURGED,
        KnowledgePlaneLifecycleState.FAILED,
    ]


# =============================================================================
# INV-001: Valid Transitions Work
# =============================================================================


class TestValidTransitionsAccepted:
    """Tests that all declared valid transitions are accepted."""

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Onboarding happy path
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.PENDING_VERIFY),
            (KnowledgePlaneLifecycleState.PENDING_VERIFY, KnowledgePlaneLifecycleState.VERIFIED),
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.INGESTING),
            (KnowledgePlaneLifecycleState.INGESTING, KnowledgePlaneLifecycleState.INDEXED),
            (KnowledgePlaneLifecycleState.INDEXED, KnowledgePlaneLifecycleState.CLASSIFIED),
            (KnowledgePlaneLifecycleState.CLASSIFIED, KnowledgePlaneLifecycleState.PENDING_ACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_ACTIVATE, KnowledgePlaneLifecycleState.ACTIVE),
        ],
    )
    def test_onboarding_happy_path_transitions_valid(
        self, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState
    ):
        """Onboarding happy path transitions must be valid."""
        assert is_valid_transition(from_state, to_state), (
            f"Expected valid transition: {from_state.name} → {to_state.name}"
        )

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Offboarding happy path
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PENDING_DEACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.DEACTIVATED),
            (KnowledgePlaneLifecycleState.DEACTIVATED, KnowledgePlaneLifecycleState.ARCHIVED),
            (KnowledgePlaneLifecycleState.ARCHIVED, KnowledgePlaneLifecycleState.PURGED),
        ],
    )
    def test_offboarding_happy_path_transitions_valid(
        self, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState
    ):
        """Offboarding happy path transitions must be valid."""
        assert is_valid_transition(from_state, to_state), (
            f"Expected valid transition: {from_state.name} → {to_state.name}"
        )

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Retry paths (back transitions for error recovery)
            (KnowledgePlaneLifecycleState.PENDING_VERIFY, KnowledgePlaneLifecycleState.DRAFT),
            (KnowledgePlaneLifecycleState.INGESTING, KnowledgePlaneLifecycleState.VERIFIED),
            (KnowledgePlaneLifecycleState.PENDING_ACTIVATE, KnowledgePlaneLifecycleState.CLASSIFIED),
            # Cancel deactivation (grace period)
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.ACTIVE),
        ],
    )
    def test_retry_path_transitions_valid(
        self, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState
    ):
        """Retry/recovery path transitions must be valid."""
        assert is_valid_transition(from_state, to_state), (
            f"Expected valid retry transition: {from_state.name} → {to_state.name}"
        )

    @pytest.mark.parametrize(
        "from_state",
        [
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.INDEXED,
            KnowledgePlaneLifecycleState.CLASSIFIED,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
            KnowledgePlaneLifecycleState.ARCHIVED,
        ],
    )
    def test_failure_transition_valid_from_non_terminal(
        self, from_state: KnowledgePlaneLifecycleState
    ):
        """Transition to FAILED must be valid from non-terminal states."""
        if from_state not in [
            KnowledgePlaneLifecycleState.ACTIVE,
            KnowledgePlaneLifecycleState.PURGED,
            KnowledgePlaneLifecycleState.FAILED,
        ]:
            assert is_valid_transition(from_state, KnowledgePlaneLifecycleState.FAILED), (
                f"Expected valid transition to FAILED from {from_state.name}"
            )

    def test_all_declared_transitions_are_valid(self):
        """Every transition in VALID_TRANSITIONS must pass is_valid_transition."""
        for from_state, to_states in VALID_TRANSITIONS.items():
            for to_state in to_states:
                assert is_valid_transition(from_state, to_state), (
                    f"Declared valid transition not accepted: {from_state.name} → {to_state.name}"
                )


# =============================================================================
# INV-002: Invalid Transitions Rejected (Cannot Skip States)
# =============================================================================


class TestInvalidTransitionsRejected:
    """Tests that invalid transitions are rejected."""

    @pytest.mark.parametrize(
        "from_state,to_state,reason",
        ILLEGAL_TRANSITIONS,
    )
    def test_documented_illegal_transitions_rejected(
        self,
        from_state: KnowledgePlaneLifecycleState,
        to_state: KnowledgePlaneLifecycleState,
        reason: str,
    ):
        """Documented illegal transitions must be rejected."""
        assert not is_valid_transition(from_state, to_state), (
            f"Illegal transition was accepted: {from_state.name} → {to_state.name} ({reason})"
        )

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Skip verification
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.VERIFIED),
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.INGESTING),
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.ACTIVE),
            # Skip ingestion
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.INDEXED),
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.CLASSIFIED),
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.ACTIVE),
            # Skip classification
            (KnowledgePlaneLifecycleState.INDEXED, KnowledgePlaneLifecycleState.PENDING_ACTIVATE),
            (KnowledgePlaneLifecycleState.INDEXED, KnowledgePlaneLifecycleState.ACTIVE),
            # Skip offboarding stages
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.DEACTIVATED),
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.ARCHIVED),
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PURGED),
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.ARCHIVED),
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.PURGED),
            (KnowledgePlaneLifecycleState.DEACTIVATED, KnowledgePlaneLifecycleState.PURGED),
        ],
    )
    def test_state_skipping_rejected(
        self, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState
    ):
        """Cannot skip states in the lifecycle (LIFECYCLE-002)."""
        assert not is_valid_transition(from_state, to_state), (
            f"State skipping was allowed: {from_state.name} → {to_state.name}"
        )

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # Backward jumps across phases
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.DRAFT),
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PENDING_VERIFY),
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.VERIFIED),
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.INGESTING),
            (KnowledgePlaneLifecycleState.DEACTIVATED, KnowledgePlaneLifecycleState.ACTIVE),
            (KnowledgePlaneLifecycleState.ARCHIVED, KnowledgePlaneLifecycleState.ACTIVE),
            (KnowledgePlaneLifecycleState.ARCHIVED, KnowledgePlaneLifecycleState.DEACTIVATED),
        ],
    )
    def test_backward_phase_jumps_rejected(
        self, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState
    ):
        """Cannot jump backward across lifecycle phases."""
        assert not is_valid_transition(from_state, to_state), (
            f"Backward phase jump was allowed: {from_state.name} → {to_state.name}"
        )

    def test_self_transition_rejected(self, all_states: list[KnowledgePlaneLifecycleState]):
        """Self-transitions (state → same state) must be rejected."""
        for state in all_states:
            assert not is_valid_transition(state, state), (
                f"Self-transition was allowed: {state.name} → {state.name}"
            )


# =============================================================================
# INV-003: Terminal States Have No Exits
# =============================================================================


class TestTerminalStatesAreTerminal:
    """Tests that terminal states (PURGED, FAILED) have no exits."""

    def test_purged_has_no_exits(self):
        """PURGED must have no valid exit transitions (LIFECYCLE-003)."""
        exits = get_valid_transitions(KnowledgePlaneLifecycleState.PURGED)
        assert len(exits) == 0, (
            f"PURGED should have no exits but has: {[s.name for s in exits]}"
        )

    def test_failed_has_no_exits(self):
        """FAILED must have no valid exit transitions (manual intervention required)."""
        exits = get_valid_transitions(KnowledgePlaneLifecycleState.FAILED)
        assert len(exits) == 0, (
            f"FAILED should have no exits but has: {[s.name for s in exits]}"
        )

    @pytest.mark.parametrize(
        "to_state",
        list(KnowledgePlaneLifecycleState),
    )
    def test_purged_cannot_transition_to_any_state(
        self, to_state: KnowledgePlaneLifecycleState
    ):
        """PURGED cannot transition to any state including itself."""
        assert not is_valid_transition(KnowledgePlaneLifecycleState.PURGED, to_state), (
            f"PURGED was able to transition to {to_state.name}"
        )

    @pytest.mark.parametrize(
        "to_state",
        list(KnowledgePlaneLifecycleState),
    )
    def test_failed_cannot_transition_to_any_state(
        self, to_state: KnowledgePlaneLifecycleState
    ):
        """FAILED cannot transition to any state including itself."""
        assert not is_valid_transition(KnowledgePlaneLifecycleState.FAILED, to_state), (
            f"FAILED was able to transition to {to_state.name}"
        )

    def test_terminal_states_identified_correctly(
        self, terminal_states: list[KnowledgePlaneLifecycleState]
    ):
        """Terminal states must be identified by is_terminal()."""
        for state in terminal_states:
            assert state.is_terminal(), f"{state.name} should be terminal"

    def test_non_terminal_states_not_terminal(
        self, all_states: list[KnowledgePlaneLifecycleState],
        terminal_states: list[KnowledgePlaneLifecycleState],
    ):
        """Non-terminal states must not be identified as terminal."""
        for state in all_states:
            if state not in terminal_states:
                assert not state.is_terminal(), f"{state.name} should not be terminal"


# =============================================================================
# State Category Helpers
# =============================================================================


class TestStateCategoryHelpers:
    """Tests for state category helper methods."""

    def test_onboarding_states_identified(
        self, onboarding_states: list[KnowledgePlaneLifecycleState]
    ):
        """Onboarding states (100-199) must be identified correctly."""
        for state in onboarding_states:
            assert state.is_onboarding(), f"{state.name} should be onboarding"

    def test_non_onboarding_states_not_onboarding(
        self,
        all_states: list[KnowledgePlaneLifecycleState],
        onboarding_states: list[KnowledgePlaneLifecycleState],
    ):
        """Non-onboarding states must not be identified as onboarding."""
        for state in all_states:
            if state not in onboarding_states:
                assert not state.is_onboarding(), f"{state.name} should not be onboarding"

    def test_active_is_operational(self):
        """ACTIVE must be identified as operational."""
        assert KnowledgePlaneLifecycleState.ACTIVE.is_operational()

    def test_non_active_states_not_operational(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Only ACTIVE should be identified as operational."""
        for state in all_states:
            if state != KnowledgePlaneLifecycleState.ACTIVE:
                assert not state.is_operational(), f"{state.name} should not be operational"

    @pytest.mark.parametrize(
        "state",
        [
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
            KnowledgePlaneLifecycleState.ARCHIVED,
        ],
    )
    def test_offboarding_states_identified(self, state: KnowledgePlaneLifecycleState):
        """Offboarding states (300-399) must be identified correctly."""
        assert state.is_offboarding(), f"{state.name} should be offboarding"

    def test_failed_state_identified(self):
        """FAILED must be identified by is_failed()."""
        assert KnowledgePlaneLifecycleState.FAILED.is_failed()

    def test_non_failed_states_not_failed(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Only FAILED should return True for is_failed()."""
        for state in all_states:
            if state != KnowledgePlaneLifecycleState.FAILED:
                assert not state.is_failed(), f"{state.name} should not be failed"


# =============================================================================
# Capability Helpers
# =============================================================================


class TestCapabilityHelpers:
    """Tests for state capability helper methods."""

    def test_only_active_allows_queries(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Only ACTIVE state should allow queries."""
        for state in all_states:
            if state == KnowledgePlaneLifecycleState.ACTIVE:
                assert state.allows_queries(), "ACTIVE should allow queries"
            else:
                assert not state.allows_queries(), f"{state.name} should not allow queries"

    def test_only_active_allows_new_runs(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Only ACTIVE state should allow new runs."""
        for state in all_states:
            if state == KnowledgePlaneLifecycleState.ACTIVE:
                assert state.allows_new_runs(), "ACTIVE should allow new runs"
            else:
                assert not state.allows_new_runs(), f"{state.name} should not allow new runs"

    @pytest.mark.parametrize(
        "state",
        [
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        ],
    )
    def test_policy_binding_allowed_states(self, state: KnowledgePlaneLifecycleState):
        """Policy binding should be allowed in PENDING_ACTIVATE and ACTIVE."""
        assert state.allows_policy_binding(), f"{state.name} should allow policy binding"

    def test_policy_binding_not_allowed_in_other_states(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Policy binding should not be allowed in non-activation states."""
        allowed = {
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        }
        for state in all_states:
            if state not in allowed:
                assert not state.allows_policy_binding(), (
                    f"{state.name} should not allow policy binding"
                )

    @pytest.mark.parametrize(
        "state",
        [
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.ARCHIVED,
        ],
    )
    def test_async_job_states(self, state: KnowledgePlaneLifecycleState):
        """States involving async jobs should be identified."""
        assert state.requires_async_job(), f"{state.name} should require async job"

    @pytest.mark.parametrize(
        "state",
        [
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.ARCHIVED,
        ],
    )
    def test_policy_gate_states(self, state: KnowledgePlaneLifecycleState):
        """States requiring policy gate should be identified."""
        assert state.requires_policy_gate(), f"{state.name} should require policy gate"

    def test_modifications_allowed_in_onboarding_and_operational(
        self,
        onboarding_states: list[KnowledgePlaneLifecycleState],
    ):
        """Modifications should be allowed in onboarding and operational states."""
        for state in onboarding_states:
            assert state.allows_modifications(), f"{state.name} should allow modifications"
        assert KnowledgePlaneLifecycleState.ACTIVE.allows_modifications()

    def test_modifications_not_allowed_in_offboarding_or_terminal(
        self,
        offboarding_states: list[KnowledgePlaneLifecycleState],
        terminal_states: list[KnowledgePlaneLifecycleState],
    ):
        """Modifications should not be allowed in offboarding or terminal states."""
        for state in offboarding_states:
            if state != KnowledgePlaneLifecycleState.ACTIVE:
                assert not state.allows_modifications(), (
                    f"{state.name} should not allow modifications"
                )
        for state in terminal_states:
            assert not state.allows_modifications(), (
                f"{state.name} should not allow modifications"
            )


# =============================================================================
# Transition Validation Details
# =============================================================================


class TestTransitionValidation:
    """Tests for validate_transition() function."""

    def test_valid_transition_returns_allowed(self):
        """Valid transitions should return TransitionResult with allowed=True."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert result.allowed is True
        assert result.from_state == KnowledgePlaneLifecycleState.DRAFT
        assert result.to_state == KnowledgePlaneLifecycleState.PENDING_VERIFY

    def test_invalid_transition_returns_not_allowed(self):
        """Invalid transitions should return TransitionResult with allowed=False."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.ACTIVE,
        )
        assert result.allowed is False
        assert result.reason is not None
        assert "Invalid transition" in result.reason

    def test_policy_gate_flagged_for_activation(self):
        """Transition to ACTIVE should flag policy gate requirement."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        )
        assert result.allowed is True
        assert result.requires_gate is True

    def test_policy_gate_flagged_for_deactivation(self):
        """Transition to DEACTIVATED should flag policy gate requirement."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
        )
        assert result.allowed is True
        assert result.requires_gate is True

    def test_policy_gate_flagged_for_purge(self):
        """Transition to PURGED should flag policy gate requirement."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.ARCHIVED,
            KnowledgePlaneLifecycleState.PURGED,
        )
        assert result.allowed is True
        assert result.requires_gate is True

    def test_async_flagged_for_pending_verify(self):
        """Transition to PENDING_VERIFY should flag async requirement."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert result.allowed is True
        assert result.requires_async is True

    def test_async_flagged_for_ingesting(self):
        """Transition to INGESTING should flag async requirement."""
        result = validate_transition(
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.INGESTING,
        )
        assert result.allowed is True
        assert result.requires_async is True

    def test_transition_result_bool_conversion(self):
        """TransitionResult should be truthy when allowed, falsy when not."""
        valid = validate_transition(
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        invalid = validate_transition(
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.ACTIVE,
        )
        assert bool(valid) is True
        assert bool(invalid) is False


# =============================================================================
# Action-to-Transition Mapping
# =============================================================================


class TestActionTransitionMapping:
    """Tests for action-to-transition mapping."""

    @pytest.mark.parametrize(
        "action,from_state,expected_to",
        [
            (LifecycleAction.VERIFY, KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.PENDING_VERIFY),
            (LifecycleAction.INGEST, KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.INGESTING),
            (LifecycleAction.CLASSIFY, KnowledgePlaneLifecycleState.INDEXED, KnowledgePlaneLifecycleState.CLASSIFIED),
            (LifecycleAction.DEREGISTER, KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PENDING_DEACTIVATE),
            (LifecycleAction.PURGE, KnowledgePlaneLifecycleState.ARCHIVED, KnowledgePlaneLifecycleState.PURGED),
        ],
    )
    def test_action_maps_to_correct_transition(
        self,
        action: str,
        from_state: KnowledgePlaneLifecycleState,
        expected_to: KnowledgePlaneLifecycleState,
    ):
        """Actions must map to their correct target states."""
        result = get_transition_for_action(action, from_state)
        assert result == expected_to, (
            f"Action {action} from {from_state.name} should map to {expected_to.name}, got {result}"
        )

    def test_invalid_action_returns_none(self):
        """Invalid actions should return None."""
        result = get_transition_for_action("invalid_action", KnowledgePlaneLifecycleState.DRAFT)
        assert result is None

    def test_action_from_wrong_state_returns_none(self):
        """Actions from invalid states should return None."""
        result = get_transition_for_action(
            LifecycleAction.PURGE,
            KnowledgePlaneLifecycleState.DRAFT,
        )
        assert result is None


# =============================================================================
# State Progression Helpers
# =============================================================================


class TestStateProgressionHelpers:
    """Tests for state progression helper functions."""

    @pytest.mark.parametrize(
        "current,expected_next",
        [
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.PENDING_VERIFY),
            (KnowledgePlaneLifecycleState.PENDING_VERIFY, KnowledgePlaneLifecycleState.VERIFIED),
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.INGESTING),
            (KnowledgePlaneLifecycleState.INGESTING, KnowledgePlaneLifecycleState.INDEXED),
            (KnowledgePlaneLifecycleState.INDEXED, KnowledgePlaneLifecycleState.CLASSIFIED),
            (KnowledgePlaneLifecycleState.CLASSIFIED, KnowledgePlaneLifecycleState.PENDING_ACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_ACTIVATE, KnowledgePlaneLifecycleState.ACTIVE),
        ],
    )
    def test_get_next_onboarding_state(
        self,
        current: KnowledgePlaneLifecycleState,
        expected_next: KnowledgePlaneLifecycleState,
    ):
        """get_next_onboarding_state returns correct next state."""
        result = get_next_onboarding_state(current)
        assert result == expected_next

    def test_get_next_onboarding_state_from_active_returns_none(self):
        """No onboarding state after ACTIVE."""
        result = get_next_onboarding_state(KnowledgePlaneLifecycleState.ACTIVE)
        assert result is None

    @pytest.mark.parametrize(
        "current,expected_next",
        [
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PENDING_DEACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.DEACTIVATED),
            (KnowledgePlaneLifecycleState.DEACTIVATED, KnowledgePlaneLifecycleState.ARCHIVED),
            (KnowledgePlaneLifecycleState.ARCHIVED, KnowledgePlaneLifecycleState.PURGED),
        ],
    )
    def test_get_next_offboarding_state(
        self,
        current: KnowledgePlaneLifecycleState,
        expected_next: KnowledgePlaneLifecycleState,
    ):
        """get_next_offboarding_state returns correct next state."""
        result = get_next_offboarding_state(current)
        assert result == expected_next

    def test_get_next_offboarding_state_from_purged_returns_none(self):
        """No offboarding state after PURGED."""
        result = get_next_offboarding_state(KnowledgePlaneLifecycleState.PURGED)
        assert result is None


# =============================================================================
# State Value Ordering (LIFECYCLE-001)
# =============================================================================


class TestStateValueOrdering:
    """Tests that state values are properly ordered for comparison."""

    def test_onboarding_states_increase(
        self, onboarding_states: list[KnowledgePlaneLifecycleState]
    ):
        """Onboarding states must have increasing values."""
        for i in range(len(onboarding_states) - 1):
            assert onboarding_states[i].value < onboarding_states[i + 1].value, (
                f"{onboarding_states[i].name} should have lower value than {onboarding_states[i + 1].name}"
            )

    def test_active_after_onboarding(
        self, onboarding_states: list[KnowledgePlaneLifecycleState]
    ):
        """ACTIVE must have higher value than all onboarding states."""
        for state in onboarding_states:
            assert state.value < KnowledgePlaneLifecycleState.ACTIVE.value

    def test_offboarding_after_active(self):
        """Offboarding states must have higher values than ACTIVE."""
        offboarding = [
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
            KnowledgePlaneLifecycleState.ARCHIVED,
            KnowledgePlaneLifecycleState.PURGED,
        ]
        for state in offboarding:
            assert state.value > KnowledgePlaneLifecycleState.ACTIVE.value

    def test_failed_has_highest_value(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """FAILED must have the highest value (error state)."""
        for state in all_states:
            if state != KnowledgePlaneLifecycleState.FAILED:
                assert state.value < KnowledgePlaneLifecycleState.FAILED.value


# =============================================================================
# Transition Matrix Completeness
# =============================================================================


class TestTransitionMatrixCompleteness:
    """Tests that the transition matrix is complete and consistent."""

    def test_all_states_have_transition_entry(
        self, all_states: list[KnowledgePlaneLifecycleState]
    ):
        """Every state must have an entry in VALID_TRANSITIONS."""
        for state in all_states:
            assert state in VALID_TRANSITIONS, (
                f"{state.name} missing from VALID_TRANSITIONS"
            )

    def test_transition_targets_are_valid_states(self):
        """All transition targets must be valid states."""
        valid_states = set(KnowledgePlaneLifecycleState)
        for from_state, to_states in VALID_TRANSITIONS.items():
            for to_state in to_states:
                assert to_state in valid_states, (
                    f"Invalid target state in {from_state.name} transitions"
                )

    def test_no_bidirectional_transitions_except_recovery(self):
        """
        Bidirectional transitions should only exist for recovery paths.
        E.g., PENDING_VERIFY ↔ DRAFT (retry verification)
        """
        allowed_bidirectional = {
            # Recovery: verification failed, retry
            (KnowledgePlaneLifecycleState.DRAFT, KnowledgePlaneLifecycleState.PENDING_VERIFY),
            (KnowledgePlaneLifecycleState.PENDING_VERIFY, KnowledgePlaneLifecycleState.DRAFT),
            # Recovery: ingestion failed, retry
            (KnowledgePlaneLifecycleState.VERIFIED, KnowledgePlaneLifecycleState.INGESTING),
            (KnowledgePlaneLifecycleState.INGESTING, KnowledgePlaneLifecycleState.VERIFIED),
            # Recovery: policy binding failed, retry
            (KnowledgePlaneLifecycleState.CLASSIFIED, KnowledgePlaneLifecycleState.PENDING_ACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_ACTIVATE, KnowledgePlaneLifecycleState.CLASSIFIED),
            # Grace period: cancel deactivation
            (KnowledgePlaneLifecycleState.ACTIVE, KnowledgePlaneLifecycleState.PENDING_DEACTIVATE),
            (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE, KnowledgePlaneLifecycleState.ACTIVE),
        }

        for from_state, to_states in VALID_TRANSITIONS.items():
            for to_state in to_states:
                if to_state in VALID_TRANSITIONS.get(to_state, set()):
                    pair = (from_state, to_state)
                    reverse = (to_state, from_state)
                    assert pair in allowed_bidirectional or reverse in allowed_bidirectional, (
                        f"Unexpected bidirectional transition: {from_state.name} ↔ {to_state.name}"
                    )
