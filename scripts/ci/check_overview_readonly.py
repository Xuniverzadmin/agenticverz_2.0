#!/usr/bin/env python3
"""
GUARDRAIL: DOMAIN-003 - Overview is Read-Only Projection
Rule: Overview domain owns NO tables. All data derived via queries. No mutations.

This script ensures overview.py contains no write operations.
"""

import re
import sys
from pathlib import Path

# Forbidden write patterns in Overview
FORBIDDEN_PATTERNS = [
    (r'\bINSERT\b', "SQL INSERT statement"),
    (r'\bUPDATE\b(?!\s*=)', "SQL UPDATE statement"),  # Exclude UPDATE = in column names
    (r'\bDELETE\b', "SQL DELETE statement"),
    (r'session\.add\s*\(', "SQLAlchemy session.add()"),
    (r'session\.delete\s*\(', "SQLAlchemy session.delete()"),
    (r'session\.commit\s*\(', "SQLAlchemy session.commit()"),
    (r'\.create\s*\(', "Repository .create() call"),
    (r'\.update\s*\(', "Repository .update() call"),
    (r'\.delete\s*\(', "Repository .delete() call"),
    (r'db\.execute\s*\([^)]*(?:INSERT|UPDATE|DELETE)', "Direct DB execute with mutation"),
]

# Allowed exceptions (false positives)
ALLOWED_PATTERNS = [
    r'#.*\b(INSERT|UPDATE|DELETE)\b',  # Comments
    r'""".*\b(INSERT|UPDATE|DELETE)\b.*"""',  # Docstrings
    r"'''.*\b(INSERT|UPDATE|DELETE)\b.*'''",  # Docstrings
    r'last_updated',  # Field names
    r'updated_at',  # Field names
]


def is_allowed(line: str) -> bool:
    """Check if line is an allowed exception."""
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def check_overview_file(file_path: str) -> list:
    """Check overview.py for write operations."""
    violations = []

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Skip if allowed exception
        if is_allowed(line):
            continue

        for pattern, description in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append(
                    f"Line {i}: {description} detected\n"
                    f"  {line.strip()}\n"
                    f"  → Overview MUST be read-only projection"
                )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app" / "api"
    overview_file = backend_path / "overview.py"

    print("DOMAIN-003: Overview Read-Only Check")
    print("=" * 50)

    if not overview_file.exists():
        print(f"overview.py not found at {overview_file}")
        sys.exit(1)

    violations = check_overview_file(str(overview_file))

    print(f"File checked: {overview_file}")
    print(f"Violations found: {len(violations)}")
    print()

    if violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in violations:
            print(v)
            print()
        print("\nOverview is a DERIVED STATE domain.")
        print("It must only contain SELECT queries, never mutations.")
        sys.exit(1)
    else:
        print("✓ Overview is read-only - no write operations detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
