#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Add New Lint Pattern - Helper for Prevention System Updates
# artifact_class: CODE
"""Add New Lint Pattern - Helper for Prevention System Updates

Interactive tool to add new unsafe patterns to the SQLModel linter.

Usage:
    python scripts/ops/add_lint_pattern.py

This will prompt you for:
1. The unsafe pattern (regex)
2. Error message
3. Fix suggestion
4. Optional safe patterns to whitelist

Exit codes:
    0 - Pattern added successfully
    1 - Aborted or error
"""

import re
import sys
from pathlib import Path
from datetime import datetime

LINTER_FILE = Path("scripts/ops/lint_sqlmodel_patterns.py")


def validate_regex(pattern: str) -> bool:
    """Check if pattern is valid regex."""
    try:
        re.compile(pattern)
        return True
    except re.error as e:
        print(f"  Invalid regex: {e}")
        return False


def read_linter():
    """Read current linter file."""
    return LINTER_FILE.read_text()


def add_unsafe_pattern(content: str, pattern: dict) -> str:
    """Add new pattern to UNSAFE_PATTERNS list."""
    # Find the end of UNSAFE_PATTERNS list
    marker = "]\n\n# Safe patterns"

    new_entry = f"""    # Added: {datetime.now().strftime("%Y-%m-%d")}
    {{
        "regex": r"{pattern["regex"]}",
        "message": "{pattern["message"]}",
        "suggestion": "{pattern["suggestion"]}",
    }},
"""

    return content.replace(marker, new_entry + marker)


def add_safe_pattern(content: str, pattern: str) -> str:
    """Add new pattern to SAFE_PATTERNS list."""
    # Find the end of SAFE_PATTERNS list
    marker = "]\n\n\ndef is_safe_context"

    new_entry = f'    r"{pattern}",  # Added: {datetime.now().strftime("%Y-%m-%d")}\n'

    return content.replace(marker, new_entry + marker)


def main():
    print("=" * 60)
    print("Add New Lint Pattern - Prevention System Update")
    print("=" * 60)
    print()

    if not LINTER_FILE.exists():
        print(f"Error: Linter file not found at {LINTER_FILE}")
        sys.exit(1)

    # Get unsafe pattern
    print("Step 1: Define the UNSAFE pattern to detect")
    print("-" * 40)
    print("Enter the regex pattern that matches the UNSAFE code.")
    print('Example: r"session\\.exec\\([^)]+\\)\\.first\\(\\)\\.\\w+"')
    print()

    regex = input("Regex pattern: ").strip()
    if not regex:
        print("Aborted: No pattern entered")
        sys.exit(1)

    # Remove r" prefix if user included it
    regex = regex.strip("r\"'")

    if not validate_regex(regex):
        sys.exit(1)

    print()
    print("Step 2: Error message")
    print("-" * 40)
    print("What's wrong with this pattern?")
    print("Example: Unsafe: accessing attribute on .first() result (Row tuple)")
    print()

    message = input("Error message: ").strip()
    if not message:
        print("Aborted: No message entered")
        sys.exit(1)

    print()
    print("Step 3: Fix suggestion")
    print("-" * 40)
    print("How should the code be fixed?")
    print(
        "Example: Extract model first: row = session.exec(stmt).first(); obj = row[0] if row else None"
    )
    print()

    suggestion = input("Fix suggestion: ").strip()
    if not suggestion:
        print("Aborted: No suggestion entered")
        sys.exit(1)

    print()
    print("Step 4: Safe patterns (optional)")
    print("-" * 40)
    print(
        "Enter regex patterns that should be WHITELISTED (false positive prevention)."
    )
    print("Press Enter with empty input when done.")
    print()

    safe_patterns = []
    while True:
        safe = input("Safe pattern (or Enter to finish): ").strip()
        if not safe:
            break
        safe = safe.strip("r\"'")
        if validate_regex(safe):
            safe_patterns.append(safe)

    # Show summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Unsafe pattern: {regex}")
    print(f"Message: {message}")
    print(f"Suggestion: {suggestion}")
    if safe_patterns:
        print(f"Safe patterns: {safe_patterns}")
    print()

    confirm = input("Add this pattern? (y/N): ").strip().lower()
    if confirm != "y":
        print("Aborted")
        sys.exit(1)

    # Update file
    content = read_linter()

    content = add_unsafe_pattern(
        content,
        {
            "regex": regex,
            "message": message,
            "suggestion": suggestion,
        },
    )

    for safe in safe_patterns:
        content = add_safe_pattern(content, safe)

    LINTER_FILE.write_text(content)

    print()
    print("Pattern added to linter!")
    print()
    print("Next steps:")
    print(f"  1. Test: python {LINTER_FILE} backend/app/")
    print("  2. Commit: git add scripts/ops/lint_sqlmodel_patterns.py")
    print("  3. Push to ensure CI catches this pattern")
    print()


if __name__ == "__main__":
    main()
