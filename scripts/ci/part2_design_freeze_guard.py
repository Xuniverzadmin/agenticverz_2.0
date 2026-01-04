#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Enforce Part-2 design document freeze
# Callers: CI pipeline, pre-commit
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, part2-design-v1 tag
#
# GATE-10: Phase-2 Lock
# Risk: Design drift
# Enforcement: All 9 design docs + closure note frozen

"""
Part-2 Design Freeze Guard

Ensures Part-2 constitutional design documents remain immutable.
Any modification requires explicit amendment process referencing part2-design-v1.

Exit codes:
  0 - All frozen files intact
  1 - Frozen file modified (BLOCKING)
  2 - Configuration error
"""

import subprocess
import sys
from pathlib import Path

# Frozen at part2-design-v1 tag (2026-01-04)
PART2_FROZEN_FILES = [
    "docs/governance/part2/PART2_CRM_WORKFLOW_CHARTER.md",
    "docs/governance/part2/SYSTEM_CONTRACT_OBJECT.md",
    "docs/governance/part2/ELIGIBILITY_RULES.md",
    "docs/governance/part2/VALIDATOR_LOGIC.md",
    "docs/governance/part2/GOVERNANCE_JOB_MODEL.md",
    "docs/governance/part2/FOUNDER_REVIEW_SEMANTICS.md",
    "docs/governance/part2/GOVERNANCE_AUDIT_MODEL.md",
    "docs/governance/part2/END_TO_END_STATE_MACHINE.md",
    "docs/governance/part2/PART2_CLOSURE_CRITERIA.md",
    "docs/governance/part2/PART2_CLOSURE_NOTE.md",
    "docs/governance/part2/INDEX.md",
]

DESIGN_TAG = "part2-design-v1"


def get_repo_root() -> Path:
    """Get repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Not a git repository", file=sys.stderr)
        sys.exit(2)
    return Path(result.stdout.strip())


def get_changed_files() -> set[str]:
    """Get files changed in current commit or staging area."""
    # Check staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    staged = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

    # Check uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
    )
    unstaged = (
        set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
    )

    # Check files changed since design tag (for CI)
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{DESIGN_TAG}..HEAD"],
        capture_output=True,
        text=True,
    )
    since_tag = (
        set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
    )

    return staged | unstaged | since_tag


def check_frozen_files(changed: set[str]) -> list[str]:
    """Check if any frozen files were modified."""
    violations = []
    for frozen in PART2_FROZEN_FILES:
        if frozen in changed:
            violations.append(frozen)
    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Design Freeze Guard")
    print(f"Reference: {DESIGN_TAG}")
    print("=" * 70)
    print()

    repo_root = get_repo_root()

    # Verify frozen files exist
    missing = []
    for frozen in PART2_FROZEN_FILES:
        if not (repo_root / frozen).exists():
            missing.append(frozen)

    if missing:
        print("ERROR: Missing frozen files (design incomplete):")
        for f in missing:
            print(f"  - {f}")
        return 2

    print(f"Frozen files: {len(PART2_FROZEN_FILES)}")
    print()

    # Check for modifications
    changed = get_changed_files()
    violations = check_frozen_files(changed)

    if violations:
        print("GATE-10 VIOLATION: Part-2 design files modified")
        print()
        print("The following files are frozen at part2-design-v1:")
        for v in violations:
            print(f"  ❌ {v}")
        print()
        print("Resolution options:")
        print("  1. Revert changes: git checkout part2-design-v1 -- <file>")
        print("  2. Propose Part-3 amendment (requires explicit ratification)")
        print()
        print("Part-2 design is CONSTITUTIONAL. Changes require:")
        print("  - New phase proposal")
        print("  - Explicit reference to part2-design-v1")
        print("  - Founder ratification")
        print()
        return 1

    print("✅ All Part-2 design files intact")
    print()
    print("Part-2 constitutional documents:")
    for f in PART2_FROZEN_FILES:
        print(f"  ✓ {f}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
