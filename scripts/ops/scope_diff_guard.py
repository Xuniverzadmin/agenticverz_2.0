#!/usr/bin/env python3
# Layer: L8 — Meta / Enforcement
# Product: system-wide
# Temporal:
#   Trigger: pre-commit hook, CI
#   Execution: sync
# Role: Prevent closure-tagged commits from mutating frozen scope
# Callers: pre-commit, CI workflow
# Allowed Imports: stdlib only
# Forbidden Imports: app.*, backend.*
# Reference: PIN-290, POST_CLOSURE_HYGIENE_NOTE.md
"""
Scope Diff Guard — L8 Enforcement for Closure Commits

PURPOSE:
    Closure commits are legal acts, not coding acts.
    They must only touch governance/documentation paths.
    Any mutation to frozen code scope is a governance violation.

TRIGGER KEYWORDS:
    If commit message contains any of:
    - CLOSED
    - RATIFIED
    - ANCHOR
    - FREEZE
    - PART-2
    - PART-3
    - CONSTITUTIONAL

ENFORCEMENT:
    - Only allow diffs under explicitly whitelisted paths
    - Hard fail if any file outside allowed paths is staged
    - No auto-fix, no overrides
    - Even formatting-only changes are blocked

PHILOSOPHY:
    A closure commit is a legal act, not a coding act.
    Lint fixes must be separate commits before closure.

USAGE:
    # As pre-commit hook
    python scripts/ops/scope_diff_guard.py

    # With explicit message (CI mode)
    python scripts/ops/scope_diff_guard.py --message "Part-2 - CLOSED"

    # Dry run (check without failing)
    python scripts/ops/scope_diff_guard.py --dry-run
"""

import argparse
import subprocess
import sys
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Keywords that trigger scope enforcement
CLOSURE_KEYWORDS = [
    "CLOSED",
    "RATIFIED",
    "ANCHOR",
    "FREEZE",
    "PART-2",
    "PART-3",
    "CONSTITUTIONAL",
]

# Paths allowed in closure commits (governance, docs, CI only)
ALLOWED_PATHS = [
    "docs/governance/",
    "docs/memory-pins/",
    "docs/contracts/",
    "docs/playbooks/",
    "docs/templates/",
    "scripts/ci/",
    "scripts/ops/scope_diff_guard.py",  # Allow self-modification
    ".github/workflows/",
    ".pre-commit-config.yaml",  # Pre-commit config is governance
    "CLAUDE.md",
    "CLAUDE_AUTHORITY.md",
    "CLAUDE_BOOT_CONTRACT.md",
    "CLAUDE_PRE_CODE_DISCIPLINE.md",
    "CLAUDE_BEHAVIOR_LIBRARY.md",
]

# Paths explicitly forbidden even if they match a pattern
FORBIDDEN_PATHS = [
    "backend/app/",
    "backend/tests/",
    "sdk/",
    "website/",
]


# =============================================================================
# CORE LOGIC
# =============================================================================


def get_commit_message() -> str:
    """Get the commit message from git."""
    try:
        # Try to get message from COMMIT_EDITMSG (pre-commit hook)
        git_dir = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        commit_msg_file = Path(git_dir) / "COMMIT_EDITMSG"
        if commit_msg_file.exists():
            return commit_msg_file.read_text()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return ""


def is_closure_commit(message: str) -> bool:
    """Check if commit message contains closure keywords."""
    message_upper = message.upper()
    for keyword in CLOSURE_KEYWORDS:
        if keyword in message_upper:
            return True
    return False


def get_staged_files() -> list[str]:
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files
    except subprocess.CalledProcessError:
        return []


def is_path_allowed(filepath: str) -> bool:
    """Check if a file path is allowed in closure commits."""
    # Check forbidden paths first (they override allowed)
    for forbidden in FORBIDDEN_PATHS:
        if filepath.startswith(forbidden):
            return False

    # Check allowed paths
    for allowed in ALLOWED_PATHS:
        if filepath.startswith(allowed) or filepath == allowed.rstrip("/"):
            return True

    return False


def check_scope_violation(staged_files: list[str]) -> tuple[bool, list[str]]:
    """
    Check if any staged files violate scope rules.

    Returns:
        (has_violation, violating_files)
    """
    violations = []
    for filepath in staged_files:
        if not is_path_allowed(filepath):
            violations.append(filepath)

    return len(violations) > 0, violations


def format_error_message(violations: list[str], message: str) -> str:
    """Format the error message for violations."""
    triggered_keywords = [kw for kw in CLOSURE_KEYWORDS if kw in message.upper()]

    lines = [
        "",
        "=" * 72,
        "SCOPE DIFF GUARD — GOVERNANCE VIOLATION DETECTED",
        "=" * 72,
        "",
        "Closure-tagged commit attempted to modify frozen scope.",
        "",
        f"Triggered by keyword(s): {', '.join(triggered_keywords)}",
        "",
        "VIOLATION: The following files are outside allowed scope:",
        "",
    ]

    for v in violations[:20]:  # Limit to first 20
        lines.append(f"  - {v}")

    if len(violations) > 20:
        lines.append(f"  ... and {len(violations) - 20} more")

    lines.extend(
        [
            "",
            "ALLOWED PATHS for closure commits:",
            "",
        ]
    )

    for allowed in ALLOWED_PATHS[:10]:
        lines.append(f"  + {allowed}")

    lines.extend(
        [
            "",
            "RESOLUTION:",
            "",
            "  1. Split this commit into TWO commits:",
            "",
            "     FIRST:  Lint/format fixes (non-closure)",
            "            git add <formatting files>",
            '            git commit -m "chore: lint fixes"',
            "",
            "     SECOND: Closure commit (governance only)",
            "            git add <governance files only>",
            '            git commit -m "Part-X ... - CLOSED"',
            "",
            "  2. Or remove closure keyword from message if this is not a closure.",
            "",
            "PHILOSOPHY:",
            "",
            "  A closure commit is a legal act, not a coding act.",
            "  Lint fixes must be separate commits before closure.",
            "",
            "Reference: PIN-290, POST_CLOSURE_HYGIENE_NOTE.md",
            "=" * 72,
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scope Diff Guard — Enforce closure commit boundaries"
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Commit message (if not provided, reads from git)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check without failing (warning mode)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Get commit message
    message = args.message or get_commit_message()

    if not message:
        if args.verbose:
            print("[scope-guard] No commit message found, skipping check")
        return 0

    # Check if this is a closure commit
    if not is_closure_commit(message):
        if args.verbose:
            print("[scope-guard] Not a closure commit, skipping check")
        return 0

    if args.verbose:
        print("[scope-guard] Closure commit detected, checking scope...")

    # Get staged files
    staged_files = get_staged_files()

    if not staged_files:
        if args.verbose:
            print("[scope-guard] No staged files, skipping check")
        return 0

    # Check for violations
    has_violation, violations = check_scope_violation(staged_files)

    if has_violation:
        error_msg = format_error_message(violations, message)
        print(error_msg, file=sys.stderr)

        if args.dry_run:
            print("[scope-guard] DRY RUN: Would have blocked commit", file=sys.stderr)
            return 0
        else:
            return 1

    if args.verbose:
        print(f"[scope-guard] All {len(staged_files)} staged files are within scope")

    return 0


if __name__ == "__main__":
    sys.exit(main())
