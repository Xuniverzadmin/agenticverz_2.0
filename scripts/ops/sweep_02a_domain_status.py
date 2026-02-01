#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Sweep-02A: Domain Status Report
# artifact_class: CODE
"""
Sweep-02A: Domain Status Report

Shows the status of each domain folder for the L4 Runtime Wiring sweep.

Usage:
    python scripts/ops/sweep_02a_domain_status.py [OPTIONS]

Options:
    --domain DOMAIN   Show only specific domain
    --deferred        Show only domains with deferred imports
    --clean           Show only clean domains
    --verbose         Show file-level details
    --json            Output as JSON
    --ci              Exit 1 if any actionable items remain
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


HOC_ROOT = Path("app/hoc/cus")

# Services that have L4_runtime equivalents (CAN BE REWIRED)
L4_RUNTIME_COVERED = [
    "app.services.governance.audit_service",
    "app.services.governance.contract_service",
    "app.services.governance.eligibility_engine",
    "app.services.governance.governance_orchestrator",
    "app.services.governance.job_executor",
    "app.services.governance.rollout_projection",
    "app.services.governance.validator_service",
    "app.services.governance.cross_domain",
    "app.services.governance.run_governance_facade",
    "app.services.governance.transaction_coordinator",
]

SCAN_PATTERNS = ["L5_engines/*.py", "L5_controls/*.py"]


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a file for app.services.* imports."""
    result = {
        "actionable": [],
        "docstring": [],
        "deferred": [],
    }

    try:
        content = file_path.read_text()
        lines = content.split('\n')

        in_docstring = False
        docstring_delim = None

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track docstring boundaries
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_delim = stripped[:3]
                    if stripped.count(docstring_delim) == 1:
                        in_docstring = True
            else:
                if docstring_delim and docstring_delim in stripped:
                    in_docstring = False
                    docstring_delim = None

            if not (stripped.startswith('from app.services') or
                    stripped.startswith('import app.services')):
                continue

            is_actionable = any(covered in line for covered in L4_RUNTIME_COVERED)

            if in_docstring or (i > 1 and lines[i-2].strip().startswith('Usage:')):
                result["docstring"].append((i, stripped))
            elif is_actionable:
                result["actionable"].append((i, stripped))
            else:
                result["deferred"].append((i, stripped))

    except Exception as e:
        pass

    return result


def scan_domain(domain_path: Path, backend_root: Path) -> Dict[str, Any]:
    """Scan a single domain and return stats."""
    stats = {
        "files": 0,
        "clean": 0,
        "actionable": 0,
        "docstring": 0,
        "deferred": 0,
        "file_details": [],
    }

    for pattern in SCAN_PATTERNS:
        for file_path in domain_path.glob(pattern):
            if file_path.name.startswith('__'):
                continue

            stats["files"] += 1
            result = analyze_file(file_path)

            rel_path = str(file_path.relative_to(backend_root))
            file_info = {
                "path": rel_path,
                "actionable": len(result["actionable"]),
                "docstring": len(result["docstring"]),
                "deferred": len(result["deferred"]),
                "details": result,
            }

            if file_info["actionable"] == 0 and file_info["deferred"] == 0 and file_info["docstring"] == 0:
                stats["clean"] += 1
                file_info["status"] = "clean"
            elif file_info["actionable"] > 0:
                file_info["status"] = "actionable"
            elif file_info["deferred"] > 0:
                file_info["status"] = "deferred"
            else:
                file_info["status"] = "docstring"

            stats["actionable"] += file_info["actionable"]
            stats["docstring"] += file_info["docstring"]
            stats["deferred"] += file_info["deferred"]
            stats["file_details"].append(file_info)

    # Determine domain status
    if stats["actionable"] > 0:
        stats["status"] = "INCOMPLETE"
    elif stats["deferred"] > 0:
        stats["status"] = "DEFERRED"
    elif stats["docstring"] > 0:
        stats["status"] = "CLEAN (docs)"
    else:
        stats["status"] = "CLEAN"

    return stats


def print_table(domain_stats: Dict[str, Dict], verbose: bool = False):
    """Print domain status table."""
    print("=" * 80)
    print("SWEEP-02A: Domain Status Report")
    print("=" * 80)
    print()
    print(f"{'Domain':<15} {'Files':<8} {'Clean':<8} {'Action':<8} {'Docstr':<8} {'Defer':<8} {'Status'}")
    print("-" * 80)

    totals = {"files": 0, "clean": 0, "actionable": 0, "docstring": 0, "deferred": 0}

    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        for key in totals:
            totals[key] += stats[key]

        print(f"{domain:<15} {stats['files']:<8} {stats['clean']:<8} {stats['actionable']:<8} {stats['docstring']:<8} {stats['deferred']:<8} {stats['status']}")

        if verbose and (stats['actionable'] > 0 or stats['deferred'] > 0):
            for f in stats['file_details']:
                if f['actionable'] > 0 or f['deferred'] > 0:
                    print(f"    {f['path']}: A={f['actionable']} D={f['deferred']}")

    print("-" * 80)
    print(f"{'TOTAL':<15} {totals['files']:<8} {totals['clean']:<8} {totals['actionable']:<8} {totals['docstring']:<8} {totals['deferred']:<8}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Sweep-02A Domain Status Report")
    parser.add_argument("--domain", help="Show only specific domain")
    parser.add_argument("--deferred", action="store_true", help="Show only domains with deferred imports")
    parser.add_argument("--clean", action="store_true", help="Show only clean domains")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show file-level details")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--ci", action="store_true", help="Exit 1 if any actionable items remain")
    args = parser.parse_args()

    # Find backend root
    script_path = Path(__file__).resolve()
    backend_root = script_path.parent.parent.parent / "backend"

    if not backend_root.exists():
        backend_root = Path.cwd()
        if not (backend_root / "app" / "hoc").exists():
            print("ERROR: Must run from backend/ or repository root", file=sys.stderr)
            sys.exit(1)

    hoc_path = backend_root / HOC_ROOT

    # Scan all domains
    domain_stats = {}
    for domain_path in sorted(hoc_path.iterdir()):
        if not domain_path.is_dir():
            continue

        domain = domain_path.name

        # Filter by domain if specified
        if args.domain and domain != args.domain:
            continue

        stats = scan_domain(domain_path, backend_root)

        # Filter by status
        if args.deferred and stats["status"] not in ("DEFERRED", "INCOMPLETE"):
            continue
        if args.clean and stats["status"] not in ("CLEAN", "CLEAN (docs)"):
            continue

        domain_stats[domain] = stats

    # Output
    if args.json:
        # Remove file_details from JSON output unless verbose
        output = {}
        for domain, stats in domain_stats.items():
            output[domain] = {k: v for k, v in stats.items() if k != "file_details" or args.verbose}
        print(json.dumps(output, indent=2))
    else:
        print_table(domain_stats, verbose=args.verbose)

        print("Legend:")
        print("  Files    = L5 engine/control files scanned")
        print("  Clean    = Files with no app.services.* imports")
        print("  Action   = Actionable imports (should be 0 after sweep)")
        print("  Docstr   = Docstring examples (not actual imports)")
        print("  Defer    = Deferred imports (need module migration)")
        print()
        print("Status:")
        print("  CLEAN        = No violations")
        print("  CLEAN (docs) = Only docstring examples remain")
        print("  DEFERRED     = Has imports requiring module migration")
        print("  INCOMPLETE   = Has actionable imports not yet rewired")

    # CI mode: exit 1 if actionable items remain
    if args.ci:
        total_actionable = sum(s["actionable"] for s in domain_stats.values())
        if total_actionable > 0:
            print(f"\nCI FAILURE: {total_actionable} actionable imports remain", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
