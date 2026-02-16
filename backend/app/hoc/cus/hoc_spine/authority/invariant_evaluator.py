# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Invariant evaluator — validates business invariants before/after operations
# Product: system-wide
# Temporal:
#   Trigger: operation dispatch
#   Execution: sync
# Callers: L4 operation_registry, L4 handlers
# Allowed Imports: stdlib only + business_invariants (same package)
# Forbidden Imports: FastAPI, Starlette, DB, ORM
# Reference: BA-04 Business Assurance Guardrails
# artifact_class: CODE

"""
Invariant Evaluator (BA-04 — Business Assurance Guardrails)

Evaluates business invariants before and after critical operations.
Supports three enforcement modes:

  MONITOR  — log results, never block (safe for rollout / shadow testing)
  ENFORCE  — raise on CRITICAL invariant violations only
  STRICT   — raise on ANY invariant violation

The evaluator delegates actual invariant definitions and checks to the
``business_invariants`` sibling module. This module is the *execution
surface* — it orchestrates evaluation, logging, and mode-aware error
propagation.

This module contains NO framework imports — it is pure evaluation logic.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass

from .business_invariants import (
    BusinessInvariantViolation,
    BUSINESS_INVARIANTS,
    check_all_for_operation,
)

logger = logging.getLogger("nova.hoc.invariant_evaluator")


# =============================================================================
# ENFORCEMENT MODE
# =============================================================================


class InvariantMode(enum.Enum):
    """Controls how invariant evaluation failures are handled."""

    MONITOR = "monitor"   # Log only, never block
    ENFORCE = "enforce"   # Raise on CRITICAL violations
    STRICT = "strict"     # Raise on ANY violation


# =============================================================================
# EVALUATION RESULT
# =============================================================================


@dataclass(frozen=True)
class InvariantResult:
    """Outcome of evaluating a single business invariant."""

    invariant_id: str
    passed: bool
    message: str
    severity: str
    mode: InvariantMode


# =============================================================================
# CORE EVALUATION
# =============================================================================


def evaluate_invariants(
    operation: str,
    context: dict,
    mode: InvariantMode = InvariantMode.MONITOR,
) -> list[InvariantResult]:
    """
    Evaluate all business invariants registered for *operation*.

    Steps:
        1. Delegate to ``check_all_for_operation`` to run every invariant
           that applies to the given operation.
        2. Log each result via stdlib logging.
        3. In ENFORCE mode: raise ``BusinessInvariantViolation`` if any
           CRITICAL invariant fails.
        4. In STRICT mode: raise ``BusinessInvariantViolation`` if ANY
           invariant fails.
        5. In MONITOR mode: always return results without raising.

    Returns:
        A list of ``InvariantResult`` — one per evaluated invariant.
    """
    raw_outcomes = check_all_for_operation(operation, context)

    results: list[InvariantResult] = []
    failures_critical: list[InvariantResult] = []
    failures_any: list[InvariantResult] = []

    for invariant_id, passed, message in raw_outcomes:
        # Look up severity from the invariant registry
        inv = BUSINESS_INVARIANTS.get(invariant_id)
        severity: str = inv.severity if inv else "MEDIUM"

        result = InvariantResult(
            invariant_id=invariant_id,
            passed=passed,
            message=message,
            severity=severity,
            mode=mode,
        )
        results.append(result)

        # --- Structured logging per result --------------------------------
        log_extra = {
            "invariant_id": invariant_id,
            "passed": passed,
            "severity": severity,
            "operation": operation,
            "mode": mode.value,
        }

        if passed:
            logger.debug(
                "invariant_passed: %s (op=%s)",
                invariant_id,
                operation,
                extra=log_extra,
            )
        else:
            logger.warning(
                "invariant_failed: %s (op=%s, severity=%s, mode=%s) — %s",
                invariant_id,
                operation,
                severity,
                mode.value,
                message,
                extra=log_extra,
            )

            # Track failures by severity bucket
            if severity == "CRITICAL":
                failures_critical.append(result)
            failures_any.append(result)

    # --- Mode-aware error propagation -------------------------------------

    if mode is InvariantMode.ENFORCE and failures_critical:
        first = failures_critical[0]
        raise BusinessInvariantViolation(
            invariant_id=first.invariant_id,
            operation=operation,
            severity=first.severity,
            message=f"CRITICAL invariant(s) failed: {[r.invariant_id for r in failures_critical]}",
        )

    if mode is InvariantMode.STRICT and failures_any:
        first = failures_any[0]
        raise BusinessInvariantViolation(
            invariant_id=first.invariant_id,
            operation=operation,
            severity=first.severity,
            message=f"Invariant(s) failed: {[r.invariant_id for r in failures_any]}",
        )

    # MONITOR mode (or no failures): always return results
    return results


# =============================================================================
# CONVENIENCE WRAPPERS
# =============================================================================


def evaluate_preconditions(
    operation: str,
    context: dict,
    mode: InvariantMode = InvariantMode.MONITOR,
) -> list[InvariantResult]:
    """
    Evaluate invariants as *preconditions* before an operation executes.

    Delegates to ``evaluate_invariants`` with the operation name suffixed
    by ``:pre`` so that callers can register phase-specific invariants.
    """
    pre_operation = f"{operation}:pre"
    logger.debug("evaluate_preconditions: op=%s", pre_operation)
    return evaluate_invariants(pre_operation, context, mode)


def evaluate_postconditions(
    operation: str,
    context: dict,
    mode: InvariantMode = InvariantMode.MONITOR,
) -> list[InvariantResult]:
    """
    Evaluate invariants as *postconditions* after an operation completes.

    Delegates to ``evaluate_invariants`` with the operation name suffixed
    by ``:post`` so that callers can register phase-specific invariants.
    """
    post_operation = f"{operation}:post"
    logger.debug("evaluate_postconditions: op=%s", post_operation)
    return evaluate_invariants(post_operation, context, mode)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "InvariantMode",
    "InvariantResult",
    "evaluate_invariants",
    "evaluate_preconditions",
    "evaluate_postconditions",
]
