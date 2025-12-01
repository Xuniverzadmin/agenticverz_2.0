# runtime/contracts.py
"""
Contract Dataclasses for Machine-Native Runtime

These are auxiliary contract shapes used alongside the core runtime types.
Provides structured metadata for skill contracts and versioning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime, timezone


@dataclass(frozen=True)
class ContractMetadata:
    """
    Metadata about a contract's version and lifecycle.

    Fields:
        version: Semantic version of the contract
        frozen_at: ISO date when contract was frozen
        changelog: Description of changes in this version
        author: Who created/modified this contract
    """
    version: str
    frozen_at: str  # ISO date when contract was frozen
    changelog: str = ""
    author: str = "system"

    @classmethod
    def now(cls, version: str, changelog: str = "") -> "ContractMetadata":
        """Create metadata with current timestamp."""
        return cls(
            version=version,
            frozen_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            changelog=changelog
        )


@dataclass(frozen=True)
class SkillContract:
    """
    Full contract for a skill including schemas and stability rules.

    Used for contract validation and drift detection in CI.

    Fields:
        skill_id: Unique skill identifier
        inputs_schema: JSON Schema for inputs
        outputs_schema: JSON Schema for outputs
        stable_fields: Field -> stability rule mapping
        metadata: Version and lifecycle info
    """
    skill_id: str
    inputs_schema: Dict[str, Any]
    outputs_schema: Dict[str, Any]
    stable_fields: Dict[str, str]  # field -> stability rule
    metadata: ContractMetadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "skill_id": self.skill_id,
            "inputs_schema": self.inputs_schema,
            "outputs_schema": self.outputs_schema,
            "stable_fields": self.stable_fields,
            "metadata": {
                "version": self.metadata.version,
                "frozen_at": self.metadata.frozen_at,
                "changelog": self.metadata.changelog,
                "author": self.metadata.author
            }
        }


@dataclass(frozen=True)
class FailureMode:
    """
    A known failure mode for a skill.

    Used by failure catalog and planner for recovery suggestions.

    Fields:
        code: Error code (e.g., ERR_TIMEOUT)
        category: TRANSIENT, PERMANENT, RESOURCE, PERMISSION, VALIDATION
        typical_cause: Human-readable cause description
        recovery_hints: List of recovery suggestions
        retryable: Whether retry might work
    """
    code: str
    category: str
    typical_cause: str
    recovery_hints: List[str] = field(default_factory=list)
    retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "code": self.code,
            "category": self.category,
            "typical_cause": self.typical_cause,
            "recovery_hints": self.recovery_hints,
            "retryable": self.retryable
        }


@dataclass(frozen=True)
class CostModel:
    """
    Cost estimation model for a skill.

    Used for budget tracking and simulation.

    Fields:
        base_cents: Fixed cost per execution
        per_kb_cents: Cost per KB of input/output
        per_token_cents: Cost per token (for LLM skills)
        max_cents: Maximum possible cost
    """
    base_cents: int = 0
    per_kb_cents: float = 0.0
    per_token_cents: float = 0.0
    max_cents: int = 100

    def estimate(self, input_size_kb: float = 0, tokens: int = 0) -> int:
        """Estimate cost in cents."""
        cost = self.base_cents
        cost += int(input_size_kb * self.per_kb_cents)
        cost += int(tokens * self.per_token_cents)
        return min(cost, self.max_cents)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "base_cents": self.base_cents,
            "per_kb_cents": self.per_kb_cents,
            "per_token_cents": self.per_token_cents,
            "max_cents": self.max_cents
        }


@dataclass
class BudgetTracker:
    """
    Mutable budget tracker for a run.

    Tracks spending and enforces limits.

    Fields:
        total_cents: Total budget allocation
        spent_cents: Amount spent so far
        per_step_max_cents: Max allowed per single step
    """
    total_cents: int = 1000
    spent_cents: int = 0
    per_step_max_cents: int = 100

    @property
    def remaining_cents(self) -> int:
        """Get remaining budget."""
        return max(0, self.total_cents - self.spent_cents)

    def can_spend(self, amount: int) -> bool:
        """Check if amount can be spent."""
        return (
            amount <= self.remaining_cents and
            amount <= self.per_step_max_cents
        )

    def spend(self, amount: int) -> bool:
        """
        Attempt to spend amount.

        Returns True if successful, False if exceeds limits.
        """
        if not self.can_spend(amount):
            return False
        self.spent_cents += amount
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "total_cents": self.total_cents,
            "spent_cents": self.spent_cents,
            "remaining_cents": self.remaining_cents,
            "per_step_max_cents": self.per_step_max_cents
        }
