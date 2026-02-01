#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Layer Segregation Guard
# artifact_class: CODE
"""
Layer Segregation Guard

Enforces L4/L6 boundary contracts per DRIVER_ENGINE_CONTRACT.md

Usage:
    python3 scripts/ops/layer_segregation_guard.py --check
    python3 scripts/ops/layer_segregation_guard.py --ci  # Exit 1 on violations

Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, DRIVER_ENGINE_PATTERN_LOCKED.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns that indicate DB access (forbidden in engines)
ENGINE_FORBIDDEN_PATTERNS = [
    (r"^from sqlalchemy", "sqlalchemy import"),
    (r"^from sqlmodel", "sqlmodel import"),
    (r"^import sqlalchemy", "sqlalchemy import"),
    (r"^import sqlmodel", "sqlmodel import"),
    (r"from app\.models\.[a-z]+ import", "ORM model import"),
    (r"\.exec\(", "session.exec() call"),
    (r"\.execute\(", "session.execute() call"),
    (r"\.commit\(", "session.commit() call"),
    (r"\.rollback\(", "session.rollback() call"),
    (r"select\(", "select() call"),
]

# Patterns that indicate business logic (forbidden in drivers)
DRIVER_FORBIDDEN_PATTERNS = [
    (r"if.*severity", "severity check"),
    (r"if.*threshold", "threshold check"),
    (r"if.*policy", "policy check"),
    (r"if.*enforce", "enforcement logic"),
    (r"if.*budget", "budget logic"),
    (r"if.*is_valid", "validation logic"),
    (r"if.*is_allowed", "authorization logic"),
    (r"\.validate\(", "validate() call"),
    (r"\.check\(", "check() call"),
]

# Patterns that indicate engine imports (forbidden in drivers)
DRIVER_IMPORT_FORBIDDEN_PATTERNS = [
    (r"from app\.hoc\.[^/]+\.engines", "engine import in driver"),
    (r"from app\.services\.[a-z_]+_engine import", "engine import in driver"),
]


def check_file(filepath: Path, patterns: List[Tuple[str, str]], skip_type_checking: bool = True) -> List[Tuple[int, str, str]]:
    """Check a file for forbidden patterns."""
    violations = []
    in_type_checking = False
    in_docstring = False

    try:
        content = filepath.read_text()
    except Exception as e:
        return [(0, "read_error", str(e))]

    for lineno, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()

        # Track TYPE_CHECKING block
        if "if TYPE_CHECKING:" in line:
            in_type_checking = True
            continue
        if in_type_checking and stripped and not stripped.startswith((" ", "\t", "#")):
            in_type_checking = False

        # Skip if in TYPE_CHECKING block
        if skip_type_checking and in_type_checking:
            continue

        # Track docstrings
        if '"""' in line:
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue

        # Skip comment lines
        if stripped.startswith("#"):
            continue

        # Check patterns
        for pattern, description in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((lineno, description, line.strip()[:80]))

    return violations


def check_layer_header(filepath: Path) -> bool:
    """Check if file has a Layer header."""
    try:
        content = filepath.read_text()
        # Check first 50 lines for Layer header
        lines = content.split("\n")[:50]
        for line in lines:
            if re.match(r"^# Layer:", line):
                return True
        return False
    except Exception:
        return False


def scan_directory(base_path: Path, subdir: str, file_pattern: str, forbidden_patterns: List[Tuple[str, str]]) -> dict:
    """Scan a directory for violations."""
    results = {}
    search_path = base_path / "app" / "hoc"

    if not search_path.exists():
        return results

    for filepath in search_path.rglob(f"*/{subdir}/{file_pattern}"):
        violations = check_file(filepath, forbidden_patterns)
        if violations:
            rel_path = filepath.relative_to(base_path)
            results[str(rel_path)] = violations

    return results


def scan_services_directory(base_path: Path, file_pattern: str, forbidden_patterns: List[Tuple[str, str]]) -> dict:
    """Scan services directory for violations."""
    results = {}
    search_path = base_path / "app" / "services"

    if not search_path.exists():
        return results

    for filepath in search_path.glob(file_pattern):
        violations = check_file(filepath, forbidden_patterns)
        if violations:
            rel_path = filepath.relative_to(base_path)
            results[str(rel_path)] = violations

    return results


def check_naming_violations(base_path: Path) -> List[str]:
    """Check for banned *_service.py files in engines directories."""
    violations = []
    search_path = base_path / "app" / "hoc"

    if not search_path.exists():
        return violations

    for filepath in search_path.rglob("*/engines/*_service.py"):
        rel_path = filepath.relative_to(base_path)
        violations.append(str(rel_path))

    return violations


def check_new_service_files(base_path: Path) -> List[str]:
    """Check for any new *_service.py files in hoc (banned)."""
    violations = []
    search_path = base_path / "app" / "hoc"

    if not search_path.exists():
        return violations

    for filepath in search_path.rglob("*_service.py"):
        rel_path = filepath.relative_to(base_path)
        violations.append(str(rel_path))

    return violations


def check_missing_layer_headers(base_path: Path) -> List[str]:
    """Check for Python files missing Layer headers."""
    violations = []
    search_path = base_path / "app" / "hoc"

    if not search_path.exists():
        return violations

    # Check engines and drivers
    for subdir in ["engines", "drivers"]:
        for filepath in search_path.rglob(f"*/{subdir}/*.py"):
            if filepath.name == "__init__.py":
                continue
            if not check_layer_header(filepath):
                rel_path = filepath.relative_to(base_path)
                violations.append(str(rel_path))

    return violations


def main():
    parser = argparse.ArgumentParser(description="Layer Segregation Guard")
    parser.add_argument("--check", action="store_true", help="Run checks and report")
    parser.add_argument("--ci", action="store_true", help="CI mode - exit 1 on violations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--strict", action="store_true", help="Strict mode - include service file ban")
    args = parser.parse_args()

    base_path = Path(__file__).parent.parent.parent / "backend"
    if not base_path.exists():
        base_path = Path("/root/agenticverz2.0/backend")

    total_violations = 0

    print("=" * 60)
    print("LAYER SEGREGATION GUARD")
    print("Reference: DRIVER_ENGINE_PATTERN_LOCKED.md")
    print("=" * 60)
    print()

    # Check 1: Engine DB violations
    print("### Check 1: Engine DB Access Violations")
    print("Engines must not import sqlalchemy/sqlmodel or access DB directly")
    print()

    engine_violations = scan_directory(
        base_path, "engines", "*_engine.py", ENGINE_FORBIDDEN_PATTERNS
    )

    # Also check app/services/*_engine.py
    engine_violations.update(scan_services_directory(
        base_path, "*_engine.py", ENGINE_FORBIDDEN_PATTERNS
    ))

    if engine_violations:
        for filepath, violations in engine_violations.items():
            print(f"  ❌ {filepath}")
            for lineno, desc, line in violations:
                print(f"     Line {lineno}: {desc}")
                if args.verbose:
                    print(f"       > {line}")
            total_violations += len(violations)
    else:
        print("  ✅ No violations found")
    print()

    # Check 2: Driver business logic violations
    print("### Check 2: Driver Business Logic Violations")
    print("Drivers must not contain policy/threshold/validation logic")
    print()

    driver_violations = scan_directory(
        base_path, "drivers", "*_driver.py", DRIVER_FORBIDDEN_PATTERNS
    )

    # Also check app/services/*_driver.py
    driver_violations.update(scan_services_directory(
        base_path, "*_driver.py", DRIVER_FORBIDDEN_PATTERNS
    ))

    if driver_violations:
        for filepath, violations in driver_violations.items():
            print(f"  ❌ {filepath}")
            for lineno, desc, line in violations:
                print(f"     Line {lineno}: {desc}")
                if args.verbose:
                    print(f"       > {line}")
            total_violations += len(violations)
    else:
        print("  ✅ No violations found")
    print()

    # Check 3: Driver importing engines
    print("### Check 3: Driver Engine Import Violations")
    print("Drivers must not import from engines")
    print()

    driver_import_violations = scan_directory(
        base_path, "drivers", "*_driver.py", DRIVER_IMPORT_FORBIDDEN_PATTERNS
    )

    # Also check app/services/*_driver.py
    driver_import_violations.update(scan_services_directory(
        base_path, "*_driver.py", DRIVER_IMPORT_FORBIDDEN_PATTERNS
    ))

    if driver_import_violations:
        for filepath, violations in driver_import_violations.items():
            print(f"  ❌ {filepath}")
            for lineno, desc, line in violations:
                print(f"     Line {lineno}: {desc}")
                if args.verbose:
                    print(f"       > {line}")
            total_violations += len(violations)
    else:
        print("  ✅ No violations found")
    print()

    # Check 4: Naming violations (service files in engines)
    print("### Check 4: Naming Violations (engines/)")
    print("*_service.py files are banned in engines directories")
    print()

    naming_violations = check_naming_violations(base_path)

    if naming_violations:
        for filepath in naming_violations:
            print(f"  ❌ {filepath} (should be *_engine.py)")
            total_violations += 1
    else:
        print("  ✅ No violations found")
    print()

    # Check 5: Service files banned entirely (strict mode)
    if args.strict:
        print("### Check 5: Service File Ban (strict)")
        print("*_service.py files are banned in hoc")
        print()

        service_violations = check_new_service_files(base_path)

        if service_violations:
            for filepath in service_violations:
                print(f"  ❌ {filepath} (service files banned)")
                total_violations += 1
        else:
            print("  ✅ No violations found")
        print()

    # Check 6: Missing Layer headers
    print("### Check 5: Missing Layer Headers")
    print("All engine/driver files must have # Layer: header")
    print()

    header_violations = check_missing_layer_headers(base_path)

    if header_violations:
        for filepath in header_violations:
            print(f"  ⚠️  {filepath} (missing Layer header)")
            # Warning only, not counted as violation for now
    else:
        print("  ✅ No violations found")
    print()

    # Summary
    print("=" * 60)
    if total_violations == 0:
        print("✅ PASS - All layer segregation checks passed")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"❌ FAIL - {total_violations} violation(s) found")
        print("=" * 60)
        if args.ci:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
