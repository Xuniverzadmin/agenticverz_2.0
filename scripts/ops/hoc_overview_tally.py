#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for overview domain consolidation
# Reference: PIN-502
# artifact_class: CODE

"""
Overview Domain Consolidation Verification Script

Verifies:
- L5_engines: 2 .py files
- L5_schemas: 1 .py file
- L6_drivers: 2 .py files
- No *_service.py files
- 1 header correction applied
- No active legacy imports
"""

import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/overview/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/overview/L6_drivers"
SCHEMAS_PATH = BASE_DIR / "app/hoc/cus/overview/L5_schemas"
OVERVIEW_INIT = BASE_DIR / "app/hoc/cus/overview/__init__.py"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def print_pass(check_name: str):
    print(f"{GREEN}✓ PASS{RESET}: {check_name}")


def print_fail(check_name: str, details: str = ""):
    print(f"{RED}✗ FAIL{RESET}: {check_name}")
    if details:
        print(f"  Details: {details}")


def count_py_files(directory: Path) -> Tuple[int, List[str]]:
    if not directory.exists():
        return 0, []
    py_files = [f.name for f in directory.iterdir() if f.is_file() and f.suffix == ".py"]
    return len(py_files), sorted(py_files)


def file_starts_with(file_path: Path, pattern: str) -> bool:
    if not file_path.exists():
        return False
    try:
        return file_path.read_text().strip().startswith(pattern)
    except Exception:
        return False


def has_active_import(file_path: Path, pattern: str) -> bool:
    if not file_path.exists():
        return False
    try:
        content = file_path.read_text()
        in_docstring = False
        docstring_char = None
        for line in content.splitlines():
            stripped = line.strip()
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    if stripped.count(docstring_char) >= 2:
                        continue
                    in_docstring = True
                    continue
            else:
                if docstring_char and docstring_char in stripped:
                    in_docstring = False
                continue
            if stripped.startswith("#"):
                continue
            if pattern in stripped and (stripped.startswith("from ") or stripped.startswith("import ")):
                return True
        return False
    except Exception:
        return False


def check_file_counts() -> bool:
    success = True
    for label, path, expected in [
        ("L5_engines", L5_PATH, 2),
        ("L5_schemas", SCHEMAS_PATH, 1),
        ("L6_drivers", L6_PATH, 2),
    ]:
        actual, _ = count_py_files(path)
        if actual == expected:
            print_pass(f"{label} file count: {actual}")
        else:
            print_fail(f"{label} file count", f"Expected {expected}, found {actual}")
            success = False
    return success


def check_naming_compliance() -> bool:
    _, l5_files = count_py_files(L5_PATH)
    _, l6_files = count_py_files(L6_PATH)
    success = True
    service_l5 = [f for f in l5_files if f.endswith("_service.py")]
    service_l6 = [f for f in l6_files if f.endswith("_service.py")]
    if not service_l5:
        print_pass("L5_engines: No *_service.py files")
    else:
        print_fail("L5_engines naming", f"Found {service_l5}")
        success = False
    if not service_l6:
        print_pass("L6_drivers: No *_service.py files")
    else:
        print_fail("L6_drivers naming", f"Found {service_l6}")
        success = False
    return success


def check_header() -> bool:
    if file_starts_with(OVERVIEW_INIT, "# Layer: L5"):
        print_pass("overview/__init__.py starts with '# Layer: L5'")
        return True
    else:
        print_fail("overview/__init__.py header", "Does not start with '# Layer: L5'")
        return False


def check_no_legacy() -> bool:
    facade = L5_PATH / "overview_facade.py"
    if not facade.exists():
        print_fail("overview_facade.py exists", "File not found")
        return False
    if not has_active_import(facade, "app.services"):
        print_pass("overview_facade.py has no legacy imports")
        return True
    else:
        print_fail("overview_facade.py", "Has active import from app.services")
        return False


OVERVIEW_ROOT = BASE_DIR / "app/hoc/cus/overview"


def check_no_abolished_general() -> bool:
    py_files = list(OVERVIEW_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(OVERVIEW_ROOT)) for f in py_files if has_active_import(f, "cus.general")]
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_no_active_legacy_all() -> bool:
    py_files = list(OVERVIEW_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(OVERVIEW_ROOT)) for f in py_files if has_active_import(f, "app.services")]
    if not violations:
        print_pass("Zero active app.services imports in overview domain")
        return True
    for v in violations:
        print_fail(f"{v}", "Active import from app.services")
    return False


def main():
    print("=" * 80)
    print("OVERVIEW DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []
    checks = [
        ("Check 1: File Counts", check_file_counts),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: Header Correction", check_header),
        ("Check 4: No Legacy Imports", check_no_legacy),
        # Cleansing Cycle (PIN-503)
        ("Check 5: No Abolished general/ Imports", check_no_abolished_general),
        ("Check 6: Zero app.services (Full Domain)", check_no_active_legacy_all),
    ]

    for label, fn in checks:
        print(label)
        print("-" * 80)
        results.append(fn())
        print()

    print("=" * 80)
    if all(results):
        print(f"{GREEN}ALL CHECKS PASSED{RESET}")
        print("=" * 80)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"{RED}FAILED: {failed}/{len(results)} checks failed{RESET}")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
