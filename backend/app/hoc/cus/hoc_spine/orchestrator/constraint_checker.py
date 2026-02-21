# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (in-memory logic)
#   Writes: none
# Role: Enforce MonitorConfig inspection constraints before logging (pure business logic)
# Callers: worker/runtime/trace_collector.py, services/logging_service.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy (runtime)
# Reference: PIN-470, GAP-033 (Inspection Constraints)
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)

"""
Module: constraint_checker
Purpose: Enforce inspection constraints from MonitorConfig.

Inspection constraints are "negative capabilities" - they define what
a policy is NOT allowed to inspect or capture. Before any logging
operation, the runner/worker must check these constraints.

Constraint Fields (from MonitorConfig):
    - allow_prompt_logging: Can prompts be logged?
    - allow_response_logging: Can responses be logged?
    - allow_pii_capture: Can PII be captured?
    - allow_secret_access: Can secrets be accessed?

Exports:
    - InspectionOperation: Enum of operations requiring checks
    - InspectionConstraintViolation: Violation record
    - InspectionConstraintChecker: Main enforcement class
    - check_inspection_allowed: Quick helper function
    - get_constraint_violations: Get all violations
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class InspectionOperation(str, Enum):
    """Operations that require inspection constraint checks."""

    LOG_PROMPT = "log_prompt"
    LOG_RESPONSE = "log_response"
    CAPTURE_PII = "capture_pii"
    ACCESS_SECRET = "access_secret"


# Mapping of operations to their constraint field names
OPERATION_TO_CONSTRAINT: dict[InspectionOperation, str] = {
    InspectionOperation.LOG_PROMPT: "allow_prompt_logging",
    InspectionOperation.LOG_RESPONSE: "allow_response_logging",
    InspectionOperation.CAPTURE_PII: "allow_pii_capture",
    InspectionOperation.ACCESS_SECRET: "allow_secret_access",
}


@dataclass
class InspectionConstraintViolation:
    """
    Record of an inspection constraint violation.

    Created when an operation is attempted that violates
    the MonitorConfig inspection constraints.
    """

    operation: InspectionOperation
    constraint_field: str
    constraint_value: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "operation": self.operation.value,
            "constraint_field": self.constraint_field,
            "constraint_value": self.constraint_value,
            "message": self.message,
        }


class InspectionConstraintChecker:
    """
    Enforces inspection constraints from MonitorConfig.

    This class checks whether logging and data capture operations
    are allowed based on the MonitorConfig's inspection constraint
    settings (negative capabilities).

    GAP-033: Wire MonitorConfig flags to runner.

    Usage:
        checker = InspectionConstraintChecker(monitor_config)
        if checker.is_allowed(InspectionOperation.LOG_PROMPT):
            # Log the prompt
        else:
            # Skip logging, constraint forbids it
    """

    def __init__(
        self,
        allow_prompt_logging: bool = False,
        allow_response_logging: bool = False,
        allow_pii_capture: bool = False,
        allow_secret_access: bool = False,
    ):
        """
        Initialize checker with constraint values.

        Args:
            allow_prompt_logging: Whether prompts can be logged
            allow_response_logging: Whether responses can be logged
            allow_pii_capture: Whether PII can be captured
            allow_secret_access: Whether secrets can be accessed

        Note: All defaults are False (restrictive by default).
        """
        self._constraints = {
            "allow_prompt_logging": allow_prompt_logging,
            "allow_response_logging": allow_response_logging,
            "allow_pii_capture": allow_pii_capture,
            "allow_secret_access": allow_secret_access,
        }

    @classmethod
    def from_monitor_config(cls, config: Any) -> "InspectionConstraintChecker":
        """
        Create checker from a MonitorConfig instance.

        Args:
            config: MonitorConfig model instance

        Returns:
            InspectionConstraintChecker configured with the config's constraints
        """
        return cls(
            allow_prompt_logging=getattr(config, "allow_prompt_logging", False),
            allow_response_logging=getattr(config, "allow_response_logging", False),
            allow_pii_capture=getattr(config, "allow_pii_capture", False),
            allow_secret_access=getattr(config, "allow_secret_access", False),
        )

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> "InspectionConstraintChecker":
        """
        Create checker from a MonitorConfig snapshot dict.

        Args:
            snapshot: Snapshot dict (from MonitorConfig.to_snapshot())

        Returns:
            InspectionConstraintChecker configured from snapshot
        """
        constraints = snapshot.get("inspection_constraints", {})
        return cls(
            allow_prompt_logging=constraints.get("allow_prompt_logging", False),
            allow_response_logging=constraints.get("allow_response_logging", False),
            allow_pii_capture=constraints.get("allow_pii_capture", False),
            allow_secret_access=constraints.get("allow_secret_access", False),
        )

    def is_allowed(self, operation: InspectionOperation) -> bool:
        """
        Check if an operation is allowed.

        Args:
            operation: The operation to check

        Returns:
            True if the operation is allowed, False otherwise
        """
        constraint_field = OPERATION_TO_CONSTRAINT.get(operation)
        if constraint_field is None:
            # Unknown operation, deny by default
            return False
        return self._constraints.get(constraint_field, False)

    def check(self, operation: InspectionOperation) -> Optional[InspectionConstraintViolation]:
        """
        Check an operation and return violation if not allowed.

        Args:
            operation: The operation to check

        Returns:
            InspectionConstraintViolation if not allowed, None if allowed
        """
        if self.is_allowed(operation):
            return None

        constraint_field = OPERATION_TO_CONSTRAINT.get(operation, "unknown")
        constraint_value = self._constraints.get(constraint_field, False)

        messages = {
            InspectionOperation.LOG_PROMPT: "Prompt logging not allowed by inspection constraints",
            InspectionOperation.LOG_RESPONSE: "Response logging not allowed by inspection constraints",
            InspectionOperation.CAPTURE_PII: "PII capture not allowed by inspection constraints",
            InspectionOperation.ACCESS_SECRET: "Secret access not allowed by inspection constraints",
        }

        return InspectionConstraintViolation(
            operation=operation,
            constraint_field=constraint_field,
            constraint_value=constraint_value,
            message=messages.get(operation, f"Operation {operation.value} not allowed"),
        )

    def check_all(
        self, operations: list[InspectionOperation]
    ) -> list[InspectionConstraintViolation]:
        """
        Check multiple operations and return all violations.

        Args:
            operations: List of operations to check

        Returns:
            List of violations (empty if all allowed)
        """
        violations = []
        for op in operations:
            violation = self.check(op)
            if violation:
                violations.append(violation)
        return violations

    def get_allowed_operations(self) -> list[InspectionOperation]:
        """Get all allowed operations."""
        return [op for op in InspectionOperation if self.is_allowed(op)]

    def get_denied_operations(self) -> list[InspectionOperation]:
        """Get all denied operations."""
        return [op for op in InspectionOperation if not self.is_allowed(op)]

    def to_dict(self) -> dict[str, Any]:
        """Convert constraints to dictionary."""
        return {
            "allow_prompt_logging": self._constraints["allow_prompt_logging"],
            "allow_response_logging": self._constraints["allow_response_logging"],
            "allow_pii_capture": self._constraints["allow_pii_capture"],
            "allow_secret_access": self._constraints["allow_secret_access"],
            "allowed_operations": [op.value for op in self.get_allowed_operations()],
            "denied_operations": [op.value for op in self.get_denied_operations()],
        }


def check_inspection_allowed(
    operation: InspectionOperation,
    allow_prompt_logging: bool = False,
    allow_response_logging: bool = False,
    allow_pii_capture: bool = False,
    allow_secret_access: bool = False,
) -> bool:
    """
    Quick helper to check if an operation is allowed.

    Args:
        operation: The operation to check
        allow_prompt_logging: Whether prompts can be logged
        allow_response_logging: Whether responses can be logged
        allow_pii_capture: Whether PII can be captured
        allow_secret_access: Whether secrets can be accessed

    Returns:
        True if operation is allowed, False otherwise
    """
    checker = InspectionConstraintChecker(
        allow_prompt_logging=allow_prompt_logging,
        allow_response_logging=allow_response_logging,
        allow_pii_capture=allow_pii_capture,
        allow_secret_access=allow_secret_access,
    )
    return checker.is_allowed(operation)


def get_constraint_violations(
    operations: list[InspectionOperation],
    allow_prompt_logging: bool = False,
    allow_response_logging: bool = False,
    allow_pii_capture: bool = False,
    allow_secret_access: bool = False,
) -> list[dict[str, Any]]:
    """
    Get all constraint violations for a set of operations.

    Args:
        operations: List of operations to check
        allow_prompt_logging: Whether prompts can be logged
        allow_response_logging: Whether responses can be logged
        allow_pii_capture: Whether PII can be captured
        allow_secret_access: Whether secrets can be accessed

    Returns:
        List of violation dicts (empty if all allowed)
    """
    checker = InspectionConstraintChecker(
        allow_prompt_logging=allow_prompt_logging,
        allow_response_logging=allow_response_logging,
        allow_pii_capture=allow_pii_capture,
        allow_secret_access=allow_secret_access,
    )
    violations = checker.check_all(operations)
    return [v.to_dict() for v in violations]
