#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: No-regression guard for Priority-4 intent declarations
# Callers: CI pipeline, pre-commit hooks
# Reference: PIN-265 (Phase-3 Intent-Driven Refactoring)

"""
Priority-4 Feature Intent Guard

This script ensures the 7 Priority-4 (HIGH blast radius) files
maintain their FEATURE_INTENT and RETRY_POLICY declarations.

PRIORITY-4 FILES (HIGH BLAST RADIUS)
------------------------------------

Jobs:
  - jobs/failure_aggregation.py       EXTERNAL_SIDE_EFFECT + NEVER
  - jobs/failure_classification_engine.py PURE_QUERY (no policy)
  - jobs/graduation_evaluator.py      STATE_MUTATION + SAFE
  - jobs/storage.py                   EXTERNAL_SIDE_EFFECT + NEVER

Optimization:
  - optimization/audit_persistence.py STATE_MUTATION + SAFE
  - optimization/coordinator.py       STATE_MUTATION + SAFE

Tasks:
  - tasks/m10_metrics_collector.py    PURE_QUERY (no policy)

USAGE
-----
    python scripts/ci/check_priority4_intent.py [--verbose]

EXIT CODES
----------
    0 = All Priority-4 files pass
    1 = Regressions detected
    2 = Script error
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

# Priority-4 files with expected intent declarations
# Format: (path relative to app/, (FeatureIntent, RetryPolicy or None))
PRIORITY_4_FILES: Dict[str, Tuple[str, Optional[str]]] = {
    "jobs/failure_aggregation.py": ("EXTERNAL_SIDE_EFFECT", "NEVER"),
    "jobs/failure_classification_engine.py": ("PURE_QUERY", None),
    "jobs/graduation_evaluator.py": ("STATE_MUTATION", "SAFE"),
    "jobs/storage.py": ("EXTERNAL_SIDE_EFFECT", "NEVER"),
    "optimization/audit_persistence.py": ("STATE_MUTATION", "SAFE"),
    "optimization/coordinator.py": ("STATE_MUTATION", "SAFE"),
    "tasks/m10_metrics_collector.py": ("PURE_QUERY", None),
}


@dataclass
class Regression:
    """A detected regression in Priority-4 intent declarations."""

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


def check_priority4_files(verbose: bool = False) -> list[Regression]:
    """Check all Priority-4 files for regressions."""
    regressions = []
    app_dir = Path("app")

    for relative_path, (expected_intent, expected_policy) in PRIORITY_4_FILES.items():
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

        # Check RETRY_POLICY (only if expected)
        if expected_policy is not None:
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

        if verbose:
            if actual_intent == expected_intent:
                policy_str = f" + {expected_policy}" if expected_policy else ""
                print(f"  [OK] {expected_intent}{policy_str}")

    return regressions


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Priority-4 files for intent declaration regressions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 70)
    print("PRIORITY-4 FEATURE INTENT GUARD")
    print("=" * 70)
    print(f"Checking {len(PRIORITY_4_FILES)} Priority-4 files...\n")

    regressions = check_priority4_files(args.verbose)

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
        print("\nPriority-4 files are HIGH blast radius modules.")
        print("These declarations MUST NOT be removed or changed without review.")
        print("\nSee: PIN-265 (Phase-3 Intent-Driven Refactoring)")
        return 1

    print("=" * 70)
    print(f"PASSED: All {len(PRIORITY_4_FILES)} Priority-4 files have correct declarations")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
