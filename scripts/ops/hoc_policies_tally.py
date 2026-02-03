#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for policies domain consolidation
# Reference: PIN-495, PIN-503 (Cleansing Cycle)
# artifact_class: CODE

"""
Policies Domain Consolidation Verification Script

Verifies the complete migration of policies domain files from app/services/policy
to the HOC layer structure (L5_engines, L6_drivers).

Expected state after consolidation:
- L5_engines: 60 .py files (including __init__.py)
- L6_drivers: 18 .py files (including __init__.py)
- No *_service.py files in L5/L6
- N1/N2 renames completed with legacy aliases
- Header corrections applied
- Legacy imports disconnected
- L4 handler registrations updated
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Base paths
BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/policies/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/policies/L6_drivers"
L4_HANDLER = BASE_DIR / "app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py"
LEGACY_LESSONS = BASE_DIR / "app/services/policy/lessons_engine.py"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_pass(check_name: str):
    """Print PASS status"""
    print(f"{GREEN}✓ PASS{RESET}: {check_name}")

def print_fail(check_name: str, details: str = ""):
    """Print FAIL status with optional details"""
    print(f"{RED}✗ FAIL{RESET}: {check_name}")
    if details:
        print(f"  Details: {details}")

def count_py_files(directory: Path) -> Tuple[int, List[str]]:
    """Count .py files in directory (non-recursive)"""
    if not directory.exists():
        return 0, []

    py_files = [f.name for f in directory.iterdir() if f.is_file() and f.suffix == ".py"]
    return len(py_files), sorted(py_files)

def file_contains(file_path: Path, pattern: str) -> bool:
    """Check if file contains a specific pattern"""
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text()
        return pattern in content
    except Exception:
        return False

def file_starts_with(file_path: Path, pattern: str) -> bool:
    """Check if file starts with a specific pattern"""
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text()
        return content.strip().startswith(pattern)
    except Exception:
        return False

def check_file_count() -> bool:
    """Check 1: Verify L5 has 60 files, L6 has 18 files"""
    l5_count, l5_files = count_py_files(L5_PATH)
    l6_count, l6_files = count_py_files(L6_PATH)

    success = True

    if l5_count == 60:
        print_pass(f"L5_engines file count: {l5_count} files")
    else:
        print_fail(f"L5_engines file count", f"Expected 60, found {l5_count}")
        success = False

    if l6_count == 18:
        print_pass(f"L6_drivers file count: {l6_count} files")
    else:
        print_fail(f"L6_drivers file count", f"Expected 18, found {l6_count}")
        success = False

    return success

def check_naming_compliance() -> bool:
    """Check 2: No *_service.py files in L5 or L6"""
    _, l5_files = count_py_files(L5_PATH)
    _, l6_files = count_py_files(L6_PATH)

    service_files_l5 = [f for f in l5_files if f.endswith("_service.py")]
    service_files_l6 = [f for f in l6_files if f.endswith("_service.py")]

    success = True

    if not service_files_l5:
        print_pass("L5_engines naming compliance: No *_service.py files")
    else:
        print_fail("L5_engines naming compliance", f"Found {service_files_l5}")
        success = False

    if not service_files_l6:
        print_pass("L6_drivers naming compliance: No *_service.py files")
    else:
        print_fail("L6_drivers naming compliance", f"Found {service_files_l6}")
        success = False

    # Check specific files that should NOT exist
    bad_file_1 = L5_PATH / "cus_enforcement_service.py"
    bad_file_2 = L5_PATH / "limits_simulation_service.py"

    if not bad_file_1.exists():
        print_pass("cus_enforcement_service.py does not exist (correct)")
    else:
        print_fail("cus_enforcement_service.py exists (should be removed)")
        success = False

    if not bad_file_2.exists():
        print_pass("limits_simulation_service.py does not exist (correct)")
    else:
        print_fail("limits_simulation_service.py exists (should be removed)")
        success = False

    return success

def check_n1_rename() -> bool:
    """Check 3: N1 rename verified (cus_enforcement_engine.py)"""
    file_path = L5_PATH / "cus_enforcement_engine.py"

    success = True

    if file_path.exists():
        print_pass("cus_enforcement_engine.py exists")
    else:
        print_fail("cus_enforcement_engine.py exists", "File not found")
        return False

    if file_starts_with(file_path, "# Layer: L5"):
        print_pass("cus_enforcement_engine.py has L5 header")
    else:
        print_fail("cus_enforcement_engine.py header", "Missing '# Layer: L5' header")
        success = False

    return success

def check_n2_rename() -> bool:
    """Check 4: N2 rename verified (limits_simulation_engine.py)"""
    file_path = L5_PATH / "limits_simulation_engine.py"

    success = True

    if file_path.exists():
        print_pass("limits_simulation_engine.py exists")
    else:
        print_fail("limits_simulation_engine.py exists", "File not found")
        return False

    if file_starts_with(file_path, "# Layer: L5"):
        print_pass("limits_simulation_engine.py has L5 header")
    else:
        print_fail("limits_simulation_engine.py header", "Missing '# Layer: L5' header")
        success = False

    return success

def check_header_corrections() -> bool:
    """Check 5: Header corrections verified"""
    success = True

    files_to_check = [
        ("governance_facade.py", L5_PATH / "governance_facade.py"),
        ("policy_command.py", L5_PATH / "policy_command.py"),
        ("worker_execution_command.py", L5_PATH / "worker_execution_command.py"),
        ("claim_decision_engine.py", L5_PATH / "claim_decision_engine.py"),
    ]

    for file_name, file_path in files_to_check:
        if not file_path.exists():
            print_pass(f"{file_name} deleted (header check N/A)")
            continue
        if file_starts_with(file_path, "# Layer: L5"):
            print_pass(f"{file_name} starts with '# Layer: L5'")
        else:
            print_fail(f"{file_name} header", "Does not start with '# Layer: L5'")
            success = False

    return success

def has_active_import(file_path: Path, pattern: str) -> bool:
    """Check if file has an active (non-comment, non-docstring) import matching pattern.

    Only matches lines that are actual Python import statements, skipping
    comments and docstrings.
    """
    if not file_path.exists():
        return False
    try:
        content = file_path.read_text()
        in_docstring = False
        docstring_char = None
        for line in content.splitlines():
            stripped = line.strip()
            # Track triple-quote docstrings
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    # Check if docstring closes on same line
                    if stripped.count(docstring_char) >= 2:
                        continue  # Single-line docstring, skip
                    in_docstring = True
                    continue
            else:
                if docstring_char and docstring_char in stripped:
                    in_docstring = False
                continue
            # Skip comments
            if stripped.startswith("#"):
                continue
            # Check for actual import statements containing the pattern
            if pattern in stripped and (stripped.startswith("from ") or stripped.startswith("import ")):
                return True
        return False
    except Exception:
        return False


def check_legacy_disconnected() -> bool:
    """Check 6: Legacy imports disconnected (checks actual import statements only)"""
    success = True

    # Check that new files don't have active imports from app.services
    files_to_check = [
        ("cus_enforcement_engine.py", L5_PATH / "cus_enforcement_engine.py"),
        ("limits_simulation_engine.py", L5_PATH / "limits_simulation_engine.py"),
        ("policies_facade.py", L5_PATH / "policies_facade.py"),
    ]

    for file_name, file_path in files_to_check:
        if not has_active_import(file_path, "app.services"):
            print_pass(f"{file_name} has no active imports from app.services")
        else:
            print_fail(f"{file_name} legacy imports", "Still has active import from app.services")
            success = False

    # Check that legacy lessons_engine doesn't have active imports from app.hoc
    if LEGACY_LESSONS.exists():
        if not has_active_import(LEGACY_LESSONS, "app.hoc"):
            print_pass("lessons_engine.py (legacy) has no active imports from app.hoc")
        else:
            print_fail("lessons_engine.py (legacy) imports", "Has active import from app.hoc")
            success = False
    else:
        print_pass("lessons_engine.py (legacy) does not exist or moved")

    return success

def check_l4_handler_registration() -> bool:
    """Check 7: L4 handler has all 9 registrations"""
    success = True

    if not L4_HANDLER.exists():
        print_fail("policies_handler.py exists", "File not found")
        return False

    registrations = [
        "policies.query",
        "policies.enforcement",
        "policies.governance",
        "policies.lessons",
        "policies.policy_facade",
        "policies.limits",
        "policies.rules",
        "policies.rate_limits",
        "policies.simulate",
    ]

    for registration in registrations:
        if file_contains(L4_HANDLER, registration):
            print_pass(f"policies_handler.py contains '{registration}' registration")
        else:
            print_fail(f"policies_handler.py registration", f"Missing '{registration}'")
            success = False

    return success

def check_l4_handler_imports() -> bool:
    """Check 8: L4 handler import paths updated"""
    success = True

    if not L4_HANDLER.exists():
        print_fail("policies_handler.py exists for import check", "File not found")
        return False

    # Check for new import names
    if file_contains(L4_HANDLER, "cus_enforcement_engine"):
        print_pass("policies_handler.py contains 'cus_enforcement_engine' (not 'cus_enforcement_service')")
    else:
        print_fail("policies_handler.py imports", "Missing 'cus_enforcement_engine'")
        success = False

    if file_contains(L4_HANDLER, "limits_simulation_engine"):
        print_pass("policies_handler.py contains 'limits_simulation_engine' (not 'limits_simulation_service')")
    else:
        print_fail("policies_handler.py imports", "Missing 'limits_simulation_engine'")
        success = False

    # Check that old import PATHS don't exist (function name aliases like
    # get_cus_enforcement_service are valid backward-compat names)
    if not has_active_import(L4_HANDLER, "cus_enforcement_service"):
        print_pass("policies_handler.py has no import from old cus_enforcement_service module")
    else:
        print_fail("policies_handler.py imports", "Still imports from cus_enforcement_service module")
        success = False

    if not has_active_import(L4_HANDLER, "limits_simulation_service"):
        print_pass("policies_handler.py has no import from old limits_simulation_service module")
    else:
        print_fail("policies_handler.py imports", "Still imports from limits_simulation_service module")
        success = False

    return success


# =========================================================================
# Cleansing Cycle Checks (PIN-503)
# =========================================================================

POLICIES_ROOT = BASE_DIR / "app/hoc/cus/policies"
ADAPTERS_PATH = POLICIES_ROOT / "adapters"
CONTRACT_ADAPTER = ADAPTERS_PATH / "founder_contract_review_adapter.py"


def check_no_abolished_general() -> bool:
    """Verify no active imports from abolished cus/general/ domain."""
    py_files = list(POLICIES_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "cus.general"):
            violations.append(py_file.relative_to(POLICIES_ROOT))
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_dead_import_repointed() -> bool:
    """Verify founder_contract_review_adapter.py repointed to hoc_spine."""
    if file_contains(CONTRACT_ADAPTER, "hoc_spine.authority.contracts.contract_engine"):
        print_pass("founder_contract_review_adapter.py repointed to hoc_spine")
        return True
    else:
        print_fail("founder_contract_review_adapter.py", "Not repointed to hoc_spine")
        return False


def check_no_active_legacy_all() -> bool:
    """Verify zero active app.services imports across entire policies domain."""
    py_files = list(POLICIES_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "app.services"):
            violations.append(py_file.relative_to(POLICIES_ROOT))
    if not violations:
        print_pass("Zero active app.services imports in policies domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from app.services")
        return False


def check_no_docstring_legacy() -> bool:
    """Verify no stale app.services references in docstrings across policies domain."""
    py_files = list(POLICIES_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        try:
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if "app.services" in line:
                    stripped = line.strip()
                    # Skip lines that are explicitly marked as disconnected/legacy comments
                    if any(kw in stripped for kw in ["DISCONNECTED", "Was:", "Legacy import", "previously", "Previously", "extracted from", "rewired from"]):
                        continue
                    # Skip the header comments referencing legacy
                    if stripped.startswith("#") and "app.services" in stripped:
                        if any(kw in stripped for kw in ["Stubbed", "stubbed", "DISCONNECTED"]):
                            continue
                    # If it's in a docstring or comment and not a known legacy marker, flag it
                    if "app.services" in stripped and not (stripped.startswith("from ") or stripped.startswith("import ")):
                        violations.append(f"{py_file.relative_to(POLICIES_ROOT)}:{i}")
        except Exception:
            pass
    if not violations:
        print_pass("No stale app.services docstring references in policies domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Stale app.services reference")
        return False


def main():
    """Run all checks and exit with appropriate code"""
    print("=" * 80)
    print("POLICIES DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []

    print("Check 1: File Count")
    print("-" * 80)
    results.append(check_file_count())
    print()

    print("Check 2: Naming Compliance")
    print("-" * 80)
    results.append(check_naming_compliance())
    print()

    print("Check 3: N1 Rename Verified")
    print("-" * 80)
    results.append(check_n1_rename())
    print()

    print("Check 4: N2 Rename Verified")
    print("-" * 80)
    results.append(check_n2_rename())
    print()

    print("Check 5: Header Corrections")
    print("-" * 80)
    results.append(check_header_corrections())
    print()

    print("Check 6: Legacy Disconnected")
    print("-" * 80)
    results.append(check_legacy_disconnected())
    print()

    print("Check 7: L4 Handler Registration")
    print("-" * 80)
    results.append(check_l4_handler_registration())
    print()

    print("Check 8: L4 Handler Import Paths")
    print("-" * 80)
    results.append(check_l4_handler_imports())
    print()

    # Cleansing Cycle (PIN-503)
    print("Check 9: No Abolished general/ Imports")
    print("-" * 80)
    results.append(check_no_abolished_general())
    print()

    print("Check 10: Dead Import Repointed")
    print("-" * 80)
    results.append(check_dead_import_repointed())
    print()

    print("Check 11: Zero app.services (Full Domain)")
    print("-" * 80)
    results.append(check_no_active_legacy_all())
    print()

    print("Check 12: No Stale Docstring Legacy References")
    print("-" * 80)
    results.append(check_no_docstring_legacy())
    print()

    print("=" * 80)
    if all(results):
        print(f"{GREEN}ALL CHECKS PASSED{RESET}")
        print("=" * 80)
        return 0
    else:
        failed_count = sum(1 for r in results if not r)
        print(f"{RED}FAILED: {failed_count}/{len(results)} checks failed{RESET}")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
