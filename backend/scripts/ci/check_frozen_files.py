#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: PIN-399 Design Freeze Enforcement
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: None (static analysis only)
# Forbidden Imports: L1, L2, L3, L4, L5, L6
# Reference: PIN-399, docs/governance/FREEZE.md

"""
Design Freeze Enforcement — Phases 4–6

This script FAILS CI if frozen files are modified without a PIN reference
in the commit message.

FROZEN FILES (per FREEZE.md):
- Onboarding: onboarding_state.py, onboarding_transitions.py, onboarding_gate.py
- Roles: role_guard.py, tenant_roles.py
- Billing Design: PHASE_6_BILLING_LIMITS.md

USAGE
-----
    python scripts/ci/check_frozen_files.py [--verbose] [--check-commit MSG]

EXIT CODES
----------
    0 = No frozen files modified (or PIN reference present)
    1 = Frozen files modified without PIN reference
    2 = Script error

PHILOSOPHY
----------
Freezes are not bureaucracy. They are structural protection.
A frozen file represents a design decision that downstream code depends on.
Changing it without acknowledgment breaks the contract.
"""

import argparse
import re
import subprocess
import sys


# Files frozen per docs/governance/FREEZE.md
FROZEN_FILES = [
    # Onboarding (Phase-4)
    "app/auth/onboarding_state.py",
    "app/auth/onboarding_transitions.py",
    "app/auth/onboarding_gate.py",
    "app/api/founder_onboarding.py",
    # Roles (Phase-5)
    "app/auth/role_guard.py",
    "app/auth/tenant_roles.py",
    # Billing Design (Phase-6)
    "docs/architecture/PHASE_6_BILLING_LIMITS.md",
]

# Pattern to match PIN references in commit messages
PIN_PATTERN = re.compile(r"PIN-\d+", re.IGNORECASE)


def get_changed_files() -> list[str]:
    """Get list of files changed in the current commit/staging."""
    try:
        # Try to get staged files first (pre-commit)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        if files and files[0]:
            return [f for f in files if f]

        # Fall back to last commit (CI)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f]

    except subprocess.CalledProcessError:
        return []


def get_commit_message() -> str:
    """Get the current/last commit message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def is_frozen(file_path: str) -> bool:
    """Check if a file is in the frozen list."""
    # Normalize path
    normalized = file_path.replace("\\", "/")

    for frozen in FROZEN_FILES:
        if normalized.endswith(frozen) or frozen in normalized:
            return True

    return False


def has_pin_reference(message: str) -> bool:
    """Check if commit message contains a PIN reference."""
    return bool(PIN_PATTERN.search(message))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for modifications to frozen files (PIN-399)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--check-commit",
        metavar="MSG",
        help="Check against specific commit message (for testing)",
    )
    parser.add_argument(
        "--list-frozen",
        action="store_true",
        help="List all frozen files and exit",
    )

    args = parser.parse_args()

    if args.list_frozen:
        print("Frozen files (per FREEZE.md):")
        for f in FROZEN_FILES:
            print(f"  - {f}")
        return 0

    print("PIN-399 Design Freeze Check")
    print()

    # Get changed files
    changed_files = get_changed_files()

    if args.verbose:
        print(f"Changed files: {len(changed_files)}")
        for f in changed_files:
            print(f"  - {f}")
        print()

    # Find frozen files that were modified
    modified_frozen = [f for f in changed_files if is_frozen(f)]

    if not modified_frozen:
        print("No frozen files modified.")
        return 0

    # Check for PIN reference
    commit_msg = args.check_commit or get_commit_message()

    if args.verbose:
        print(f"Commit message: {commit_msg[:100]}...")
        print()

    if has_pin_reference(commit_msg):
        print(f"Frozen files modified WITH PIN reference:")
        for f in modified_frozen:
            print(f"  - {f}")
        print()
        pin_match = PIN_PATTERN.search(commit_msg)
        if pin_match:
            print(f"PIN reference found in commit: {pin_match.group()}")
        print("Change approved (PIN reference present).")
        return 0

    # Frozen files modified without PIN reference
    print(f"{'#' * 60}")
    print("# FROZEN FILES MODIFIED WITHOUT PIN REFERENCE")
    print(f"{'#' * 60}")
    print()
    print("The following frozen files were modified:")
    for f in modified_frozen:
        print(f"  - {f}")
    print()
    print("Frozen files require explicit PIN reference in commit message.")
    print()
    print("To fix:")
    print("  1. Include 'PIN-XXX' in your commit message")
    print("  2. Ensure the PIN documents why this change is necessary")
    print()
    print("Example commit message:")
    print('  "Fix role guard edge case (PIN-399)"')
    print()
    print("Reference: docs/governance/FREEZE.md")

    return 1


if __name__ == "__main__":
    sys.exit(main())
