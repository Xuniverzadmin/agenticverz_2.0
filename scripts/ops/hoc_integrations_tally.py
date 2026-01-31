#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for integrations domain consolidation
# Reference: PIN-498
# artifact_class: CODE

"""
Integrations Domain Consolidation Verification Script

Verifies:
- L5_engines: 16 .py files
- L6_drivers: 5 .py files
- adapters: 23 .py files
- L5_schemas: 5 .py files
- No *_service.py files in L5/L6
- 6 renames completed with header notes
- 1 header correction applied
- Legacy import disconnected (cus_integration_engine.py)
- Import path fixes (4 files)
- bridges_driver.py restored
- external_adapters/ directory removed
- No active legacy imports
"""

import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/integrations/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/integrations/L6_drivers"
ADAPTERS_PATH = BASE_DIR / "app/hoc/cus/integrations/adapters"
SCHEMAS_PATH = BASE_DIR / "app/hoc/cus/integrations/L5_schemas"
INTEGRATIONS_INIT = BASE_DIR / "app/hoc/cus/integrations/__init__.py"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def print_pass(check_name: str):
    print(f"{GREEN}✓ PASS{RESET}: {check_name}")


def print_fail(check_name: str, details: str = ""):
    print(f"{RED}✗ FAIL{RESET}: {check_name}")
    if details:
        print(f"  Details: {details}")


def count_py_files(directory: Path, maxdepth: int = 1) -> Tuple[int, List[str]]:
    if not directory.exists():
        return 0, []
    if maxdepth == 1:
        py_files = [f.name for f in directory.iterdir() if f.is_file() and f.suffix == ".py"]
    else:
        py_files = [str(f.relative_to(directory)) for f in directory.rglob("*.py")]
    return len(py_files), sorted(py_files)


def file_contains(file_path: Path, pattern: str) -> bool:
    if not file_path.exists():
        return False
    try:
        return pattern in file_path.read_text()
    except Exception:
        return False


def file_starts_with(file_path: Path, pattern: str) -> bool:
    if not file_path.exists():
        return False
    try:
        return file_path.read_text().strip().startswith(pattern)
    except Exception:
        return False


def has_active_import(file_path: Path, pattern: str) -> bool:
    """Check if file has an active (non-comment, non-docstring) import matching pattern."""
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
    l5_count, _ = count_py_files(L5_PATH)
    l6_count, _ = count_py_files(L6_PATH)
    adapters_count, _ = count_py_files(ADAPTERS_PATH)
    schemas_count, _ = count_py_files(SCHEMAS_PATH)

    for label, actual, expected in [
        ("L5_engines", l5_count, 16),
        ("L6_drivers", l6_count, 5),
        ("adapters", adapters_count, 23),
        ("L5_schemas", schemas_count, 5),
    ]:
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

    # Old files must NOT exist
    old_files = [
        (L5_PATH / "cus_integration_service.py", "cus_integration_service.py"),
        (L5_PATH / "bridges.py", "bridges.py"),
        (L5_PATH / "dispatcher.py", "dispatcher.py"),
        (L5_PATH / "http_connector.py", "http_connector.py"),
        (L5_PATH / "mcp_connector.py", "mcp_connector.py"),
        (L6_PATH / "connector_registry.py", "connector_registry.py"),
    ]
    for old_path, label in old_files:
        if not old_path.exists():
            print_pass(f"{label} does not exist (correct)")
        else:
            print_fail(f"{label} still exists")
            success = False

    return success


def check_new_files_exist() -> bool:
    success = True
    new_files = [
        (L5_PATH / "cus_integration_engine.py", "cus_integration_engine.py"),
        (L5_PATH / "bridges_engine.py", "bridges_engine.py"),
        (L5_PATH / "dispatcher_engine.py", "dispatcher_engine.py"),
        (L5_PATH / "http_connector_engine.py", "http_connector_engine.py"),
        (L5_PATH / "mcp_connector_engine.py", "mcp_connector_engine.py"),
        (L6_PATH / "connector_registry_driver.py", "connector_registry_driver.py"),
        (L6_PATH / "bridges_driver.py", "bridges_driver.py (restored)"),
    ]
    for path, label in new_files:
        if path.exists():
            print_pass(f"{label} exists")
        else:
            print_fail(f"{label} missing")
            success = False

    return success


def check_rename_headers() -> bool:
    success = True
    checks = [
        (L5_PATH / "cus_integration_engine.py", "Renamed cus_integration_service.py"),
        (L5_PATH / "bridges_engine.py", "Renamed bridges.py"),
        (L5_PATH / "dispatcher_engine.py", "Renamed dispatcher.py"),
        (L5_PATH / "http_connector_engine.py", "Renamed http_connector.py"),
        (L5_PATH / "mcp_connector_engine.py", "Renamed mcp_connector.py"),
        (L6_PATH / "connector_registry_driver.py", "Renamed connector_registry.py"),
    ]
    for path, pattern in checks:
        if file_contains(path, pattern):
            print_pass(f"{path.name} has rename note")
        else:
            print_fail(f"{path.name} rename note", f"Missing '{pattern}'")
            success = False

    return success


def check_header_correction() -> bool:
    if file_starts_with(INTEGRATIONS_INIT, "# Layer: L5"):
        print_pass("integrations/__init__.py starts with '# Layer: L5'")
        return True
    else:
        print_fail("integrations/__init__.py header", "Does not start with '# Layer: L5'")
        return False


def check_legacy_disconnected() -> bool:
    success = True
    cus_engine = L5_PATH / "cus_integration_engine.py"

    if file_contains(cus_engine, "LEGACY DISCONNECTED"):
        print_pass("cus_integration_engine.py has LEGACY DISCONNECTED marker")
    else:
        print_fail("cus_integration_engine.py", "Missing LEGACY DISCONNECTED marker")
        success = False

    if not has_active_import(cus_engine, "app.services"):
        print_pass("cus_integration_engine.py has no active legacy imports")
    else:
        print_fail("cus_integration_engine.py", "Still has active import from app.services")
        success = False

    return success


def check_import_fixes() -> bool:
    success = True

    # integrations_facade.py should import from cus_integration_engine (not _service)
    facade = L5_PATH / "integrations_facade.py"
    if file_contains(facade, "cus_integration_engine"):
        print_pass("integrations_facade.py imports from cus_integration_engine")
    else:
        print_fail("integrations_facade.py import", "Missing cus_integration_engine")
        success = False

    # connectors_facade.py should import from connector_registry_driver
    connectors = L5_PATH / "connectors_facade.py"
    if file_contains(connectors, "connector_registry_driver"):
        print_pass("connectors_facade.py imports from connector_registry_driver")
    else:
        print_fail("connectors_facade.py import", "Missing connector_registry_driver")
        success = False

    # bridges_engine.py should import from dispatcher_engine (not dispatcher)
    bridges = L5_PATH / "bridges_engine.py"
    if file_contains(bridges, "dispatcher_engine"):
        print_pass("bridges_engine.py imports from dispatcher_engine")
    else:
        print_fail("bridges_engine.py import", "Missing dispatcher_engine")
        success = False

    # bridges_engine.py should import from L6_drivers.bridges_driver
    if file_contains(bridges, "L6_drivers.bridges_driver"):
        print_pass("bridges_engine.py imports from L6_drivers.bridges_driver")
    else:
        print_fail("bridges_engine.py import", "Missing L6_drivers.bridges_driver")
        success = False

    return success


def check_external_adapters_removed() -> bool:
    ext_path = L5_PATH / "external_adapters"
    if not ext_path.exists():
        print_pass("L5_engines/external_adapters/ directory removed")
        return True
    else:
        print_fail("L5_engines/external_adapters/", "Directory still exists")
        return False


def check_no_legacy() -> bool:
    success = True
    files_to_check = [
        L5_PATH / "integrations_facade.py",
        L5_PATH / "connectors_facade.py",
        L5_PATH / "datasources_facade.py",
    ]
    for path in files_to_check:
        if not path.exists():
            print_fail(f"{path.name} exists", "File not found")
            success = False
            continue
        if not has_active_import(path, "app.services"):
            print_pass(f"{path.name} has no legacy imports")
        else:
            print_fail(f"{path.name}", "Has active import from app.services")
            success = False
    return success


INTEGRATIONS_ROOT = BASE_DIR / "app/hoc/cus/integrations"


def check_no_abolished_general() -> bool:
    py_files = list(INTEGRATIONS_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(INTEGRATIONS_ROOT)) for f in py_files if has_active_import(f, "cus.general")]
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_no_active_legacy_all() -> bool:
    py_files = list(INTEGRATIONS_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(INTEGRATIONS_ROOT)) for f in py_files if has_active_import(f, "app.services")]
    if not violations:
        print_pass("Zero active app.services imports in integrations domain")
        return True
    for v in violations:
        print_fail(f"{v}", "Active import from app.services")
    return False


def check_no_docstring_legacy() -> bool:
    py_files = list(INTEGRATIONS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        try:
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if "app.services" in line:
                    stripped = line.strip()
                    if any(kw in stripped for kw in ["DISCONNECTED", "Was:", "Legacy import", "previously", "Previously"]):
                        continue
                    if stripped.startswith("#") and any(kw in stripped for kw in ["Stubbed", "stubbed", "DISCONNECTED", "Was:"]):
                        continue
                    if "app.services" in stripped and not (stripped.startswith("from ") or stripped.startswith("import ")):
                        violations.append(f"{py_file.relative_to(INTEGRATIONS_ROOT)}:{i}")
        except Exception:
            pass
    if not violations:
        print_pass("No stale app.services docstring references in integrations domain")
        return True
    for v in violations:
        print_fail(f"{v}", "Stale app.services reference")
    return False


def main():
    print("=" * 80)
    print("INTEGRATIONS DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []
    checks = [
        ("Check 1: File Counts", check_file_counts),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: New Files Exist", check_new_files_exist),
        ("Check 4: Rename Headers", check_rename_headers),
        ("Check 5: Header Correction", check_header_correction),
        ("Check 6: Legacy Disconnected", check_legacy_disconnected),
        ("Check 7: Import Path Fixes", check_import_fixes),
        ("Check 8: External Adapters Removed", check_external_adapters_removed),
        ("Check 9: No Legacy Imports", check_no_legacy),
        # Cleansing Cycle (PIN-503)
        ("Check 10: No Abolished general/ Imports", check_no_abolished_general),
        ("Check 11: Zero app.services (Full Domain)", check_no_active_legacy_all),
        ("Check 12: No Stale Docstring Legacy References", check_no_docstring_legacy),
    ]

    for label, fn in checks:
        print(label)
        print("-" * 80)
        results.append(fn())
        print()

    print("=" * 80)
    total_checks = sum(1 for _ in checks)
    if all(results):
        print(f"{GREEN}ALL CHECKS PASSED{RESET}")
        print("=" * 80)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"{RED}FAILED: {failed}/{total_checks} checks failed{RESET}")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
