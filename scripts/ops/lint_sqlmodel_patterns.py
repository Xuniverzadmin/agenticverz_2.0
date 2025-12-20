#!/usr/bin/env python3
"""SQLModel Pattern Linter - Detect Unsafe Query Patterns

Detects patterns that can cause Row tuple extraction issues:
1. result.first() without [0] extraction
2. result.all() without list comprehension extraction
3. session.exec().one() used for counts without [0]

Usage:
    python scripts/ops/lint_sqlmodel_patterns.py [path]
    python scripts/ops/lint_sqlmodel_patterns.py backend/app/api/

Exit codes:
    0 - No issues found
    1 - Issues found
"""

import re
import sys
from pathlib import Path
from typing import List, NamedTuple


class LintIssue(NamedTuple):
    file: str
    line: int
    pattern: str
    message: str
    suggestion: str


# Unsafe patterns to detect
UNSAFE_PATTERNS = [
    # Pattern: result = session.exec(stmt); obj = result.first()
    # This is unsafe because .first() returns Row tuple
    {
        "regex": r"result\s*=\s*session\.exec\([^)]+\)\s*\n\s*\w+\s*=\s*result\.first\(\)",
        "message": "Unsafe: result.first() returns Row tuple, not model instance",
        "suggestion": "Use: row = session.exec(stmt).first(); obj = row[0] if row else None",
    },
    # Pattern: session.exec(stmt).first() assigned directly without [0]
    {
        "regex": r"(\w+)\s*=\s*session\.exec\([^)]+\)\.first\(\)\s*$",
        "message": "Potential issue: .first() returns Row tuple",
        "suggestion": "Use: row = session.exec(stmt).first(); obj = row[0] if row else None",
        "exclude_if_followed_by": r"\[\s*0\s*\]",  # OK if followed by [0]
    },
    # Pattern: for x in session.exec(stmt).all() without extraction
    {
        "regex": r"for\s+\w+\s+in\s+session\.exec\([^)]+\)\.all\(\)",
        "message": "Unsafe: iterating .all() yields Row tuples, not model instances",
        "suggestion": "Use: for item in [r[0] for r in session.exec(stmt).all()]",
    },
    # Pattern: .one() without [0] for scalar queries
    {
        "regex": r"session\.exec\([^)]*func\.(count|sum|avg|max|min)[^)]*\)\.one\(\)\s*$",
        "message": "Unsafe: .one() on aggregate returns Row tuple",
        "suggestion": "Use: result = session.exec(query).one(); value = result[0]",
    },
    # Pattern: accessing .attribute on result.first() directly
    {
        "regex": r"session\.exec\([^)]+\)\.first\(\)\.\w+",
        "message": "Unsafe: accessing attribute on .first() result (Row tuple)",
        "suggestion": "Extract model first: row = session.exec(stmt).first(); obj = row[0] if row else None",
    },
    # Pattern: session.exec(text(...), params) - exec() doesn't accept params dict
    # Discovered during M24 Ops Console implementation (PIN-105)
    {
        "regex": r"session\.exec\s*\(\s*text\s*\([^)]+\)\s*,\s*\{",
        "message": "Unsafe: session.exec() does not accept params dict. Only takes 1 argument.",
        "suggestion": "Use session.execute(text(...), params) for raw SQL with parameters",
    },
]

# Safe patterns to allow (false positive prevention)
SAFE_PATTERNS = [
    r"row\s*=\s*session\.exec\([^)]+\)\.first\(\)",  # Using 'row' variable name
    r"result\s*=\s*session\.exec\([^)]+\)\.first\(\)",  # Using 'result' variable name
    r"row\[0\]",  # Extracting from row
    r"result\[0\]",  # Extracting from result
    r"r\[0\]\s+for\s+r\s+in",  # List comprehension extraction
    r"from app\.db_helpers import",  # Using safe helpers
    r"query_one\(|query_all\(|query_scalar\(",  # Using helper functions
    r"session\.execute\s*\(\s*text\s*\(",  # Correct: session.execute() for raw SQL with params
    r"exec_sql\(",  # Helper function for raw SQL execution
    r"hasattr\(result,",  # Safe model-or-tuple extraction pattern
    r"hasattr\(r,",  # Safe model-or-tuple extraction in loop
]


def is_safe_context(content: str, match_start: int, match_end: int) -> bool:
    """Check if the match is in a safe context."""
    # Get surrounding context (5 lines before and after)
    lines = content[:match_end].split("\n")
    current_line = len(lines)

    context_start = max(0, match_start - 500)
    context_end = min(len(content), match_end + 500)
    context = content[context_start:context_end]

    for safe in SAFE_PATTERNS:
        if re.search(safe, context):
            return True
    return False


def lint_file(filepath: Path) -> List[LintIssue]:
    """Lint a single Python file for unsafe SQLModel patterns."""
    issues = []

    try:
        content = filepath.read_text()
    except Exception:
        return []

    lines = content.split("\n")

    for pattern_def in UNSAFE_PATTERNS:
        regex = pattern_def["regex"]
        for match in re.finditer(regex, content, re.MULTILINE):
            # Calculate line number
            line_num = content[: match.start()].count("\n") + 1

            # Check for exclusions
            if "exclude_if_followed_by" in pattern_def:
                next_chars = content[match.end() : match.end() + 20]
                if re.match(pattern_def["exclude_if_followed_by"], next_chars):
                    continue

            # Check if in safe context
            if is_safe_context(content, match.start(), match.end()):
                continue

            issues.append(
                LintIssue(
                    file=str(filepath),
                    line=line_num,
                    pattern=match.group()[:80] + "..."
                    if len(match.group()) > 80
                    else match.group(),
                    message=pattern_def["message"],
                    suggestion=pattern_def["suggestion"],
                )
            )

    return issues


def lint_directory(path: Path) -> List[LintIssue]:
    """Lint all Python files in a directory."""
    issues = []

    for filepath in path.rglob("*.py"):
        # Skip test files, migrations, and __pycache__
        if any(
            skip in str(filepath)
            for skip in ["__pycache__", ".venv", "alembic/versions"]
        ):
            continue

        file_issues = lint_file(filepath)
        issues.extend(file_issues)

    return issues


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backend/app")

    print("=" * 70)
    print("SQLModel Pattern Linter - Detecting Unsafe Query Patterns")
    print("=" * 70)
    print()

    if path.is_file():
        issues = lint_file(path)
    else:
        issues = lint_directory(path)

    if not issues:
        print("✅ No unsafe SQLModel patterns detected!")
        print()
        print("Safe patterns in use:")
        print("  - row = session.exec(stmt).first(); obj = row[0] if row else None")
        print("  - objs = [r[0] for r in session.exec(stmt).all()]")
        print("  - from app.db_helpers import query_one, query_all")
        print("  - session.execute(text(...), params) for raw SQL with parameters")
        sys.exit(0)

    print(f"⚠️  Found {len(issues)} potential issue(s):")
    print()

    for issue in issues:
        print(f"📍 {issue.file}:{issue.line}")
        print(f"   Pattern: {issue.pattern}")
        print(f"   Issue: {issue.message}")
        print(f"   Fix: {issue.suggestion}")
        print()

    print("-" * 70)
    print(f"Total: {len(issues)} issue(s) found")
    print()
    print("To fix, use the safe helpers:")
    print("  from app.db_helpers import query_one, query_all, query_scalar")
    print()

    sys.exit(1)


if __name__ == "__main__":
    main()
