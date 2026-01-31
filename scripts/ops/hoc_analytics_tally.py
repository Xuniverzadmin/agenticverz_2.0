#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for analytics domain consolidation
# Reference: PIN-497
# artifact_class: CODE

"""
Analytics Domain Consolidation Verification Script

Verifies:
- L5_engines: 21 .py files
- L6_drivers: 9 .py files
- No *_service.py files in L5/L6
- 18 renames completed with header notes
- 1 header correction applied
- 1 class rename (CostWriteService → CostWriteEngine + alias)
- Import path fix (detection_facade → cost_anomaly_detector_engine)
- No active legacy imports
"""

import sys
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path("/root/agenticverz2.0/backend")
L5_PATH = BASE_DIR / "app/hoc/cus/analytics/L5_engines"
L6_PATH = BASE_DIR / "app/hoc/cus/analytics/L6_drivers"
ANALYTICS_INIT = BASE_DIR / "app/hoc/cus/analytics/__init__.py"
DETECTION_FACADE = L5_PATH / "detection_facade.py"
COST_WRITE = L5_PATH / "cost_write_engine.py"

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
    l5_count, _ = count_py_files(L5_PATH)
    l6_count, _ = count_py_files(L6_PATH)
    success = True

    if l5_count == 21:
        print_pass(f"L5_engines file count: {l5_count}")
    else:
        print_fail("L5_engines file count", f"Expected 21, found {l5_count}")
        success = False

    if l6_count == 9:
        print_pass(f"L6_drivers file count: {l6_count}")
    else:
        print_fail("L6_drivers file count", f"Expected 9, found {l6_count}")
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
        (L5_PATH / "canary.py", "canary.py"),
        (L5_PATH / "config.py", "config.py"),
        (L5_PATH / "coordinator.py", "coordinator.py"),
        (L5_PATH / "cost_anomaly_detector.py", "cost_anomaly_detector.py"),
        (L5_PATH / "cost_snapshots.py", "cost_snapshots.py"),
        (L5_PATH / "costsim_models.py", "costsim_models.py"),
        (L5_PATH / "datasets.py", "datasets.py"),
        (L5_PATH / "divergence.py", "divergence.py"),
        (L5_PATH / "envelope.py", "envelope.py"),
        (L5_PATH / "metrics.py", "metrics.py"),
        (L5_PATH / "pattern_detection.py", "pattern_detection.py"),
        (L5_PATH / "prediction.py", "prediction.py"),
        (L5_PATH / "provenance.py", "provenance.py"),
        (L5_PATH / "s1_retry_backoff.py", "s1_retry_backoff.py"),
        (L5_PATH / "sandbox.py", "sandbox.py"),
        (L6_PATH / "audit_persistence.py", "audit_persistence.py"),
        (L6_PATH / "leader.py", "leader.py"),
        (L6_PATH / "provenance_async.py", "provenance_async.py"),
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
        (L5_PATH / "canary_engine.py", "canary_engine.py"),
        (L5_PATH / "config_engine.py", "config_engine.py"),
        (L5_PATH / "coordinator_engine.py", "coordinator_engine.py"),
        (L5_PATH / "cost_anomaly_detector_engine.py", "cost_anomaly_detector_engine.py"),
        (L5_PATH / "cost_snapshots_engine.py", "cost_snapshots_engine.py"),
        (L5_PATH / "costsim_models_engine.py", "costsim_models_engine.py"),
        (L5_PATH / "datasets_engine.py", "datasets_engine.py"),
        (L5_PATH / "divergence_engine.py", "divergence_engine.py"),
        (L5_PATH / "envelope_engine.py", "envelope_engine.py"),
        (L5_PATH / "metrics_engine.py", "metrics_engine.py"),
        (L5_PATH / "pattern_detection_engine.py", "pattern_detection_engine.py"),
        (L5_PATH / "prediction_engine.py", "prediction_engine.py"),
        (L5_PATH / "provenance_engine.py", "provenance_engine.py"),
        (L5_PATH / "s1_retry_backoff_engine.py", "s1_retry_backoff_engine.py"),
        (L5_PATH / "sandbox_engine.py", "sandbox_engine.py"),
        (L6_PATH / "coordination_audit_driver.py", "coordination_audit_driver.py"),
        (L6_PATH / "leader_driver.py", "leader_driver.py"),
        (L6_PATH / "provenance_driver.py", "provenance_driver.py"),
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
        (L5_PATH / "canary_engine.py", "Renamed canary.py"),
        (L5_PATH / "config_engine.py", "Renamed config.py"),
        (L5_PATH / "coordinator_engine.py", "Renamed coordinator.py"),
        (L5_PATH / "cost_anomaly_detector_engine.py", "Renamed cost_anomaly_detector.py"),
        (L5_PATH / "cost_snapshots_engine.py", "Renamed cost_snapshots.py"),
        (L5_PATH / "costsim_models_engine.py", "Renamed costsim_models.py"),
        (L5_PATH / "datasets_engine.py", "Renamed datasets.py"),
        (L5_PATH / "divergence_engine.py", "Renamed divergence.py"),
        (L5_PATH / "envelope_engine.py", "Renamed envelope.py"),
        (L5_PATH / "metrics_engine.py", "Renamed metrics.py"),
        (L5_PATH / "pattern_detection_engine.py", "Renamed pattern_detection.py"),
        (L5_PATH / "prediction_engine.py", "Renamed prediction.py"),
        (L5_PATH / "provenance_engine.py", "Renamed provenance.py"),
        (L5_PATH / "s1_retry_backoff_engine.py", "Renamed s1_retry_backoff.py"),
        (L5_PATH / "sandbox_engine.py", "Renamed sandbox.py"),
        (L6_PATH / "coordination_audit_driver.py", "Renamed audit_persistence.py"),
        (L6_PATH / "leader_driver.py", "Renamed leader.py"),
        (L6_PATH / "provenance_driver.py", "Renamed provenance_async.py"),
    ]
    for path, pattern in checks:
        if file_contains(path, pattern):
            print_pass(f"{path.name} has rename note")
        else:
            print_fail(f"{path.name} rename note", f"Missing '{pattern}'")
            success = False

    return success


def check_header_correction() -> bool:
    success = True
    if file_starts_with(ANALYTICS_INIT, "# Layer: L5"):
        print_pass("analytics/__init__.py starts with '# Layer: L5'")
    else:
        print_fail("analytics/__init__.py header", "Does not start with '# Layer: L5'")
        success = False
    return success


def check_class_rename() -> bool:
    success = True
    if file_contains(COST_WRITE, "class CostWriteEngine"):
        print_pass("cost_write_engine.py has class CostWriteEngine")
    else:
        print_fail("cost_write_engine.py class", "Missing 'class CostWriteEngine'")
        success = False

    if file_contains(COST_WRITE, "CostWriteService = CostWriteEngine"):
        print_pass("cost_write_engine.py has backward alias")
    else:
        print_fail("cost_write_engine.py alias", "Missing backward alias")
        success = False

    return success


def check_import_fix() -> bool:
    success = True
    if file_contains(DETECTION_FACADE, "cost_anomaly_detector_engine"):
        print_pass("detection_facade.py imports from cost_anomaly_detector_engine")
    else:
        print_fail("detection_facade.py import", "Missing cost_anomaly_detector_engine")
        success = False
    return success


def check_no_legacy() -> bool:
    success = True
    files_to_check = [
        L5_PATH / "analytics_facade.py",
        L5_PATH / "detection_facade.py",
        L5_PATH / "cost_write_engine.py",
        L5_PATH / "cost_model_engine.py",
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


ANALYTICS_ROOT = BASE_DIR / "app/hoc/cus/analytics"


def check_no_abolished_general() -> bool:
    """Verify no active imports from abolished cus/general/ domain."""
    py_files = list(ANALYTICS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "cus.general"):
            violations.append(str(py_file.relative_to(ANALYTICS_ROOT)))
    if not violations:
        print_pass("No active imports from abolished cus/general/")
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from abolished cus/general/")
    return not violations


def check_no_active_legacy_all() -> bool:
    """Verify zero active app.services imports across entire analytics domain."""
    py_files = list(ANALYTICS_ROOT.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "app.services"):
            violations.append(str(py_file.relative_to(ANALYTICS_ROOT)))
    if not violations:
        print_pass("Zero active app.services imports in analytics domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Active import from app.services")
        return False


def check_no_docstring_legacy() -> bool:
    """Verify no stale app.services references in docstrings across analytics domain."""
    py_files = list(ANALYTICS_ROOT.rglob("*.py"))
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
                        violations.append(f"{py_file.relative_to(ANALYTICS_ROOT)}:{i}")
        except Exception:
            pass
    if not violations:
        print_pass("No stale app.services docstring references in analytics domain")
        return True
    else:
        for v in violations:
            print_fail(f"{v}", "Stale app.services reference")
        return False


def main():
    print("=" * 80)
    print("ANALYTICS DOMAIN CONSOLIDATION VERIFICATION")
    print("=" * 80)
    print()

    results = []
    checks = [
        ("Check 1: File Count", check_file_count),
        ("Check 2: Naming Compliance", check_naming_compliance),
        ("Check 3: New Files Exist", check_new_files_exist),
        ("Check 4: Rename Headers", check_rename_headers),
        ("Check 5: Header Correction", check_header_correction),
        ("Check 6: Class Rename", check_class_rename),
        ("Check 7: Import Path Fix", check_import_fix),
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
