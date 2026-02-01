#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Sweep-02A: RUNTIME_IMPORT_LEAK Detector
# artifact_class: CODE
"""
Sweep-02A: RUNTIME_IMPORT_LEAK Detector

Invariant: All HOC engines must import runtime authorities from HOC L4,
           never from legacy app/services/*

Metric: RUNTIME_IMPORT_LEAK count

Usage:
    python scripts/ops/sweep_02a_runtime_import_checker.py [--verbose]
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


# HOC root relative to backend/
HOC_ROOT = Path("app/hoc/cus")

# Patterns that indicate runtime authority imports from legacy locations
LEGACY_RUNTIME_PATTERNS = [
    "app.services.",
    "from app.services",
]

# Files to scan (L5 engines only per scope)
SCAN_PATTERNS = [
    "*/L5_engines/*.py",
    "*/L5_controls/*.py",  # Include controls which have engine-like behavior
]


def find_legacy_imports(file_path: Path) -> List[Tuple[int, str]]:
    """
    Find legacy runtime imports in a file.

    Returns list of (line_number, import_statement) tuples.
    """
    violations = []

    try:
        content = file_path.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments and empty lines
            if stripped.startswith('#') or not stripped:
                continue

            # Check for legacy import patterns
            for pattern in LEGACY_RUNTIME_PATTERNS:
                if pattern in line:
                    # Verify it's actually an import statement
                    if stripped.startswith('from ') or stripped.startswith('import '):
                        violations.append((i, stripped))
                        break

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return violations


def scan_hoc_engines(backend_root: Path, verbose: bool = False) -> dict:
    """
    Scan all HOC L5 engines for legacy runtime imports.

    Returns dict with:
        - total_violations: int
        - files_with_violations: list of (file, violations)
        - files_scanned: int
    """
    hoc_path = backend_root / HOC_ROOT

    if not hoc_path.exists():
        print(f"ERROR: HOC root not found: {hoc_path}", file=sys.stderr)
        sys.exit(1)

    results = {
        "total_violations": 0,
        "files_with_violations": [],
        "files_scanned": 0,
        "clean_files": 0,
    }

    # Scan all matching files
    for pattern in SCAN_PATTERNS:
        for file_path in hoc_path.glob(pattern):
            if file_path.name.startswith('__'):
                continue

            results["files_scanned"] += 1
            violations = find_legacy_imports(file_path)

            if violations:
                rel_path = file_path.relative_to(backend_root)
                results["files_with_violations"].append((str(rel_path), violations))
                results["total_violations"] += len(violations)
            else:
                results["clean_files"] += 1

    return results


def print_report(results: dict, verbose: bool = False):
    """Print the scan report."""

    print("=" * 70)
    print("SWEEP-02A: RUNTIME_IMPORT_LEAK Report")
    print("=" * 70)
    print()
    print(f"Invariant: HOC engines must import from HOC L4, not app.services.*")
    print()
    print("-" * 70)
    print("METRIC SUMMARY")
    print("-" * 70)
    print(f"  Files scanned:        {results['files_scanned']}")
    print(f"  Files clean:          {results['clean_files']}")
    print(f"  Files with violations: {len(results['files_with_violations'])}")
    print(f"  RUNTIME_IMPORT_LEAK:  {results['total_violations']}")
    print()

    if results['files_with_violations']:
        print("-" * 70)
        print("VIOLATIONS BY FILE")
        print("-" * 70)

        for file_path, violations in sorted(results['files_with_violations']):
            print(f"\n  {file_path} ({len(violations)} violations)")
            if verbose:
                for line_num, stmt in violations:
                    print(f"    Line {line_num}: {stmt[:60]}{'...' if len(stmt) > 60 else ''}")

        print()

    print("-" * 70)
    print("STATUS")
    print("-" * 70)

    if results['total_violations'] == 0:
        print("  SWEEP-02A: COMPLETE (0 violations)")
    else:
        print(f"  SWEEP-02A: IN PROGRESS ({results['total_violations']} violations remaining)")

    print("=" * 70)

    return results['total_violations']


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    # Determine backend root
    script_path = Path(__file__).resolve()
    backend_root = script_path.parent.parent.parent / "backend"

    if not backend_root.exists():
        # Try current directory
        backend_root = Path.cwd()
        if not (backend_root / "app" / "hoc").exists():
            print("ERROR: Must run from backend/ or repository root", file=sys.stderr)
            sys.exit(1)

    results = scan_hoc_engines(backend_root, verbose)
    violation_count = print_report(results, verbose)

    # Exit with violation count for CI integration
    sys.exit(min(violation_count, 255))


if __name__ == "__main__":
    main()
