#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Enforce feature-level intent declarations via static analysis
# Callers: CI pipeline, pre-commit hooks
# Reference: PIN-264 (Phase-2.3 Feature Intent System)

"""
Feature Intent Checker

This script FAILS CI if modules touch persistence without intent declarations.

WHAT THIS CHECKS
----------------

1. FEATURE_INTENT Required
   - Modules importing persistence (Session, engine, select) must declare FEATURE_INTENT
   - Modules with @transactional decorators must declare FEATURE_INTENT

2. Intent Consistency
   - TransactionIntent must be allowed for the declared FeatureIntent
   - See INTENT_CONSISTENCY_MATRIX in feature_intent.py

3. Retry Policy Required
   - EXTERNAL_SIDE_EFFECT requires RetryPolicy.NEVER
   - RECOVERABLE_OPERATION requires RetryPolicy.SAFE

4. Dangerous Combinations Blocked
   - EXTERNAL_SIDE_EFFECT + SAFE = forbidden
   - LOCKED_MUTATION in non-RECOVERABLE feature = warning

PHILOSOPHY
----------
This enforces FEATURE-LEVEL thinking, not just function-level.

A feature is rarely one function. This ensures the entire module
has consistent intent before any function is written.

USAGE
-----
    python scripts/ci/check_feature_intent.py [--verbose] [path]

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
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# DB-AUTH-001: Declare local-only authority
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts._db_guard import assert_db_authority  # noqa: E402
assert_db_authority("local")

# Patterns that indicate persistence usage
PERSISTENCE_PATTERNS = [
    r"from\s+app\.db\s+import",
    r"from\s+sqlmodel\s+import\s+.*Session",
    r"from\s+sqlmodel\s+import\s+.*select",
    r"from\s+sqlalchemy\s+import",
    r"@transactional\s*\(",
    r"\.commit\s*\(",
    r"\.add\s*\(",
    r"\.exec\s*\(",
    r"session\.execute",
]

# Modules that are allowed to skip feature intent (infrastructure)
EXEMPT_MODULES = [
    "app/infra/",
    "app/db.py",
    "app/db_async.py",
    "app/db_helpers.py",
    "tests/",
    "alembic/",
]


@dataclass
class FeatureIntentViolation:
    """A detected feature intent violation."""

    file: Path
    line_num: int
    violation_type: str
    description: str
    fix_hint: str


@dataclass
class ModuleAnalysis:
    """Analysis results for a single module."""

    file_path: Path
    has_persistence: bool = False
    has_feature_intent: bool = False
    has_retry_policy: bool = False
    feature_intent_value: Optional[str] = None
    retry_policy_value: Optional[str] = None
    transaction_intents: List[str] = field(default_factory=list)
    persistence_indicators: List[str] = field(default_factory=list)


class FeatureIntentAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze feature intent declarations."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.feature_intent: Optional[str] = None
        self.retry_policy: Optional[str] = None
        self.transaction_intents: List[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check for FEATURE_INTENT and RETRY_POLICY assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id == "FEATURE_INTENT":
                    self.feature_intent = self._extract_enum_value(node.value)
                elif target.id == "RETRY_POLICY":
                    self.retry_policy = self._extract_enum_value(node.value)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check for @transactional decorators."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "transactional":
                    for keyword in decorator.keywords:
                        if keyword.arg == "intent":
                            intent = self._extract_enum_value(keyword.value)
                            if intent:
                                self.transaction_intents.append(intent)
        self.generic_visit(node)

    def _extract_enum_value(self, node: ast.expr) -> Optional[str]:
        """Extract enum value from AST node."""
        if isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Name):
            return node.id
        return None


def check_module(file_path: Path, verbose: bool = False) -> ModuleAnalysis:
    """Analyze a single module for feature intent."""
    analysis = ModuleAnalysis(file_path=file_path)

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Could not read {file_path}: {e}")
        return analysis

    # Check for persistence patterns
    for pattern in PERSISTENCE_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            analysis.has_persistence = True
            analysis.persistence_indicators.extend(matches)

    if not analysis.has_persistence:
        return analysis

    # Parse AST for intent declarations
    try:
        tree = ast.parse(content)
        analyzer = FeatureIntentAnalyzer(file_path)
        analyzer.visit(tree)

        analysis.feature_intent_value = analyzer.feature_intent
        analysis.retry_policy_value = analyzer.retry_policy
        analysis.transaction_intents = analyzer.transaction_intents
        analysis.has_feature_intent = analyzer.feature_intent is not None
        analysis.has_retry_policy = analyzer.retry_policy is not None

    except SyntaxError:
        if verbose:
            print(f"  [WARNING] Syntax error in {file_path}, skipping AST analysis")

    return analysis


def validate_intent_consistency(
    feature_intent: str,
    transaction_intents: List[str],
) -> List[str]:
    """Validate that transaction intents are consistent with feature intent."""
    # Intent consistency matrix
    allowed = {
        "PURE_QUERY": {"READ_ONLY"},
        "STATE_MUTATION": {"ATOMIC_WRITE", "LOCKED_MUTATION"},
        "EXTERNAL_SIDE_EFFECT": {"ATOMIC_WRITE"},
        "RECOVERABLE_OPERATION": {"LOCKED_MUTATION"},
    }

    violations = []
    allowed_intents = allowed.get(feature_intent, set())

    for txn_intent in transaction_intents:
        if txn_intent not in allowed_intents:
            violations.append(
                f"TransactionIntent.{txn_intent} not allowed for "
                f"FeatureIntent.{feature_intent}. Allowed: {sorted(allowed_intents)}"
            )

    return violations


def validate_retry_policy(
    feature_intent: str,
    retry_policy: Optional[str],
) -> List[str]:
    """Validate retry policy is consistent with feature intent."""
    violations = []

    # Required policies
    required = {
        "EXTERNAL_SIDE_EFFECT": "NEVER",
        "RECOVERABLE_OPERATION": "SAFE",
    }

    # Forbidden combinations
    forbidden = {
        ("EXTERNAL_SIDE_EFFECT", "SAFE"),
    }

    if feature_intent in required:
        if retry_policy != required[feature_intent]:
            violations.append(
                f"FeatureIntent.{feature_intent} requires RETRY_POLICY = RetryPolicy.{required[feature_intent]}"
            )

    if (feature_intent, retry_policy) in forbidden:
        violations.append(f"RetryPolicy.{retry_policy} is forbidden for FeatureIntent.{feature_intent}")

    return violations


def check_file(file_path: Path, verbose: bool = False) -> List[FeatureIntentViolation]:
    """Check a single file for feature intent violations."""
    violations = []

    # Skip exempt modules
    path_str = str(file_path)
    for exempt in EXEMPT_MODULES:
        if exempt in path_str:
            if verbose:
                print(f"  [SKIP] {file_path} (exempt module)")
            return []

    analysis = check_module(file_path, verbose)

    if not analysis.has_persistence:
        return []

    # Violation 1: Missing FEATURE_INTENT
    if not analysis.has_feature_intent:
        violations.append(
            FeatureIntentViolation(
                file=file_path,
                line_num=1,
                violation_type="MISSING_FEATURE_INTENT",
                description=(
                    f"Module uses persistence ({', '.join(analysis.persistence_indicators[:3])}) "
                    f"but has no FEATURE_INTENT declaration"
                ),
                fix_hint=(
                    "Add at module level:\n"
                    "  from app.infra import FeatureIntent\n"
                    "  FEATURE_INTENT = FeatureIntent.STATE_MUTATION  # or appropriate intent"
                ),
            )
        )
        return violations  # Can't validate consistency without intent

    # Violation 2: Intent consistency
    if analysis.transaction_intents:
        consistency_violations = validate_intent_consistency(
            analysis.feature_intent_value,
            analysis.transaction_intents,
        )
        for desc in consistency_violations:
            violations.append(
                FeatureIntentViolation(
                    file=file_path,
                    line_num=1,
                    violation_type="INTENT_CONSISTENCY",
                    description=desc,
                    fix_hint=(
                        "Either change the FEATURE_INTENT or the @transactional intent "
                        "to a valid combination. See INTENT_CONSISTENCY_MATRIX."
                    ),
                )
            )

    # Violation 3: Retry policy
    if analysis.feature_intent_value in ("EXTERNAL_SIDE_EFFECT", "RECOVERABLE_OPERATION"):
        if not analysis.has_retry_policy:
            violations.append(
                FeatureIntentViolation(
                    file=file_path,
                    line_num=1,
                    violation_type="MISSING_RETRY_POLICY",
                    description=(f"FeatureIntent.{analysis.feature_intent_value} requires RETRY_POLICY declaration"),
                    fix_hint=(
                        "Add at module level:\n"
                        "  from app.infra import RetryPolicy\n"
                        "  RETRY_POLICY = RetryPolicy.NEVER  # or SAFE for RECOVERABLE"
                    ),
                )
            )
        else:
            policy_violations = validate_retry_policy(
                analysis.feature_intent_value,
                analysis.retry_policy_value,
            )
            for desc in policy_violations:
                violations.append(
                    FeatureIntentViolation(
                        file=file_path,
                        line_num=1,
                        violation_type="RETRY_POLICY_VIOLATION",
                        description=desc,
                        fix_hint="Update RETRY_POLICY to the required value.",
                    )
                )

    return violations


def check_directory(root: Path, verbose: bool = False) -> List[FeatureIntentViolation]:
    """Check all Python files in a directory."""
    all_violations = []

    python_files = list(root.rglob("*.py"))

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


def print_violation(v: FeatureIntentViolation) -> None:
    """Print a single violation."""
    print(f"\n{'=' * 70}")
    print(f"FEATURE INTENT VIOLATION: {v.violation_type}")
    print(f"{'=' * 70}")
    print(f"File: {v.file}:{v.line_num}")
    print(f"\n{v.description}")
    print(f"\nFix:\n{v.fix_hint}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check feature-level intent declarations",
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
        "--warn-only",
        action="store_true",
        help="Exit 0 even if violations found (warning mode)",
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

    print(f"Checking feature intent declarations in: {root}")
    print()

    violations = check_directory(root, args.verbose)

    if violations:
        print(f"\n{'#' * 70}")
        print(f"# FEATURE INTENT VIOLATIONS: {len(violations)}")
        print(f"{'#' * 70}")

        for v in violations:
            print_violation(v)

        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total violations: {len(violations)}")
        print()
        print("Feature intent declarations ensure:")
        print("  - Design thinking before coding")
        print("  - Consistent intent across function boundaries")
        print("  - Explicit retry safety declarations")
        print()
        print("See: PIN-264 (Phase-2.3 Feature Intent System)")

        return 0 if args.warn_only else 1

    print("✅ No feature intent violations detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
