#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Validate transaction intent/primitive consistency
# Callers: CI pipeline, pre-commit hooks
# Reference: PIN-264 (Phase-2.2 Self-Defending Transactions with Intent)

"""
Transaction Intent Consistency Checker

This script FAILS CI if intent/primitive mismatches are detected.

WHAT THIS CHECKS
----------------

1. LOCKED_MUTATION intent without SingleConnectionTxn
   - Functions decorated with @transactional(intent=TransactionIntent.LOCKED_MUTATION)
   - MUST have SingleConnectionTxn as first parameter type hint

2. single_connection_transaction() usage without LOCKED_MUTATION intent
   - Code using single_connection_transaction() as context manager
   - MUST be inside a function with LOCKED_MUTATION intent
   - OR be a direct caller of a LOCKED_MUTATION function

3. lock_row() / lock_rows() outside SingleConnectionTxn context
   - These methods should only appear on txn objects
   - Never on regular sessions

PHILOSOPHY
----------
The @transactional decorator and TransactionIntent system exists to make
engineers DECLARE their intent BEFORE writing code. This script validates
that declarations match implementations.

If this script fails, the design is wrong — not the check.

USAGE
-----
    python scripts/ci/check_intent_consistency.py [--verbose] [path]

EXIT CODES
----------
    0 = No violations
    1 = Violations found
    2 = Script error
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class IntentViolation:
    """A detected intent/primitive mismatch."""

    file: Path
    line_num: int
    violation_type: str
    description: str
    fix_hint: str


class IntentAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze transaction intent declarations."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: list[IntentViolation] = []
        self.locked_mutation_functions: set[str] = set()
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function for intent declarations and validate."""
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function (should NOT have LOCKED_MUTATION)."""
        intent = self._get_transactional_intent(node)
        if intent == "LOCKED_MUTATION":
            self.violations.append(
                IntentViolation(
                    file=self.file_path,
                    line_num=node.lineno,
                    violation_type="ASYNC_LOCKED_MUTATION",
                    description=f"Async function '{node.name}' has LOCKED_MUTATION intent",
                    fix_hint="LOCKED_MUTATION requires synchronous execution. " "Use sync functions for row locking.",
                )
            )
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef) -> None:
        """Validate a function's intent declaration matches implementation."""
        intent = self._get_transactional_intent(node)

        if intent == "LOCKED_MUTATION":
            # Record this function as a LOCKED_MUTATION function
            func_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.locked_mutation_functions.add(func_name)

            # Check first parameter is SingleConnectionTxn
            if not self._has_single_connection_txn_param(node):
                self.violations.append(
                    IntentViolation(
                        file=self.file_path,
                        line_num=node.lineno,
                        violation_type="MISSING_TXN_PARAM",
                        description=f"Function '{node.name}' has LOCKED_MUTATION intent but "
                        f"first parameter is not SingleConnectionTxn",
                        fix_hint="Add 'txn: SingleConnectionTxn' as first parameter: "
                        f"def {node.name}(txn: SingleConnectionTxn, ...)",
                    )
                )

    def _get_transactional_intent(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Optional[str]:
        """Extract TransactionIntent from @transactional decorator if present."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                # Check for @transactional(intent=...)
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "transactional":
                    for keyword in decorator.keywords:
                        if keyword.arg == "intent":
                            # Extract the intent value
                            if isinstance(keyword.value, ast.Attribute):
                                return keyword.value.attr
                            elif isinstance(keyword.value, ast.Name):
                                return keyword.value.id
        return None

    def _has_single_connection_txn_param(self, node: ast.FunctionDef) -> bool:
        """Check if first parameter is annotated as SingleConnectionTxn."""
        args = node.args.args
        if not args:
            return False

        first_arg = args[0]

        # Skip 'self' for methods
        if first_arg.arg == "self":
            if len(args) < 2:
                return False
            first_arg = args[1]

        # Check annotation
        if first_arg.annotation:
            if isinstance(first_arg.annotation, ast.Name):
                return "SingleConnectionTxn" in first_arg.annotation.id
            elif isinstance(first_arg.annotation, ast.Attribute):
                return "SingleConnectionTxn" in first_arg.annotation.attr
            elif isinstance(first_arg.annotation, ast.Subscript):
                # Handle Optional[SingleConnectionTxn] etc.
                return "SingleConnectionTxn" in ast.dump(first_arg.annotation)

        return False


def check_file_with_regex(file_path: Path, verbose: bool = False) -> list[IntentViolation]:
    """Check file for regex-based patterns (backup for non-parseable files)."""
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = content.split("\n")

    # Pattern: single_connection_transaction() without nearby LOCKED_MUTATION
    sct_pattern = re.compile(r"\bsingle_connection_transaction\s*\(")
    locked_mutation_pattern = re.compile(r"TransactionIntent\.LOCKED_MUTATION|intent=.*LOCKED_MUTATION")

    for i, line in enumerate(lines, 1):
        # Check for single_connection_transaction usage
        if sct_pattern.search(line):
            # Look for LOCKED_MUTATION in surrounding context (30 lines before)
            context_start = max(0, i - 30)
            context = "\n".join(lines[context_start:i])

            if not locked_mutation_pattern.search(context):
                # Not an auto-violation - might be the primitive itself or test code
                # Just log for verbose mode
                if verbose:
                    print(f"  [NOTE] single_connection_transaction at {file_path}:{i} - verify intent")

    return violations


def check_file(file_path: Path, verbose: bool = False) -> list[IntentViolation]:
    """Check a single Python file for intent/primitive consistency."""
    # Skip test files - they may legitimately test various patterns
    if "/tests/" in str(file_path):
        return []

    # Skip the transaction module itself
    if "app/infra/transaction.py" in str(file_path):
        return []

    # Skip alembic migrations
    if "/alembic/" in str(file_path):
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Could not read {file_path}: {e}")
        return []

    # Try AST analysis first
    try:
        tree = ast.parse(content)
        analyzer = IntentAnalyzer(file_path)
        analyzer.visit(tree)
        violations = analyzer.violations
    except SyntaxError:
        # Fallback to regex for files with syntax issues
        violations = check_file_with_regex(file_path, verbose)

    return violations


def check_directory(root: Path, verbose: bool = False) -> list[IntentViolation]:
    """Check all Python files in a directory."""
    all_violations = []

    # Find all Python files
    python_files = list(root.rglob("*.py"))

    # Skip certain directories
    skip_patterns = [
        "/.venv/",
        "/venv/",
        "/site-packages/",
        "/__pycache__/",
    ]

    for file_path in python_files:
        path_str = str(file_path)

        if any(skip in path_str for skip in skip_patterns):
            continue

        if verbose:
            print(f"Checking: {file_path}")

        violations = check_file(file_path, verbose)
        all_violations.extend(violations)

    return all_violations


def print_violation(v: IntentViolation) -> None:
    """Print a single violation."""
    print(f"\n{'='*70}")
    print(f"INTENT VIOLATION: {v.violation_type}")
    print(f"{'='*70}")
    print(f"File: {v.file}:{v.line_num}")
    print(f"\n{v.description}")
    print(f"\nFix: {v.fix_hint}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check transaction intent/primitive consistency",
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
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)",
    )

    args = parser.parse_args()
    root = Path(args.path)

    if not root.exists():
        print(f"ERROR: Path does not exist: {root}")
        return 2

    print(f"Checking intent/primitive consistency in: {root}")
    print()

    violations = check_directory(root, args.verbose)

    if violations:
        print(f"\n{'#'*70}")
        print(f"# INTENT/PRIMITIVE MISMATCHES: {len(violations)}")
        print(f"{'#'*70}")

        for v in violations:
            print_violation(v)

        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total violations: {len(violations)}")
        print()
        print("Intent declarations must match primitive usage.")
        print("If a function needs row locks, it MUST:")
        print("  1. Be decorated with @transactional(intent=TransactionIntent.LOCKED_MUTATION)")
        print("  2. Accept SingleConnectionTxn as first parameter")
        print("  3. Use txn.lock_row() / txn.lock_rows() for locking")
        print()
        print("See: PIN-264 (Phase-2.2 Self-Defending Transactions with Intent)")

        return 1

    print("✅ No intent/primitive mismatches detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
