# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: AI Console
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policies
#   Writes: none
# Database:
#   Scope: domain (policies)
#   Models: PolicyRule
# Role: Resolve conflicts between multiple applicable policies
# Callers: policy/prevention_engine.py, worker/runner.py
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-004

"""
Policy Arbitrator Engine

Resolves conflicts when multiple policies apply to the same run:
1. Sort policies by precedence (lower = higher priority)
2. Resolve limit conflicts using conflict strategy
3. Resolve action conflicts (harshest action wins)
4. Return effective limits and actions

Arbitration Rules:
- MOST_RESTRICTIVE: Smallest limit, harshest action wins
- EXPLICIT_PRIORITY: Higher precedence (lower number) wins
- FAIL_CLOSED: If ambiguous, deny/stop
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.db import engine
from app.models.policy_precedence import (
    ArbitrationResult,
    ConflictStrategy,
    PolicyPrecedence,
)

logger = logging.getLogger("nova.policy.arbitrator")


@dataclass
class PolicyLimit:
    """Represents a policy limit."""

    policy_id: str
    limit_type: str  # token, cost, burn_rate, step_count
    value: float
    precedence: int = 100


@dataclass
class PolicyAction:
    """Represents a policy breach action."""

    policy_id: str
    action: str  # pause, stop, kill
    precedence: int = 100


# Action severity ranking (higher = more severe)
ACTION_SEVERITY = {
    "pause": 1,
    "stop": 2,
    "kill": 3,
}


@dataclass
class ArbitrationInput:
    """Input for policy arbitration."""

    policy_ids: list[str]
    token_limits: list[PolicyLimit] = field(default_factory=list)
    cost_limits: list[PolicyLimit] = field(default_factory=list)
    burn_rate_limits: list[PolicyLimit] = field(default_factory=list)
    breach_actions: list[PolicyAction] = field(default_factory=list)


class PolicyArbitrator:
    """
    Resolves conflicts between multiple applicable policies.

    The arbitrator determines effective limits and actions when
    multiple policies apply to the same run.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize policy arbitrator.

        Args:
            session: Optional SQLModel session (for testing)
        """
        self._session = session

    def arbitrate(
        self,
        policy_ids: list[str],
        tenant_id: str,
        arb_input: Optional[ArbitrationInput] = None,
    ) -> ArbitrationResult:
        """
        Arbitrate between multiple policies.

        Args:
            policy_ids: List of policy IDs to arbitrate
            tenant_id: Tenant ID
            arb_input: Optional pre-loaded arbitration input

        Returns:
            ArbitrationResult with effective limits and actions
        """
        # Load precedence for each policy
        precedence_map = self._load_precedence_map(policy_ids, tenant_id)

        # Sort by precedence (lower = higher priority)
        sorted_policies = sorted(
            policy_ids,
            key=lambda p: precedence_map.get(p, PolicyPrecedence(policy_id=p, tenant_id=tenant_id)).precedence,
        )

        # Determine conflict strategy (use highest priority policy's strategy)
        strategy = ConflictStrategy.MOST_RESTRICTIVE
        if sorted_policies:
            first_prec = precedence_map.get(sorted_policies[0])
            if first_prec:
                strategy = ConflictStrategy(first_prec.conflict_strategy)

        # Resolve limits
        effective_token_limit = None
        effective_cost_limit = None
        effective_burn_rate_limit = None
        conflicts_resolved = 0

        if arb_input:
            if arb_input.token_limits:
                effective_token_limit, resolved = self._resolve_limit_conflict(
                    arb_input.token_limits,
                    strategy,
                    precedence_map,
                )
                conflicts_resolved += resolved

            if arb_input.cost_limits:
                effective_cost_limit, resolved = self._resolve_limit_conflict(
                    arb_input.cost_limits,
                    strategy,
                    precedence_map,
                )
                conflicts_resolved += resolved

            if arb_input.burn_rate_limits:
                effective_burn_rate_limit, resolved = self._resolve_limit_conflict(
                    arb_input.burn_rate_limits,
                    strategy,
                    precedence_map,
                )
                conflicts_resolved += resolved

        # Resolve action
        effective_action = "stop"  # Default
        if arb_input and arb_input.breach_actions:
            effective_action, resolved = self._resolve_action_conflict(
                arb_input.breach_actions,
                strategy,
                precedence_map,
            )
            conflicts_resolved += resolved

        # Generate snapshot hash
        snapshot_data = {
            "policy_ids": sorted_policies,
            "effective_limits": {
                "token": effective_token_limit,
                "cost": effective_cost_limit,
                "burn_rate": effective_burn_rate_limit,
            },
            "effective_action": effective_action,
            "strategy": strategy.value,
        }
        snapshot_hash = hashlib.sha256(
            json.dumps(snapshot_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        logger.info(
            "policy_arbitration_complete",
            extra={
                "policy_count": len(policy_ids),
                "conflicts_resolved": conflicts_resolved,
                "strategy": strategy.value,
                "snapshot_hash": snapshot_hash,
            },
        )

        return ArbitrationResult(
            policy_ids=sorted_policies,
            precedence_order=[
                precedence_map.get(p, PolicyPrecedence(policy_id=p, tenant_id=tenant_id)).precedence
                for p in sorted_policies
            ],
            effective_token_limit=int(effective_token_limit) if effective_token_limit else None,
            effective_cost_limit_cents=int(effective_cost_limit) if effective_cost_limit else None,
            effective_burn_rate_limit=effective_burn_rate_limit,
            effective_breach_action=effective_action,
            conflicts_resolved=conflicts_resolved,
            resolution_strategy=strategy.value,
            arbitration_timestamp=datetime.now(timezone.utc),
            snapshot_hash=snapshot_hash,
        )

    def _load_precedence_map(
        self,
        policy_ids: list[str],
        tenant_id: str,
    ) -> dict[str, PolicyPrecedence]:
        """Load precedence for all policies."""
        if self._session:
            return self._get_precedence_map(self._session, policy_ids, tenant_id)
        else:
            with Session(engine) as session:
                return self._get_precedence_map(session, policy_ids, tenant_id)

    def _get_precedence_map(
        self,
        session: Session,
        policy_ids: list[str],
        tenant_id: str,
    ) -> dict[str, PolicyPrecedence]:
        """Get precedence map from database."""
        stmt = select(PolicyPrecedence).where(
            PolicyPrecedence.policy_id.in_(policy_ids),
            PolicyPrecedence.tenant_id == tenant_id,
        )
        result = session.exec(stmt)
        return {p.policy_id: p for p in result.all()}

    def _resolve_limit_conflict(
        self,
        limits: list[PolicyLimit],
        strategy: ConflictStrategy,
        precedence_map: dict[str, PolicyPrecedence],
    ) -> tuple[Optional[float], int]:
        """
        Resolve conflicting limits.

        Returns:
            Tuple of (effective_limit, conflicts_resolved)
        """
        if not limits:
            return None, 0

        if len(limits) == 1:
            return limits[0].value, 0

        conflicts = len(limits) - 1

        if strategy == ConflictStrategy.MOST_RESTRICTIVE:
            # Smallest limit wins
            return min(limit.value for limit in limits), conflicts

        elif strategy == ConflictStrategy.EXPLICIT_PRIORITY:
            # Higher precedence (lower number) wins
            sorted_limits = sorted(
                limits,
                key=lambda l: precedence_map.get(
                    l.policy_id,
                    PolicyPrecedence(policy_id=l.policy_id, tenant_id=""),
                ).precedence,
            )
            return sorted_limits[0].value, conflicts

        else:  # FAIL_CLOSED
            # Most restrictive on ambiguity
            return min(limit.value for limit in limits), conflicts

    def _resolve_action_conflict(
        self,
        actions: list[PolicyAction],
        strategy: ConflictStrategy,
        precedence_map: dict[str, PolicyPrecedence],
    ) -> tuple[str, int]:
        """
        Resolve conflicting actions.

        Returns:
            Tuple of (effective_action, conflicts_resolved)
        """
        if not actions:
            return "stop", 0

        if len(actions) == 1:
            return actions[0].action, 0

        conflicts = len(actions) - 1

        if strategy == ConflictStrategy.MOST_RESTRICTIVE:
            # Harshest action wins
            return max(actions, key=lambda a: ACTION_SEVERITY.get(a.action, 0)).action, conflicts

        elif strategy == ConflictStrategy.EXPLICIT_PRIORITY:
            # Higher precedence (lower number) wins
            sorted_actions = sorted(
                actions,
                key=lambda a: precedence_map.get(
                    a.policy_id,
                    PolicyPrecedence(policy_id=a.policy_id, tenant_id=""),
                ).precedence,
            )
            return sorted_actions[0].action, conflicts

        else:  # FAIL_CLOSED
            # Harshest action on ambiguity
            return max(actions, key=lambda a: ACTION_SEVERITY.get(a.action, 0)).action, conflicts


# Singleton instance
_arbitrator: Optional[PolicyArbitrator] = None


def get_policy_arbitrator() -> PolicyArbitrator:
    """Get or create PolicyArbitrator singleton."""
    global _arbitrator
    if _arbitrator is None:
        _arbitrator = PolicyArbitrator()
    return _arbitrator
