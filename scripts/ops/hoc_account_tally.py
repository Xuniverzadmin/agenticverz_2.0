#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for account domain consolidation
# Reference: PIN-500
# artifact_class: CODE

"""
Account Domain Consolidation Verification Script

Verifies:
- L5_engines: 10 .py files
- L5_schemas: 1 .py file
- L6_drivers: 4 .py files
- No *_service.py files in L5/L6
- 4 renames completed with header notes
- 1 relocation (crm_validator_engine) with note
- 1 header correction applied
- 1 import path fix
- L5_support/ removed
- No active legacy imports
"""

import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/account/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/account/L6_drivers"
SCHEMAS_PATH = BASE_DIR / "app/hoc/cus/account/L5_schemas"
ACCOUNT_INIT = BASE_DIR / "app/hoc/cus/account/__init__.py"
L5_SUPPORT = BASE_DIR / "app/hoc/cus/account/L5_support"

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
        ("L5_engines", L5_PATH, 10),
        ("L5_schemas", SCHEMAS_PATH, 1),
        ("L6_drivers", L6_PATH, 4),
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
        (L5_PATH / "billing_provider.py", "billing_provider.py"),
        (L5_PATH / "email_verification.py", "email_verification.py"),
        (L5_PATH / "identity_resolver.py", "identity_resolver.py"),
        (L5_PATH / "profile.py", "profile.py"),
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
        (L5_PATH / "billing_provider_engine.py", "billing_provider_engine.py"),
        (L5_PATH / "email_verification_engine.py", "email_verification_engine.py"),
        (L5_PATH / "identity_resolver_engine.py", "identity_resolver_engine.py"),
        (L5_PATH / "profile_engine.py", "profile_engine.py"),
        (L5_PATH / "crm_validator_engine.py", "crm_validator_engine.py (relocated)"),
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
        (L5_PATH / "billing_provider_engine.py", "Renamed billing_provider.py"),
        (L5_PATH / "email_verification_engine.py", "Renamed email_verification.py"),
        (L5_PATH / "identity_resolver_engine.py", "Renamed identity_resolver.py"),
        (L5_PATH / "profile_engine.py", "Renamed profile.py"),
        (L5_PATH / "crm_validator_engine.py", "Relocated from L5_support"),
    ]
    for path, pattern in checks:
        if file_contains(path, pattern):
            print_pass(f"{path.name} has note")
        else:
            print_fail(f"{path.name} note", f"Missing '{pattern}'")
            success = False
    return success


def check_header_correction() -> bool:
    if file_starts_with(ACCOUNT_INIT, "# Layer: L5"):
        print_pass("account/__init__.py starts with '# Layer: L5'")
        return True
    else:
        print_fail("account/__init__.py header", "Does not start with '# Layer: L5'")
        return False


def check_import_fix() -> bool:
    init = L5_PATH / "__init__.py"
    if file_contains(init, "email_verification_engine"):
        print_pass("L5_engines/__init__.py imports from email_verification_engine")
        return True
    else:
        print_fail("L5_engines/__init__.py import", "Missing email_verification_engine")
        return False


def check_l5_support_removed() -> bool:
    if not L5_SUPPORT.exists():
        print_pass("L5_support/ directory removed")
        return True
    else:
        print_fail("L5_support/", "Directory still exists")
        return False


def check_no_legacy() -> bool:
    success = True
    files_to_check = [
        L5_PATH / "accounts_facade.py",
        L5_PATH / "email_verification_engine.py",
        L5_PATH / "tenant_engine.py",
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


ACCOUNT_ROOT = BASE_DIR / "app/hoc/cus/account"


def check_no_abolished_general() -> bool:
    py_files = list(ACCOUNT_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(ACCOUNT_ROOT)) for f in py_files if has_active_import(f, "cus.general")]
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_no_active_legacy_all() -> bool:
    py_files = list(ACCOUNT_ROOT.rglob("*.py"))
    violations = [str(f.relative_to(ACCOUNT_ROOT)) for f in py_files if has_active_import(f, "app.services")]
    if not violations:
        print_pass("Zero active app.services imports in account domain")
        return True
    for v in violations:
        print_fail(f"{v}", "Active import from app.services")
    return False


def check_no_docstring_legacy() -> bool:
    py_files = list(ACCOUNT_ROOT.rglob("*.py"))
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
                        violations.append(f"{py_file.relative_to(ACCOUNT_ROOT)}:{i}")
        except Exception:
            pass
    if not violations:
        print_pass("No stale app.services docstring references in account domain")
        return True
    for v in violations:
        print_fail(f"{v}", "Stale app.services reference")
    return False


def main():
    print("=" * 80)
    print("ACCOUNT DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []
    checks = [
        ("Check 1: File Counts", check_file_counts),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: New Files Exist", check_new_files_exist),
        ("Check 4: Rename/Relocation Headers", check_rename_headers),
        ("Check 5: Header Correction", check_header_correction),
        ("Check 6: Import Path Fix", check_import_fix),
        ("Check 7: L5_support Removed", check_l5_support_removed),
        ("Check 8: No Legacy Imports", check_no_legacy),
        # Cleansing Cycle (PIN-503)
        ("Check 9: No Abolished general/ Imports", check_no_abolished_general),
        ("Check 10: Zero app.services (Full Domain)", check_no_active_legacy_all),
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
