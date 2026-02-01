#!/usr/bin/env python3
# Layer: L0 — Operations Script
# AUDIENCE: INTERNAL
# Role: Detect and auto-remove tombstone files with zero dependents
# Reference: PIN-509 Gap 3 — Tombstone auto-collapse

"""
Tombstone Auto-Collapse (PIN-509 Gap 3)

Scans HOC tree for files with TOMBSTONE markers.
For each tombstone, checks if any other file imports from it.
If zero dependents → deletes the file and reports.

Usage:
    python3 scripts/ops/collapse_tombstones.py          # dry-run (report only)
    python3 scripts/ops/collapse_tombstones.py --apply   # delete zero-dependent tombstones
"""

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
APP_ROOT = BACKEND_ROOT / "app"
HOC_ROOT = APP_ROOT / "hoc"


def find_tombstones() -> list[Path]:
    """Find all files with TOMBSTONE + re-export markers."""
    tombstones = []
    for py_file in HOC_ROOT.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "TOMBSTONE" in source and ("re-export" in source.lower() or "re_export" in source.lower()):
            tombstones.append(py_file)
    return tombstones


def count_dependents(tombstone: Path) -> int:
    """Count how many files import from this tombstone module."""
    try:
        rel = tombstone.relative_to(BACKEND_ROOT)
    except ValueError:
        return -1
    module_path = str(rel).replace("/", ".").replace(".py", "")

    count = 0
    for py_file in APP_ROOT.rglob("*.py"):
        if py_file == tombstone:
            continue
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if module_path in source:
            count += 1
    return count


def main():
    apply = "--apply" in sys.argv
    tombstones = find_tombstones()

    if not tombstones:
        print("No tombstone files found.")
        return 0

    print(f"Found {len(tombstones)} tombstone(s):\n")

    collapsed = 0
    for ts in tombstones:
        rel = os.path.relpath(ts, BACKEND_ROOT)
        deps = count_dependents(ts)
        status = f"{deps} dependent(s)"

        if deps == 0:
            if apply:
                ts.unlink()
                status = "DELETED"
                collapsed += 1
            else:
                status = "0 dependents — would delete (use --apply)"

        print(f"  {rel}: {status}")

    print(f"\nSummary: {collapsed} collapsed" if apply else f"\nDry run complete. {sum(1 for ts in tombstones if count_dependents(ts) == 0)} eligible for collapse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
