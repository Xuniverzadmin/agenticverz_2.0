# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Differential replay — compares baseline vs candidate decisions
# artifact_class: CODE

"""
Differential Replay Verifier (BA-15)

Loads replay fixture files from a directory, validates each against the
replay contract schema, evaluates business invariants from the authority
layer, and compares the actual decision outcome against the expected
baseline decision.

Produces a deterministic diff report sorted by replay_id:
    [MATCH] — actual decision matches expected baseline
    [DRIFT] — actual decision differs from expected baseline

Exit codes:
    0 — no drifts (or no HIGH/CRITICAL drifts in non-strict mode)
    1 — at least one HIGH/CRITICAL drift (or any drift in --strict mode)

Usage:
    PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py \\
        --input tests/fixtures/replay/
    PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py \\
        --input tests/fixtures/replay/ --strict
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("nova.replay.differential")

# =============================================================================
# SCHEMA VALIDATION (manual — avoids jsonschema dependency)
# =============================================================================

_VALID_OUTCOMES = {"ALLOW", "DENY", "DEFERRED"}
_VALID_ACTOR_TYPES = {"user", "system", "sdk", "founder"}
_VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

_REQUIRED_TOP_LEVEL = {"replay_id", "operation", "input_context", "expected_decision"}


def validate_replay_case(case: dict[str, Any]) -> list[str]:
    """
    Validate a replay case dict against the replay contract schema.

    Returns a list of validation error strings (empty = valid).
    """
    errors: list[str] = []

    # Top-level required fields
    for field in _REQUIRED_TOP_LEVEL:
        if field not in case:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors  # Can't proceed without required fields

    # replay_id
    if not isinstance(case["replay_id"], str):
        errors.append("replay_id must be a string")

    # operation
    if not isinstance(case["operation"], str):
        errors.append("operation must be a string")

    # input_context
    ctx = case["input_context"]
    if not isinstance(ctx, dict):
        errors.append("input_context must be an object")
    else:
        if "tenant_id" not in ctx:
            errors.append("input_context.tenant_id is required")
        elif not isinstance(ctx["tenant_id"], str):
            errors.append("input_context.tenant_id must be a string")

        if "actor_type" in ctx and ctx["actor_type"] not in _VALID_ACTOR_TYPES:
            errors.append(
                f"input_context.actor_type must be one of {_VALID_ACTOR_TYPES}, "
                f"got '{ctx['actor_type']}'"
            )

    # expected_decision
    decision = case["expected_decision"]
    if not isinstance(decision, dict):
        errors.append("expected_decision must be an object")
    else:
        if "outcome" not in decision:
            errors.append("expected_decision.outcome is required")
        elif decision["outcome"] not in _VALID_OUTCOMES:
            errors.append(
                f"expected_decision.outcome must be one of {_VALID_OUTCOMES}, "
                f"got '{decision['outcome']}'"
            )

        if "invariants_checked" in decision:
            if not isinstance(decision["invariants_checked"], list):
                errors.append("expected_decision.invariants_checked must be an array")

    # metadata (optional)
    if "metadata" in case:
        meta = case["metadata"]
        if not isinstance(meta, dict):
            errors.append("metadata must be an object")
        else:
            if "severity" in meta and meta["severity"] not in _VALID_SEVERITIES:
                errors.append(
                    f"metadata.severity must be one of {_VALID_SEVERITIES}, "
                    f"got '{meta['severity']}'"
                )

    return errors


# =============================================================================
# DECISION EVALUATION
# =============================================================================


def evaluate_decision(case: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate business invariants for a replay case and produce an actual
    decision result.

    Attempts to import the business_invariants authority module. If the
    module is available and the operation has registered invariants, the
    actual decision is derived from invariant evaluation. Otherwise, the
    decision is based on structural analysis of the input context.

    Returns a dict with:
        outcome  — "ALLOW" | "DENY" | "DEFERRED"
        reason   — human-readable explanation
        invariants_evaluated — list of invariant IDs that were checked
    """
    operation = case["operation"]
    ctx = case.get("input_context", {})
    params = ctx.get("params", {})

    # Build evaluation context from input_context + params
    eval_context: dict[str, Any] = {
        "tenant_id": ctx.get("tenant_id"),
        "project_id": ctx.get("project_id"),
        "actor_type": ctx.get("actor_type"),
    }
    eval_context.update(params)

    invariants_evaluated: list[str] = []
    all_passed = True
    failure_reasons: list[str] = []

    # Try to use the authority layer's business invariants
    try:
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BUSINESS_INVARIANTS,
            check_all_for_operation,
        )

        # Find matching invariants for this operation
        results = check_all_for_operation(operation, eval_context)
        for inv_id, passed, message in results:
            invariants_evaluated.append(inv_id)
            if not passed:
                all_passed = False
                failure_reasons.append(f"{inv_id}: {message}")

        # If we found matching invariants, use their results
        if invariants_evaluated:
            if all_passed:
                return {
                    "outcome": "ALLOW",
                    "reason": "All invariants passed",
                    "invariants_evaluated": invariants_evaluated,
                }
            else:
                return {
                    "outcome": "DENY",
                    "reason": "; ".join(failure_reasons),
                    "invariants_evaluated": invariants_evaluated,
                }

    except ImportError:
        logger.debug(
            "business_invariants module not available — "
            "falling back to structural evaluation"
        )

    # Fallback: structural evaluation when no invariants match
    # This covers operations not yet registered in the invariant registry
    return _structural_evaluate(operation, eval_context, params)


def _structural_evaluate(
    operation: str,
    eval_context: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    Fallback structural evaluation for operations without registered
    business invariants. Uses simple heuristic rules to produce a
    decision.
    """
    tenant_id = eval_context.get("tenant_id")

    # Basic tenant scoping check
    if not tenant_id:
        return {
            "outcome": "DENY",
            "reason": "No tenant_id in context — cannot evaluate without tenant scope",
            "invariants_evaluated": [],
        }

    # Operation-specific structural checks
    if "resolve" in operation:
        current_state = params.get("current_state", "")
        if current_state == "resolved":
            return {
                "outcome": "DENY",
                "reason": "Cannot resolve already-resolved entity",
                "invariants_evaluated": [],
            }

    if "create" in operation or "activate" in operation:
        # For create/activate operations, default ALLOW if tenant is present
        return {
            "outcome": "ALLOW",
            "reason": "Structural preconditions satisfied (tenant scoped)",
            "invariants_evaluated": [],
        }

    # Default: ALLOW for unknown operations with valid tenant scope
    return {
        "outcome": "ALLOW",
        "reason": "No matching invariants; structurally valid (tenant scoped)",
        "invariants_evaluated": [],
    }


# =============================================================================
# REPLAY RUNNER
# =============================================================================


class ReplayResult:
    """Result of comparing expected vs actual decision for a single case."""

    def __init__(
        self,
        replay_id: str,
        operation: str,
        expected_outcome: str,
        actual_outcome: str,
        expected_reason: str,
        actual_reason: str,
        severity: str,
        invariants_evaluated: list[str],
    ):
        self.replay_id = replay_id
        self.operation = operation
        self.expected_outcome = expected_outcome
        self.actual_outcome = actual_outcome
        self.expected_reason = expected_reason
        self.actual_reason = actual_reason
        self.severity = severity
        self.invariants_evaluated = invariants_evaluated
        self.is_match = expected_outcome == actual_outcome

    @property
    def status_tag(self) -> str:
        return "[MATCH]" if self.is_match else "[DRIFT]"

    def format_line(self) -> str:
        tag = self.status_tag
        line = (
            f"{tag} {self.replay_id} | op={self.operation} | "
            f"expected={self.expected_outcome} actual={self.actual_outcome} | "
            f"severity={self.severity}"
        )
        if not self.is_match:
            line += f" | expected_reason=\"{self.expected_reason}\""
            line += f" | actual_reason=\"{self.actual_reason}\""
        if self.invariants_evaluated:
            line += f" | invariants={self.invariants_evaluated}"
        return line


def load_replay_cases(input_dir: str) -> list[dict[str, Any]]:
    """
    Load all .json files from the input directory.
    Returns a list of parsed replay case dicts.
    """
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"ERROR: input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(2)

    cases: list[dict[str, Any]] = []
    json_files = sorted(input_path.glob("*.json"))

    if not json_files:
        print(f"WARNING: no .json files found in {input_dir}", file=sys.stderr)
        return cases

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            data["_source_file"] = str(json_file)
            cases.append(data)
        except json.JSONDecodeError as e:
            print(
                f"ERROR: failed to parse {json_file}: {e}",
                file=sys.stderr,
            )
            sys.exit(2)

    return cases


def run_replay(
    cases: list[dict[str, Any]],
) -> list[ReplayResult]:
    """
    Run differential replay for all cases.

    For each case:
        1. Validate against the replay contract schema
        2. Evaluate the actual decision via business invariants
        3. Compare expected vs actual outcome
        4. Produce a ReplayResult

    Returns results sorted by replay_id for deterministic output.
    """
    results: list[ReplayResult] = []

    for case in cases:
        source_file = case.get("_source_file", "<unknown>")

        # Step 1: Validate schema
        errors = validate_replay_case(case)
        if errors:
            print(
                f"SCHEMA_ERROR in {source_file}: {errors}",
                file=sys.stderr,
            )
            # Create a DRIFT result for invalid cases
            results.append(
                ReplayResult(
                    replay_id=case.get("replay_id", f"<invalid:{source_file}>"),
                    operation=case.get("operation", "<unknown>"),
                    expected_outcome="<invalid>",
                    actual_outcome="SCHEMA_ERROR",
                    expected_reason="Schema validation failed",
                    actual_reason="; ".join(errors),
                    severity=case.get("metadata", {}).get("severity", "HIGH"),
                    invariants_evaluated=[],
                )
            )
            continue

        # Step 2: Evaluate actual decision
        actual = evaluate_decision(case)

        # Step 3: Compare
        expected_decision = case["expected_decision"]
        metadata = case.get("metadata", {})

        result = ReplayResult(
            replay_id=case["replay_id"],
            operation=case["operation"],
            expected_outcome=expected_decision["outcome"],
            actual_outcome=actual["outcome"],
            expected_reason=expected_decision.get("reason", ""),
            actual_reason=actual.get("reason", ""),
            severity=metadata.get("severity", "MEDIUM"),
            invariants_evaluated=actual.get("invariants_evaluated", []),
        )
        results.append(result)

    # Sort by replay_id for deterministic output
    results.sort(key=lambda r: r.replay_id)
    return results


def print_report(results: list[ReplayResult]) -> None:
    """Print the diff report to stdout."""
    print("=" * 72)
    print("DIFFERENTIAL REPLAY REPORT")
    print("=" * 72)
    print()

    for result in results:
        print(result.format_line())

    print()
    print("-" * 72)

    total = len(results)
    matches = sum(1 for r in results if r.is_match)
    drifts = total - matches
    high_critical_drifts = sum(
        1 for r in results
        if not r.is_match and r.severity in ("HIGH", "CRITICAL")
    )

    print(f"TOTAL:   {total}")
    print(f"MATCH:   {matches}")
    print(f"DRIFT:   {drifts}")
    if drifts > 0:
        print(f"  HIGH/CRITICAL drifts: {high_critical_drifts}")
    print("=" * 72)


def main() -> int:
    """
    Entry point for the differential replay script.

    Returns exit code:
        0 — no drifts (or no HIGH/CRITICAL drifts in non-strict mode)
        1 — blocking drifts detected
        2 — input error (bad dir, bad JSON, etc.)
    """
    parser = argparse.ArgumentParser(
        description="Differential replay — compares baseline vs candidate decisions"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to directory containing replay fixture .json files",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Any drift = exit 1 (default: only HIGH/CRITICAL drifts)",
    )
    args = parser.parse_args()

    # Load cases
    cases = load_replay_cases(args.input)
    if not cases:
        print("No replay cases found. Nothing to do.")
        return 0

    # Run replay
    results = run_replay(cases)

    # Print report
    print_report(results)

    # Determine exit code
    drifts = [r for r in results if not r.is_match]

    if not drifts:
        return 0

    if args.strict:
        # Any drift is a failure in strict mode
        return 1

    # Non-strict: only HIGH/CRITICAL drifts are failures
    high_critical = [r for r in drifts if r.severity in ("HIGH", "CRITICAL")]
    if high_critical:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
