# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-9 Tenant Lifecycle States
# Callers: Lifecycle provider, auth middleware, protection
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)

"""
Phase-9 Tenant Lifecycle States

PIN-400 Phase-9: A tenant must be able to leave the system safely,
deterministically, and irreversibly.

This module defines the lifecycle states that govern tenant runtime existence.

RELATIONSHIP TO ONBOARDING:
    OnboardingState answers: "Did you ever earn the right to run?"
    LifecycleState answers:  "Are you currently allowed to run?"

    OnboardingState.COMPLETE causes entry into TenantLifecycleState.ACTIVE.
    They are ADJACENT state machines, not the same machine.
    No back-references. No coupling.

DESIGN INVARIANTS (LOCKED):
- OFFBOARD-001: Lifecycle transitions are monotonic
- OFFBOARD-002: TERMINATED is irreversible
- OFFBOARD-003: ARCHIVED is unreachable from ACTIVE
- OFFBOARD-004: No customer-initiated offboarding mutations
"""

from enum import IntEnum
from typing import Set, Tuple


class TenantLifecycleState(IntEnum):
    """
    Tenant lifecycle states (runtime existence).

    Values are monotonically increasing — higher values are more terminal.
    This enforces OFFBOARD-001 (monotonic transitions) mechanically.

    State semantics:
    - ACTIVE (100): Normal operation, all systems enabled
    - SUSPENDED (200): Temporary halt, reversible to ACTIVE
    - TERMINATED (300): Permanent shutdown, irreversible
    - ARCHIVED (400): Cold storage / compliance boundary, terminal-terminal
    """

    ACTIVE = 100
    SUSPENDED = 200
    TERMINATED = 300
    ARCHIVED = 400

    def allows_sdk_execution(self) -> bool:
        """Check if SDK execution is allowed in this state."""
        return self == TenantLifecycleState.ACTIVE

    def allows_writes(self) -> bool:
        """Check if data writes are allowed in this state."""
        return self == TenantLifecycleState.ACTIVE

    def allows_reads(self) -> bool:
        """Check if data reads are allowed in this state."""
        return self in (
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.SUSPENDED,
        )

    def allows_new_api_keys(self) -> bool:
        """Check if new API keys can be created in this state."""
        return self == TenantLifecycleState.ACTIVE

    def allows_token_refresh(self) -> bool:
        """Check if auth token refresh is allowed in this state."""
        return self in (
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.SUSPENDED,
        )

    def is_terminal(self) -> bool:
        """Check if this is a terminal state (no return to ACTIVE)."""
        return self >= TenantLifecycleState.TERMINATED

    def is_reversible(self) -> bool:
        """Check if this state can be reversed to ACTIVE."""
        return self == TenantLifecycleState.SUSPENDED


# Valid transitions matrix (from_state -> set of valid to_states)
# Enforces OFFBOARD-001 (monotonic), OFFBOARD-002 (TERMINATED irreversible),
# OFFBOARD-003 (ARCHIVED unreachable from ACTIVE)
VALID_TRANSITIONS: dict[TenantLifecycleState, Set[TenantLifecycleState]] = {
    TenantLifecycleState.ACTIVE: {
        TenantLifecycleState.SUSPENDED,
        TenantLifecycleState.TERMINATED,
    },
    TenantLifecycleState.SUSPENDED: {
        TenantLifecycleState.ACTIVE,  # resume (only reversible path)
        TenantLifecycleState.TERMINATED,
    },
    TenantLifecycleState.TERMINATED: {
        TenantLifecycleState.ARCHIVED,
    },
    TenantLifecycleState.ARCHIVED: set(),  # terminal-terminal, no exits
}


def is_valid_transition(
    from_state: TenantLifecycleState,
    to_state: TenantLifecycleState,
) -> bool:
    """
    Check if a lifecycle transition is valid.

    Enforces:
    - OFFBOARD-001: Monotonic transitions (except SUSPENDED -> ACTIVE)
    - OFFBOARD-002: TERMINATED is irreversible
    - OFFBOARD-003: ARCHIVED is unreachable from ACTIVE
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_valid_transitions(
    from_state: TenantLifecycleState,
) -> Set[TenantLifecycleState]:
    """Get all valid target states from a given state."""
    return VALID_TRANSITIONS.get(from_state, set()).copy()


# Transition actions (named actions that map to state changes)
class LifecycleAction:
    """Named lifecycle actions that trigger state transitions."""

    SUSPEND = "suspend_tenant"
    RESUME = "resume_tenant"
    TERMINATE = "terminate_tenant"
    ARCHIVE = "archive_tenant"


# Action to transition mapping
ACTION_TRANSITIONS: dict[str, Tuple[Set[TenantLifecycleState], TenantLifecycleState]] = {
    LifecycleAction.SUSPEND: (
        {TenantLifecycleState.ACTIVE},
        TenantLifecycleState.SUSPENDED,
    ),
    LifecycleAction.RESUME: (
        {TenantLifecycleState.SUSPENDED},
        TenantLifecycleState.ACTIVE,
    ),
    LifecycleAction.TERMINATE: (
        {TenantLifecycleState.ACTIVE, TenantLifecycleState.SUSPENDED},
        TenantLifecycleState.TERMINATED,
    ),
    LifecycleAction.ARCHIVE: (
        {TenantLifecycleState.TERMINATED},
        TenantLifecycleState.ARCHIVED,
    ),
}


def get_action_for_transition(
    from_state: TenantLifecycleState,
    to_state: TenantLifecycleState,
) -> str | None:
    """Get the action name for a given transition, if valid."""
    for action, (valid_from, target) in ACTION_TRANSITIONS.items():
        if from_state in valid_from and to_state == target:
            return action
    return None


__all__ = [
    "TenantLifecycleState",
    "LifecycleAction",
    "VALID_TRANSITIONS",
    "ACTION_TRANSITIONS",
    "is_valid_transition",
    "get_valid_transitions",
    "get_action_for_transition",
]
