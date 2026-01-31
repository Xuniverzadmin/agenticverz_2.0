#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for controls domain consolidation
# Reference: PIN-499, PIN-503 (Cleansing Cycle)
# artifact_class: CODE

"""
Controls Domain Consolidation Verification Script

Verifies:
- L5_engines: 11 .py files
- L5_schemas: 4 .py files
- L6_drivers: 10 .py files
- adapters: 2 .py files
- No *_service.py files in L5/L6
- 9 renames completed with header notes
- 2 relocations from L5_controls/ with notes
- L5_controls/ directory removed
- Import path fix (customer_killswitch_adapter.py)
- No active legacy imports
"""

import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/controls/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/controls/L6_drivers"
SCHEMAS_PATH = BASE_DIR / "app/hoc/cus/controls/L5_schemas"
ADAPTERS_PATH = BASE_DIR / "app/hoc/cus/controls/adapters"
CONTROLS_INIT = BASE_DIR / "app/hoc/cus/controls/__init__.py"
L5_CONTROLS_PATH = BASE_DIR / "app/hoc/cus/controls/L5_controls"
KILLSWITCH_ADAPTER = ADAPTERS_PATH / "customer_killswitch_adapter.py"

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
    for label, path, expected in [
        ("L5_engines", L5_PATH, 11),
        ("L5_schemas", SCHEMAS_PATH, 4),
        ("L6_drivers", L6_PATH, 10),
        ("adapters", ADAPTERS_PATH, 2),
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

    old_files = [
        (L5_PATH / "alert_fatigue.py", "alert_fatigue.py"),
        (L5_PATH / "cb_sync_wrapper.py", "cb_sync_wrapper.py"),
        (L5_PATH / "cost_safety_rails.py", "cost_safety_rails.py"),
        (L5_PATH / "decisions.py", "decisions.py"),
        (L5_PATH / "killswitch.py", "killswitch.py"),
        (L5_PATH / "s2_cost_smoothing.py", "s2_cost_smoothing.py"),
        (L6_PATH / "circuit_breaker.py", "circuit_breaker.py"),
        (L6_PATH / "circuit_breaker_async.py", "circuit_breaker_async.py"),
        (L6_PATH / "scoped_execution.py", "scoped_execution.py"),
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
        (L5_PATH / "alert_fatigue_engine.py", "alert_fatigue_engine.py"),
        (L5_PATH / "cb_sync_wrapper_engine.py", "cb_sync_wrapper_engine.py"),
        (L5_PATH / "cost_safety_rails_engine.py", "cost_safety_rails_engine.py"),
        (L5_PATH / "decisions_engine.py", "decisions_engine.py"),
        (L5_PATH / "killswitch_engine.py", "killswitch_engine.py"),
        (L5_PATH / "s2_cost_smoothing_engine.py", "s2_cost_smoothing_engine.py"),
        (L5_PATH / "customer_killswitch_read_engine.py", "customer_killswitch_read_engine.py (relocated)"),
        (L6_PATH / "circuit_breaker_driver.py", "circuit_breaker_driver.py"),
        (L6_PATH / "circuit_breaker_async_driver.py", "circuit_breaker_async_driver.py"),
        (L6_PATH / "scoped_execution_driver.py", "scoped_execution_driver.py"),
        (L6_PATH / "killswitch_read_driver.py", "killswitch_read_driver.py (relocated)"),
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
        (L5_PATH / "alert_fatigue_engine.py", "Renamed alert_fatigue.py"),
        (L5_PATH / "cb_sync_wrapper_engine.py", "Renamed cb_sync_wrapper.py"),
        (L5_PATH / "cost_safety_rails_engine.py", "Renamed cost_safety_rails.py"),
        (L5_PATH / "decisions_engine.py", "Renamed decisions.py"),
        (L5_PATH / "killswitch_engine.py", "Renamed killswitch.py"),
        (L5_PATH / "s2_cost_smoothing_engine.py", "Renamed s2_cost_smoothing.py"),
        (L6_PATH / "circuit_breaker_driver.py", "Renamed circuit_breaker.py"),
        (L6_PATH / "circuit_breaker_async_driver.py", "Renamed circuit_breaker_async.py"),
        (L6_PATH / "scoped_execution_driver.py", "Renamed scoped_execution.py"),
        (L5_PATH / "customer_killswitch_read_engine.py", "Relocated from L5_controls"),
        (L6_PATH / "killswitch_read_driver.py", "Relocated from L5_controls"),
    ]
    for path, pattern in checks:
        if file_contains(path, pattern):
            print_pass(f"{path.name} has note")
        else:
            print_fail(f"{path.name} note", f"Missing '{pattern}'")
            success = False
    return success


def check_header() -> bool:
    if file_starts_with(CONTROLS_INIT, "# Layer: L5"):
        print_pass("controls/__init__.py starts with '# Layer: L5'")
        return True
    else:
        print_fail("controls/__init__.py header", "Does not start with '# Layer: L5'")
        return False


def check_l5_controls_removed() -> bool:
    if not L5_CONTROLS_PATH.exists():
        print_pass("L5_controls/ directory removed")
        return True
    else:
        print_fail("L5_controls/", "Directory still exists")
        return False


def check_import_fix() -> bool:
    if file_contains(KILLSWITCH_ADAPTER, "controls.L5_engines.customer_killswitch_read_engine"):
        print_pass("customer_killswitch_adapter.py imports from L5_engines (not L5_controls)")
        return True
    else:
        print_fail("customer_killswitch_adapter.py import", "Missing L5_engines path")
        return False


def check_no_legacy() -> bool:
    success = True
    files_to_check = [
        L5_PATH / "controls_facade.py",
        L5_PATH / "alert_fatigue_engine.py",
        L5_PATH / "threshold_engine.py",
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


# =========================================================================
# Cleansing Cycle Checks (PIN-503)
# =========================================================================


def check_no_abolished_general() -> bool:
    """Verify no active imports from abolished cus/general/ domain."""
    success = True
    # Check all .py files in controls domain
    controls_root = BASE_DIR / "app/hoc/cus/controls"
    py_files = list(controls_root.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "cus.general"):
            violations.append(py_file.relative_to(controls_root))
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
        success = False
    return success


def check_dead_import_repointed() -> bool:
    """Verify customer_killswitch_adapter.py repointed to hoc_spine."""
    if file_contains(KILLSWITCH_ADAPTER, "hoc_spine.authority.guard_write_engine"):
        print_pass("customer_killswitch_adapter.py repointed to hoc_spine")
        return True
    else:
        print_fail("customer_killswitch_adapter.py", "Not repointed to hoc_spine")
        return False


def check_no_active_legacy_all() -> bool:
    """Verify zero active app.services imports across entire controls domain."""
    controls_root = BASE_DIR / "app/hoc/cus/controls"
    py_files = list(controls_root.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "app.services"):
            violations.append(py_file.relative_to(controls_root))
    if not violations:
        print_pass("Zero active app.services imports in controls domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from app.services")
        return False


def main():
    print("=" * 80)
    print("CONTROLS DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []
    checks = [
        ("Check 1: File Counts", check_file_counts),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: New Files Exist", check_new_files_exist),
        ("Check 4: Rename/Relocation Headers", check_rename_headers),
        ("Check 5: Header Correct", check_header),
        ("Check 6: L5_controls Removed", check_l5_controls_removed),
        ("Check 7: Import Path Fix", check_import_fix),
        ("Check 8: No Legacy Imports", check_no_legacy),
        # Cleansing Cycle (PIN-503)
        ("Check 9: No Abolished general/ Imports", check_no_abolished_general),
        ("Check 10: Dead Import Repointed", check_dead_import_repointed),
        ("Check 11: Zero app.services (Full Domain)", check_no_active_legacy_all),
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
