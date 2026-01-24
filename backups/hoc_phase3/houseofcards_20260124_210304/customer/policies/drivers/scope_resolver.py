# Layer: L6 — Driver
# Product: AI Console
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Resolve which policies apply to a given run context
# Callers: policy/prevention_engine.py, worker/runner.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-002

"""
Scope Resolver Engine

Resolves which policies apply to a run based on:
- Tenant ID (always required)
- Agent ID (for AGENT scope)
- API Key ID (for API_KEY scope)
- Human Actor ID (for HUMAN_ACTOR scope)

Resolution happens BEFORE run starts and the result is frozen
into the policy snapshot for audit purposes.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session, select

from app.db import engine
from app.models.policy_scope import PolicyScope, ScopeType

logger = logging.getLogger("nova.policy.scope_resolver")


@dataclass
class RunContext:
    """Context for scope resolution."""

    tenant_id: str
    agent_id: Optional[str] = None
    api_key_id: Optional[str] = None
    human_actor_id: Optional[str] = None
    run_id: Optional[str] = None


@dataclass
class ScopeResolutionResult:
    """Result of scope resolution."""

    # Matching policy IDs
    matching_policy_ids: list[str]

    # Resolution details
    all_runs_policies: list[str]  # Policies with ALL_RUNS scope
    agent_policies: list[str]  # Policies matching agent_id
    api_key_policies: list[str]  # Policies matching api_key_id
    human_actor_policies: list[str]  # Policies matching human_actor_id

    # Context used for resolution
    context: RunContext

    # Audit data
    scopes_evaluated: int
    resolution_timestamp: str

    def to_snapshot(self) -> dict:
        """Convert to snapshot dict for immutable storage."""
        return {
            "matching_policy_ids": self.matching_policy_ids,
            "all_runs_policies": self.all_runs_policies,
            "agent_policies": self.agent_policies,
            "api_key_policies": self.api_key_policies,
            "human_actor_policies": self.human_actor_policies,
            "context": {
                "tenant_id": self.context.tenant_id,
                "agent_id": self.context.agent_id,
                "api_key_id": self.context.api_key_id,
                "human_actor_id": self.context.human_actor_id,
            },
            "scopes_evaluated": self.scopes_evaluated,
            "resolution_timestamp": self.resolution_timestamp,
        }


class ScopeResolver:
    """
    Resolves which policies apply to a given run context.

    The resolver evaluates all active policy scopes for a tenant
    and returns the list of policies that match the run context.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize scope resolver.

        Args:
            session: Optional SQLModel session (for testing)
        """
        self._session = session

    def resolve_applicable_policies(
        self,
        context: RunContext,
    ) -> ScopeResolutionResult:
        """
        Resolve all policies that apply to the given run context.

        Args:
            context: Run context with tenant, agent, API key, and human actor IDs

        Returns:
            ScopeResolutionResult with matching policies
        """
        from datetime import datetime, timezone

        all_runs_policies: list[str] = []
        agent_policies: list[str] = []
        api_key_policies: list[str] = []
        human_actor_policies: list[str] = []
        scopes_evaluated = 0

        # Use provided session or create new one
        if self._session:
            scopes = self._load_scopes(self._session, context.tenant_id)
        else:
            with Session(engine) as session:
                scopes = self._load_scopes(session, context.tenant_id)

        for scope in scopes:
            scopes_evaluated += 1

            if self.matches_scope(scope, context):
                # Categorize by scope type
                scope_type = ScopeType(scope.scope_type)

                if scope_type == ScopeType.ALL_RUNS:
                    all_runs_policies.append(scope.policy_id)
                elif scope_type == ScopeType.AGENT:
                    agent_policies.append(scope.policy_id)
                elif scope_type == ScopeType.API_KEY:
                    api_key_policies.append(scope.policy_id)
                elif scope_type == ScopeType.HUMAN_ACTOR:
                    human_actor_policies.append(scope.policy_id)

        # Combine all matching policies (deduplicated)
        matching_policy_ids = list(
            set(
                all_runs_policies
                + agent_policies
                + api_key_policies
                + human_actor_policies
            )
        )

        logger.info(
            "scope_resolution_complete",
            extra={
                "tenant_id": context.tenant_id,
                "agent_id": context.agent_id,
                "api_key_id": context.api_key_id,
                "human_actor_id": context.human_actor_id,
                "matching_policies": len(matching_policy_ids),
                "scopes_evaluated": scopes_evaluated,
            },
        )

        return ScopeResolutionResult(
            matching_policy_ids=matching_policy_ids,
            all_runs_policies=all_runs_policies,
            agent_policies=agent_policies,
            api_key_policies=api_key_policies,
            human_actor_policies=human_actor_policies,
            context=context,
            scopes_evaluated=scopes_evaluated,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _load_scopes(self, session: Session, tenant_id: str) -> list[PolicyScope]:
        """Load all scopes for a tenant."""
        stmt = select(PolicyScope).where(PolicyScope.tenant_id == tenant_id)
        result = session.exec(stmt)
        return list(result.all())

    def matches_scope(self, scope: PolicyScope, context: RunContext) -> bool:
        """
        Check if a single scope matches the run context.

        Args:
            scope: Policy scope to check
            context: Run context

        Returns:
            True if scope matches, False otherwise
        """
        return scope.matches(
            agent_id=context.agent_id,
            api_key_id=context.api_key_id,
            human_actor_id=context.human_actor_id,
        )

    def get_scope_for_policy(
        self,
        policy_id: str,
        tenant_id: str,
    ) -> Optional[PolicyScope]:
        """
        Get the scope configuration for a specific policy.

        Args:
            policy_id: Policy ID
            tenant_id: Tenant ID

        Returns:
            PolicyScope or None if not found
        """
        if self._session:
            return self._get_scope(self._session, policy_id, tenant_id)
        else:
            with Session(engine) as session:
                return self._get_scope(session, policy_id, tenant_id)

    def _get_scope(
        self,
        session: Session,
        policy_id: str,
        tenant_id: str,
    ) -> Optional[PolicyScope]:
        """Get scope from database."""
        stmt = select(PolicyScope).where(
            PolicyScope.policy_id == policy_id,
            PolicyScope.tenant_id == tenant_id,
        )
        result = session.exec(stmt)
        return result.first()


# Singleton instance
_scope_resolver: Optional[ScopeResolver] = None


def get_scope_resolver() -> ScopeResolver:
    """Get or create ScopeResolver singleton."""
    global _scope_resolver
    if _scope_resolver is None:
        _scope_resolver = ScopeResolver()
    return _scope_resolver
