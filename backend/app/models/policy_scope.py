# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Define policy scope selectors for targeting runs by agent, API key, or human actor
# Callers: policy/scope_resolver.py, api/policy_scopes.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-001

"""
Policy Scope Model

Defines WHO a policy applies to:
- ALL_RUNS: All LLM runs for the tenant
- AGENT: Specific agent IDs (native or spawned)
- API_KEY: Specific API keys
- HUMAN_ACTOR: Specific human actor IDs

Invariants:
1. ALL_RUNS cannot be combined with specific IDs
2. Scope is resolved BEFORE run starts
3. Resolved scope is stored in policy snapshot
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel


class ScopeType(str, Enum):
    """Type of scope selector."""

    ALL_RUNS = "all_runs"  # All LLM runs for tenant
    AGENT = "agent"  # Specific agent IDs
    API_KEY = "api_key"  # Specific API keys
    HUMAN_ACTOR = "human_actor"  # Specific human actors


class PolicyScope(SQLModel, table=True):
    """
    Scope selector that defines WHO a policy applies to.

    The scope selector is used at run start to determine if a policy
    should be applied. Scopes are mutually exclusive with ALL_RUNS
    being the broadest scope.
    """

    __tablename__ = "policy_scopes"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope_id: str = Field(
        default_factory=lambda: f"SCOPE-{uuid.uuid4().hex[:12]}",
        index=True,
        unique=True,
    )
    policy_id: str = Field(index=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id

    # Scope definition
    scope_type: str = Field(default=ScopeType.ALL_RUNS.value)

    # Target IDs (JSON arrays, only used when scope_type matches)
    agent_ids_json: Optional[str] = Field(default=None)  # JSON array of agent IDs
    api_key_ids_json: Optional[str] = Field(default=None)  # JSON array of API key IDs
    human_actor_ids_json: Optional[str] = Field(
        default=None
    )  # JSON array of human actor IDs

    # Metadata
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(default=None)

    @property
    def agent_ids(self) -> list[str]:
        """Get agent IDs as list."""
        if self.agent_ids_json:
            return json.loads(self.agent_ids_json)
        return []

    @agent_ids.setter
    def agent_ids(self, value: list[str]) -> None:
        """Set agent IDs from list."""
        self.agent_ids_json = json.dumps(value) if value else None

    @property
    def api_key_ids(self) -> list[str]:
        """Get API key IDs as list."""
        if self.api_key_ids_json:
            return json.loads(self.api_key_ids_json)
        return []

    @api_key_ids.setter
    def api_key_ids(self, value: list[str]) -> None:
        """Set API key IDs from list."""
        self.api_key_ids_json = json.dumps(value) if value else None

    @property
    def human_actor_ids(self) -> list[str]:
        """Get human actor IDs as list."""
        if self.human_actor_ids_json:
            return json.loads(self.human_actor_ids_json)
        return []

    @human_actor_ids.setter
    def human_actor_ids(self, value: list[str]) -> None:
        """Set human actor IDs from list."""
        self.human_actor_ids_json = json.dumps(value) if value else None

    def matches(
        self,
        agent_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        human_actor_id: Optional[str] = None,
    ) -> bool:
        """
        Check if this scope matches the given run context.

        Args:
            agent_id: Agent ID of the run
            api_key_id: API key ID used for the run
            human_actor_id: Human actor ID who initiated the run

        Returns:
            True if scope matches, False otherwise
        """
        scope_type = ScopeType(self.scope_type)

        if scope_type == ScopeType.ALL_RUNS:
            return True

        if scope_type == ScopeType.AGENT:
            return agent_id is not None and agent_id in self.agent_ids

        if scope_type == ScopeType.API_KEY:
            return api_key_id is not None and api_key_id in self.api_key_ids

        if scope_type == ScopeType.HUMAN_ACTOR:
            return human_actor_id is not None and human_actor_id in self.human_actor_ids

        return False

    def to_snapshot(self) -> dict:
        """Convert to snapshot dict for immutable storage."""
        return {
            "scope_id": self.scope_id,
            "scope_type": self.scope_type,
            "agent_ids": self.agent_ids,
            "api_key_ids": self.api_key_ids,
            "human_actor_ids": self.human_actor_ids,
        }

    @classmethod
    def create_all_runs_scope(
        cls,
        policy_id: str,
        tenant_id: str,
        created_by: Optional[str] = None,
    ) -> "PolicyScope":
        """Factory method for ALL_RUNS scope."""
        return cls(
            policy_id=policy_id,
            tenant_id=tenant_id,
            scope_type=ScopeType.ALL_RUNS.value,
            created_by=created_by,
        )

    @classmethod
    def create_agent_scope(
        cls,
        policy_id: str,
        tenant_id: str,
        agent_ids: list[str],
        created_by: Optional[str] = None,
    ) -> "PolicyScope":
        """Factory method for AGENT scope."""
        scope = cls(
            policy_id=policy_id,
            tenant_id=tenant_id,
            scope_type=ScopeType.AGENT.value,
            created_by=created_by,
        )
        scope.agent_ids = agent_ids
        return scope

    @classmethod
    def create_api_key_scope(
        cls,
        policy_id: str,
        tenant_id: str,
        api_key_ids: list[str],
        created_by: Optional[str] = None,
    ) -> "PolicyScope":
        """Factory method for API_KEY scope."""
        scope = cls(
            policy_id=policy_id,
            tenant_id=tenant_id,
            scope_type=ScopeType.API_KEY.value,
            created_by=created_by,
        )
        scope.api_key_ids = api_key_ids
        return scope

    @classmethod
    def create_human_actor_scope(
        cls,
        policy_id: str,
        tenant_id: str,
        human_actor_ids: list[str],
        created_by: Optional[str] = None,
    ) -> "PolicyScope":
        """Factory method for HUMAN_ACTOR scope."""
        scope = cls(
            policy_id=policy_id,
            tenant_id=tenant_id,
            scope_type=ScopeType.HUMAN_ACTOR.value,
            created_by=created_by,
        )
        scope.human_actor_ids = human_actor_ids
        return scope


# Pydantic models for API requests/responses


class PolicyScopeCreate(BaseModel):
    """Request model for creating a policy scope."""

    policy_id: str
    scope_type: ScopeType
    agent_ids: Optional[list[str]] = None
    api_key_ids: Optional[list[str]] = None
    human_actor_ids: Optional[list[str]] = None
    description: Optional[str] = None


class PolicyScopeUpdate(BaseModel):
    """Request model for updating a policy scope."""

    scope_type: Optional[ScopeType] = None
    agent_ids: Optional[list[str]] = None
    api_key_ids: Optional[list[str]] = None
    human_actor_ids: Optional[list[str]] = None
    description: Optional[str] = None


class PolicyScopeResponse(BaseModel):
    """Response model for policy scope."""

    scope_id: str
    policy_id: str
    tenant_id: str
    scope_type: ScopeType
    agent_ids: list[str] = PydanticField(default_factory=list)
    api_key_ids: list[str] = PydanticField(default_factory=list)
    human_actor_ids: list[str] = PydanticField(default_factory=list)
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
