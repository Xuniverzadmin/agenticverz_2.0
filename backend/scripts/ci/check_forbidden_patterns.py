#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Enforce forbidden code patterns via static analysis
# Callers: CI pipeline, pre-commit hooks
# Reference: PIN-264 (Phase-2.1 Self-Defending Transactions)

"""
Forbidden Patterns Checker

This script FAILS CI if forbidden patterns are detected outside approved modules.

FORBIDDEN PATTERNS
------------------

1. `with_for_update()` — Row locking
   Allowed ONLY in: app/infra/transaction.py
   Why: Prevents cross-connection deadlocks

2. `FOR UPDATE` in raw SQL
   Allowed ONLY in: app/infra/transaction.py
   Why: Same as above

3. `SELECT ... FOR UPDATE` in docstrings/comments
   Allowed EVERYWHERE (for documentation)

USAGE
-----
    python scripts/ci/check_forbidden_patterns.py [--fix] [--verbose]

EXIT CODES
----------
    0 = No violations
    1 = Violations found
    2 = Script error

PHILOSOPHY
----------
This is not a style check. This is an ARCHITECTURE ENFORCEMENT gate.

The patterns banned here are not "bad practice" — they are
STRUCTURALLY DANGEROUS and have caused production incidents.

If you need to use these patterns, you MUST use the blessed primitives
in app/infra/transaction.py. If those primitives don't support your
use case, extend them — don't bypass them.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Violation:
    """A detected forbidden pattern."""

    file: Path
    line_num: int
    pattern: str
    line_content: str
    reason: str
    fix_hint: str


# Files where patterns are ALLOWED (the blessed implementations)
ALLOWED_FILES = {
    "app/infra/transaction.py",  # The blessed transaction primitives
}

# Patterns that are forbidden outside allowed files
FORBIDDEN_PATTERNS = [
    {
        "name": "with_for_update",
        "pattern": r"\.with_for_update\s*\(",
        "reason": "Row locking must use single_connection_transaction()",
        "fix_hint": "Use: from app.infra import single_connection_transaction; with single_connection_transaction() as txn: row = txn.lock_row(...)",
        "in_comments_ok": True,  # Allow in docstrings for documentation
    },
    {
        "name": "FOR UPDATE raw SQL",
        "pattern": r'["\'].*\bFOR\s+UPDATE\b.*["\']',
        "reason": "Raw SQL row locking must use single_connection_transaction()",
        "fix_hint": "Use: txn.lock_row() instead of raw SQL FOR UPDATE",
        "in_comments_ok": True,
    },
]


def is_in_comment(line: str, match_start: int) -> bool:
    """Check if the match is inside a comment."""
    # Check for # comment before the match
    hash_pos = line.find("#")
    if hash_pos != -1 and hash_pos < match_start:
        return True
    return False


def is_docstring_line(line: str) -> bool:
    """Check if line appears to be in a docstring."""
    stripped = line.strip()
    # Lines starting with these are likely docstring content
    return (
        stripped.startswith('"""')
        or stripped.startswith("'''")
        or stripped.startswith(">")
        or stripped.startswith("-")
        or stripped.startswith("*")
    )


def check_file(file_path: Path, verbose: bool = False) -> list[Violation]:
    """Check a single file for forbidden patterns."""
    violations = []

    # Skip allowed files
    rel_path = str(file_path)
    for allowed in ALLOWED_FILES:
        if allowed in rel_path:
            if verbose:
                print(f"  [SKIP] {file_path} (allowed file)")
            return []

    # Skip non-Python files
    if file_path.suffix != ".py":
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Could not read {file_path}: {e}")
        return []

    lines = content.split("\n")
    in_docstring = False
    docstring_char: Optional[str] = None

    for line_num, line in enumerate(lines, 1):
        # Track docstring state
        stripped = line.strip()

        # Detect docstring start/end
        for doc_marker in ['"""', "'''"]:
            count = stripped.count(doc_marker)
            if count > 0:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = doc_marker
                    # Check if it closes on same line
                    if count >= 2 or (
                        count == 1
                        and stripped.startswith(doc_marker)
                        and stripped.endswith(doc_marker)
                        and len(stripped) > 3
                    ):
                        in_docstring = False
                        docstring_char = None
                elif docstring_char == doc_marker:
                    in_docstring = False
                    docstring_char = None

        # Check each forbidden pattern
        for pattern_def in FORBIDDEN_PATTERNS:
            regex = re.compile(pattern_def["pattern"], re.IGNORECASE)
            match = regex.search(line)

            if match:
                # Skip if in comment and comments are OK
                if pattern_def.get("in_comments_ok", False):
                    if is_in_comment(line, match.start()):
                        continue
                    if in_docstring:
                        continue

                violations.append(
                    Violation(
                        file=file_path,
                        line_num=line_num,
                        pattern=pattern_def["name"],
                        line_content=line.strip(),
                        reason=pattern_def["reason"],
                        fix_hint=pattern_def["fix_hint"],
                    )
                )

    return violations


def check_directory(root: Path, verbose: bool = False) -> list[Violation]:
    """Check all Python files in a directory."""
    all_violations = []

    # Find all Python files
    python_files = list(root.rglob("*.py"))

    # Skip test files, migrations, and vendor code
    skip_patterns = [
        "/tests/",
        "/alembic/",
        "/.venv/",
        "/venv/",
        "/site-packages/",
        "/__pycache__/",
    ]

    for file_path in python_files:
        path_str = str(file_path)

        # Skip excluded paths
        if any(skip in path_str for skip in skip_patterns):
            continue

        if verbose:
            print(f"Checking: {file_path}")

        violations = check_file(file_path, verbose)
        all_violations.extend(violations)

    return all_violations


def print_violation(v: Violation) -> None:
    """Print a single violation."""
    print(f"\n{'=' * 70}")
    print(f"FORBIDDEN PATTERN: {v.pattern}")
    print(f"{'=' * 70}")
    print(f"File: {v.file}:{v.line_num}")
    print(f"Line: {v.line_content}")
    print(f"\nReason: {v.reason}")
    print(f"\nFix: {v.fix_hint}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for forbidden code patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show files being checked",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Only check backend directory",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )

    args = parser.parse_args()

    # Determine root path
    root = Path(args.path)
    if args.backend_only:
        root = root / "backend" / "app"

    if not root.exists():
        print(f"ERROR: Path does not exist: {root}")
        return 2

    print(f"Checking for forbidden patterns in: {root}")
    print(f"Allowed files: {', '.join(ALLOWED_FILES)}")
    print()

    violations = check_directory(root, args.verbose)

    if violations:
        print(f"\n{'#' * 70}")
        print(f"# FORBIDDEN PATTERNS DETECTED: {len(violations)}")
        print(f"{'#' * 70}")

        for v in violations:
            print_violation(v)

        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total violations: {len(violations)}")
        print()
        print("These patterns are forbidden because they can cause:")
        print("- Cross-connection deadlocks")
        print("- Hanging tests")
        print("- Production incidents")
        print()
        print("Use the blessed primitives in app/infra/transaction.py instead.")
        print("See: PIN-264 (Phase-2.1 Self-Defending Transactions)")

        return 1

    print("✅ No forbidden patterns detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
