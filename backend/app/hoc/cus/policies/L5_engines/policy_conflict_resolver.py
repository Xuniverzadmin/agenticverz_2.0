# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (during policy evaluation)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Resolve conflicts when multiple policies trigger different actions (pure logic)
# Callers: prevention_engine.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-068
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

"""
Module: conflict_resolver
Purpose: Defines explicit rules for resolving policy conflicts.

Implements INV-005: Policy Conflict Determinism (CONFLICT-DET-001)
> When multiple policies apply to the same action, the most restrictive action wins.
> If two policies have equal restrictiveness, the policy with the lowest policy_id wins
> (deterministic tiebreaker).

Imports (Dependencies):
    - None (standalone)

Exports (Provides):
    - resolve_policy_conflict(actions: List[PolicyAction]) -> ResolvedAction
    - ConflictResolutionStrategy: Enum
    - PolicyConflictLog: Audit record of conflict resolution

Wiring Points:
    - Called from: prevention_engine.py:evaluate_policies()
    - Emits: PolicyConflictLog to audit ledger

Conflict Resolution Rules (INV-005):
    1. Higher precedence wins (lower number = higher priority)
    2. Within same precedence, more restrictive action wins
    3. Action restrictiveness order: KILL > STOP > PAUSE > WARN > CONTINUE
    4. If precedence and action are equal, lowest policy_id wins (deterministic tiebreaker)

Acceptance Criteria:
    - [x] AC-068-01: Single policy returns without conflict
    - [x] AC-068-02: Multiple policies same action no conflict
    - [x] AC-068-03: Precedence resolves conflict
    - [x] AC-068-04: Severity resolves same-precedence
    - [x] AC-068-05: Conflict logged to audit
    - [x] AC-068-06: Wired to prevention_engine
    - [x] AC-068-07: Deterministic tiebreaker (INV-005)
"""

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger("nova.policy.conflict_resolver")


class ActionSeverity(IntEnum):
    """
    Action severity for conflict resolution. Higher = more restrictive.

    INV-005 Restrictiveness Order: KILL > STOP > PAUSE > WARN > CONTINUE
    """
    CONTINUE = 0
    ALLOW = 0  # Alias
    WARN = 1
    PAUSE = 2
    STOP = 3
    BLOCK = 3  # Alias
    KILL = 4
    ABORT = 4  # Alias


class ConflictResolutionStrategy(str, Enum):
    """Resolution strategy for policy conflicts."""
    PRECEDENCE_FIRST = "precedence_first"  # Higher precedence wins, then severity
    SEVERITY_FIRST = "severity_first"       # More restrictive action wins, then precedence
    FAIL_CLOSED = "fail_closed"             # Always most restrictive


@dataclass
class PolicyAction:
    """A triggered policy action."""
    policy_id: str
    policy_name: str
    action: str  # CONTINUE, WARN, PAUSE, STOP, KILL
    precedence: int  # Lower = higher priority
    reason: str


@dataclass
class ResolvedAction:
    """Result of conflict resolution."""
    winning_action: str
    winning_policy_id: Optional[str]
    resolution_reason: str
    all_triggered: List[PolicyAction]
    conflict_detected: bool


@dataclass
class PolicyConflictLog:
    """Audit log entry for conflict resolution."""
    run_id: str
    triggered_policies: List[str]
    winning_policy: Optional[str]
    winning_action: str
    resolution_strategy: str
    timestamp: str


# Action severity mapping (normalized)
ACTION_SEVERITY = {
    "CONTINUE": ActionSeverity.CONTINUE,
    "ALLOW": ActionSeverity.ALLOW,
    "WARN": ActionSeverity.WARN,
    "PAUSE": ActionSeverity.PAUSE,
    "STOP": ActionSeverity.STOP,
    "BLOCK": ActionSeverity.BLOCK,
    "KILL": ActionSeverity.KILL,
    "ABORT": ActionSeverity.ABORT,
}


def resolve_policy_conflict(
    actions: List[PolicyAction],
    strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PRECEDENCE_FIRST,
) -> ResolvedAction:
    """
    Resolve conflict when multiple policies trigger.

    Implements INV-005: Policy Conflict Determinism

    Resolution Algorithm:
    1. Sort by precedence (lower number = higher priority)
    2. Within same precedence, sort by action severity (higher = more restrictive)
    3. Within same precedence and severity, sort by policy_id (deterministic tiebreaker)
    4. Return the winning action

    Args:
        actions: List of triggered policy actions
        strategy: Resolution strategy to use

    Returns:
        ResolvedAction with winning policy and audit trail
    """
    if not actions:
        return ResolvedAction(
            winning_action="CONTINUE",
            winning_policy_id=None,
            resolution_reason="no_policies_triggered",
            all_triggered=[],
            conflict_detected=False,
        )

    if len(actions) == 1:
        return ResolvedAction(
            winning_action=actions[0].action,
            winning_policy_id=actions[0].policy_id,
            resolution_reason="single_policy",
            all_triggered=actions,
            conflict_detected=False,
        )

    # Multiple policies triggered - conflict resolution needed
    unique_actions = set(a.action for a in actions)
    conflict_detected = len(unique_actions) > 1

    # INV-005: Sort with deterministic tiebreaker
    # Sort key includes policy_id as final tiebreaker for determinism
    def sort_key(action: PolicyAction) -> tuple:
        severity = ACTION_SEVERITY.get(action.action.upper(), ActionSeverity.CONTINUE)

        if strategy == ConflictResolutionStrategy.PRECEDENCE_FIRST:
            # Lower precedence wins, then higher severity, then lowest policy_id
            return (action.precedence, -severity, action.policy_id)
        elif strategy == ConflictResolutionStrategy.SEVERITY_FIRST:
            # Higher severity wins, then lower precedence, then lowest policy_id
            return (-severity, action.precedence, action.policy_id)
        else:  # FAIL_CLOSED
            # Most restrictive (highest severity), then precedence, then lowest policy_id
            return (-severity, action.precedence, action.policy_id)

    sorted_actions = sorted(actions, key=sort_key)
    winner = sorted_actions[0]

    resolution_reason = f"resolved_by_{strategy.value}"
    if conflict_detected:
        resolution_reason += f"_conflict_between_{len(actions)}_policies"

    logger.info("policy_conflict.resolved", extra={
        "conflict_detected": conflict_detected,
        "winner_policy_id": winner.policy_id,
        "winner_action": winner.action,
        "strategy": strategy.value,
        "triggered_count": len(actions),
        "triggered_policies": [a.policy_id for a in actions],
    })

    return ResolvedAction(
        winning_action=winner.action,
        winning_policy_id=winner.policy_id,
        resolution_reason=resolution_reason,
        all_triggered=actions,
        conflict_detected=conflict_detected,
    )


def create_conflict_log(
    run_id: str,
    resolved: ResolvedAction,
    strategy: ConflictResolutionStrategy,
) -> PolicyConflictLog:
    """
    Create audit log entry for conflict resolution.

    Args:
        run_id: ID of the run being evaluated
        resolved: Resolution result
        strategy: Strategy used

    Returns:
        PolicyConflictLog for audit trail
    """
    return PolicyConflictLog(
        run_id=run_id,
        triggered_policies=[a.policy_id for a in resolved.all_triggered],
        winning_policy=resolved.winning_policy_id,
        winning_action=resolved.winning_action,
        resolution_strategy=strategy.value,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def get_action_severity(action: str) -> int:
    """
    Get the severity level for an action.

    Args:
        action: Action string (CONTINUE, WARN, PAUSE, STOP, KILL)

    Returns:
        Severity level (0-4)
    """
    return ACTION_SEVERITY.get(action.upper(), ActionSeverity.CONTINUE)


def is_more_restrictive(action_a: str, action_b: str) -> bool:
    """
    Check if action_a is more restrictive than action_b.

    Args:
        action_a: First action
        action_b: Second action

    Returns:
        True if action_a is more restrictive
    """
    return get_action_severity(action_a) > get_action_severity(action_b)
