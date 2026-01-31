#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Deterministic tally verification for incidents domain consolidation
# artifact_class: CODE
"""
Deterministic tally verification for the incidents domain consolidation.

Verifies file counts, class names, method counts, backward-compatible aliases,
and correct API usage across all incidents domain layers.
"""

import ast
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_INCIDENTS = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus" / "incidents"
L2_API = PROJECT_ROOT / "backend" / "app" / "hoc" / "api" / "cus" / "incidents" / "incidents.py"

LAYER_DIRS = {
    "L5_engines": CUS_INCIDENTS / "L5_engines",
    "L6_drivers": CUS_INCIDENTS / "L6_drivers",
    "L3_adapters": CUS_INCIDENTS / "adapters",
    "L5_schemas": CUS_INCIDENTS / "L5_schemas",
}

# Expected counts per layer (non-__init__.py .py files)
EXPECTED_COUNTS = {
    "L5_engines": 17,
    "L6_drivers": 11,
    "L3_adapters": 2,
}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())  # 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_py_files(directory: Path) -> list:
    """Return sorted list of .py files excluding __init__.py."""
    if not directory.exists():
        return []
    return sorted(f for f in directory.glob("*.py") if f.name != "__init__.py")


def extract_classes(tree: ast.Module) -> list:
    """Extract top-level class names from an AST."""
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def extract_public_methods(tree: ast.Module) -> int:
    """Count public methods (not starting with _) across all classes."""
    count = 0
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        count += 1
    return count


def extract_top_level_functions(tree: ast.Module) -> list:
    """Extract top-level function names."""
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
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
            top_funcs = extract_top_level_functions(tree)
            class_count = len(classes)
            method_count = methods if classes else len(top_funcs)

            rows.append((script_num, fpath.name, layer_label, class_count, method_count))

    total_files = sum(layer_counts.values())

    # ------------------------------------------------------------------
    # 2. Print summary table
    # ------------------------------------------------------------------
    hdr = f"{'#':>3}  {'File':<42} {'Layer':<14} {'Classes':>7} {'Methods':>7}"
    sep = "-" * len(hdr)
    print("\n=== INCIDENTS DOMAIN CONSOLIDATION TALLY ===\n")
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

    # 3a. Total file count
    ok = total_files == EXPECTED_TOTAL
    msg = f"Expected {EXPECTED_TOTAL}, got {total_files}"
    checks.append(("Total file count", ok, msg))
    if not ok:
        failures.append(f"File count mismatch: {msg}")

    # 3b. Per-layer counts
    for layer_label, expected in EXPECTED_COUNTS.items():
        actual = layer_counts.get(layer_label, 0)
        ok = actual == expected
        msg = f"Expected {expected}, got {actual}"
        checks.append((f"{layer_label} count", ok, msg))
        if not ok:
            failures.append(f"{layer_label} count mismatch: {msg}")

    # 3c. ExportBundleDriver class exists (not ExportBundleService as primary)
    ebd_path = CUS_INCIDENTS / "L6_drivers" / "export_bundle_driver.py"
    ebd_source = ""
    if ebd_path.exists():
        ebd_source = ebd_path.read_text()
        ebd_tree = ast.parse(ebd_source)
        ebd_classes = extract_classes(ebd_tree)
        ok = "ExportBundleDriver" in ebd_classes
        msg = f"Classes found: {ebd_classes}"
        checks.append(("ExportBundleDriver class exists", ok, msg))
        if not ok:
            failures.append(f"ExportBundleDriver not found: {msg}")

        ok2 = "ExportBundleService" not in ebd_classes
        msg2 = f"ExportBundleService should be alias, not class. Classes: {ebd_classes}"
        checks.append(("ExportBundleService is NOT a class", ok2, msg2))
        if not ok2:
            failures.append(msg2)
    else:
        failures.append("export_bundle_driver.py not found")
        checks.append(("ExportBundleDriver class exists", False, "File missing"))
        checks.append(("ExportBundleService is NOT a class", False, "File missing"))

    # 3d. Backward-compatible alias ExportBundleService = ExportBundleDriver
    if ebd_path.exists() and ebd_source:
        ok = check_alias_exists(ebd_source, "ExportBundleService", "ExportBundleDriver")
        msg = "ExportBundleService = ExportBundleDriver"
        checks.append(("Backward-compatible alias", ok, msg))
        if not ok:
            failures.append(f"Alias not found: {msg}")

    # 3e. L2 API uses get_export_bundle_driver (not get_export_bundle_service)
    if L2_API.exists():
        api_source = L2_API.read_text()
        uses_driver = "get_export_bundle_driver" in api_source
        checks.append(("L2 API imports get_export_bundle_driver", uses_driver, str(L2_API.name)))
        if not uses_driver:
            failures.append("L2 API does not use get_export_bundle_driver")

        # Ensure no direct use of get_export_bundle_service (outside comments)
        lines = api_source.splitlines()
        service_refs = [
            ln for ln in lines
            if "get_export_bundle_service" in ln and not ln.strip().startswith("#")
        ]
        ok = len(service_refs) == 0
        msg = f"Found {len(service_refs)} non-comment refs to get_export_bundle_service"
        checks.append(("L2 API does NOT use get_export_bundle_service", ok, msg))
        if not ok:
            failures.append(msg)
    else:
        failures.append(f"L2 API file not found: {L2_API}")
        checks.append(("L2 API imports get_export_bundle_driver", False, "File missing"))
        checks.append(("L2 API does NOT use get_export_bundle_service", False, "File missing"))

    # ------------------------------------------------------------------
    # 4. Cleansing Cycle Checks (PIN-503)
    # ------------------------------------------------------------------
    def _has_active_import(file_path: Path, pattern: str) -> bool:
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

    # No abolished cus/general/ imports
    py_all = list(CUS_INCIDENTS.rglob("*.py"))
    general_violations = [str(f.relative_to(CUS_INCIDENTS)) for f in py_all if _has_active_import(f, "cus.general")]
    ok = not general_violations
    msg = "No active imports from abolished cus/general/" if ok else f"Violations: {general_violations}"
    checks.append(("No abolished cus/general/ imports", ok, msg))
    if not ok:
        failures.append(msg)

    # Zero active app.services imports
    legacy_violations = [str(f.relative_to(CUS_INCIDENTS)) for f in py_all if _has_active_import(f, "app.services")]
    ok = not legacy_violations
    msg = "Zero active app.services imports in incidents domain" if ok else f"Violations: {legacy_violations}"
    checks.append(("Zero active app.services imports", ok, msg))
    if not ok:
        failures.append(msg)

    # No stale docstring legacy refs
    doc_violations = []
    for py_file in py_all:
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
                        doc_violations.append(f"{py_file.relative_to(CUS_INCIDENTS)}:{i}")
        except Exception:
            pass
    ok = not doc_violations
    msg = "No stale app.services docstring references" if ok else f"Violations: {doc_violations}"
    checks.append(("No stale docstring legacy refs", ok, msg))
    if not ok:
        failures.append(msg)

    # ------------------------------------------------------------------
    # 5. Print verification results
    # ------------------------------------------------------------------
    print("=== VERIFICATION RESULTS ===\n")
    for label, passed, detail in checks:
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
