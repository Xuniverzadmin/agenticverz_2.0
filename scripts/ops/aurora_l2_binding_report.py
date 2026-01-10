#!/usr/bin/env python3
"""
AURORA_L2 Binding Status Report

Purpose: CI visibility into capability binding status (non-blocking).
Usage:   python3 scripts/ops/aurora_l2_binding_report.py [--fail-on-unbound]

Options:
  --fail-on-unbound    Exit with error if any UNBOUND capabilities exist (future enforcement)
  --json              Output as JSON for CI integration

4-State Capability Lifecycle:
  DISCOVERED → DECLARED → OBSERVED → TRUSTED

Core Invariant:
  Capabilities are not real because backend says so.
  They are real only when the system demonstrates them.

This is a visibility tool, not an enforcement gate (yet).
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPILED_PATH = REPO_ROOT / "design/l2_1/exports/intent_store_compiled.json"


def get_binding_report() -> dict:
    """Generate binding status report from compiled intents."""
    if not COMPILED_PATH.exists():
        return {"error": "Compiled intents not found. Run pipeline first."}

    with open(COMPILED_PATH) as f:
        intents = json.load(f)

    # Count by binding status
    counts = {"INFO": 0, "DRAFT": 0, "BOUND": 0, "UNBOUND": 0}
    draft_panels = []
    bound_panels = []
    unbound_panels = []

    for intent in intents:
        status = intent.get("binding_status", "INFO")
        counts[status] = counts.get(status, 0) + 1

        panel_info = {
            "panel_id": intent["panel_id"],
            "domain": intent["domain"],
            "actions": []
        }

        # Collect actions
        if intent.get("write_action"):
            panel_info["actions"].append(intent["write_action"])
        panel_info["actions"].extend(intent.get("activate_actions", []))

        if status == "DRAFT":
            draft_panels.append(panel_info)
        elif status == "BOUND":
            bound_panels.append(panel_info)
        elif status == "UNBOUND":
            unbound_panels.append(panel_info)

    return {
        "total_panels": len(intents),
        "counts": counts,
        "draft_panels": draft_panels,
        "bound_panels": bound_panels,
        "unbound_panels": unbound_panels,
        "health": "HEALTHY" if counts["UNBOUND"] == 0 else "DEGRADED"
    }


def print_report(report: dict, as_json: bool = False):
    """Print binding status report."""
    if as_json:
        print(json.dumps(report, indent=2))
        return

    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    print("=" * 60)
    print("AURORA_L2 Binding Status Report")
    print("=" * 60)
    print()

    counts = report["counts"]
    total = report["total_panels"]

    print(f"Total Panels: {total}")
    print()
    print("4-State Lifecycle: DISCOVERED → DECLARED → OBSERVED → TRUSTED")
    print()
    print("Binding Status Distribution:")
    print(f"  INFO:    {counts['INFO']:3d} ({counts['INFO']*100//total:2d}%) - Display only, no actions")
    print(f"  DRAFT:   {counts['DRAFT']:3d} ({counts['DRAFT']*100//total:2d}%) - DISCOVERED/DECLARED (not yet system-verified)")
    print(f"  BOUND:   {counts['BOUND']:3d} ({counts['BOUND']*100//total:2d}%) - OBSERVED/TRUSTED (system verified)")
    print(f"  UNBOUND: {counts['UNBOUND']:3d} ({counts['UNBOUND']*100//total:2d}%) - Missing or deprecated capabilities")
    print()

    if report["draft_panels"]:
        print("DRAFT Panels (awaiting backend implementation):")
        for p in report["draft_panels"]:
            print(f"  {p['panel_id']}: {', '.join(p['actions'])}")
        print()

    if report["bound_panels"]:
        print("BOUND Panels (fully wired):")
        for p in report["bound_panels"]:
            print(f"  {p['panel_id']}: {', '.join(p['actions'])}")
        print()

    if report["unbound_panels"]:
        print("UNBOUND Panels (REQUIRES ATTENTION):")
        for p in report["unbound_panels"]:
            print(f"  {p['panel_id']}: {', '.join(p['actions'])}")
        print()

    print(f"System Health: {report['health']}")
    print()

    if report["health"] == "DEGRADED":
        print("WARNING: UNBOUND capabilities detected.")
        print("This indicates missing capability declarations.")
        print("Run: python3 scripts/tools/AURORA_L2_seed_capability_registry.py")


def main():
    fail_on_unbound = "--fail-on-unbound" in sys.argv
    as_json = "--json" in sys.argv

    report = get_binding_report()

    if "error" in report:
        print_report(report, as_json)
        sys.exit(1)

    print_report(report, as_json)

    # Future enforcement: fail CI if UNBOUND exists
    if fail_on_unbound and report["counts"]["UNBOUND"] > 0:
        print("\nCI FAILURE: UNBOUND capabilities detected.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
