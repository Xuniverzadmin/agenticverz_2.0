#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Router wiring enforcement
# Reference: docs/architecture/contracts/ROUTER_WIRING.md

"""
Router Wiring Check

Detects violations:
- include_router calls outside registry.py
- Router imports in main.py
- Routers not registered in registry.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: str
    line: int
    code: str
    rule: str
    message: str


def check_main_py_imports(backend_path: Path) -> list[Violation]:
    """Check that main.py only imports from registry."""
    violations = []
    main_py = backend_path / "app" / "main.py"

    if not main_py.exists():
        return violations

    content = main_py.read_text()
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Check for router imports
        if re.search(r"from\s+\.?app\.api\.", line) or re.search(r"from\s+\.api\.", line):
            # Allow registry import
            if "registry" in line:
                continue

            violations.append(Violation(
                file="app/main.py",
                line=line_num,
                code=line.strip(),
                rule="RW-001",
                message="Router import in main.py. Move to app/api/registry.py"
            ))

        # Check for include_router calls
        if "include_router" in line:
            violations.append(Violation(
                file="app/main.py",
                line=line_num,
                code=line.strip(),
                rule="RW-002",
                message="include_router in main.py. Move to app/api/registry.py"
            ))

    return violations


def check_include_router_locations(backend_path: Path) -> list[Violation]:
    """Check that include_router is only called in registry.py."""
    violations = []
    app_path = backend_path / "app"

    for py_file in app_path.rglob("*.py"):
        # Skip registry.py - that's where it should be
        if py_file.name == "registry.py":
            continue

        # Skip test files
        if "test" in str(py_file):
            continue

        rel_path = str(py_file.relative_to(backend_path))

        try:
            content = py_file.read_text()
            lines = content.split("\n")
        except (UnicodeDecodeError, IOError):
            continue

        for line_num, line in enumerate(lines, 1):
            if "include_router" in line and not line.strip().startswith("#"):
                violations.append(Violation(
                    file=rel_path,
                    line=line_num,
                    code=line.strip()[:60],
                    rule="RW-003",
                    message="include_router outside registry.py"
                ))

    return violations


def check_registry_exists(backend_path: Path) -> list[Violation]:
    """Check that registry.py exists."""
    violations = []
    registry_path = backend_path / "app" / "api" / "registry.py"

    if not registry_path.exists():
        violations.append(Violation(
            file="app/api/registry.py",
            line=0,
            code="",
            rule="RW-004",
            message="registry.py does not exist. Create app/api/registry.py"
        ))

    return violations


def find_all_routers(backend_path: Path) -> dict[str, Path]:
    """Find all router definitions in the codebase."""
    routers = {}
    api_path = backend_path / "app" / "api"

    if not api_path.exists():
        return routers

    for py_file in api_path.rglob("*.py"):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        if "registry" in py_file.name:
            continue

        try:
            content = py_file.read_text()
        except (UnicodeDecodeError, IOError):
            continue

        # Look for router = APIRouter() definitions
        if re.search(r"router\s*=\s*APIRouter\(", content):
            rel_path = str(py_file.relative_to(backend_path))
            routers[rel_path] = py_file

    return routers


def check_routers_registered(backend_path: Path) -> list[Violation]:
    """Check that all routers are registered in registry.py."""
    violations = []
    registry_path = backend_path / "app" / "api" / "registry.py"

    if not registry_path.exists():
        return violations

    registry_content = registry_path.read_text()
    all_routers = find_all_routers(backend_path)

    for router_path, router_file in all_routers.items():
        # Convert path to import-like pattern
        # app/api/limits/simulate.py -> limits.simulate or limits_simulate
        parts = router_path.replace("app/api/", "").replace(".py", "").replace("/", ".")
        module_name = parts.split(".")[-1]

        # Check if this router is imported in registry
        if module_name not in registry_content:
            # Also check for full path pattern
            full_pattern = router_path.replace("/", ".").replace(".py", "")
            if full_pattern not in registry_content:
                violations.append(Violation(
                    file=router_path,
                    line=0,
                    code="",
                    rule="RW-005",
                    message=f"Router not found in registry.py. Add import and include_router call."
                ))

    return violations


def main():
    backend_path = Path(__file__).parent.parent.parent / "backend"

    if not backend_path.exists():
        print(f"Backend path not found: {backend_path}")
        sys.exit(1)

    print("ROUTER WIRING CHECK")
    print("=" * 60)

    all_violations = []

    # Run checks
    print("\n▶ Checking registry.py exists...")
    registry_violations = check_registry_exists(backend_path)
    all_violations.extend(registry_violations)
    if registry_violations:
        print("  registry.py not found!")
    else:
        print("  registry.py exists")

    print("\n▶ Checking main.py imports...")
    main_violations = check_main_py_imports(backend_path)
    all_violations.extend(main_violations)
    print(f"  Found {len(main_violations)} violations")

    print("\n▶ Checking include_router locations...")
    include_violations = check_include_router_locations(backend_path)
    all_violations.extend(include_violations)
    print(f"  Found {len(include_violations)} violations")

    print("\n▶ Checking all routers are registered...")
    if not registry_violations:
        unregistered = check_routers_registered(backend_path)
        all_violations.extend(unregistered)
        print(f"  Found {len(unregistered)} unregistered routers")
    else:
        print("  Skipped (registry.py missing)")

    print("\n" + "=" * 60)

    if not all_violations:
        print("✓ ROUTER WIRING CHECK: PASSED")
        print("  - registry.py exists: YES")
        print("  - main.py clean: YES")
        print("  - All routers registered: YES")
        sys.exit(0)
    else:
        print("✗ ROUTER WIRING CHECK: FAILED")
        print(f"\nTotal violations: {len(all_violations)}\n")

        for i, v in enumerate(all_violations, 1):
            print(f"Violation {i}:")
            print(f"  File: {v.file}:{v.line}" if v.line else f"  File: {v.file}")
            if v.code:
                print(f"  Code: {v.code}")
            print(f"  Rule: {v.rule}")
            print(f"  Message: {v.message}")
            print()

        print("Reference: docs/architecture/contracts/ROUTER_WIRING.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
