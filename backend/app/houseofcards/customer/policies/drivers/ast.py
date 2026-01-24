# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Policy DSL AST node definitions (immutable, typed)
# Reference: PIN-341 Section 1.8, PIN-345

"""
Policy DSL Abstract Syntax Tree (AST) Definitions

DESIGN CONSTRAINTS (BLOCKING - PIN-341):
- All nodes are IMMUTABLE (frozen dataclasses)
- No dynamic fields
- No generic dicts (typed structures only)
- No runtime evaluation logic
- Must be serializable to JSON

GOVERNANCE:
- These types define the MEANING of policy structure
- No authority, no execution, no side effects
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Union

# =============================================================================
# ENUMERATIONS (Closed Sets)
# =============================================================================


class Scope(str, Enum):
    """Policy scope determines visibility boundaries."""

    ORG = "ORG"
    PROJECT = "PROJECT"


class Mode(str, Enum):
    """
    Policy mode determines enforcement semantics.

    MONITOR: Can only WARN, cannot BLOCK or REQUIRE_APPROVAL
    ENFORCE: Can WARN, BLOCK, or REQUIRE_APPROVAL
    """

    MONITOR = "MONITOR"
    ENFORCE = "ENFORCE"


class Comparator(str, Enum):
    """Comparison operators for predicates."""

    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="


class LogicalOperator(str, Enum):
    """Logical operators for compound conditions."""

    AND = "AND"
    OR = "OR"


# =============================================================================
# ACTION NODES (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class WarnAction:
    """
    Emit a warning message.
    Allowed in both MONITOR and ENFORCE modes.
    """

    message: str
    type: Literal["WARN"] = field(default="WARN", repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "message": self.message}


@dataclass(frozen=True, slots=True)
class BlockAction:
    """
    Block execution.
    ONLY allowed in ENFORCE mode (validated by validator.py).
    """

    type: Literal["BLOCK"] = field(default="BLOCK", repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type}


@dataclass(frozen=True, slots=True)
class RequireApprovalAction:
    """
    Require human approval before proceeding.
    ONLY allowed in ENFORCE mode (validated by validator.py).
    """

    type: Literal["REQUIRE_APPROVAL"] = field(default="REQUIRE_APPROVAL", repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type}


# Union type for all actions
Action = Union[WarnAction, BlockAction, RequireApprovalAction]


# =============================================================================
# CONDITION NODES (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Predicate:
    """
    A simple comparison predicate.

    Example: cost_per_hour > 200
    """

    metric: str
    comparator: Comparator
    value: Union[int, float, str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "predicate",
            "metric": self.metric,
            "comparator": self.comparator.value,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class ExistsPredicate:
    """
    Check if a metric exists.

    Example: exists(anomaly_flag)
    """

    metric: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "exists",
            "metric": self.metric,
        }


@dataclass(frozen=True, slots=True)
class LogicalCondition:
    """
    A compound condition combining two conditions with AND/OR.

    Example: cost_per_hour > 200 AND error_rate > 0.1
    """

    left: Condition
    operator: LogicalOperator
    right: Condition

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "logical",
            "operator": self.operator.value,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


# Union type for all conditions
Condition = Union[Predicate, ExistsPredicate, LogicalCondition]


# =============================================================================
# CLAUSE NODE (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Clause:
    """
    A single when-then clause.

    Structure:
        when <condition>
        then <action>+
    """

    when: Condition
    then: tuple[Action, ...]  # Tuple for immutability

    def __post_init__(self) -> None:
        # Validate that then is not empty
        if not self.then:
            raise ValueError("Clause must have at least one action in 'then'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "when": self.when.to_dict(),
            "then": [action.to_dict() for action in self.then],
        }


# =============================================================================
# METADATA NODE (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class PolicyMetadata:
    """
    Policy metadata header.

    Required fields per PIN-341:
    - name: Policy identifier
    - version: Version number (monotonically increasing)
    - scope: ORG or PROJECT
    - mode: MONITOR or ENFORCE
    """

    name: str
    version: int
    scope: Scope
    mode: Mode

    def __post_init__(self) -> None:
        # Validate version is positive
        if self.version < 1:
            raise ValueError(f"Version must be >= 1, got {self.version}")
        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValueError("Policy name cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "scope": self.scope.value,
            "mode": self.mode.value,
        }


# =============================================================================
# POLICY AST ROOT (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class PolicyAST:
    """
    Root AST node for a complete policy.

    Structure:
        policy <name>
        version <n>
        scope <ORG|PROJECT>
        mode <MONITOR|ENFORCE>

        when <condition>
        then <action>+
        [... more clauses ...]

    IMMUTABILITY: This entire structure is frozen.
    SERIALIZATION: Use to_dict() or to_json() for serialization.
    HASHING: Use compute_hash() for deterministic content hash.
    """

    metadata: PolicyMetadata
    clauses: tuple[Clause, ...]  # Tuple for immutability

    def __post_init__(self) -> None:
        # Validate at least one clause
        if not self.clauses:
            raise ValueError("Policy must have at least one clause")

    def to_dict(self) -> dict[str, Any]:
        """Convert AST to dictionary (serializable)."""
        return {
            "metadata": self.metadata.to_dict(),
            "clauses": [clause.to_dict() for clause in self.clauses],
        }

    def to_json(self, indent: int | None = None) -> str:
        """Convert AST to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def compute_hash(self) -> str:
        """
        Compute deterministic SHA256 hash of the AST.

        GUARANTEE: Same AST structure → Same hash
        This is used for:
        - IR caching
        - Audit trail linkage
        - Replay verification
        """
        canonical_json = self.to_json()
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @property
    def name(self) -> str:
        """Convenience accessor for policy name."""
        return self.metadata.name

    @property
    def version(self) -> int:
        """Convenience accessor for policy version."""
        return self.metadata.version

    @property
    def scope(self) -> Scope:
        """Convenience accessor for policy scope."""
        return self.metadata.scope

    @property
    def mode(self) -> Mode:
        """Convenience accessor for policy mode."""
        return self.metadata.mode


# =============================================================================
# TYPE GUARDS (for runtime type checking)
# =============================================================================


def is_predicate(condition: Condition) -> bool:
    """Check if condition is a simple predicate."""
    return isinstance(condition, Predicate)


def is_exists_predicate(condition: Condition) -> bool:
    """Check if condition is an exists predicate."""
    return isinstance(condition, ExistsPredicate)


def is_logical_condition(condition: Condition) -> bool:
    """Check if condition is a compound logical condition."""
    return isinstance(condition, LogicalCondition)


def is_warn_action(action: Action) -> bool:
    """Check if action is a WARN action."""
    return isinstance(action, WarnAction)


def is_block_action(action: Action) -> bool:
    """Check if action is a BLOCK action."""
    return isinstance(action, BlockAction)


def is_require_approval_action(action: Action) -> bool:
    """Check if action is a REQUIRE_APPROVAL action."""
    return isinstance(action, RequireApprovalAction)
