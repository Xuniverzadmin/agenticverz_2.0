#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Regenerates HOC_CUS_DOMAIN_AUDIT.csv from disk reality (V2.0.0 topology)
# artifact_class: CODE
"""
Scans the HOC filesystem and produces a clean HOC_CUS_DOMAIN_AUDIT.csv.

V2.0.0 topology:
  - No L1 frontend columns
  - No L3 adapters columns
  - L4 = hoc_spine only
  - L5 = combined L5_engines + L5_schemas + L5_controls + L5_lifecycle +
          L5_notifications + L5_support + L5_ui + L5_utils + L5_vault + L5_workflow
  - L6 = L6_drivers
  - L7 = app/models (assigned by import analysis from L6_drivers)

Usage:
    cd /root/agenticverz2.0/backend
    python3 ../scripts/ops/regenerate_hoc_audit_csv.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # /root/agenticverz2.0
BACKEND_ROOT = REPO_ROOT / "backend"

OUTPUT_CSV = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "hoc"
    / "HOC_CUS_DOMAIN_AUDIT.csv"
)

HOC_CUS = BACKEND_ROOT / "app" / "hoc" / "cus"
HOC_API_CUS = BACKEND_ROOT / "app" / "hoc" / "api" / "cus"
HOC_FACADES = BACKEND_ROOT / "app" / "hoc" / "api" / "facades" / "cus"
MODELS_DIR = BACKEND_ROOT / "app" / "models"

DOMAINS_V2 = [
    "hoc_spine",
    "overview",
    "activity",
    "incidents",
    "policies",
    "controls",
    "logs",
    "analytics",
    "integrations",
    "apis",
    "account",
    "agent",
    "api_keys",
    "docs",
    "ops",
]

EXCLUDE_DIRS = {"__pycache__", "_domain_map"}

# L5 sub-directories to scan (all counted as L5)
L5_PREFIXES = [
    "L5_engines",
    "L5_schemas",
    "L5_controls",
    "L5_lifecycle",
    "L5_notifications",
    "L5_support",
    "L5_ui",
    "L5_utils",
    "L5_vault",
    "L5_workflow",
]

CSV_COLUMNS = [
    "S No",
    "Domain",
    "L2.1 Count",
    "L2.1 File Names",
    "L2.1 File Paths",
    "L2 Count",
    "L2 File Names",
    "L2 File Paths",
    "L4 Count",
    "L4 File Names",
    "L4 File Paths",
    "L5 Count",
    "L5 File Names",
    "L5 File Paths",
    "L6 Count",
    "L6 File Names",
    "L6 File Paths",
    "L7 Count",
    "L7 File Names",
    "L7 File Paths",
    "Total Files",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scan_py_files(directory: Path) -> List[Path]:
    """Recursively collect .py files, excluding __init__.py and __pycache__."""
    if not directory.is_dir():
        return []
    results: List[Path] = []
    for root_str, dirs, files in os.walk(directory):
        # Prune __pycache__ from traversal
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if f.endswith(".py") and f != "__init__.py":
                results.append(Path(root_str) / f)
    return sorted(results)


def _rel_path(p: Path) -> str:
    """Return path relative to repo root, prefixed with 'backend/'."""
    try:
        return "backend/" + str(p.relative_to(BACKEND_ROOT))
    except ValueError:
        return str(p)


def _file_name(p: Path) -> str:
    return p.name


def _join_names(paths: List[Path]) -> str:
    return "\n".join(_file_name(p) for p in paths)


def _join_paths(paths: List[Path]) -> str:
    return "\n".join(_rel_path(p) for p in paths)


# ---------------------------------------------------------------------------
# Domain discovery
# ---------------------------------------------------------------------------


def discover_domains() -> List[str]:
    """Discover active domains from disk, ordered by DOMAINS_V2."""
    found: Set[str] = set()

    # From hoc/cus/ directories
    if HOC_CUS.is_dir():
        for entry in HOC_CUS.iterdir():
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
                found.add(entry.name)

    # From hoc/api/cus/ directories
    if HOC_API_CUS.is_dir():
        for entry in HOC_API_CUS.iterdir():
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
                found.add(entry.name)

    # Order by DOMAINS_V2, then anything not in the list alphabetically
    ordered = [d for d in DOMAINS_V2 if d in found]
    extra = sorted(found - set(DOMAINS_V2))
    return ordered + extra


# ---------------------------------------------------------------------------
# Layer scanners
# ---------------------------------------------------------------------------


def scan_l21_facade(domain: str) -> List[Path]:
    """L2.1 Facade: a single file per domain at facades/cus/{domain}.py."""
    facade_file = HOC_FACADES / f"{domain}.py"
    if facade_file.is_file():
        return [facade_file]
    return []


def scan_l2_api(domain: str) -> List[Path]:
    """L2 APIs: hoc/api/cus/{domain}/*.py recursively."""
    api_dir = HOC_API_CUS / domain
    return _scan_py_files(api_dir)


def scan_l4_spine() -> List[Path]:
    """L4 Spine: only for hoc_spine domain — full recursive scan."""
    return _scan_py_files(HOC_CUS / "hoc_spine")


def scan_l5(domain: str) -> List[Path]:
    """L5 combined: scan all L5_* sub-directories for the domain."""
    if domain == "hoc_spine":
        return []  # hoc_spine files go in L4, not L5
    all_files: List[Path] = []
    domain_dir = HOC_CUS / domain
    for prefix in L5_PREFIXES:
        sub = domain_dir / prefix
        all_files.extend(_scan_py_files(sub))
    return sorted(all_files)


def scan_l6(domain: str) -> List[Path]:
    """L6 Drivers: hoc/cus/{domain}/L6_drivers/ recursively."""
    if domain == "hoc_spine":
        return []  # hoc_spine files go in L4
    return _scan_py_files(HOC_CUS / domain / "L6_drivers")


# ---------------------------------------------------------------------------
# L7 model assignment
# ---------------------------------------------------------------------------

# Pattern to match: from app.models.foo import ... or from app.models import foo
_MODEL_IMPORT_RE = re.compile(
    r"^\s*from\s+app\.models\.(\w+)\s+import\s+",
    re.MULTILINE,
)
_MODEL_IMPORT_RE2 = re.compile(
    r"^\s*from\s+app\.models\s+import\s+",
    re.MULTILINE,
)


def _extract_model_imports(py_file: Path) -> Set[str]:
    """Extract model module names imported via `from app.models.X import ...`."""
    try:
        content = py_file.read_text(errors="replace")
    except OSError:
        return set()
    modules: Set[str] = set()
    for m in _MODEL_IMPORT_RE.finditer(content):
        modules.add(m.group(1))
    return modules


def assign_l7_models(domain_l6_files: Dict[str, List[Path]]) -> Dict[str, List[Path]]:
    """
    For each domain, inspect L6 driver files for `from app.models.X import ...`.
    Assign each model to the first domain alphabetically that imports it.
    Unassigned models go to "shared".

    Returns: domain -> list of model Paths
    """
    # Collect all model .py files
    all_model_files: Dict[str, Path] = {}
    if MODELS_DIR.is_dir():
        for f in sorted(MODELS_DIR.iterdir()):
            if f.is_file() and f.suffix == ".py" and f.name != "__init__.py":
                module_name = f.stem
                all_model_files[module_name] = f

    # Map: model_module -> set of domains importing it
    model_to_domains: Dict[str, Set[str]] = {m: set() for m in all_model_files}

    # Also scan hoc_spine (which has drivers/, services/, etc. that may import models)
    all_domain_files: Dict[str, List[Path]] = dict(domain_l6_files)
    # For hoc_spine, scan all .py files since its drivers live in various places
    spine_files = _scan_py_files(HOC_CUS / "hoc_spine")
    all_domain_files["hoc_spine"] = spine_files

    for domain, files in sorted(all_domain_files.items()):
        for py_file in files:
            imported_modules = _extract_model_imports(py_file)
            for mod in imported_modules:
                if mod in model_to_domains:
                    model_to_domains[mod].add(domain)

    # Assign each model to first domain alphabetically, or "shared" if no domain
    result: Dict[str, List[Path]] = {}
    for mod, domains in sorted(model_to_domains.items()):
        if not domains:
            target = "shared"
        else:
            target = sorted(domains)[0]
        result.setdefault(target, []).append(all_model_files[mod])

    # Sort each domain's list
    for k in result:
        result[k] = sorted(result[k])

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_rows() -> List[Dict[str, str]]:
    """Build one row per domain, plus a TOTAL row."""
    domains = discover_domains()

    # Pre-compute L6 files for model assignment
    domain_l6: Dict[str, List[Path]] = {}
    for d in domains:
        if d == "hoc_spine":
            continue
        files = scan_l6(d)
        if files:
            domain_l6[d] = files

    l7_assignment = assign_l7_models(domain_l6)

    # Add "shared" to domain list if it has models
    if "shared" in l7_assignment and "shared" not in domains:
        domains.append("shared")

    rows: List[Dict[str, str]] = []
    totals = {col: 0 for col in CSV_COLUMNS if col.endswith("Count") or col == "Total Files"}
    serial = 0

    for domain in domains:
        l21 = scan_l21_facade(domain)
        l2 = scan_l2_api(domain)
        l4 = scan_l4_spine() if domain == "hoc_spine" else []
        l5 = scan_l5(domain)
        l6 = scan_l6(domain)
        l7 = l7_assignment.get(domain, [])

        total = len(l21) + len(l2) + len(l4) + len(l5) + len(l6) + len(l7)
        if total == 0:
            continue  # Skip domains with 0 files

        serial += 1
        row = {
            "S No": str(serial),
            "Domain": domain,
            "L2.1 Count": str(len(l21)),
            "L2.1 File Names": _join_names(l21),
            "L2.1 File Paths": _join_paths(l21),
            "L2 Count": str(len(l2)),
            "L2 File Names": _join_names(l2),
            "L2 File Paths": _join_paths(l2),
            "L4 Count": str(len(l4)),
            "L4 File Names": _join_names(l4),
            "L4 File Paths": _join_paths(l4),
            "L5 Count": str(len(l5)),
            "L5 File Names": _join_names(l5),
            "L5 File Paths": _join_paths(l5),
            "L6 Count": str(len(l6)),
            "L6 File Names": _join_names(l6),
            "L6 File Paths": _join_paths(l6),
            "L7 Count": str(len(l7)),
            "L7 File Names": _join_names(l7),
            "L7 File Paths": _join_paths(l7),
            "Total Files": str(total),
        }
        rows.append(row)

        # Accumulate totals
        totals["L2.1 Count"] += len(l21)
        totals["L2 Count"] += len(l2)
        totals["L4 Count"] += len(l4)
        totals["L5 Count"] += len(l5)
        totals["L6 Count"] += len(l6)
        totals["L7 Count"] += len(l7)
        totals["Total Files"] += total

    # TOTAL row
    total_row = {col: "" for col in CSV_COLUMNS}
    total_row["S No"] = ""
    total_row["Domain"] = "TOTAL"
    for key, val in totals.items():
        total_row[key] = str(val)
    rows.append(total_row)

    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    """Write rows to CSV with proper quoting for multiline cells."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=CSV_COLUMNS,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: List[Dict[str, str]]) -> None:
    """Print a human-readable summary to stdout."""
    print(f"\n{'='*72}")
    print("HOC CUS DOMAIN AUDIT — V2.0.0 Topology")
    print(f"{'='*72}\n")

    header = f"{'#':>3}  {'Domain':<16} {'L2.1':>5} {'L2':>5} {'L4':>5} {'L5':>5} {'L6':>5} {'L7':>5} {'Total':>6}"
    print(header)
    print("-" * len(header))

    for row in rows:
        domain = row["Domain"]
        sno = row["S No"]
        if domain == "TOTAL":
            print("-" * len(header))
            sno = ""
        print(
            f"{sno:>3}  {domain:<16} "
            f"{row['L2.1 Count']:>5} "
            f"{row['L2 Count']:>5} "
            f"{row['L4 Count']:>5} "
            f"{row['L5 Count']:>5} "
            f"{row['L6 Count']:>5} "
            f"{row['L7 Count']:>5} "
            f"{row['Total Files']:>6}"
        )

    print(f"\nCSV written to: {OUTPUT_CSV}")


def main() -> None:
    # Verify we can find the backend root
    if not BACKEND_ROOT.is_dir():
        print(f"ERROR: Backend root not found at {BACKEND_ROOT}", file=sys.stderr)
        sys.exit(1)

    if not HOC_CUS.is_dir():
        print(f"ERROR: HOC cus directory not found at {HOC_CUS}", file=sys.stderr)
        sys.exit(1)

    rows = build_rows()
    write_csv(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()
