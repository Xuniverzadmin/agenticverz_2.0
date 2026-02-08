#!/usr/bin/env python3
# Layer: L4 — Tooling
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Detect L5 entry modules not wired through L4 hoc_spine (orphans)
#       and L2 API files that import L5 directly (bypasses).
# Reference: DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md
# artifact_class: CODE

"""
L5 Spine Pairing Gap Detector

Scans L5_engines directories for entry modules (*_engine.py, *_facade.py,
*_bridge.py) and checks whether they are:
  - Wired via L4 (imported by hoc_spine handlers/coordinators/bridges)
  - Imported directly by L2 (bypass — gap)
  - Orphaned (no L4 or L2 reference)

Usage:
    python3 scripts/ops/l5_spine_pairing_gap_detector.py           # human summary
    python3 scripts/ops/l5_spine_pairing_gap_detector.py --json    # machine-readable
    python3 scripts/ops/l5_spine_pairing_gap_detector.py --freeze-baseline
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

BACKEND = Path(__file__).resolve().parent.parent.parent  # backend/
HOC_CUS = BACKEND / "app" / "hoc" / "cus"
HOC_SPINE = HOC_CUS / "hoc_spine"
L2_API = BACKEND / "app" / "hoc" / "api" / "cus"
BASELINE_PATH = (
    BACKEND.parent / "docs" / "architecture" / "hoc" / "L2_L4_L5_BASELINE.json"
)

# L4 directories to scan for imports of L5 entry modules
# Scan the entire hoc_spine tree (all subdirs are L4 scope)
L4_DIRS = [
    HOC_SPINE,
]

# Entry module suffixes (per plan definition)
ENTRY_SUFFIXES = ("_engine.py", "_facade.py", "_bridge.py")


def find_l5_entry_modules() -> list[dict]:
    """Find all L5 entry modules across cus domains."""
    entries = []
    if not HOC_CUS.exists():
        return entries

    for domain_dir in sorted(HOC_CUS.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name == "hoc_spine":
            continue  # L4 — not an L5 domain

        # Walk all L5_engines directories (including nested like account/auth/)
        for l5_dir in sorted(domain_dir.rglob("L5_engines")):
            if not l5_dir.is_dir():
                continue
            for py_file in sorted(l5_dir.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                if not any(py_file.name.endswith(s) for s in ENTRY_SUFFIXES):
                    continue

                stem = py_file.stem
                rel = py_file.relative_to(BACKEND)
                # Build the importable module path
                mod_path = str(rel).replace("/", ".").removesuffix(".py")
                # e.g. app.hoc.cus.policies.L5_engines.prevention_engine

                # Domain name (relative to HOC_CUS)
                domain_rel = l5_dir.parent.relative_to(HOC_CUS)
                domain = str(domain_rel)

                entries.append({
                    "stem": stem,
                    "domain": domain,
                    "file": str(rel),
                    "module": mod_path,
                })
    return entries


def _read_python_files(directory: Path) -> list[tuple[Path, str]]:
    """Read all .py files in a directory tree."""
    results = []
    if not directory.exists():
        return results
    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
            results.append((py_file, content))
        except Exception:
            pass
    return results


def _collect_import_lines(directory: Path) -> list[str]:
    """Extract only import/from lines from all .py files in directory tree."""
    lines = []
    for _, content in _read_python_files(directory):
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith(("from ", "import ")):
                lines.append(stripped)
    return lines


def check_l4_wiring(entries: list[dict]) -> dict[str, bool]:
    """Check which entries are imported by L4 hoc_spine."""
    l4_imports = []
    for d in L4_DIRS:
        l4_imports.extend(_collect_import_lines(d))
    l4_blob = "\n".join(l4_imports)

    wired = {}
    for entry in entries:
        stem = entry["stem"]
        # Match stem in actual import lines only
        pattern = rf"\b{re.escape(stem)}\b"
        wired[entry["module"]] = bool(re.search(pattern, l4_blob))
    return wired


def check_l2_direct(entries: list[dict]) -> dict[str, bool]:
    """Check which entries are imported directly by L2 API files."""
    l2_imports = _collect_import_lines(L2_API)
    l2_blob = "\n".join(l2_imports)

    direct = {}
    for entry in entries:
        stem = entry["stem"]
        # L2 directly importing L5 entry module
        pattern = rf"\bL5_engines\b.*\b{re.escape(stem)}\b"
        direct[entry["module"]] = bool(re.search(pattern, l2_blob))
    return direct


def classify(
    entries: list[dict],
    l4_wired: dict[str, bool],
    l2_direct: dict[str, bool],
) -> dict:
    """Classify each entry module."""
    wired = []
    direct_l2 = []
    orphaned = []

    for entry in entries:
        mod = entry["module"]
        is_l4 = l4_wired.get(mod, False)
        is_l2 = l2_direct.get(mod, False)

        if is_l4:
            wired.append(entry)
        elif is_l2:
            direct_l2.append(entry)
        else:
            orphaned.append(entry)

    return {
        "total_l5_engines": len(entries),
        "wired_via_l4": len(wired),
        "direct_l2_to_l5": len(direct_l2),
        "orphaned": len(orphaned),
        "wired_list": wired,
        "direct_l2_list": direct_l2,
        "orphaned_list": orphaned,
    }


def freeze_baseline(result: dict) -> None:
    """Write baseline JSON."""
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    baseline = {
        "frozen_at": __import__("datetime").datetime.now().isoformat(),
        "total_l5_engines": result["total_l5_engines"],
        "wired_via_l4": result["wired_via_l4"],
        "direct_l2_to_l5": result["direct_l2_to_l5"],
        "orphaned": result["orphaned"],
        "orphaned_modules": [e["module"] for e in result["orphaned_list"]],
        "direct_l2_modules": [e["module"] for e in result["direct_l2_list"]],
    }
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")
    print(f"Baseline frozen to {BASELINE_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="L5 Spine Pairing Gap Detector")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--freeze-baseline", action="store_true", help="Write baseline JSON"
    )
    args = parser.parse_args()

    entries = find_l5_entry_modules()
    l4_wired = check_l4_wiring(entries)
    l2_direct = check_l2_direct(entries)
    result = classify(entries, l4_wired, l2_direct)

    if args.freeze_baseline:
        freeze_baseline(result)
        return

    if args.json:
        output = {
            "total_l5_engines": result["total_l5_engines"],
            "wired_via_l4": result["wired_via_l4"],
            "direct_l2_to_l5": result["direct_l2_to_l5"],
            "orphaned": result["orphaned"],
            "orphaned_modules": [
                {"stem": e["stem"], "domain": e["domain"], "file": e["file"]}
                for e in result["orphaned_list"]
            ],
            "direct_l2_modules": [
                {"stem": e["stem"], "domain": e["domain"], "file": e["file"]}
                for e in result["direct_l2_list"]
            ],
        }
        print(json.dumps(output, indent=2))
        # Exit non-zero if gaps exist
        if result["direct_l2_to_l5"] > 0 or result["orphaned"] > 0:
            sys.exit(1)
    else:
        print("L5 Spine Pairing Gap Detector")
        print("=" * 50)
        print(f"Total L5 entry modules: {result['total_l5_engines']}")
        print(f"Wired via L4:           {result['wired_via_l4']}")
        print(f"Direct L2→L5 (gaps):    {result['direct_l2_to_l5']}")
        print(f"Orphaned:               {result['orphaned']}")

        if result["orphaned_list"]:
            print(f"\n--- Orphaned ({result['orphaned']}) ---")
            for e in result["orphaned_list"]:
                print(f"  [{e['domain']}] {e['stem']}  ({e['file']})")

        if result["direct_l2_list"]:
            print(f"\n--- Direct L2→L5 ({result['direct_l2_to_l5']}) ---")
            for e in result["direct_l2_list"]:
                print(f"  [{e['domain']}] {e['stem']}  ({e['file']})")

        if result["direct_l2_to_l5"] == 0 and result["orphaned"] == 0:
            print("\nCLEAN: All L5 entry modules are wired through L4.")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
