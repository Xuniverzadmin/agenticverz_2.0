#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: CROSS-001 - Mandatory Cross-Domain Propagation
# artifact_class: CODE
"""
GUARDRAIL: CROSS-001 - Mandatory Cross-Domain Propagation
Rule: Certain events MUST propagate to other domains.

This script validates that required propagation code exists.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Required propagations
# Format: (event, source_file_pattern, must_call_pattern, target_domain)
REQUIRED_PROPAGATIONS: List[Tuple[str, str, str, str]] = [
    # Run failure → Incident creation
    (
        "run_failed",
        r"runner\.py|run.*service\.py|activity.*service\.py",
        r"create_incident|incident.*engine|IncidentEngine",
        "Incidents"
    ),

    # Budget exceeded → Incident creation
    (
        "budget_exceeded",
        r"cost.*anomaly.*detector\.py|anomaly.*service\.py",
        r"create_incident|incident.*engine|IncidentEngine",
        "Incidents"
    ),

    # Incident created → Audit entry
    (
        "incident_created",
        r"incident.*engine\.py|incident.*service\.py",
        r"audit.*ledger|emit.*audit|AuditLedgerService",
        "Logs"
    ),

    # Policy changed → Audit entry
    (
        "policy_changed",
        r"policy.*engine\.py|policy.*service\.py",
        r"audit.*ledger|emit.*audit|AuditLedgerService",
        "Logs"
    ),

    # Limit changed → Audit entry
    (
        "limit_changed",
        r"limit.*service\.py|policy.*service\.py",
        r"audit.*ledger|emit.*audit|AuditLedgerService",
        "Logs"
    ),

    # Incident created → Policy proposal (high severity)
    (
        "high_severity_incident",
        r"incident.*engine\.py",
        r"create.*policy.*proposal|maybe.*create.*policy|PolicyProposalEngine",
        "Policies"
    ),
]


def find_matching_files(base_path: Path, pattern: str) -> List[Path]:
    """Find files matching a pattern."""
    matching = []

    for py_file in base_path.rglob("*.py"):
        if re.search(pattern, py_file.name, re.IGNORECASE):
            matching.append(py_file)

    return matching


def check_propagation_exists(files: List[Path], call_pattern: str) -> Tuple[bool, str]:
    """Check if any of the files contain the required propagation call."""
    for file_path in files:
        with open(file_path, 'r') as f:
            content = f.read()

        if re.search(call_pattern, content, re.IGNORECASE):
            return True, str(file_path)

    return False, ""


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("CROSS-001: Cross-Domain Propagation Check")
    print("=" * 50)

    missing = []
    found = []

    for event, source_pattern, call_pattern, target_domain in REQUIRED_PROPAGATIONS:
        # Find source files
        source_files = find_matching_files(backend_path, source_pattern)

        if not source_files:
            missing.append(
                f"Event: {event}\n"
                f"  Source pattern: {source_pattern}\n"
                f"  → No matching source files found\n"
                f"  → Cannot verify propagation to {target_domain}"
            )
            continue

        # Check for propagation call
        exists, found_in = check_propagation_exists(source_files, call_pattern)

        if exists:
            found.append(f"{event} → {target_domain} (in {Path(found_in).name})")
        else:
            missing.append(
                f"Event: {event}\n"
                f"  Source files: {[f.name for f in source_files]}\n"
                f"  Expected call pattern: {call_pattern}\n"
                f"  → Missing propagation to {target_domain}"
            )

    # Report results
    print(f"\nPropagations Found: {len(found)}")
    for p in found:
        print(f"  ✓ {p}")

    print(f"\nMissing Propagations: {len(missing)}")

    if missing:
        print("\nMISSING PROPAGATIONS:")
        print("-" * 50)
        for m in missing:
            print(m)
            print()

        print("\n⚠️  Cross-domain propagation is required!")
        print("Events must flow between domains as specified.")
        print()

        # Warning mode - doesn't block CI
        # Change to sys.exit(1) for strict enforcement
        sys.exit(0)
    else:
        print("\n✓ All required cross-domain propagations exist")
        sys.exit(0)


if __name__ == "__main__":
    main()
