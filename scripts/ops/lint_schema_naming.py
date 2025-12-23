#!/usr/bin/env python3
"""
Schema Naming Convention Linter

M25 Hygiene: Prevent schema drift bugs like blocked_incident_id vs incident_id_blocked.

See docs/SCHEMA_NAMING_CONVENTIONS.md for rules.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class SchemaLinter:
    """Lints migration files for naming convention violations."""

    # Pattern pairs that should not coexist
    CONFLICTING_PATTERNS = [
        # blocked_ prefix vs _blocked suffix
        (r"blocked_\w+_id", r"\w+_id_blocked"),
        # source_ prefix vs _source suffix
        (r"source_\w+_id", r"\w+_id_source"),
        # target_ prefix vs _target suffix
        (r"target_\w+_id", r"\w+_id_target"),
        # original_ prefix vs _original suffix
        (r"original_\w+_id", r"\w+_id_original"),
    ]

    # Required suffixes
    FOREIGN_KEY_PATTERN = re.compile(r"sa\.Column\(['\"](\w+)['\"].*ForeignKey")
    TIMESTAMP_PATTERN = re.compile(r"sa\.Column\(['\"](\w+)['\"].*DateTime")
    BOOLEAN_PATTERN = re.compile(r"sa\.Column\(['\"](\w+)['\"].*Boolean")

    def __init__(self):
        self.errors: List[Tuple[str, int, str]] = []
        self.warnings: List[Tuple[str, int, str]] = []

    def lint_file(self, path: Path) -> None:
        """Lint a single migration file."""
        content = path.read_text()
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            self._check_foreign_key(path, line_num, line)
            self._check_timestamp(path, line_num, line)
            self._check_boolean(path, line_num, line)

        # Check for conflicting patterns in the whole file
        self._check_conflicts(path, content)

    def _check_foreign_key(self, path: Path, line_num: int, line: str) -> None:
        """Check that foreign keys end with _id."""
        match = self.FOREIGN_KEY_PATTERN.search(line)
        if match:
            column_name = match.group(1)
            if not column_name.endswith("_id"):
                self.errors.append(
                    (
                        str(path),
                        line_num,
                        f"Foreign key '{column_name}' should end with '_id'",
                    )
                )

    def _check_timestamp(self, path: Path, line_num: int, line: str) -> None:
        """Check that timestamps end with _at."""
        match = self.TIMESTAMP_PATTERN.search(line)
        if match:
            column_name = match.group(1)
            # Common exceptions
            if column_name in ("date", "created", "updated"):
                return
            if not column_name.endswith("_at") and not column_name == "date":
                self.warnings.append(
                    (
                        str(path),
                        line_num,
                        f"Timestamp '{column_name}' should end with '_at' (e.g., '{column_name}_at')",
                    )
                )

    def _check_boolean(self, path: Path, line_num: int, line: str) -> None:
        """Check that booleans start with is_ or has_."""
        match = self.BOOLEAN_PATTERN.search(line)
        if match:
            column_name = match.group(1)
            if not (column_name.startswith("is_") or column_name.startswith("has_")):
                self.warnings.append(
                    (
                        str(path),
                        line_num,
                        f"Boolean '{column_name}' should start with 'is_' or 'has_' (e.g., 'is_{column_name}')",
                    )
                )

    def _check_conflicts(self, path: Path, content: str) -> None:
        """Check for conflicting naming patterns."""
        for pattern_a, pattern_b in self.CONFLICTING_PATTERNS:
            matches_a = re.findall(pattern_a, content, re.IGNORECASE)
            matches_b = re.findall(pattern_b, content, re.IGNORECASE)

            if matches_a and matches_b:
                self.errors.append(
                    (
                        str(path),
                        0,
                        f"Conflicting patterns found: {matches_a} vs {matches_b}. "
                        f"Use consistent naming (prefer prefix pattern).",
                    )
                )

    def report(self) -> int:
        """Print report and return exit code."""
        if self.errors:
            print("\n=== ERRORS (must fix) ===")
            for path, line, msg in self.errors:
                if line > 0:
                    print(f"{path}:{line}: {msg}")
                else:
                    print(f"{path}: {msg}")

        if self.warnings:
            print("\n=== WARNINGS (should fix) ===")
            for path, line, msg in self.warnings:
                print(f"{path}:{line}: {msg}")

        if not self.errors and not self.warnings:
            print("Schema naming check passed.")
            return 0

        print(f"\nTotal: {len(self.errors)} errors, {len(self.warnings)} warnings")
        return 1 if self.errors else 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: lint_schema_naming.py <migrations_dir>")
        print("Example: lint_schema_naming.py backend/alembic/versions/")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)

    linter = SchemaLinter()

    if path.is_file():
        linter.lint_file(path)
    else:
        for migration in sorted(path.glob("*.py")):
            if migration.name.startswith("_"):
                continue
            linter.lint_file(migration)

    exit_code = linter.report()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
