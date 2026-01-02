#!/usr/bin/env python3
"""
Intent Violation Checker (PIN-265 Enforcement)

Enforces FEATURE_INTENT declarations by scanning files for violations:

- PURE_QUERY files must NOT contain:
  - session.commit(), session.flush()
  - INSERT/UPDATE/DELETE statements
  - external API calls (httpx, requests)

- STATE_MUTATION files must have RETRY_POLICY

- EXTERNAL_SIDE_EFFECT files must have RETRY_POLICY

Usage:
    python scripts/ops/check_intent_violations.py
    python scripts/ops/check_intent_violations.py --ci  # Exit 1 on violations
    python scripts/ops/check_intent_violations.py --path backend/app/services/

Exit codes:
    0 - No violations found
    1 - Violations found (CI mode) or missing intents found
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# =============================================================================
# VIOLATION PATTERNS
# =============================================================================

# Patterns that indicate state mutation in code
MUTATION_PATTERNS = [
    re.compile(r"session\.commit\s*\("),
    re.compile(r"session\.flush\s*\("),
    re.compile(r"session\.add\s*\("),
    re.compile(r"session\.delete\s*\("),
    re.compile(r"session\.execute\s*\(.*\b(INSERT|UPDATE|DELETE)\b", re.IGNORECASE),
    re.compile(r"\.execute\s*\(.*\b(INSERT|UPDATE|DELETE)\b", re.IGNORECASE),
    re.compile(r"\bINSERT\s+INTO\b", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+\w+\s+SET\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
]

# Patterns that indicate external side effects
EXTERNAL_PATTERNS = [
    re.compile(r"httpx\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"requests\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"\.send\s*\("),  # Email sending
    re.compile(r"redis_client\.(set|delete|lpush|rpush)\s*\("),
]

# Intent enum values
INTENT_PURE_QUERY = "FeatureIntent.PURE_QUERY"
INTENT_STATE_MUTATION = "FeatureIntent.STATE_MUTATION"
INTENT_EXTERNAL_SIDE_EFFECT = "FeatureIntent.EXTERNAL_SIDE_EFFECT"
INTENT_RECOVERABLE = "FeatureIntent.RECOVERABLE_OPERATION"


@dataclass
class IntentViolation:
    """A detected intent violation."""

    file_path: str
    line_number: int
    declared_intent: str
    violation_type: str
    code_snippet: str
    message: str


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""

    file_path: str
    has_intent: bool
    declared_intent: Optional[str] = None
    has_retry_policy: bool = False
    violations: List[IntentViolation] = field(default_factory=list)


def extract_intent_from_file(file_path: Path) -> Tuple[Optional[str], bool]:
    """
    Extract FEATURE_INTENT and RETRY_POLICY from a file.

    Returns:
        Tuple of (intent_value, has_retry_policy)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None, False

    intent = None
    has_retry = False

    # Look for FEATURE_INTENT = FeatureIntent.XXX
    intent_match = re.search(r"FEATURE_INTENT\s*=\s*(FeatureIntent\.\w+)", content)
    if intent_match:
        intent = intent_match.group(1)

    # Look for RETRY_POLICY = RetryPolicy.XXX
    retry_match = re.search(r"RETRY_POLICY\s*=\s*RetryPolicy\.\w+", content)
    if retry_match:
        has_retry = True

    return intent, has_retry


def check_pure_query_violations(file_path: Path, content: str) -> List[IntentViolation]:
    """
    Check if a PURE_QUERY file contains mutation or external patterns.
    """
    violations = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Check mutation patterns
        for pattern in MUTATION_PATTERNS:
            if pattern.search(line):
                violations.append(
                    IntentViolation(
                        file_path=str(file_path),
                        line_number=i,
                        declared_intent=INTENT_PURE_QUERY,
                        violation_type="MUTATION_IN_PURE_QUERY",
                        code_snippet=line.strip()[:80],
                        message="State mutation detected in PURE_QUERY file",
                    )
                )
                break

        # Check external patterns
        for pattern in EXTERNAL_PATTERNS:
            if pattern.search(line):
                violations.append(
                    IntentViolation(
                        file_path=str(file_path),
                        line_number=i,
                        declared_intent=INTENT_PURE_QUERY,
                        violation_type="EXTERNAL_CALL_IN_PURE_QUERY",
                        code_snippet=line.strip()[:80],
                        message="External side effect detected in PURE_QUERY file",
                    )
                )
                break

    return violations


def check_missing_retry_policy(
    file_path: Path, intent: str, has_retry: bool
) -> Optional[IntentViolation]:
    """
    Check if STATE_MUTATION or EXTERNAL_SIDE_EFFECT files have RETRY_POLICY.
    """
    needs_retry = intent in [INTENT_STATE_MUTATION, INTENT_EXTERNAL_SIDE_EFFECT]

    if needs_retry and not has_retry:
        return IntentViolation(
            file_path=str(file_path),
            line_number=0,
            declared_intent=intent,
            violation_type="MISSING_RETRY_POLICY",
            code_snippet="",
            message=f"File declares {intent} but missing RETRY_POLICY declaration",
        )

    return None


def analyze_file(file_path: Path) -> FileAnalysis:
    """
    Analyze a single file for intent violations.
    """
    analysis = FileAnalysis(file_path=str(file_path), has_intent=False)

    # Skip __init__.py and test files
    if file_path.name == "__init__.py":
        return analysis
    if "test_" in file_path.name or file_path.name.startswith("test"):
        return analysis

    intent, has_retry = extract_intent_from_file(file_path)

    if intent is None:
        return analysis

    analysis.has_intent = True
    analysis.declared_intent = intent
    analysis.has_retry_policy = has_retry

    # Read file content for violation checks
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return analysis

    # Check violations based on intent
    if intent == INTENT_PURE_QUERY:
        analysis.violations.extend(check_pure_query_violations(file_path, content))

    # Check for missing RETRY_POLICY
    retry_violation = check_missing_retry_policy(file_path, intent, has_retry)
    if retry_violation:
        analysis.violations.append(retry_violation)

    return analysis


def scan_directory(path: Path) -> List[FileAnalysis]:
    """
    Scan a directory recursively for Python files.
    """
    results = []

    for py_file in path.rglob("*.py"):
        # Skip test directories
        if "/tests/" in str(py_file):
            continue
        if "/__pycache__/" in str(py_file):
            continue

        analysis = analyze_file(py_file)
        if analysis.has_intent or analysis.violations:
            results.append(analysis)

    return results


def print_report(analyses: List[FileAnalysis], show_all: bool = False):
    """
    Print the analysis report.
    """
    violations = []
    files_with_intent = 0
    _files_missing_intent = []

    for analysis in analyses:
        if analysis.has_intent:
            files_with_intent += 1
            violations.extend(analysis.violations)

    # Summary
    print("\n" + "=" * 70)
    print("INTENT VIOLATION CHECK REPORT")
    print("=" * 70)
    print(f"\nFiles with FEATURE_INTENT: {files_with_intent}")
    print(f"Total violations found: {len(violations)}")

    if violations:
        print("\n" + "-" * 70)
        print("VIOLATIONS")
        print("-" * 70)

        # Group by violation type
        by_type: Dict[str, List[IntentViolation]] = {}
        for v in violations:
            if v.violation_type not in by_type:
                by_type[v.violation_type] = []
            by_type[v.violation_type].append(v)

        for vtype, vlist in sorted(by_type.items()):
            print(f"\n[{vtype}] ({len(vlist)} occurrences)")
            for v in vlist[:10]:  # Show first 10
                print(f"  {v.file_path}:{v.line_number}")
                print(f"    Declared: {v.declared_intent}")
                print(f"    Message: {v.message}")
                if v.code_snippet:
                    print(f"    Code: {v.code_snippet}")
            if len(vlist) > 10:
                print(f"  ... and {len(vlist) - 10} more")

    # Intent coverage by directory
    if show_all:
        print("\n" + "-" * 70)
        print("INTENT COVERAGE BY DIRECTORY")
        print("-" * 70)

        by_dir: Dict[str, List[str]] = {}
        for analysis in analyses:
            if analysis.has_intent:
                dir_name = str(Path(analysis.file_path).parent)
                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(analysis.declared_intent)

        for dir_name, intents in sorted(by_dir.items()):
            from collections import Counter

            counts = Counter(intents)
            print(f"\n{dir_name}:")
            for intent, count in counts.most_common():
                short_intent = intent.replace("FeatureIntent.", "")
                print(f"  {short_intent}: {count}")

    print("\n" + "=" * 70)

    return len(violations)


def main():
    parser = argparse.ArgumentParser(description="Check for FEATURE_INTENT violations")
    parser.add_argument(
        "--ci", action="store_true", help="CI mode - exit 1 on violations"
    )
    parser.add_argument("--path", type=str, default="backend/app", help="Path to scan")
    parser.add_argument(
        "--all", action="store_true", help="Show all details including coverage"
    )
    args = parser.parse_args()

    # Resolve path
    base_path = Path(__file__).parent.parent.parent
    scan_path = base_path / args.path

    if not scan_path.exists():
        print(f"Error: Path not found: {scan_path}")
        sys.exit(1)

    print(f"Scanning: {scan_path}")

    analyses = scan_directory(scan_path)
    violation_count = print_report(analyses, show_all=args.all)

    if args.ci and violation_count > 0:
        print(f"\n❌ CI FAILURE: {violation_count} intent violation(s) found")
        sys.exit(1)
    elif violation_count > 0:
        print(f"\n⚠️  WARNING: {violation_count} intent violation(s) found")
    else:
        print("\n✅ No intent violations detected")


if __name__ == "__main__":
    main()
