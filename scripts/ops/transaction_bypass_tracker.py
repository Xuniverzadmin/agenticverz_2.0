#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: TRANSACTION_BYPASS Sweep Tracker
# artifact_class: CODE
"""
TRANSACTION_BYPASS Sweep Tracker

Automated tracking for TRANSACTION_BYPASS remediation sweep.
Reads from HOC_AUTHORITY_VIOLATIONS.yaml and tracks progress.

Usage:
    python scripts/ops/transaction_bypass_tracker.py status      # Current status
    python scripts/ops/transaction_bypass_tracker.py by-domain   # Breakdown by domain
    python scripts/ops/transaction_bypass_tracker.py by-file     # Breakdown by file
    python scripts/ops/transaction_bypass_tracker.py record      # Record current state as checkpoint
    python scripts/ops/transaction_bypass_tracker.py history     # Show checkpoint history
    python scripts/ops/transaction_bypass_tracker.py diff        # Diff against last checkpoint
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
VIOLATIONS_FILE = REPO_ROOT / "docs/architecture/hoc/HOC_AUTHORITY_VIOLATIONS.yaml"
TRACKER_STATE_FILE = REPO_ROOT / "docs/architecture/hoc/.transaction_bypass_tracker_state.json"
SWEEP_LOG_FILE = REPO_ROOT / "docs/architecture/hoc/SWEEP_01_TRANSACTION_BYPASS_LOG.md"


def load_violations() -> Dict:
    """Load violations from YAML file."""
    if not VIOLATIONS_FILE.exists():
        print(f"ERROR: Violations file not found: {VIOLATIONS_FILE}")
        print("Run: python scripts/ops/hoc_authority_analyzer.py --mode full")
        sys.exit(1)

    with open(VIOLATIONS_FILE) as f:
        return yaml.safe_load(f)


def extract_transaction_bypass(data: Dict) -> List[Dict]:
    """Extract all TRANSACTION_BYPASS violations."""
    violations = []

    # Check critical violations
    for v in data.get("violations", {}).get("critical", []):
        if v.get("violation") == "TRANSACTION_BYPASS":
            violations.append(v)

    # Check high violations
    for v in data.get("violations", {}).get("high", []):
        if v.get("violation") == "TRANSACTION_BYPASS":
            violations.append(v)

    return violations


def group_by_domain(violations: List[Dict]) -> Dict[str, List[Dict]]:
    """Group violations by domain."""
    by_domain = {}
    for v in violations:
        file_path = v.get("file", "")
        parts = file_path.split("/")
        domain = parts[0] if parts else "unknown"
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(v)
    return by_domain


def group_by_file(violations: List[Dict]) -> Dict[str, List[Dict]]:
    """Group violations by file."""
    by_file = {}
    for v in violations:
        file_path = v.get("file", "")
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(v)
    return by_file


def load_state() -> Dict:
    """Load tracker state (checkpoints)."""
    if not TRACKER_STATE_FILE.exists():
        return {"checkpoints": [], "start_count": None}
    with open(TRACKER_STATE_FILE) as f:
        return json.load(f)


def save_state(state: Dict):
    """Save tracker state."""
    with open(TRACKER_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def cmd_status(args):
    """Show current status."""
    data = load_violations()
    violations = extract_transaction_bypass(data)
    by_domain = group_by_domain(violations)
    state = load_state()

    print("=" * 60)
    print("TRANSACTION_BYPASS SWEEP STATUS")
    print("=" * 60)
    print()

    # Summary
    total = len(violations)
    start = state.get("start_count", total)
    removed = start - total
    pct = (removed / start * 100) if start > 0 else 0

    print(f"Start count:     {start}")
    print(f"Current count:   {total}")
    print(f"Removed:         {removed}")
    print(f"Progress:        {pct:.1f}%")
    print()

    # By domain summary
    print("By Domain:")
    print("-" * 40)
    for domain in sorted(by_domain.keys(), key=lambda d: -len(by_domain[d])):
        count = len(by_domain[domain])
        status = "✅ DONE" if count == 0 else f"⏳ {count} remaining"
        print(f"  {domain:15} {status}")
    print()

    # Timestamp
    ts = data.get("scan_metadata", {}).get("timestamp", "unknown")
    print(f"Last scan: {ts}")


def cmd_by_domain(args):
    """Show breakdown by domain."""
    data = load_violations()
    violations = extract_transaction_bypass(data)
    by_domain = group_by_domain(violations)

    print("TRANSACTION_BYPASS by Domain")
    print("=" * 60)

    for domain in sorted(by_domain.keys(), key=lambda d: -len(by_domain[d])):
        domain_violations = by_domain[domain]
        print(f"\n{domain.upper()} ({len(domain_violations)} violations):")
        print("-" * 40)

        # Group by file within domain
        by_file = group_by_file(domain_violations)
        for file_path in sorted(by_file.keys()):
            file_violations = by_file[file_path]
            lines = [str(v.get("line")) for v in file_violations]
            print(f"  {file_path}")
            print(f"    Lines: {', '.join(lines)}")
            print(f"    Count: {len(file_violations)}")


def cmd_by_file(args):
    """Show breakdown by file."""
    data = load_violations()
    violations = extract_transaction_bypass(data)
    by_file = group_by_file(violations)

    print("TRANSACTION_BYPASS by File")
    print("=" * 60)

    # Sort by violation count descending
    for file_path in sorted(by_file.keys(), key=lambda f: -len(by_file[f])):
        file_violations = by_file[file_path]
        print(f"\n{file_path} ({len(file_violations)} commits):")
        for v in sorted(file_violations, key=lambda x: x.get("line", 0)):
            print(f"  Line {v.get('line'):4}: {v.get('call')}")


def cmd_record(args):
    """Record current state as checkpoint."""
    data = load_violations()
    violations = extract_transaction_bypass(data)
    by_domain = group_by_domain(violations)

    state = load_state()

    # Set start count if not set
    if state.get("start_count") is None:
        state["start_count"] = len(violations)

    # Create checkpoint
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "total": len(violations),
        "by_domain": {d: len(v) for d, v in by_domain.items()},
        "note": args.note if args.note else None
    }

    state["checkpoints"].append(checkpoint)
    save_state(state)

    print(f"Checkpoint recorded: {len(violations)} violations")
    print(f"Start count: {state['start_count']}")
    print(f"Checkpoints: {len(state['checkpoints'])}")

    # Also append to log file
    _append_to_log(checkpoint, state)


def _append_to_log(checkpoint: Dict, state: Dict):
    """Append checkpoint to markdown log."""
    if not SWEEP_LOG_FILE.exists():
        # Create initial log file
        with open(SWEEP_LOG_FILE, "w") as f:
            f.write("# Sweep-1: TRANSACTION_BYPASS Elimination Log\n\n")
            f.write("## Invariant\n\n")
            f.write("> Only L4 Runtime Coordinators may call commit/rollback.\n\n")
            f.write("## Progress Log\n\n")
            f.write("| Timestamp | Total | Delta | Note |\n")
            f.write("|-----------|-------|-------|------|\n")

    # Calculate delta
    checkpoints = state.get("checkpoints", [])
    if len(checkpoints) >= 2:
        prev = checkpoints[-2]["total"]
        delta = checkpoint["total"] - prev
        delta_str = f"{delta:+d}"
    else:
        delta_str = "—"

    # Append row
    with open(SWEEP_LOG_FILE, "a") as f:
        note = checkpoint.get("note") or ""
        f.write(f"| {checkpoint['timestamp'][:19]} | {checkpoint['total']} | {delta_str} | {note} |\n")

    print(f"Log updated: {SWEEP_LOG_FILE}")


def cmd_history(args):
    """Show checkpoint history."""
    state = load_state()
    checkpoints = state.get("checkpoints", [])

    if not checkpoints:
        print("No checkpoints recorded yet.")
        print("Run: python scripts/ops/transaction_bypass_tracker.py record")
        return

    print("TRANSACTION_BYPASS Checkpoint History")
    print("=" * 60)
    print(f"Start count: {state.get('start_count', 'unknown')}")
    print()
    print(f"{'Timestamp':<20} {'Total':>6} {'Delta':>6} Note")
    print("-" * 60)

    prev_total = state.get("start_count", 0)
    for cp in checkpoints:
        total = cp["total"]
        delta = total - prev_total
        delta_str = f"{delta:+d}" if delta != 0 else "—"
        note = cp.get("note") or ""
        print(f"{cp['timestamp'][:19]:<20} {total:>6} {delta_str:>6} {note}")
        prev_total = total


def cmd_diff(args):
    """Show diff against last checkpoint."""
    data = load_violations()
    violations = extract_transaction_bypass(data)
    current_by_domain = group_by_domain(violations)

    state = load_state()
    checkpoints = state.get("checkpoints", [])

    if not checkpoints:
        print("No previous checkpoint to diff against.")
        return

    last = checkpoints[-1]
    last_by_domain = last.get("by_domain", {})

    print("TRANSACTION_BYPASS Diff (vs last checkpoint)")
    print("=" * 60)
    print(f"Checkpoint: {last['timestamp'][:19]}")
    print()

    all_domains = set(current_by_domain.keys()) | set(last_by_domain.keys())

    print(f"{'Domain':<15} {'Before':>8} {'After':>8} {'Delta':>8}")
    print("-" * 45)

    total_before = 0
    total_after = 0

    for domain in sorted(all_domains):
        before = last_by_domain.get(domain, 0)
        after = len(current_by_domain.get(domain, []))
        delta = after - before
        delta_str = f"{delta:+d}" if delta != 0 else "—"

        total_before += before
        total_after += after

        print(f"{domain:<15} {before:>8} {after:>8} {delta_str:>8}")

    print("-" * 45)
    total_delta = total_after - total_before
    print(f"{'TOTAL':<15} {total_before:>8} {total_after:>8} {total_delta:+d}")


def main():
    parser = argparse.ArgumentParser(
        description="TRANSACTION_BYPASS Sweep Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    subparsers.add_parser("status", help="Show current status")

    # by-domain
    subparsers.add_parser("by-domain", help="Breakdown by domain")

    # by-file
    subparsers.add_parser("by-file", help="Breakdown by file")

    # record
    record_parser = subparsers.add_parser("record", help="Record checkpoint")
    record_parser.add_argument("--note", "-n", help="Note for this checkpoint")

    # history
    subparsers.add_parser("history", help="Show checkpoint history")

    # diff
    subparsers.add_parser("diff", help="Diff against last checkpoint")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "by-domain":
        cmd_by_domain(args)
    elif args.command == "by-file":
        cmd_by_file(args)
    elif args.command == "record":
        cmd_record(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "diff":
        cmd_diff(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
