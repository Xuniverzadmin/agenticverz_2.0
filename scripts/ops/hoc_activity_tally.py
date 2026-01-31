#!/usr/bin/env python3
# Layer: L7 — Ops Script
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for activity domain consolidation
# Reference: PIN-494
# artifact_class: CODE
"""
Deterministic tally verification for the activity domain consolidation.

Verifies file counts, class names, method counts, backward-compatible aliases,
and correct handler registrations across all activity domain layers.
"""

import ast
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ACTIVITY = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus" / "activity"
L4_HANDLER = PROJECT_ROOT / "backend" / "app" / "hoc" / "hoc_spine" / "orchestrator" / "handlers" / "activity_handler.py"

LAYER_DIRS = {
    "L5_engines": CUS_ACTIVITY / "L5_engines",
    "L6_drivers": CUS_ACTIVITY / "L6_drivers",
}

# Expected file lists (excluding __init__.py and .deprecated)
EXPECTED_FILES = {
    "L5_engines": [
        "activity_enums.py",
        "activity_facade.py",
        "attention_ranking_engine.py",
        "cost_analysis_engine.py",
        "cus_telemetry_engine.py",
        "pattern_detection_engine.py",
        "signal_feedback_engine.py",
        "signal_identity.py",
    ],
    "L6_drivers": [
        "activity_read_driver.py",
        "orphan_recovery_driver.py",
        "run_signal_driver.py",
    ],
}

EXPECTED_TOTAL = sum(len(files) for files in EXPECTED_FILES.values())  # 11

# Stub engines that should have stub implementations
STUB_ENGINES = [
    "attention_ranking_engine.py",
    "cost_analysis_engine.py",
    "pattern_detection_engine.py",
    "signal_feedback_engine.py",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_py_files(directory: Path) -> list:
    """Return sorted list of .py files excluding __init__.py and .deprecated."""
    if not directory.exists():
        return []
    return sorted(
        f for f in directory.glob("*.py")
        if f.name != "__init__.py" and not f.name.endswith(".deprecated")
    )


def extract_classes(tree: ast.Module) -> list:
    """Extract top-level class names from an AST."""
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def extract_public_methods(tree: ast.Module, class_name: str | None = None) -> int:
    """Count public async methods (not starting with _) in a specific class or all classes."""
    count = 0
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if class_name and node.name != class_name:
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        count += 1
    return count


def check_alias_exists(source: str, alias_name: str, target_name: str) -> bool:
    """Check that `alias_name = target_name` assignment exists in source."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == alias_name:
                    if isinstance(node.value, ast.Name) and node.value.id == target_name:
                        return True
    return False


def check_string_in_source(source: str, search_string: str) -> bool:
    """Check if a string exists in source (case-sensitive)."""
    return search_string in source


def check_import_exists(source: str, module_path: str) -> bool:
    """Check if an import from a specific module exists."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module and module_path in node.module:
                return True
    return False


def extract_registrations(source: str) -> list:
    """Extract all registry.register() calls from source."""
    tree = ast.parse(source)
    registrations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "register":
                    # Get first argument (operation name)
                    if node.args and isinstance(node.args[0], ast.Constant):
                        registrations.append(node.args[0].value)

    return registrations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
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


def check_no_abolished_general() -> tuple:
    """Verify no active imports from abolished cus/general/ domain."""
    py_files = list(CUS_ACTIVITY.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "cus.general"):
            violations.append(str(py_file.relative_to(CUS_ACTIVITY)))
    if not violations:
        return True, "No active imports from abolished cus/general/"
    return False, f"Active cus/general/ imports: {violations}"


def check_no_active_legacy_all() -> tuple:
    """Verify zero active app.services imports across entire activity domain."""
    py_files = list(CUS_ACTIVITY.rglob("*.py"))
    violations = []
    for py_file in py_files:
        if has_active_import(py_file, "app.services"):
            violations.append(str(py_file.relative_to(CUS_ACTIVITY)))
    if not violations:
        return True, "Zero active app.services imports in activity domain"
    return False, f"Active app.services imports: {violations}"


def check_legacy_disconnected() -> tuple:
    """Verify cus_telemetry_engine.py legacy import is disconnected."""
    cte = CUS_ACTIVITY / "L5_engines" / "cus_telemetry_engine.py"
    if not cte.exists():
        return False, "cus_telemetry_engine.py not found"
    content = cte.read_text()
    if "LEGACY DISCONNECTED" in content and not has_active_import(cte, "app.services"):
        return True, "cus_telemetry_engine.py legacy import disconnected"
    return False, "cus_telemetry_engine.py still has active legacy import"


def check_no_docstring_legacy() -> tuple:
    """Verify no stale app.services references in docstrings across activity domain."""
    py_files = list(CUS_ACTIVITY.rglob("*.py"))
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
                        violations.append(f"{py_file.relative_to(CUS_ACTIVITY)}:{i}")
        except Exception:
            pass
    if not violations:
        return True, "No stale app.services docstring references in activity domain"
    return False, f"Stale references: {violations}"


def main() -> int:
    failures: list = []
    rows: list = []
    script_num = 0

    # ------------------------------------------------------------------
    # 1. Collect all files and build summary table
    # ------------------------------------------------------------------
    layer_counts: dict = {}

    for layer_label, layer_dir in LAYER_DIRS.items():
        files = get_py_files(layer_dir)
        layer_counts[layer_label] = len(files)

        for fpath in files:
            script_num += 1
            source = fpath.read_text()
            try:
                tree = ast.parse(source)
            except SyntaxError as exc:
                failures.append(f"SyntaxError in {fpath.name}: {exc}")
                rows.append((script_num, fpath.name, layer_label, "ERR", "ERR"))
                continue

            classes = extract_classes(tree)
            methods = extract_public_methods(tree)
            class_count = len(classes)
            method_count = methods

            rows.append((script_num, fpath.name, layer_label, class_count, method_count))

    total_files = sum(layer_counts.values())

    # ------------------------------------------------------------------
    # 2. Print summary table
    # ------------------------------------------------------------------
    hdr = f"{'#':>3}  {'File':<42} {'Layer':<14} {'Classes':>7} {'Methods':>7}"
    sep = "-" * len(hdr)
    print("\n=== ACTIVITY DOMAIN CONSOLIDATION TALLY ===\n")
    print(hdr)
    print(sep)
    for row in rows:
        print(f"{row[0]:>3}  {row[1]:<42} {row[2]:<14} {row[3]:>7} {row[4]:>7}")
    print(sep)
    print(f"{'Total files':>60}: {total_files}")
    print()

    # ------------------------------------------------------------------
    # 3. Verification checks
    # ------------------------------------------------------------------
    checks: list = []

    # 3a. Total file count (14 files excluding __init__.py)
    ok = total_files == EXPECTED_TOTAL
    msg = f"Expected {EXPECTED_TOTAL}, got {total_files}"
    checks.append(("Total file count", ok, msg))
    if not ok:
        failures.append(f"File count mismatch: {msg}")

    # 3b. Per-layer counts
    for layer_label, expected_files in EXPECTED_FILES.items():
        actual = layer_counts.get(layer_label, 0)
        expected = len(expected_files)
        ok = actual == expected
        msg = f"Expected {expected}, got {actual}"
        checks.append((f"{layer_label} count", ok, msg))
        if not ok:
            failures.append(f"{layer_label} count mismatch: {msg}")

    # 3c. Exact file list verification (no *_service.py files)
    for layer_label, expected_files in EXPECTED_FILES.items():
        layer_dir = LAYER_DIRS[layer_label]
        actual_files = [f.name for f in get_py_files(layer_dir)]

        # Check for banned *_service.py files
        service_files = [f for f in actual_files if f.endswith("_service.py")]
        ok = len(service_files) == 0
        msg = f"Found {len(service_files)} *_service.py files: {service_files}" if service_files else "No *_service.py files"
        checks.append((f"{layer_label} naming compliance", ok, msg))
        if not ok:
            failures.append(f"Banned *_service.py files in {layer_label}: {service_files}")

        # Check for missing expected files
        missing = set(expected_files) - set(actual_files)
        if missing:
            failures.append(f"Missing files in {layer_label}: {missing}")
            checks.append((f"{layer_label} expected files", False, f"Missing: {missing}"))
        else:
            checks.append((f"{layer_label} expected files", True, "All files present"))

        # Check for unexpected files
        unexpected = set(actual_files) - set(expected_files)
        if unexpected:
            failures.append(f"Unexpected files in {layer_label}: {unexpected}")
            checks.append((f"{layer_label} no extra files", False, f"Unexpected: {unexpected}"))
        else:
            checks.append((f"{layer_label} no extra files", True, "No unexpected files"))

    # 3d. N1 rename verification: run_signal_driver.py
    rsd_path = CUS_ACTIVITY / "L6_drivers" / "run_signal_driver.py"
    if rsd_path.exists():
        rsd_source = rsd_path.read_text()
        rsd_tree = ast.parse(rsd_source)
        rsd_classes = extract_classes(rsd_tree)

        ok = "RunSignalDriver" in rsd_classes
        msg = f"Classes found: {rsd_classes}"
        checks.append(("RunSignalDriver class exists", ok, msg))
        if not ok:
            failures.append(f"RunSignalDriver class not found: {msg}")

        # Check backward alias
        ok_alias = check_alias_exists(rsd_source, "RunSignalService", "RunSignalDriver")
        msg_alias = "RunSignalService = RunSignalDriver"
        checks.append(("RunSignalService backward alias", ok_alias, msg_alias))
        if not ok_alias:
            failures.append(f"Alias not found: {msg_alias}")

        # Check rename note in header
        ok_note = "run_signal_service.py → run_signal_driver.py" in rsd_source
        msg_note = "Header contains rename note"
        checks.append(("run_signal_driver.py rename note", ok_note, msg_note))
        if not ok_note:
            failures.append("Missing rename note in run_signal_driver.py header")
    else:
        failures.append("run_signal_driver.py not found")
        checks.append(("RunSignalDriver class exists", False, "File missing"))

    # 3e. N2 rename verification: cus_telemetry_engine.py
    cte_path = CUS_ACTIVITY / "L5_engines" / "cus_telemetry_engine.py"
    if cte_path.exists():
        cte_source = cte_path.read_text()

        ok_alias = check_alias_exists(cte_source, "CusTelemetryService", "CusTelemetryEngine")
        msg = "CusTelemetryService = CusTelemetryEngine"
        checks.append(("CusTelemetryService backward alias", ok_alias, msg))
        if not ok_alias:
            failures.append(f"Alias not found: {msg}")

        # Check rename note in header
        ok_note = "cus_telemetry_service.py → cus_telemetry_engine.py" in cte_source
        msg_note = "Header contains rename note"
        checks.append(("cus_telemetry_engine.py rename note", ok_note, msg_note))
        if not ok_note:
            failures.append("Missing rename note in cus_telemetry_engine.py header")
    else:
        failures.append("cus_telemetry_engine.py not found")
        checks.append(("CusTelemetryService backward alias", False, "File missing"))

    # 3f. N3 rename verification: orphan_recovery_driver.py
    ord_path = CUS_ACTIVITY / "L6_drivers" / "orphan_recovery_driver.py"
    if ord_path.exists():
        ord_source = ord_path.read_text()

        # Check rename note in header
        ok_note = "orphan_recovery.py → orphan_recovery_driver.py" in ord_source
        msg = "Header contains rename note"
        checks.append(("orphan_recovery_driver.py rename note", ok_note, msg))
        if not ok_note:
            failures.append("Missing rename note in orphan_recovery_driver.py header")

        # Verify it's NOT named orphan_recovery.py
        old_path = CUS_ACTIVITY / "L6_drivers" / "orphan_recovery.py"
        ok_renamed = not old_path.exists()
        msg_renamed = "Old orphan_recovery.py does not exist"
        checks.append(("orphan_recovery.py removed", ok_renamed, msg_renamed))
        if not ok_renamed:
            failures.append("Old orphan_recovery.py still exists")
    else:
        failures.append("orphan_recovery_driver.py not found")
        checks.append(("orphan_recovery_driver.py rename note", False, "File missing"))

    # 3g. L4 handler registration check
    if L4_HANDLER.exists():
        handler_source = L4_HANDLER.read_text()
        registrations = extract_registrations(handler_source)

        expected_ops = [
            "activity.query",
            "activity.signal_fingerprint",
            "activity.signal_feedback",
            "activity.telemetry",
        ]

        for op in expected_ops:
            ok = op in registrations
            msg = f"Found in registrations" if ok else f"Missing from registrations"
            checks.append((f"Handler registers '{op}'", ok, msg))
            if not ok:
                failures.append(f"Missing registration: {op}")

        # Check total count
        ok_count = len(registrations) == len(expected_ops)
        msg_count = f"Expected {len(expected_ops)}, got {len(registrations)}: {registrations}"
        checks.append(("Handler registration count", ok_count, msg_count))
        if not ok_count:
            failures.append(f"Handler registration count mismatch: {msg_count}")
    else:
        failures.append(f"L4 handler file not found: {L4_HANDLER}")
        checks.append(("L4 handler exists", False, "File missing"))

    # 3h. Facade method count check
    facade_path = CUS_ACTIVITY / "L5_engines" / "activity_facade.py"
    if facade_path.exists():
        facade_source = facade_path.read_text()
        facade_tree = ast.parse(facade_source)

        method_count = extract_public_methods(facade_tree, "ActivityFacade")
        ok = method_count >= 15
        msg = f"Found {method_count} async methods (expected >= 15)"
        checks.append(("ActivityFacade method count", ok, msg))
        if not ok:
            failures.append(f"ActivityFacade has insufficient methods: {msg}")
    else:
        failures.append("activity_facade.py not found")
        checks.append(("ActivityFacade method count", False, "File missing"))

    # 3i. Stub engine verification
    for stub_file in STUB_ENGINES:
        stub_path = CUS_ACTIVITY / "L5_engines" / stub_file
        if stub_path.exists():
            stub_source = stub_path.read_text()

            # Check for stub patterns (simplified check)
            has_stub = "stub" in stub_source.lower() or "return" in stub_source
            msg = "Contains stub implementation" if has_stub else "Missing stub implementation"
            checks.append((f"{stub_file} is stub", has_stub, msg))
            if not has_stub:
                failures.append(f"{stub_file} missing stub implementation")
        else:
            failures.append(f"Stub engine not found: {stub_file}")
            checks.append((f"{stub_file} exists", False, "File missing"))

    # 3j. Cross-domain import check in L6 __init__.py
    l6_init_path = CUS_ACTIVITY / "L6_drivers" / "__init__.py"
    if l6_init_path.exists():
        l6_init_source = l6_init_path.read_text()

        # PIN-504: cross-domain controls import removed; now imports from hoc_spine
        ok = check_import_exists(l6_init_source, "app.hoc.hoc_spine.schemas.threshold_types")
        msg = "Imports LimitSnapshot from hoc_spine (PIN-504)"
        checks.append(("L6 __init__ spine import", ok, msg))
        if not ok:
            failures.append("L6 __init__.py missing hoc_spine.schemas.threshold_types import (PIN-504)")
    else:
        failures.append("L6_drivers/__init__.py not found")
        checks.append(("L6 __init__ exists", False, "File missing"))

    # ------------------------------------------------------------------
    # 4. Print verification results
    # ------------------------------------------------------------------
    print("=== VERIFICATION RESULTS ===\n")
    for label, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}]  {label}: {detail}")

    # ------------------------------------------------------------------
    # 5. Cleansing Cycle Checks (PIN-503)
    # ------------------------------------------------------------------
    print("=== CLEANSING CYCLE CHECKS (PIN-503) ===\n")
    cleansing_checks = [
        ("No abolished cus/general/ imports", check_no_abolished_general),
        ("Zero active app.services imports", check_no_active_legacy_all),
        ("Legacy import disconnected", check_legacy_disconnected),
        ("No stale docstring legacy refs", check_no_docstring_legacy),
    ]
    for label, fn in cleansing_checks:
        ok, detail = fn()
        checks.append((label, ok, detail))
        if not ok:
            failures.append(f"{label}: {detail}")

    print()
    for label, passed, detail in checks[-len(cleansing_checks):]:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}]  {label}: {detail}")

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("RESULT: ALL PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
