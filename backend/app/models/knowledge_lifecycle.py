# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: GAP-089 Knowledge Plane Lifecycle State Machine
# Callers: KnowledgeLifecycleManager, SDK facade, policy gates
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-089, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.2

"""
GAP-089: Knowledge Plane Lifecycle State Machine

This module defines the lifecycle states and valid transitions for knowledge planes.
Knowledge planes follow a strict lifecycle from registration through activation,
and optionally through deactivation and purge.

ARCHITECTURAL PRINCIPLE:
    Lifecycle operations are governance-controlled, not user-controlled.
    SDK calls REQUEST transitions. LifecycleManager DECIDES.
    Policy + state machine ARBITRATE.

DESIGN INVARIANTS (LOCKED):
- LIFECYCLE-001: States are ordered (draft < active < purged)
- LIFECYCLE-002: Cannot skip states (must complete verification before ingestion)
- LIFECYCLE-003: PURGED is irreversible
- LIFECYCLE-004: ACTIVE requires policy binding (GAP-087 gate)
- LIFECYCLE-005: Every transition emits audit event (GAP-088)
- LIFECYCLE-006: Offboarding requires dependency checks

STATE MACHINE:
    ONBOARDING PATH:
    DRAFT → PENDING_VERIFY → VERIFIED → INGESTING → INDEXED →
    CLASSIFIED → PENDING_ACTIVATE → ACTIVE

    OFFBOARDING PATH:
    ACTIVE → PENDING_DEACTIVATE → DEACTIVATED → ARCHIVED → PURGED
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Set, Tuple, Optional


class KnowledgePlaneLifecycleState(IntEnum):
    """
    Knowledge plane lifecycle states.

    Values are ordered — higher values represent further progression.
    This allows simple comparison: state_a < state_b means a is earlier.

    State categories:
    - ONBOARDING (100-199): Registration through activation
    - OPERATIONAL (200-299): Normal operation
    - OFFBOARDING (300-399): Deactivation through purge
    - TERMINAL (400+): Final states
    """

    # === ONBOARDING STATES (100-199) ===
    DRAFT = 100  # Registered but not verified
    PENDING_VERIFY = 110  # Verification in progress
    VERIFIED = 120  # Connectivity/credentials confirmed
    INGESTING = 130  # Data ingestion in progress (async)
    INDEXED = 140  # Data indexed/vectorized
    CLASSIFIED = 150  # Data classified (sensitivity, schema)
    PENDING_ACTIVATE = 160  # Awaiting policy binding (GAP-087 gate)

    # === OPERATIONAL STATES (200-299) ===
    ACTIVE = 200  # Fully operational, policies bound

    # === OFFBOARDING STATES (300-399) ===
    PENDING_DEACTIVATE = 300  # Deregistration requested, grace period
    DEACTIVATED = 310  # Soft-deleted, no new runs, data preserved
    ARCHIVED = 320  # Exported to cold storage

    # === TERMINAL STATES (400+) ===
    PURGED = 400  # Data deleted, audit trail preserved

    # === ERROR STATES (500+) ===
    FAILED = 500  # Unrecoverable failure during lifecycle

    # === State category helpers ===

    def is_onboarding(self) -> bool:
        """Check if state is in onboarding phase."""
        return 100 <= self.value < 200

    def is_operational(self) -> bool:
        """Check if state is operational (ACTIVE)."""
        return 200 <= self.value < 300

    def is_offboarding(self) -> bool:
        """Check if state is in offboarding phase."""
        return 300 <= self.value < 400

    def is_terminal(self) -> bool:
        """Check if state is terminal (no further transitions except FAILED)."""
        return self.value >= 400

    def is_failed(self) -> bool:
        """Check if state is a failure state."""
        return self.value >= 500

    # === Capability helpers ===

    def allows_queries(self) -> bool:
        """Check if queries against this knowledge plane are allowed."""
        return self == KnowledgePlaneLifecycleState.ACTIVE

    def allows_policy_binding(self) -> bool:
        """Check if policies can be bound to this knowledge plane."""
        return self in (
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        )

    def allows_new_runs(self) -> bool:
        """Check if new runs can use this knowledge plane."""
        return self == KnowledgePlaneLifecycleState.ACTIVE

    def allows_modifications(self) -> bool:
        """Check if the knowledge plane configuration can be modified."""
        return self.is_onboarding() or self.is_operational()

    def requires_async_job(self) -> bool:
        """Check if this state involves an async background job."""
        return self in (
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.ARCHIVED,  # export job
        )

    def requires_policy_gate(self) -> bool:
        """Check if transition FROM this state requires policy gate (GAP-087)."""
        return self in (
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,  # → ACTIVE
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,  # → DEACTIVATED
            KnowledgePlaneLifecycleState.ARCHIVED,  # → PURGED
        )


# === Valid Transitions Matrix ===
# Enforces LIFECYCLE-002 (no skipping states)

VALID_TRANSITIONS: dict[KnowledgePlaneLifecycleState, Set[KnowledgePlaneLifecycleState]] = {
    # Onboarding path
    KnowledgePlaneLifecycleState.DRAFT: {
        KnowledgePlaneLifecycleState.PENDING_VERIFY,
        KnowledgePlaneLifecycleState.FAILED,  # registration failure
    },
    KnowledgePlaneLifecycleState.PENDING_VERIFY: {
        KnowledgePlaneLifecycleState.VERIFIED,
        KnowledgePlaneLifecycleState.DRAFT,  # verification failed, retry
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.VERIFIED: {
        KnowledgePlaneLifecycleState.INGESTING,
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.INGESTING: {
        KnowledgePlaneLifecycleState.INDEXED,
        KnowledgePlaneLifecycleState.VERIFIED,  # ingestion failed, retry
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.INDEXED: {
        KnowledgePlaneLifecycleState.CLASSIFIED,
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.CLASSIFIED: {
        KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.PENDING_ACTIVATE: {
        KnowledgePlaneLifecycleState.ACTIVE,  # requires GAP-087 policy gate
        KnowledgePlaneLifecycleState.CLASSIFIED,  # policy binding failed, retry
        KnowledgePlaneLifecycleState.FAILED,
    },
    # Operational (can start offboarding)
    KnowledgePlaneLifecycleState.ACTIVE: {
        KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
    },
    # Offboarding path
    KnowledgePlaneLifecycleState.PENDING_DEACTIVATE: {
        KnowledgePlaneLifecycleState.DEACTIVATED,  # requires GAP-087 policy gate
        KnowledgePlaneLifecycleState.ACTIVE,  # cancel deactivation (grace period)
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.DEACTIVATED: {
        KnowledgePlaneLifecycleState.ARCHIVED,
        KnowledgePlaneLifecycleState.FAILED,
    },
    KnowledgePlaneLifecycleState.ARCHIVED: {
        KnowledgePlaneLifecycleState.PURGED,  # requires GAP-087 policy gate
        KnowledgePlaneLifecycleState.FAILED,
    },
    # Terminal states - no exits
    KnowledgePlaneLifecycleState.PURGED: set(),
    KnowledgePlaneLifecycleState.FAILED: set(),  # manual intervention required
}


# === Transition Actions ===
# Named actions that map to state changes (for SDK facade)


class LifecycleAction:
    """Named lifecycle actions that trigger state transitions."""

    # Onboarding actions
    REGISTER = "register_knowledge_plane"
    VERIFY = "verify_knowledge_plane"
    INGEST = "ingest_knowledge_plane"
    INDEX = "index_knowledge_plane"
    CLASSIFY = "classify_knowledge_plane"
    ACTIVATE = "activate_knowledge_plane"

    # Offboarding actions
    DEREGISTER = "deregister_knowledge_plane"
    CANCEL_DEREGISTER = "cancel_deregister_knowledge_plane"
    DEACTIVATE = "deactivate_knowledge_plane"
    ARCHIVE = "archive_knowledge_plane"
    PURGE = "purge_knowledge_plane"

    # Recovery actions
    RETRY = "retry_knowledge_plane"
    FAIL = "fail_knowledge_plane"


# Action to transition mapping: (valid_from_states, target_state)
ACTION_TRANSITIONS: dict[str, Tuple[Set[KnowledgePlaneLifecycleState], KnowledgePlaneLifecycleState]] = {
    # Onboarding
    LifecycleAction.REGISTER: (
        set(),  # No prior state (creation)
        KnowledgePlaneLifecycleState.DRAFT,
    ),
    LifecycleAction.VERIFY: (
        {KnowledgePlaneLifecycleState.DRAFT},
        KnowledgePlaneLifecycleState.PENDING_VERIFY,
    ),
    LifecycleAction.INGEST: (
        {KnowledgePlaneLifecycleState.VERIFIED},
        KnowledgePlaneLifecycleState.INGESTING,
    ),
    LifecycleAction.INDEX: (
        {KnowledgePlaneLifecycleState.INGESTING},
        KnowledgePlaneLifecycleState.INDEXED,
    ),
    LifecycleAction.CLASSIFY: (
        {KnowledgePlaneLifecycleState.INDEXED},
        KnowledgePlaneLifecycleState.CLASSIFIED,
    ),
    LifecycleAction.ACTIVATE: (
        {KnowledgePlaneLifecycleState.PENDING_ACTIVATE},
        KnowledgePlaneLifecycleState.ACTIVE,
    ),
    # Separate action to move from CLASSIFIED to PENDING_ACTIVATE
    "request_activation": (
        {KnowledgePlaneLifecycleState.CLASSIFIED},
        KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
    ),
    # Offboarding
    LifecycleAction.DEREGISTER: (
        {KnowledgePlaneLifecycleState.ACTIVE},
        KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
    ),
    LifecycleAction.CANCEL_DEREGISTER: (
        {KnowledgePlaneLifecycleState.PENDING_DEACTIVATE},
        KnowledgePlaneLifecycleState.ACTIVE,
    ),
    LifecycleAction.DEACTIVATE: (
        {KnowledgePlaneLifecycleState.PENDING_DEACTIVATE},
        KnowledgePlaneLifecycleState.DEACTIVATED,
    ),
    LifecycleAction.ARCHIVE: (
        {KnowledgePlaneLifecycleState.DEACTIVATED},
        KnowledgePlaneLifecycleState.ARCHIVED,
    ),
    LifecycleAction.PURGE: (
        {KnowledgePlaneLifecycleState.ARCHIVED},
        KnowledgePlaneLifecycleState.PURGED,
    ),
}

# States that can accept job_complete action (async states)
JOB_COMPLETE_STATES: Set[KnowledgePlaneLifecycleState] = {
    KnowledgePlaneLifecycleState.PENDING_VERIFY,
    KnowledgePlaneLifecycleState.INGESTING,
    KnowledgePlaneLifecycleState.ARCHIVED,  # export job
}


# === Transition Result ===


@dataclass(frozen=True)
class TransitionResult:
    """Result of a lifecycle transition attempt."""

    allowed: bool
    from_state: KnowledgePlaneLifecycleState
    to_state: KnowledgePlaneLifecycleState
    reason: Optional[str] = None
    requires_gate: bool = False  # True if GAP-087 policy gate required
    requires_async: bool = False  # True if async job required

    def __bool__(self) -> bool:
        return self.allowed


# === Validation Functions ===


def is_valid_transition(
    from_state: KnowledgePlaneLifecycleState,
    to_state: KnowledgePlaneLifecycleState,
) -> bool:
    """
    Check if a lifecycle transition is valid.

    Enforces:
    - LIFECYCLE-002: Cannot skip states
    - LIFECYCLE-003: PURGED is irreversible
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_valid_transitions(
    from_state: KnowledgePlaneLifecycleState,
) -> Set[KnowledgePlaneLifecycleState]:
    """Get all valid target states from a given state."""
    return VALID_TRANSITIONS.get(from_state, set()).copy()


def validate_transition(
    from_state: KnowledgePlaneLifecycleState,
    to_state: KnowledgePlaneLifecycleState,
) -> TransitionResult:
    """
    Validate a lifecycle transition and return detailed result.

    Returns TransitionResult with:
    - allowed: Whether transition is valid
    - reason: If blocked, why
    - requires_gate: If GAP-087 policy gate check is required
    - requires_async: If transition involves async job
    """
    if not is_valid_transition(from_state, to_state):
        valid = get_valid_transitions(from_state)
        return TransitionResult(
            allowed=False,
            from_state=from_state,
            to_state=to_state,
            reason=f"Invalid transition: {from_state.name} → {to_state.name}. "
            f"Valid targets: {[s.name for s in valid]}",
        )

    # Check if policy gate required
    requires_gate = from_state.requires_policy_gate() and to_state in (
        KnowledgePlaneLifecycleState.ACTIVE,
        KnowledgePlaneLifecycleState.DEACTIVATED,
        KnowledgePlaneLifecycleState.PURGED,
    )

    # Check if async job required
    requires_async = to_state.requires_async_job()

    return TransitionResult(
        allowed=True,
        from_state=from_state,
        to_state=to_state,
        requires_gate=requires_gate,
        requires_async=requires_async,
    )


def get_action_for_transition(
    from_state: KnowledgePlaneLifecycleState,
    to_state: KnowledgePlaneLifecycleState,
) -> Optional[str]:
    """Get the action name for a given transition, if valid."""
    for action, (valid_from, target) in ACTION_TRANSITIONS.items():
        if from_state in valid_from and to_state == target:
            return action
    return None


def get_transition_for_action(
    action: str,
    current_state: KnowledgePlaneLifecycleState,
) -> Optional[KnowledgePlaneLifecycleState]:
    """Get the target state for an action from current state, if valid."""
    # Special handling for job_complete action - target depends on current state
    if action == "job_complete":
        if current_state in JOB_COMPLETE_STATES:
            # Return next state in progression for async state completion
            return get_next_onboarding_state(current_state)
        return None

    if action not in ACTION_TRANSITIONS:
        return None
    valid_from, target = ACTION_TRANSITIONS[action]
    if current_state in valid_from:
        return target
    return None


# === State Progression Helpers ===


def get_next_onboarding_state(
    current: KnowledgePlaneLifecycleState,
) -> Optional[KnowledgePlaneLifecycleState]:
    """Get the next state in the onboarding path, if applicable."""
    progression = [
        KnowledgePlaneLifecycleState.DRAFT,
        KnowledgePlaneLifecycleState.PENDING_VERIFY,
        KnowledgePlaneLifecycleState.VERIFIED,
        KnowledgePlaneLifecycleState.INGESTING,
        KnowledgePlaneLifecycleState.INDEXED,
        KnowledgePlaneLifecycleState.CLASSIFIED,
        KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        KnowledgePlaneLifecycleState.ACTIVE,
    ]
    try:
        idx = progression.index(current)
        if idx + 1 < len(progression):
            return progression[idx + 1]
    except ValueError:
        pass
    return None


def get_next_offboarding_state(
    current: KnowledgePlaneLifecycleState,
) -> Optional[KnowledgePlaneLifecycleState]:
    """Get the next state in the offboarding path, if applicable."""
    progression = [
        KnowledgePlaneLifecycleState.ACTIVE,
        KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
        KnowledgePlaneLifecycleState.DEACTIVATED,
        KnowledgePlaneLifecycleState.ARCHIVED,
        KnowledgePlaneLifecycleState.PURGED,
    ]
    try:
        idx = progression.index(current)
        if idx + 1 < len(progression):
            return progression[idx + 1]
    except ValueError:
        pass
    return None


# === Illegal Transitions (for documentation/testing) ===

ILLEGAL_TRANSITIONS: list[Tuple[KnowledgePlaneLifecycleState, KnowledgePlaneLifecycleState, str]] = [
    (
        KnowledgePlaneLifecycleState.DRAFT,
        KnowledgePlaneLifecycleState.ACTIVE,
        "Must complete verification + ingestion",
    ),
    (
        KnowledgePlaneLifecycleState.ACTIVE,
        KnowledgePlaneLifecycleState.PURGED,
        "Must go through deactivate + archive",
    ),
    # Note: PENDING_ACTIVATE → ACTIVE is VALID in state machine but GATED by policy.
    # It's tested in policy_gate_dominance tests, not here.
    (
        KnowledgePlaneLifecycleState.DEACTIVATED,
        KnowledgePlaneLifecycleState.PURGED,
        "Must archive first",
    ),
    (
        KnowledgePlaneLifecycleState.PURGED,
        KnowledgePlaneLifecycleState.ACTIVE,
        "PURGED is terminal and irreversible",
    ),
]


__all__ = [
    "KnowledgePlaneLifecycleState",
    "LifecycleAction",
    "TransitionResult",
    "VALID_TRANSITIONS",
    "ACTION_TRANSITIONS",
    "ILLEGAL_TRANSITIONS",
    "is_valid_transition",
    "get_valid_transitions",
    "validate_transition",
    "get_action_for_transition",
    "get_transition_for_action",
    "get_next_onboarding_state",
    "get_next_offboarding_state",
]
