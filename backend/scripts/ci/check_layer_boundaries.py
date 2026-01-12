#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Layer boundary enforcement
# Callers: CI pipeline, pre-commit
# Allowed Imports: stdlib only
# Forbidden Imports: app.*
# Reference: docs/architecture/LAYER_MODEL.md

"""
Layer Boundary Checker

Enforces the layer model from docs/architecture/LAYER_MODEL.md.

Rules Enforced:
1. Domain code (billing, protection, observability) must not import FastAPI
2. Route files must live in app/api/
3. Dependency direction is correct (no upward imports)

Exit Codes:
  0 = CLEAN (no violations)
  1 = VIOLATIONS FOUND
"""

import ast
import os
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    """A layer boundary violation."""
    file: str
    line: int
    rule: str
    message: str


# Directories that must NOT import FastAPI
FASTAPI_FORBIDDEN_DIRS = [
    "app/billing",
    "app/protection",
    "app/observability",
]

# Forbidden import patterns
FORBIDDEN_FASTAPI_IMPORTS = [
    "fastapi",
    "from fastapi",
]

# Directories that must NOT be imported by domain code
FORBIDDEN_UPWARD_IMPORTS = [
    "app.api",
]

# Domain directories (for checking upward imports)
DOMAIN_DIRS = [
    "app/billing",
    "app/protection",
    "app/observability",
]


def get_imports_from_file(filepath: Path) -> list[tuple[int, str]]:
    """
    Extract all imports from a Python file.

    Returns list of (line_number, import_string) tuples.
    """
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append((node.lineno, f"from {module} import ..."))
    except SyntaxError:
        # Skip files with syntax errors (they'll fail elsewhere)
        pass
    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)

    return imports


def check_fastapi_imports(root: Path) -> list[Violation]:
    """
    Check that domain directories don't import FastAPI.

    Rule A: Domain Code Must Not Import FastAPI.
    """
    violations = []

    for dir_path in FASTAPI_FORBIDDEN_DIRS:
        full_dir = root / dir_path
        if not full_dir.exists():
            continue

        for py_file in full_dir.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            imports = get_imports_from_file(py_file)

            for line_no, import_str in imports:
                for forbidden in FORBIDDEN_FASTAPI_IMPORTS:
                    if forbidden in import_str.lower():
                        violations.append(Violation(
                            file=str(py_file.relative_to(root)),
                            line=line_no,
                            rule="LAYER-001",
                            message=f"Domain code must not import FastAPI: {import_str}",
                        ))

    return violations


def check_upward_imports(root: Path) -> list[Violation]:
    """
    Check that domain code doesn't import from routes.

    Rule: Dependency direction must be downward only.
    """
    violations = []

    for dir_path in DOMAIN_DIRS:
        full_dir = root / dir_path
        if not full_dir.exists():
            continue

        for py_file in full_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            imports = get_imports_from_file(py_file)

            for line_no, import_str in imports:
                for forbidden in FORBIDDEN_UPWARD_IMPORTS:
                    if forbidden in import_str:
                        violations.append(Violation(
                            file=str(py_file.relative_to(root)),
                            line=line_no,
                            rule="LAYER-002",
                            message=f"Domain code must not import from routes: {import_str}",
                        ))

    return violations


def check_route_file_placement(root: Path) -> list[Violation]:
    """
    Check that files with router definitions are in app/api/.

    Rule: If it speaks HTTP, it lives in app/api/.
    """
    violations = []

    # Check domain directories for router definitions
    for dir_path in DOMAIN_DIRS:
        full_dir = root / dir_path
        if not full_dir.exists():
            continue

        for py_file in full_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for router patterns
                router_patterns = [
                    "APIRouter(",
                    "@router.get",
                    "@router.post",
                    "@router.put",
                    "@router.patch",
                    "@router.delete",
                ]

                for pattern in router_patterns:
                    if pattern in content:
                        violations.append(Violation(
                            file=str(py_file.relative_to(root)),
                            line=0,
                            rule="LAYER-003",
                            message=f"Router definitions must be in app/api/, not domain code: {pattern}",
                        ))
                        break  # One violation per file is enough
            except Exception:
                pass

    return violations


def check_observability_query_boundary(root: Path) -> list[Violation]:
    """
    Check that observability.query() is only called from ops/founder routes.

    Rule: Observability is write-only from domain code.
    """
    violations = []

    # Check domain directories for query() calls on observability provider
    for dir_path in DOMAIN_DIRS:
        # observability itself is allowed to define query()
        if "observability" in dir_path:
            continue

        full_dir = root / dir_path
        if not full_dir.exists():
            continue

        for py_file in full_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for observability query patterns
                if "get_observability_provider().query" in content:
                    violations.append(Violation(
                        file=str(py_file.relative_to(root)),
                        line=0,
                        rule="LAYER-004",
                        message="Domain code must not query observability (write-only)",
                    ))

                if "observability_provider.query" in content:
                    violations.append(Violation(
                        file=str(py_file.relative_to(root)),
                        line=0,
                        rule="LAYER-004",
                        message="Domain code must not query observability (write-only)",
                    ))
            except Exception:
                pass

    return violations


def main() -> int:
    """Run all layer boundary checks."""
    # Determine root directory
    script_dir = Path(__file__).parent
    root = script_dir.parent.parent  # backend/

    # Support running from different directories
    if not (root / "app").exists():
        root = Path.cwd()
        if not (root / "app").exists():
            print("Error: Cannot find app/ directory. Run from backend/", file=sys.stderr)
            return 1

    print("=" * 60)
    print("LAYER BOUNDARY CHECK")
    print("=" * 60)
    print(f"Root: {root}")
    print()

    all_violations: list[Violation] = []

    # Run all checks
    print("Checking FastAPI imports in domain code...")
    all_violations.extend(check_fastapi_imports(root))

    print("Checking upward imports (domain -> routes)...")
    all_violations.extend(check_upward_imports(root))

    print("Checking route file placement...")
    all_violations.extend(check_route_file_placement(root))

    print("Checking observability query boundary...")
    all_violations.extend(check_observability_query_boundary(root))

    print()

    if all_violations:
        print("=" * 60)
        print(f"VIOLATIONS FOUND: {len(all_violations)}")
        print("=" * 60)

        for v in all_violations:
            print(f"\n[{v.rule}] {v.file}:{v.line}")
            print(f"  {v.message}")

        print()
        print("Reference: docs/architecture/LAYER_MODEL.md")
        return 1
    else:
        print("=" * 60)
        print("CLEAN: No layer boundary violations found")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
