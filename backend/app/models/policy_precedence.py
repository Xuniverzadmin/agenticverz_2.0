# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Define policy precedence and conflict resolution strategies
# Callers: policy/arbitrator.py, api/policy_precedence.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-003

"""
Policy Precedence Model

Defines conflict resolution when multiple policies apply to the same run:
- Precedence number (lower = higher priority)
- Conflict strategy (most_restrictive, explicit_priority, fail_closed)
- Binding moment (when policy becomes authoritative)

Arbitration Rules:
1. Lower precedence number wins
2. Same precedence → use conflict_strategy
3. MOST_RESTRICTIVE → smallest limit, harshest action
4. FAIL_CLOSED → if ambiguous, deny
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ConflictStrategy(str, Enum):
    """Strategy for resolving policy conflicts."""

    MOST_RESTRICTIVE = "most_restrictive"  # Smallest limit, harshest action wins
    EXPLICIT_PRIORITY = "explicit_priority"  # Higher precedence (lower number) wins
    FAIL_CLOSED = "fail_closed"  # If ambiguous, deny/stop


class BindingMoment(str, Enum):
    """When the policy becomes authoritative."""

    RUN_START = "run_start"  # Policy binds when run is created
    FIRST_TOKEN = "first_token"  # Policy binds on first LLM token
    EACH_STEP = "each_step"  # Policy evaluated fresh each step


class PolicyPrecedence(SQLModel, table=True):
    """
    Policy precedence configuration for conflict resolution.

    When multiple policies apply to the same run, precedence determines
    which policy's limits and actions take effect.
    """

    __tablename__ = "policy_precedence"

    id: Optional[int] = Field(default=None, primary_key=True)
    policy_id: str = Field(index=True, unique=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id

    # Precedence (lower = higher priority)
    precedence: int = Field(default=100)

    # Conflict resolution strategy
    conflict_strategy: str = Field(default=ConflictStrategy.MOST_RESTRICTIVE.value)

    # Binding moment
    bind_at: str = Field(default=BindingMoment.RUN_START.value)

    # Failure semantics
    failure_mode: str = Field(default="fail_closed")  # fail_closed or fail_open

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_snapshot(self) -> dict:
        """Convert to snapshot dict for immutable storage."""
        return {
            "policy_id": self.policy_id,
            "precedence": self.precedence,
            "conflict_strategy": self.conflict_strategy,
            "bind_at": self.bind_at,
            "failure_mode": self.failure_mode,
        }


class ArbitrationResult(BaseModel):
    """Result of policy arbitration."""

    # Resolved policies (in precedence order)
    policy_ids: list[str]
    precedence_order: list[int]

    # Effective limits (after conflict resolution)
    effective_token_limit: Optional[int] = None
    effective_cost_limit_cents: Optional[int] = None
    effective_burn_rate_limit: Optional[float] = None

    # Effective action on breach
    effective_breach_action: str = "stop"  # pause, stop, kill

    # Conflict resolution details
    conflicts_resolved: int = 0
    resolution_strategy: str = "most_restrictive"

    # Snapshot for audit
    arbitration_timestamp: datetime
    snapshot_hash: str


class PolicyPrecedenceCreate(BaseModel):
    """Request model for creating policy precedence."""

    policy_id: str
    precedence: int = 100
    conflict_strategy: ConflictStrategy = ConflictStrategy.MOST_RESTRICTIVE
    bind_at: BindingMoment = BindingMoment.RUN_START
    failure_mode: str = "fail_closed"


class PolicyPrecedenceUpdate(BaseModel):
    """Request model for updating policy precedence."""

    precedence: Optional[int] = None
    conflict_strategy: Optional[ConflictStrategy] = None
    bind_at: Optional[BindingMoment] = None
    failure_mode: Optional[str] = None


class PolicyPrecedenceResponse(BaseModel):
    """Response model for policy precedence."""

    policy_id: str
    tenant_id: str
    precedence: int
    conflict_strategy: ConflictStrategy
    bind_at: BindingMoment
    failure_mode: str
    created_at: datetime
    updated_at: datetime
