#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Naming contract enforcement
# Reference: docs/architecture/contracts/NAMING.md

"""
Naming Contract Check

Detects violations of the naming contract:
- Runtime schemas with context suffixes (_remaining, _current, _total)
- Database columns with camelCase
- Enum values not in UPPER_SNAKE_CASE
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: str
    line: int
    field: str
    rule: str
    message: str


# Patterns that indicate context suffixes (forbidden in runtime schemas)
CONTEXT_SUFFIX_PATTERNS = [
    r"_remaining$",
    r"_current$",
    r"_total$",
    r"^current_",
    r"^total_",
    r"^is_.*_exceeded$",
]

# camelCase pattern (forbidden in DB columns)
CAMEL_CASE_PATTERN = re.compile(r"^[a-z]+[A-Z]")


def check_runtime_schemas(backend_path: Path) -> list[Violation]:
    """Check runtime schemas for naming violations."""
    violations = []
    schemas_path = backend_path / "app" / "schemas"

    if not schemas_path.exists():
        return violations

    for py_file in schemas_path.rglob("*.py"):
        # Skip __init__.py and test files
        if py_file.name.startswith("_") or "test" in py_file.name:
            continue

        try:
            content = py_file.read_text()
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            # Check class definitions (Pydantic models)
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    # Check annotated assignments (field: type)
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id

                        # Check for context suffixes
                        for pattern in CONTEXT_SUFFIX_PATTERNS:
                            if re.search(pattern, field_name):
                                violations.append(Violation(
                                    file=str(py_file.relative_to(backend_path)),
                                    line=item.lineno,
                                    field=field_name,
                                    rule="NC-001",
                                    message=f"Context suffix in runtime schema. "
                                           f"Move context to API adapter layer."
                                ))
                                break

    return violations


def check_enum_values(backend_path: Path) -> list[Violation]:
    """Check enum values are UPPER_SNAKE_CASE."""
    violations = []
    schemas_path = backend_path / "app" / "schemas"

    if not schemas_path.exists():
        return violations

    for py_file in schemas_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        try:
            content = py_file.read_text()
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this is an Enum class
                is_enum = any(
                    (isinstance(base, ast.Name) and base.id in ("Enum", "StrEnum", "IntEnum"))
                    or (isinstance(base, ast.Attribute) and base.attr in ("Enum", "StrEnum", "IntEnum"))
                    for base in node.bases
                )

                if is_enum:
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    value_name = target.id
                                    # Skip dunder methods
                                    if value_name.startswith("_"):
                                        continue
                                    # Check UPPER_SNAKE_CASE
                                    if not re.match(r"^[A-Z][A-Z0-9_]*$", value_name):
                                        violations.append(Violation(
                                            file=str(py_file.relative_to(backend_path)),
                                            line=item.lineno,
                                            field=value_name,
                                            rule="NC-002",
                                            message=f"Enum value not UPPER_SNAKE_CASE"
                                        ))

    return violations


def check_model_columns(backend_path: Path) -> list[Violation]:
    """Check SQLModel/SQLAlchemy columns for camelCase."""
    violations = []
    models_path = backend_path / "app" / "models"

    if not models_path.exists():
        return violations

    for py_file in models_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        try:
            content = py_file.read_text()
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id

                        # Skip private fields
                        if field_name.startswith("_"):
                            continue

                        # Check for camelCase
                        if CAMEL_CASE_PATTERN.match(field_name):
                            violations.append(Violation(
                                file=str(py_file.relative_to(backend_path)),
                                line=item.lineno,
                                field=field_name,
                                rule="NC-003",
                                message=f"camelCase in model column. Use snake_case."
                            ))

    return violations


def main():
    backend_path = Path(__file__).parent.parent.parent / "backend"

    if not backend_path.exists():
        print(f"Backend path not found: {backend_path}")
        sys.exit(1)

    print("NAMING CONTRACT CHECK")
    print("=" * 60)

    all_violations = []

    # Run checks
    print("\n▶ Checking runtime schemas for context suffixes...")
    schema_violations = check_runtime_schemas(backend_path)
    all_violations.extend(schema_violations)
    print(f"  Found {len(schema_violations)} violations")

    print("\n▶ Checking enum values for UPPER_SNAKE_CASE...")
    enum_violations = check_enum_values(backend_path)
    all_violations.extend(enum_violations)
    print(f"  Found {len(enum_violations)} violations")

    print("\n▶ Checking model columns for camelCase...")
    column_violations = check_model_columns(backend_path)
    all_violations.extend(column_violations)
    print(f"  Found {len(column_violations)} violations")

    print("\n" + "=" * 60)

    if not all_violations:
        print("✓ NAMING CONTRACT CHECK: PASSED")
        print("  - Runtime schemas: 0 violations")
        print("  - Enum values: 0 violations")
        print("  - Model columns: 0 violations")
        sys.exit(0)
    else:
        print("✗ NAMING CONTRACT CHECK: FAILED")
        print(f"\nTotal violations: {len(all_violations)}\n")

        for i, v in enumerate(all_violations, 1):
            print(f"Violation {i}:")
            print(f"  File: {v.file}:{v.line}")
            print(f"  Field: {v.field}")
            print(f"  Rule: {v.rule}")
            print(f"  Message: {v.message}")
            print()

        print("Reference: docs/architecture/contracts/NAMING.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
