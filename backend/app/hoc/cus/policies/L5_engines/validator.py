# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Policy DSL semantic validator (pure validation logic)
# Callers: policy engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-341 Section 1.8, PIN-345
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

"""
Policy DSL Semantic Validator

Validates AST against semantic rules. Does NOT parse.

DESIGN CONSTRAINTS (BLOCKING - PIN-341):
- Pure validation logic
- No side effects
- No I/O, no DB
- Must produce validation result (errors/warnings), not exceptions

SEMANTIC RULES:
1. Mode Enforcement:
   - MONITOR mode: Only WARN actions allowed
   - ENFORCE mode: WARN, BLOCK, REQUIRE_APPROVAL allowed

2. Metric Validation (optional):
   - If metric registry provided, validate metrics exist

3. Version Validation:
   - Version must be >= 1

4. Structural Validation:
   - At least one clause
   - At least one action per clause

GOVERNANCE:
- Validator is the authority on policy correctness
- All enforcement decisions derive from validator
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from app.dsl.ast import (
    Condition,
    Mode,
    PolicyAST,
    is_block_action,
    is_exists_predicate,
    is_logical_condition,
    is_predicate,
    is_require_approval_action,
)

# =============================================================================
# VALIDATION RESULT TYPES
# =============================================================================


class Severity(str, Enum):
    """Severity level for validation issues."""

    ERROR = "ERROR"  # Blocking - policy cannot be used
    WARNING = "WARNING"  # Non-blocking - policy can be used with caution


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single validation issue found in the policy."""

    code: str  # Unique error code (e.g., "V001")
    message: str  # Human-readable message
    severity: Severity  # ERROR or WARNING
    path: str = ""  # Path to the issue (e.g., "clauses[0].then[1]")

    def __str__(self) -> str:
        loc = f" at {self.path}" if self.path else ""
        return f"[{self.code}] {self.severity.value}{loc}: {self.message}"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of policy validation."""

    issues: tuple[ValidationIssue, ...]
    is_valid: bool = field(init=False)

    def __post_init__(self) -> None:
        # is_valid if no ERROR severity issues
        has_errors = any(i.severity == Severity.ERROR for i in self.issues)
        object.__setattr__(self, "is_valid", not has_errors)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return only ERROR severity issues."""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return only WARNING severity issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def __bool__(self) -> bool:
        """ValidationResult is truthy if valid."""
        return self.is_valid


# =============================================================================
# ERROR CODES
# =============================================================================

# Mode enforcement errors
V001 = "V001"  # BLOCK action in MONITOR mode
V002 = "V002"  # REQUIRE_APPROVAL action in MONITOR mode

# Metric validation errors
V010 = "V010"  # Unknown metric

# Structural errors (should be caught by parser, but defense in depth)
V020 = "V020"  # Empty clauses
V021 = "V021"  # Empty actions in clause

# Warnings
W001 = "W001"  # Policy has only WARN actions in ENFORCE mode (could be MONITOR)
W002 = "W002"  # Redundant condition (same predicate twice)


# =============================================================================
# VALIDATOR
# =============================================================================


class PolicyValidator:
    """
    Validates PolicyAST against semantic rules.

    Usage:
        validator = PolicyValidator()
        result = validator.validate(ast)
        if not result.is_valid:
            for error in result.errors:
                print(error)
    """

    def __init__(
        self,
        allowed_metrics: set[str] | None = None,
        custom_rules: list[Callable[[PolicyAST], list[ValidationIssue]]] | None = None,
    ) -> None:
        """
        Initialize validator.

        Args:
            allowed_metrics: If provided, validate that metrics are in this set.
                           If None, any metric name is allowed.
            custom_rules: Additional validation rules (functions that return issues).
        """
        self.allowed_metrics = allowed_metrics
        self.custom_rules = custom_rules or []

    def validate(self, policy: PolicyAST) -> ValidationResult:
        """
        Validate a policy AST.

        Returns:
            ValidationResult with all issues found.
        """
        issues: list[ValidationIssue] = []

        # Run all validation rules
        issues.extend(self._validate_mode_enforcement(policy))
        issues.extend(self._validate_metrics(policy))
        issues.extend(self._validate_structure(policy))
        issues.extend(self._check_warnings(policy))

        # Run custom rules
        for rule in self.custom_rules:
            issues.extend(rule(policy))

        return ValidationResult(issues=tuple(issues))

    def _validate_mode_enforcement(self, policy: PolicyAST) -> list[ValidationIssue]:
        """
        Validate that actions match the policy mode.

        MONITOR mode: Only WARN allowed
        ENFORCE mode: WARN, BLOCK, REQUIRE_APPROVAL allowed
        """
        issues: list[ValidationIssue] = []

        if policy.mode == Mode.MONITOR:
            # Check for forbidden actions
            for clause_idx, clause in enumerate(policy.clauses):
                for action_idx, action in enumerate(clause.then):
                    path = f"clauses[{clause_idx}].then[{action_idx}]"

                    if is_block_action(action):
                        issues.append(
                            ValidationIssue(
                                code=V001,
                                message="BLOCK action is not allowed in MONITOR mode",
                                severity=Severity.ERROR,
                                path=path,
                            )
                        )

                    if is_require_approval_action(action):
                        issues.append(
                            ValidationIssue(
                                code=V002,
                                message="REQUIRE_APPROVAL action is not allowed in MONITOR mode",
                                severity=Severity.ERROR,
                                path=path,
                            )
                        )

        return issues

    def _validate_metrics(self, policy: PolicyAST) -> list[ValidationIssue]:
        """
        Validate that all metrics are in the allowed set (if provided).
        """
        if self.allowed_metrics is None:
            return []

        issues: list[ValidationIssue] = []

        for clause_idx, clause in enumerate(policy.clauses):
            metrics = self._extract_metrics(clause.when)
            for metric in metrics:
                if metric not in self.allowed_metrics:
                    issues.append(
                        ValidationIssue(
                            code=V010,
                            message=f"Unknown metric: {metric}",
                            severity=Severity.ERROR,
                            path=f"clauses[{clause_idx}].when",
                        )
                    )

        return issues

    def _extract_metrics(self, condition: Condition) -> list[str]:
        """Extract all metric names from a condition."""
        metrics: list[str] = []

        if is_predicate(condition):
            metrics.append(condition.metric)
        elif is_exists_predicate(condition):
            metrics.append(condition.metric)
        elif is_logical_condition(condition):
            metrics.extend(self._extract_metrics(condition.left))
            metrics.extend(self._extract_metrics(condition.right))

        return metrics

    def _validate_structure(self, policy: PolicyAST) -> list[ValidationIssue]:
        """
        Validate structural integrity (defense in depth).

        These should be caught by the AST constructor, but we double-check.
        """
        issues: list[ValidationIssue] = []

        if not policy.clauses:
            issues.append(
                ValidationIssue(
                    code=V020,
                    message="Policy must have at least one clause",
                    severity=Severity.ERROR,
                    path="clauses",
                )
            )

        for clause_idx, clause in enumerate(policy.clauses):
            if not clause.then:
                issues.append(
                    ValidationIssue(
                        code=V021,
                        message="Clause must have at least one action",
                        severity=Severity.ERROR,
                        path=f"clauses[{clause_idx}].then",
                    )
                )

        return issues

    def _check_warnings(self, policy: PolicyAST) -> list[ValidationIssue]:
        """
        Check for non-blocking issues (warnings).
        """
        issues: list[ValidationIssue] = []

        # Check if ENFORCE mode only has WARN actions
        if policy.mode == Mode.ENFORCE:
            has_enforcement_action = False
            for clause in policy.clauses:
                for action in clause.then:
                    if is_block_action(action) or is_require_approval_action(action):
                        has_enforcement_action = True
                        break
                if has_enforcement_action:
                    break

            if not has_enforcement_action:
                issues.append(
                    ValidationIssue(
                        code=W001,
                        message="ENFORCE mode policy only uses WARN actions; consider MONITOR mode",
                        severity=Severity.WARNING,
                        path="metadata.mode",
                    )
                )

        return issues


# =============================================================================
# PUBLIC API
# =============================================================================


def validate(
    policy: PolicyAST,
    allowed_metrics: set[str] | None = None,
) -> ValidationResult:
    """
    Validate a policy AST.

    Args:
        policy: The PolicyAST to validate
        allowed_metrics: If provided, validate metrics against this set

    Returns:
        ValidationResult with all issues found

    Example:
        >>> from app.dsl import parse
        >>> ast = parse('''
        ... policy Test
        ... version 1
        ... scope ORG
        ... mode MONITOR
        ...
        ... when x > 0
        ... then BLOCK
        ... ''')
        >>> result = validate(ast)
        >>> result.is_valid
        False
        >>> result.errors[0].code
        'V001'
    """
    validator = PolicyValidator(allowed_metrics=allowed_metrics)
    return validator.validate(policy)


def is_valid(
    policy: PolicyAST,
    allowed_metrics: set[str] | None = None,
) -> bool:
    """
    Quick check if a policy is valid.

    Args:
        policy: The PolicyAST to validate
        allowed_metrics: If provided, validate metrics against this set

    Returns:
        True if valid, False otherwise
    """
    result = validate(policy, allowed_metrics)
    return result.is_valid
