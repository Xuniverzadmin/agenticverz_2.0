#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Shim Kill Guard - Prevents modification of deprecated service shims.
# artifact_class: CODE
"""Shim Kill Guard - Prevents modification of deprecated service shims.

Layer: L8 — Catalyst / Meta
AUDIENCE: INTERNAL
Product: system-wide
Role: CI enforcement for shim immutability

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation

RULE: Shim files are READ-ONLY after creation.
      They may ONLY contain:
      - Deprecation warning
      - Re-exports from engine
      - __all__ declaration

Any logic, imports beyond engine, or modifications are VIOLATIONS.
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Set


class Violation(NamedTuple):
    """A shim violation."""
    file: str
    line: int
    code: str
    message: str


# Known shim files (deprecated *_service.py that delegate to *_engine.py)
SHIM_FILES = [
    "app/services/cus_integration_service.py",
    "app/services/cus_telemetry_service.py",
    "app/services/cus_enforcement_service.py",
    "app/services/cus_health_service.py",
    "app/services/platform/platform_health_service.py",
    "app/services/limits/simulation_service.py",
    "app/auth/api_key_service.py",
    "app/services/incident_write_service.py",
    "app/services/llm_failure_service.py",
]

# Allowed import patterns in shims (only from corresponding engine)
ALLOWED_IMPORT_PATTERNS = [
    r"^from app\..*_engine import",
    r"^import warnings$",
]

# Forbidden patterns in shims (any logic)
FORBIDDEN_PATTERNS = [
    (r"^\s*class\s+\w+.*:", "SHIM-001", "Class definition in shim - logic must be in engine"),
    (r"^\s*def\s+(?!__)", "SHIM-002", "Function definition in shim - logic must be in engine"),
    (r"^\s*async\s+def\s+", "SHIM-003", "Async function in shim - logic must be in engine"),
    (r"from sqlmodel import", "SHIM-004", "SQLModel import in shim - DB access must be in driver"),
    (r"from sqlalchemy import", "SHIM-005", "SQLAlchemy import in shim - DB access must be in driver"),
    (r"from app\.models\.", "SHIM-006", "Model import in shim - must be in driver"),
    (r"from app\.db import", "SHIM-007", "DB import in shim - must be in driver"),
    (r"Session\(", "SHIM-008", "Session usage in shim - must be in driver"),
    (r"\.query\(", "SHIM-009", "Query in shim - must be in driver"),
    (r"\.execute\(", "SHIM-010", "Execute in shim - must be in driver"),
]

# Required header for shims
REQUIRED_HEADER_MARKER = "DEPRECATED"


def find_shim_files(backend_root: Path) -> List[Path]:
    """Find all shim files in the backend."""
    shims = []
    for shim_path in SHIM_FILES:
        full_path = backend_root / shim_path
        if full_path.exists():
            shims.append(full_path)
    return shims


def check_shim_header(content: str, file_path: str) -> List[Violation]:
    """Check that shim has proper deprecation header."""
    violations = []

    # Check for DEPRECATED marker in first 30 lines
    lines = content.split('\n')[:30]
    has_deprecated_marker = any(REQUIRED_HEADER_MARKER in line for line in lines)

    if not has_deprecated_marker:
        violations.append(Violation(
            file=file_path,
            line=1,
            code="SHIM-100",
            message="Shim missing DEPRECATED marker in header"
        ))

    # Check for warnings.warn call
    has_warning = "warnings.warn(" in content
    if not has_warning:
        violations.append(Violation(
            file=file_path,
            line=1,
            code="SHIM-101",
            message="Shim missing warnings.warn() deprecation call"
        ))

    return violations


def check_forbidden_patterns(content: str, file_path: str) -> List[Violation]:
    """Check for forbidden patterns in shim."""
    violations = []

    for line_num, line in enumerate(content.split('\n'), 1):
        for pattern, code, message in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append(Violation(
                    file=file_path,
                    line=line_num,
                    code=code,
                    message=message
                ))

    return violations


def check_import_validity(content: str, file_path: str) -> List[Violation]:
    """Check that imports are only from engine or warnings."""
    violations = []

    # Track if we're inside a docstring
    in_docstring = False
    docstring_delimiter = None

    for line_num, line in enumerate(content.split('\n'), 1):
        stripped = line.strip()

        # Handle docstring boundaries
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_delimiter = stripped[:3]
                # Check if it's a single-line docstring
                if stripped.count(docstring_delimiter) >= 2:
                    continue  # Single-line docstring, skip
                in_docstring = True
                continue
        else:
            if docstring_delimiter and docstring_delimiter in stripped:
                in_docstring = False
                docstring_delimiter = None
            continue

        # Skip if inside docstring
        if in_docstring:
            continue

        # Skip non-import lines
        if not (stripped.startswith('from ') or stripped.startswith('import ')):
            continue

        # Skip comments
        if stripped.startswith('#'):
            continue

        # Check if import is allowed
        is_allowed = False
        for pattern in ALLOWED_IMPORT_PATTERNS:
            if re.match(pattern, stripped):
                is_allowed = True
                break

        # Also allow __future__ imports
        if 'from __future__' in stripped:
            is_allowed = True

        if not is_allowed:
            # Check if it's importing from the corresponding engine
            # e.g., cus_integration_service.py can import from cus_integration_engine
            file_name = Path(file_path).stem
            if '_service' in file_name:
                engine_name = file_name.replace('_service', '_engine')
                if engine_name in stripped:
                    is_allowed = True

        if not is_allowed:
            violations.append(Violation(
                file=file_path,
                line=line_num,
                code="SHIM-200",
                message=f"Unauthorized import in shim: {stripped}"
            ))

    return violations


def check_shim_structure(content: str, file_path: str) -> List[Violation]:
    """Check that shim only contains re-exports and __all__."""
    violations = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        violations.append(Violation(
            file=file_path,
            line=1,
            code="SHIM-300",
            message="Shim has syntax error - cannot parse"
        ))
        return violations

    for node in ast.walk(tree):
        # Allow: Import, ImportFrom, Expr (for docstrings/warnings), Assign (for __all__)
        # Forbid: FunctionDef, AsyncFunctionDef, ClassDef

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.append(Violation(
                file=file_path,
                line=node.lineno,
                code="SHIM-301",
                message=f"Function '{node.name}' defined in shim - must be in engine"
            ))

        if isinstance(node, ast.ClassDef):
            violations.append(Violation(
                file=file_path,
                line=node.lineno,
                code="SHIM-302",
                message=f"Class '{node.name}' defined in shim - must be in engine"
            ))

    return violations


def check_shim_file(file_path: Path) -> List[Violation]:
    """Run all checks on a single shim file."""
    content = file_path.read_text()
    file_str = str(file_path)

    violations = []
    violations.extend(check_shim_header(content, file_str))
    violations.extend(check_forbidden_patterns(content, file_str))
    violations.extend(check_import_validity(content, file_str))
    violations.extend(check_shim_structure(content, file_str))

    return violations


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Shim Kill Guard")
    parser.add_argument("--ci", action="store_true", help="CI mode - exit 1 on violations")
    parser.add_argument("--backend", type=Path, default=Path(__file__).parent.parent.parent,
                        help="Backend root directory")
    args = parser.parse_args()

    backend_root = args.backend.resolve()

    print("=" * 60)
    print("SHIM KILL GUARD - PIN-468")
    print("=" * 60)
    print(f"Backend: {backend_root}")
    print()

    shim_files = find_shim_files(backend_root)

    if not shim_files:
        print("No shim files found.")
        return 0

    print(f"Checking {len(shim_files)} shim files...")
    print()

    all_violations: List[Violation] = []

    for shim_path in shim_files:
        relative_path = shim_path.relative_to(backend_root)
        violations = check_shim_file(shim_path)

        if violations:
            print(f"❌ {relative_path}")
            for v in violations:
                print(f"   [{v.code}] Line {v.line}: {v.message}")
            all_violations.extend(violations)
        else:
            print(f"✅ {relative_path}")

    print()
    print("=" * 60)

    if all_violations:
        print(f"FAILED: {len(all_violations)} violation(s) in shim files")
        print()
        print("Shim files are READ-ONLY after creation.")
        print("All logic must be in the corresponding *_engine.py file.")
        print("All DB access must be in the corresponding *_driver.py file.")
        print()

        if args.ci:
            return 1
    else:
        print("PASSED: All shim files are compliant")

    return 0


if __name__ == "__main__":
    sys.exit(main())
