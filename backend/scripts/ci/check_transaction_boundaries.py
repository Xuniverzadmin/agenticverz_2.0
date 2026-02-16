#!/usr/bin/env python3
# Layer: L8 — CI Script
# AUDIENCE: INTERNAL
# Role: Architecture fitness — validates L4 owns commit/rollback, L5/L6 never commit
# artifact_class: CODE

"""
Transaction Boundary Checker (BA-21)

Scans all L5 engine files and L6 driver files to detect forbidden
transaction-boundary patterns.  Per PIN-520, L4 (hoc_spine orchestrator)
owns ALL transaction boundaries — L5 and L6 must NEVER commit, rollback,
or open transactions.

Forbidden patterns in L5/L6:
  - session.commit()  / await session.commit()
  - session.rollback()  / await session.rollback()
  - conn.commit()  / connection.commit()
  - conn.rollback()  / connection.rollback()
  - .begin()  (L5/L6 must not open transactions — that is L4's job)

Allowed:
  - session.flush()  (fine in L5/L6 — does not end a transaction)
  - Comments containing any of the above patterns (informational only)

Usage:
    PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
    PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py --strict

Exit codes:
    0 — no violations found
    1 — at least one forbidden transaction boundary pattern detected
"""

import argparse
import ast
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
CUS_ROOT = BACKEND_ROOT / "app" / "hoc" / "cus"

# ---------------------------------------------------------------------------
# Forbidden patterns
# ---------------------------------------------------------------------------
# Each entry is (compiled_regex, human_label).
# The regexes are designed to match the pattern anywhere on a line
# (after confirming the line is not a comment).

FORBIDDEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # session.commit() — sync and async
    (
        re.compile(r"\bsession\.commit\s*\("),
        "session.commit()",
    ),
    (
        re.compile(r"\bawait\s+session\.commit\s*\("),
        "await session.commit()",
    ),
    # session.rollback() — sync and async
    (
        re.compile(r"\bsession\.rollback\s*\("),
        "session.rollback()",
    ),
    (
        re.compile(r"\bawait\s+session\.rollback\s*\("),
        "await session.rollback()",
    ),
    # conn.commit() / connection.commit()
    (
        re.compile(r"\bconn(?:ection)?\.commit\s*\("),
        "conn/connection.commit()",
    ),
    # conn.rollback() / connection.rollback()
    (
        re.compile(r"\bconn(?:ection)?\.rollback\s*\("),
        "conn/connection.rollback()",
    ),
    # .begin() — L5/L6 must not open transactions
    (
        re.compile(r"\.begin\s*\("),
        ".begin()",
    ),
]


def _is_comment_line(line: str) -> bool:
    """Return True if the stripped line starts with #."""
    return line.lstrip().startswith("#")


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def _build_string_line_set(source: str) -> set[int]:
    """
    Use the AST to find all lines that are part of string literals
    (including docstrings).  Returns a set of 1-based line numbers that
    should be excluded from pattern matching.
    """
    string_lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return string_lines

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # node.lineno is the start line, node.end_lineno is the end line
            if node.end_lineno is not None:
                for ln in range(node.lineno, node.end_lineno + 1):
                    string_lines.add(ln)
        elif isinstance(node, ast.Expr) and isinstance(
            node.value, ast.Constant
        ):
            # Standalone string expression (docstring)
            val_node = node.value
            if isinstance(val_node.value, str) and val_node.end_lineno is not None:
                for ln in range(val_node.lineno, val_node.end_lineno + 1):
                    string_lines.add(ln)
    return string_lines


def scan_file(
    filepath: Path,
) -> list[tuple[int, str, str]]:
    """
    Scan a single file for forbidden patterns.

    Returns a list of (line_number, matched_text, pattern_label) tuples.
    """
    violations: list[tuple[int, str, str]] = []
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    lines = source.splitlines()

    # Build a set of line numbers that are inside string literals / docstrings
    # using the AST.  This is far more reliable than line-by-line tracking.
    string_lines = _build_string_line_set(source)

    for lineno, line in enumerate(lines, start=1):
        # Skip comment lines
        if _is_comment_line(line):
            continue

        # Skip lines that are part of a string literal or docstring
        if lineno in string_lines:
            continue

        # Check each forbidden pattern
        for pattern, label in FORBIDDEN_PATTERNS:
            m = pattern.search(line)
            if m:
                violations.append((lineno, line.strip(), label))

    return violations


def collect_files(layer_glob: str) -> list[Path]:
    """
    Collect all .py files matching a glob pattern under CUS_ROOT.
    Excludes __init__.py and __pycache__ directories.
    """
    files: list[Path] = []
    for p in sorted(CUS_ROOT.glob(layer_glob)):
        if p.is_file() and p.name != "__init__.py" and "__pycache__" not in str(p):
            files.append(p)
    return files


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check transaction boundaries — L5/L6 must never commit, "
            "rollback, or open transactions."
        )
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Strict mode: treat all violations as hard failures "
            "(default behaviour already fails on violations; strict "
            "additionally scans hoc_spine L5-like files if present)."
        ),
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Collect files
    # ------------------------------------------------------------------
    l5_files = collect_files("*/L5_engines/*.py")
    l6_files = collect_files("*/L6_drivers/*.py")

    # In strict mode, also scan any L5/L6 files nested deeper
    if args.strict:
        l5_files.extend(collect_files("*/L5_engines/**/*.py"))
        l6_files.extend(collect_files("*/L6_drivers/**/*.py"))
        # Deduplicate
        l5_files = sorted(set(l5_files))
        l6_files = sorted(set(l6_files))

    all_files = l5_files + l6_files

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------
    total_files = len(all_files)
    passed_files = 0
    total_violations = 0
    violation_details: list[tuple[Path, int, str, str]] = []

    for filepath in all_files:
        violations = scan_file(filepath)
        if violations:
            total_violations += len(violations)
            for lineno, matched_text, label in violations:
                violation_details.append((filepath, lineno, matched_text, label))
        else:
            passed_files += 1

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    # Report passed files
    for filepath in all_files:
        file_violations = [
            (ln, txt, lbl)
            for fp, ln, txt, lbl in violation_details
            if fp == filepath
        ]
        rel = filepath.relative_to(BACKEND_ROOT)
        if not file_violations:
            layer = "L5" if "L5_engines" in str(filepath) else "L6"
            print(f"[PASS] {rel} -- no transaction boundary violations ({layer})")

    # Report violations
    for filepath, lineno, matched_text, label in violation_details:
        rel = filepath.relative_to(BACKEND_ROOT)
        print(f"[FAIL] {rel}:{lineno} -- forbidden pattern: {label}")
        print(f"       {matched_text}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    failed_files = total_files - passed_files

    print()
    print("=" * 60)
    print("Transaction Boundary Summary")
    print("=" * 60)
    print(f"  Total files scanned    : {total_files}")
    print(f"  L5 engine files        : {len(l5_files)}")
    print(f"  L6 driver files        : {len(l6_files)}")
    print(f"  Files passed           : {passed_files}")
    print(f"  Files with violations  : {failed_files}")
    print(f"  Total violations       : {total_violations}")
    if args.strict:
        print(f"  Mode                   : STRICT")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Exit code
    # ------------------------------------------------------------------
    if total_violations > 0:
        print("\nRESULT: FAIL")
        return 1
    else:
        print("\nRESULT: PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
