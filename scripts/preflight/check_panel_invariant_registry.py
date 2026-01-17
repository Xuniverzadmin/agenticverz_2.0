#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI / pre-commit
#   Execution: sync
# Role: Ensure panel_invariant_registry.yaml is updated when policies API filters change
# Callers: CI workflow, pre-commit hooks
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L4, L5, L6
# Reference: PIN-411 (Governance Invariant GOV-POL-003)

"""
Panel Invariant Registry Consistency Guard

This script ensures that any change to /api/v1/policies/* filters
is accompanied by an update to panel_invariant_registry.yaml if
the change affects panel semantics.

CI Rule (GOV-POL-003 Enforcement):
  Any change to /api/v1/policies/* filters must update
  panel_invariant_registry.yaml if it affects panel semantics.

Usage:
  python check_panel_invariant_registry.py [--base-ref <ref>]

Exit codes:
  0 - Check passed (no issues or registry updated)
  1 - Check failed (filter change without registry update)
  2 - Script error
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Files that define policy API filters
POLICY_API_FILES = [
    "backend/app/api/policies.py",
    "backend/app/api/policy_layer.py",
    "backend/app/api/policy_proposals.py",
]

# The registry file that must be updated
REGISTRY_FILE = "backend/app/services/panel_invariant_registry.yaml"

# Patterns that indicate filter changes
FILTER_PATTERNS = [
    r"rule_type\s*[:=]",
    r"limit_type\s*[:=]",
    r"violation_kind\s*[:=]",
    r"violation_type\s*[:=]",
    r"source\s*[:=]",
    r"include_synthetic\s*[:=]",
    r"status\s*[:=]",
    r"scope\s*[:=]",
    r"enforcement\s*[:=]",
    r"Query\s*\(",
    r"@router\.(get|post|put|delete|patch)\s*\(",
    r"def\s+list_",
    r"def\s+get_",
]


def get_changed_files(base_ref: str = "HEAD~1") -> list[str]:
    """Get list of changed files compared to base ref."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        # Fallback for non-git environments or initial commits
        return []


def get_staged_files() -> list[str]:
    """Get list of staged files (for pre-commit)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def get_file_diff(filepath: str, base_ref: str = "HEAD~1") -> str:
    """Get the diff for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", base_ref, "HEAD", "--", filepath],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def contains_filter_change(diff: str) -> bool:
    """Check if diff contains filter-related changes."""
    # Only look at added/modified lines
    added_lines = [line for line in diff.split("\n") if line.startswith("+")]
    added_content = "\n".join(added_lines)

    for pattern in FILTER_PATTERNS:
        if re.search(pattern, added_content):
            return True
    return False


def check_registry_updated(changed_files: list[str]) -> bool:
    """Check if the panel invariant registry was updated."""
    return REGISTRY_FILE in changed_files


def main():
    parser = argparse.ArgumentParser(
        description="Check panel invariant registry consistency"
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD~1",
        help="Base git ref for comparison (default: HEAD~1)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check staged files only (for pre-commit)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    # Get changed files
    if args.staged:
        changed_files = get_staged_files()
    else:
        changed_files = get_changed_files(args.base_ref)

    if not changed_files:
        print("✅ No changed files detected")
        return 0

    if args.verbose:
        print(f"Changed files: {changed_files}")

    # Check if any policy API files were changed
    policy_files_changed = [f for f in changed_files if f in POLICY_API_FILES]

    if not policy_files_changed:
        print("✅ No policy API files changed")
        return 0

    # Check if changes include filter modifications
    filter_changes_detected = False
    affected_files = []

    for filepath in policy_files_changed:
        diff = get_file_diff(filepath, args.base_ref) if not args.staged else ""
        if args.staged:
            # For staged files, check if file exists and contains filter patterns
            try:
                with open(filepath) as f:
                    content = f.read()
                    for pattern in FILTER_PATTERNS:
                        if re.search(pattern, content):
                            filter_changes_detected = True
                            affected_files.append(filepath)
                            break
            except FileNotFoundError:
                pass
        else:
            if contains_filter_change(diff):
                filter_changes_detected = True
                affected_files.append(filepath)

    if not filter_changes_detected:
        print("✅ No filter-related changes detected in policy API files")
        return 0

    # Filter changes detected - check if registry was also updated
    registry_updated = check_registry_updated(changed_files)

    if registry_updated:
        print("✅ Panel invariant registry updated alongside filter changes")
        return 0

    # FAILURE: Filter changes without registry update
    print("=" * 70)
    print("❌ GOV-POL-003 VIOLATION: Panel Invariant Registry Not Updated")
    print("=" * 70)
    print()
    print("Policy API filter changes detected in:")
    for f in affected_files:
        print(f"  - {f}")
    print()
    print("But panel_invariant_registry.yaml was NOT updated.")
    print()
    print("Required action:")
    print(f"  1. Review: {REGISTRY_FILE}")
    print("  2. Add/update panel definitions if new filters affect panel semantics")
    print("  3. Update min_rows, alert_after_minutes, or zero_allowed as needed")
    print()
    print("Reference: PIN-411 Section 14.11 (Governance Invariants)")
    print("=" * 70)

    return 1


if __name__ == "__main__":
    sys.exit(main())
