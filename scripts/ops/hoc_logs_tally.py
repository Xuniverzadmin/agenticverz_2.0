#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for logs domain consolidation
# Reference: PIN-496, PIN-503 (Cleansing Cycle)
# artifact_class: CODE

"""
Logs Domain Consolidation Verification Script

Verifies the complete consolidation of logs domain files:
- L5_engines: 18 .py files (including __init__.py)
- L6_drivers: 13 .py files (including __init__.py)
- No *_service.py files in L5/L6
- 8 renames completed with header notes
- 2 header corrections applied
- Import path fix applied (panel_response_assembler)
- No legacy imports (domain is clean)
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Base paths
BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/logs/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/logs/L6_drivers"
LOGS_INIT = BASE_DIR / "app/hoc/cus/logs/__init__.py"
SCHEMAS_INIT = BASE_DIR / "app/hoc/cus/logs/L5_schemas/__init__.py"
ASSEMBLER = L5_PATH / "panel_response_assembler.py"

# ANSI color codes
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


def check_file_count() -> bool:
    """Check 1: File counts"""
    l5_count, _ = count_py_files(L5_PATH)
    l6_count, _ = count_py_files(L6_PATH)
    success = True

    if l5_count == 18:
        print_pass(f"L5_engines file count: {l5_count}")
    else:
        print_fail("L5_engines file count", f"Expected 18, found {l5_count}")
        success = False

    if l6_count == 13:
        print_pass(f"L6_drivers file count: {l6_count}")
    else:
        print_fail("L6_drivers file count", f"Expected 13, found {l6_count}")
        success = False

    return success


def check_naming_compliance() -> bool:
    """Check 2: No *_service.py files in L5 or L6"""
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
        (L5_PATH / "audit_ledger_service.py", "audit_ledger_service.py (L5)"),
        (L6_PATH / "audit_ledger_service_async.py", "audit_ledger_service_async.py (L6)"),
        (L6_PATH / "capture.py", "capture.py (L6)"),
        (L6_PATH / "idempotency.py", "idempotency.py (L6)"),
        (L6_PATH / "integrity.py", "integrity.py (L6)"),
        (L6_PATH / "job_execution.py", "job_execution.py (L6)"),
        (L6_PATH / "panel_consistency_checker.py", "panel_consistency_checker.py (L6)"),
        (L6_PATH / "replay.py", "replay.py (L6)"),
    ]
    for old_path, label in old_files:
        if not old_path.exists():
            print_pass(f"{label} does not exist (correct)")
        else:
            print_fail(f"{label} still exists (should be renamed)")
            success = False

    return success


def check_new_files_exist() -> bool:
    """Check 3: New renamed files exist"""
    success = True
    new_files = [
        (L5_PATH / "audit_ledger_engine.py", "audit_ledger_engine.py (L5)"),
        (L6_PATH / "audit_ledger_driver.py", "audit_ledger_driver.py (L6)"),
        (L6_PATH / "capture_driver.py", "capture_driver.py (L6)"),
        (L6_PATH / "idempotency_driver.py", "idempotency_driver.py (L6)"),
        (L6_PATH / "integrity_driver.py", "integrity_driver.py (L6)"),
        (L6_PATH / "job_execution_driver.py", "job_execution_driver.py (L6)"),
        (L6_PATH / "panel_consistency_driver.py", "panel_consistency_driver.py (L6)"),
        (L6_PATH / "replay_driver.py", "replay_driver.py (L6)"),
    ]
    for path, label in new_files:
        if path.exists():
            print_pass(f"{label} exists")
        else:
            print_fail(f"{label} missing")
            success = False

    return success


def check_rename_headers() -> bool:
    """Check 4: Rename notes in headers"""
    success = True
    checks = [
        (L5_PATH / "audit_ledger_engine.py", "Renamed audit_ledger_service.py"),
        (L6_PATH / "audit_ledger_driver.py", "Renamed audit_ledger_service_async.py"),
        (L6_PATH / "capture_driver.py", "Renamed capture.py"),
        (L6_PATH / "idempotency_driver.py", "Renamed idempotency.py"),
        (L6_PATH / "integrity_driver.py", "Renamed integrity.py"),
        (L6_PATH / "job_execution_driver.py", "Renamed job_execution.py"),
        (L6_PATH / "panel_consistency_driver.py", "Renamed panel_consistency_checker.py"),
        (L6_PATH / "replay_driver.py", "Renamed replay.py"),
    ]
    for path, pattern in checks:
        if file_contains(path, pattern):
            print_pass(f"{path.name} header contains rename note")
        else:
            print_fail(f"{path.name} rename note", f"Missing '{pattern}'")
            success = False

    return success


def check_header_corrections() -> bool:
    """Check 5: Header corrections"""
    success = True

    if file_starts_with(LOGS_INIT, "# Layer: L5"):
        print_pass("logs/__init__.py starts with '# Layer: L5'")
    else:
        print_fail("logs/__init__.py header", "Does not start with '# Layer: L5'")
        success = False

    if file_starts_with(SCHEMAS_INIT, "# Layer: L5 — Domain Schemas"):
        print_pass("L5_schemas/__init__.py starts with '# Layer: L5 — Domain Schemas'")
    else:
        print_fail("L5_schemas/__init__.py header", "Does not start with '# Layer: L5 — Domain Schemas'")
        success = False

    return success


def check_import_fix() -> bool:
    """Check 6: Import path fix in panel_response_assembler.py"""
    success = True

    if file_contains(ASSEMBLER, "panel_consistency_driver"):
        print_pass("panel_response_assembler.py imports from panel_consistency_driver")
    else:
        print_fail("panel_response_assembler.py import", "Missing panel_consistency_driver import")
        success = False

    if not file_contains(ASSEMBLER, "panel_consistency_checker"):
        print_pass("panel_response_assembler.py no longer references panel_consistency_checker")
    else:
        print_fail("panel_response_assembler.py import", "Still references panel_consistency_checker")
        success = False

    return success


def check_no_legacy() -> bool:
    """Check 7: No legacy imports (domain should be clean)"""
    success = True

    # Spot-check key files for app.services imports
    files_to_check = [
        L5_PATH / "logs_facade.py",
        L5_PATH / "evidence_facade.py",
        L5_PATH / "evidence_report.py",
        L5_PATH / "pdf_renderer.py",
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

LOGS_ROOT = BASE_DIR / "app/hoc/cus/logs"


def check_no_abolished_general() -> bool:
    """Verify no active imports from abolished cus/general/ domain."""
    py_files = list(LOGS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "cus.general"):
            violations.append(py_file.relative_to(LOGS_ROOT))
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_no_active_legacy_all() -> bool:
    """Verify zero active app.services imports across entire logs domain."""
    py_files = list(LOGS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "app.services"):
            violations.append(py_file.relative_to(LOGS_ROOT))
    if not violations:
        print_pass("Zero active app.services imports in logs domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from app.services")
        return False


def check_trace_facade_repointed() -> bool:
    """Verify trace_facade.py audit models repointed to hoc_spine."""
    trace = L5_PATH / "trace_facade.py"
    if file_contains(trace, "hoc_spine.schemas.rac_models"):
        print_pass("trace_facade.py audit models repointed to hoc_spine")
        return True
    else:
        print_fail("trace_facade.py", "Not repointed to hoc_spine.schemas.rac_models")
        return False


def check_no_docstring_legacy() -> bool:
    """Verify no stale app.services references in docstrings across logs domain."""
    py_files = list(LOGS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        try:
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if "app.services" in line:
                    stripped = line.strip()
                    if any(kw in stripped for kw in ["DISCONNECTED", "Was:", "Legacy import", "previously", "Previously"]):
                        continue
                    if stripped.startswith("#") and any(kw in stripped for kw in ["Stubbed", "stubbed", "DISCONNECTED"]):
                        continue
                    if "app.services" in stripped and not (stripped.startswith("from ") or stripped.startswith("import ")):
                        violations.append(f"{py_file.relative_to(LOGS_ROOT)}:{i}")
        except Exception:
            pass
    if not violations:
        print_pass("No stale app.services docstring references in logs domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Stale app.services reference")
        return False


def main():
    print("=" * 80)
    print("LOGS DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []

    checks = [
        ("Check 1: File Count", check_file_count),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: New Files Exist", check_new_files_exist),
        ("Check 4: Rename Headers", check_rename_headers),
        ("Check 5: Header Corrections", check_header_corrections),
        ("Check 6: Import Path Fix", check_import_fix),
        ("Check 7: No Legacy Imports", check_no_legacy),
        # Cleansing Cycle (PIN-503)
        ("Check 8: No Abolished general/ Imports", check_no_abolished_general),
        ("Check 9: Zero app.services (Full Domain)", check_no_active_legacy_all),
        ("Check 10: Trace Facade Repointed", check_trace_facade_repointed),
        ("Check 11: No Stale Docstring Legacy References", check_no_docstring_legacy),
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
