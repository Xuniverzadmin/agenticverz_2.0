#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: No-regression guard for Priority-5 intent declarations
# Callers: CI pipeline, pre-commit hooks
# Reference: PIN-265 (Phase-3 Intent-Driven Refactoring)

"""
Priority-5 Feature Intent Guard

This script ensures the 12 Priority-5 (CRITICAL blast radius) files
maintain their FEATURE_INTENT and RETRY_POLICY declarations.

WHAT THIS CHECKS
----------------

1. Existence Check
   - Each Priority-5 file has FEATURE_INTENT declaration
   - Each Priority-5 file has RETRY_POLICY declaration

2. Value Verification
   - FEATURE_INTENT matches expected value
   - RETRY_POLICY matches expected value

PRIORITY-5 FILES (CRITICAL BLAST RADIUS)
----------------------------------------

Worker Layer:
  - hoc/int/worker/runner.py                 RECOVERABLE_OPERATION + SAFE
  - hoc/int/worker/outbox_processor.py       RECOVERABLE_OPERATION + SAFE
  - hoc/int/worker/pool.py                   STATE_MUTATION + SAFE
  - hoc/int/worker/recovery_claim_worker.py  RECOVERABLE_OPERATION + SAFE
  - hoc/int/worker/recovery_evaluator.py     RECOVERABLE_OPERATION + SAFE

Circuit Breaker:
  - costsim/circuit_breaker.py       STATE_MUTATION + SAFE
  - costsim/circuit_breaker_async.py STATE_MUTATION + SAFE
  - costsim/alert_worker.py          EXTERNAL_SIDE_EFFECT + NEVER

Recovery Services:
  - services/orphan_recovery.py      STATE_MUTATION + SAFE
  - services/recovery_matcher.py     EXTERNAL_SIDE_EFFECT + NEVER
  - hoc/cus/policies/L6_drivers/recovery_write_driver.py STATE_MUTATION + SAFE
  - tasks/recovery_queue_stream.py   RECOVERABLE_OPERATION + SAFE

USAGE
-----
    python scripts/ci/check_priority5_intent.py [--verbose]

EXIT CODES
----------
    0 = All Priority-5 files pass
    1 = Regressions detected
    2 = Script error
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

# Priority-5 files with expected intent declarations
# Format: (path relative to app/, (FeatureIntent, RetryPolicy))
PRIORITY_5_FILES: Dict[str, Tuple[str, str]] = {
    "hoc/int/worker/runner.py": ("RECOVERABLE_OPERATION", "SAFE"),
    "hoc/int/worker/outbox_processor.py": ("RECOVERABLE_OPERATION", "SAFE"),
    "hoc/int/worker/pool.py": ("STATE_MUTATION", "SAFE"),
    "hoc/int/worker/recovery_claim_worker.py": ("RECOVERABLE_OPERATION", "SAFE"),
    "hoc/int/worker/recovery_evaluator.py": ("RECOVERABLE_OPERATION", "SAFE"),
    "costsim/circuit_breaker.py": ("STATE_MUTATION", "SAFE"),
    "costsim/circuit_breaker_async.py": ("STATE_MUTATION", "SAFE"),
    "costsim/alert_worker.py": ("EXTERNAL_SIDE_EFFECT", "NEVER"),
    "services/orphan_recovery.py": ("STATE_MUTATION", "SAFE"),
    "services/recovery_matcher.py": ("EXTERNAL_SIDE_EFFECT", "NEVER"),
    "hoc/cus/policies/L6_drivers/recovery_write_driver.py": ("STATE_MUTATION", "SAFE"),
    "tasks/recovery_queue_stream.py": ("RECOVERABLE_OPERATION", "SAFE"),
}


@dataclass
class Regression:
    """A detected regression in Priority-5 intent declarations."""

    file: str
    issue: str
    expected: str
    actual: str


def extract_intent_values(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract FEATURE_INTENT and RETRY_POLICY values from a file using AST."""
    feature_intent = None
    retry_policy = None

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "FEATURE_INTENT":
                            if isinstance(node.value, ast.Attribute):
                                feature_intent = node.value.attr
                        elif target.id == "RETRY_POLICY":
                            if isinstance(node.value, ast.Attribute):
                                retry_policy = node.value.attr
    except Exception as e:
        print(f"  [ERROR] Failed to parse {file_path}: {e}")

    return feature_intent, retry_policy


def check_priority5_files(verbose: bool = False) -> list[Regression]:
    """Check all Priority-5 files for regressions."""
    regressions = []
    app_dir = Path("app")

    for relative_path, (expected_intent, expected_policy) in PRIORITY_5_FILES.items():
        file_path = app_dir / relative_path

        if verbose:
            print(f"Checking: {file_path}")

        # Check file exists
        if not file_path.exists():
            regressions.append(
                Regression(
                    file=relative_path,
                    issue="FILE_MISSING",
                    expected="File exists",
                    actual="File not found",
                )
            )
            continue

        # Extract actual values
        actual_intent, actual_policy = extract_intent_values(file_path)

        # Check FEATURE_INTENT
        if actual_intent is None:
            regressions.append(
                Regression(
                    file=relative_path,
                    issue="MISSING_FEATURE_INTENT",
                    expected=f"FeatureIntent.{expected_intent}",
                    actual="None",
                )
            )
        elif actual_intent != expected_intent:
            regressions.append(
                Regression(
                    file=relative_path,
                    issue="WRONG_FEATURE_INTENT",
                    expected=f"FeatureIntent.{expected_intent}",
                    actual=f"FeatureIntent.{actual_intent}",
                )
            )

        # Check RETRY_POLICY
        if actual_policy is None:
            regressions.append(
                Regression(
                    file=relative_path,
                    issue="MISSING_RETRY_POLICY",
                    expected=f"RetryPolicy.{expected_policy}",
                    actual="None",
                )
            )
        elif actual_policy != expected_policy:
            regressions.append(
                Regression(
                    file=relative_path,
                    issue="WRONG_RETRY_POLICY",
                    expected=f"RetryPolicy.{expected_policy}",
                    actual=f"RetryPolicy.{actual_policy}",
                )
            )

        if verbose and actual_intent == expected_intent and actual_policy == expected_policy:
            print(f"  [OK] {expected_intent} + {expected_policy}")

    return regressions


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Priority-5 files for intent declaration regressions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 70)
    print("PRIORITY-5 FEATURE INTENT GUARD")
    print("=" * 70)
    print(f"Checking {len(PRIORITY_5_FILES)} Priority-5 files...\n")

    regressions = check_priority5_files(args.verbose)

    if regressions:
        print("\n" + "=" * 70)
        print("REGRESSIONS DETECTED")
        print("=" * 70)

        for reg in regressions:
            print(f"\nFile: {reg.file}")
            print(f"Issue: {reg.issue}")
            print(f"Expected: {reg.expected}")
            print(f"Actual: {reg.actual}")

        print("\n" + "=" * 70)
        print(f"FAILED: {len(regressions)} regression(s) detected")
        print("=" * 70)
        print("\nPriority-5 files are CRITICAL blast radius modules.")
        print("These declarations MUST NOT be removed or changed without review.")
        print("\nSee: PIN-265 (Phase-3 Intent-Driven Refactoring)")
        return 1

    print("=" * 70)
    print(f"PASSED: All {len(PRIORITY_5_FILES)} Priority-5 files have correct declarations")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
