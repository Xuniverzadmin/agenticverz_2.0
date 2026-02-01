#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: CROSS-002 - Bidirectional Query Requirement
# artifact_class: CODE
"""
GUARDRAIL: CROSS-002 - Bidirectional Query Requirement
Rule: If domain A links to domain B, both directions must be queryable.

This script validates that reverse query endpoints exist.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Required bidirectional queries
# Format: (source_domain, target_domain, forward_pattern, reverse_endpoint_pattern, required)
REQUIRED_BIDIRECTIONAL: List[Tuple[str, str, str, str, bool]] = [
    # Activity ↔ Incidents
    (
        "Activity",
        "Incidents",
        r"source_run_id",  # Forward: incident has source_run_id
        r"/runs/\{.*\}/incidents|/runs/<.*>/incidents|get_incidents_for_run",  # Reverse endpoint
        True
    ),

    # Incidents ↔ Cost
    (
        "Incidents",
        "Analytics",
        r"incident_id.*cost|cost.*incident",  # Forward: cost has incident_id
        r"/incidents/\{.*\}/cost|get_cost.*impact|cost_impact",  # Reverse endpoint
        True
    ),

    # Cost Anomalies ↔ Incidents
    (
        "Analytics",
        "Incidents",
        r"incident_id.*anomal|anomal.*incident_id",  # Forward: anomaly has incident_id
        r"/anomalies.*incident|/incidents/\{.*\}/anomal",  # Reverse endpoint
        False  # Recommended, not required
    ),

    # Activity ↔ Logs
    (
        "Activity",
        "Logs",
        r"run_id.*trace|trace.*run_id",  # Forward: trace has run_id
        r"/runs/\{.*\}/logs|/runs/<.*>/traces|get_logs_for_run",  # Reverse endpoint
        False  # Recommended, not required
    ),

    # Incidents ↔ Policies
    (
        "Incidents",
        "Policies",
        r"incident.*policy|policy.*incident|triggering_incident",  # Forward: proposal from incident
        r"/incidents/\{.*\}/polic|policies.*incident",  # Reverse endpoint
        False  # Recommended, not required
    ),
]


def find_forward_link(base_path: Path, pattern: str) -> bool:
    """Check if forward link (FK) exists in models."""
    models_path = base_path / "models"

    if not models_path.exists():
        return False

    for model_file in models_path.glob("*.py"):
        with open(model_file, 'r') as f:
            content = f.read()

        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def find_reverse_endpoint(base_path: Path, pattern: str) -> Tuple[bool, str]:
    """Check if reverse query endpoint exists in API routes."""
    api_path = base_path / "api"

    if not api_path.exists():
        return False, ""

    for api_file in api_path.glob("*.py"):
        with open(api_file, 'r') as f:
            content = f.read()

        if re.search(pattern, content, re.IGNORECASE):
            return True, api_file.name

    return False, ""


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("CROSS-002: Bidirectional Query Check")
    print("=" * 50)

    complete = []
    missing_required = []
    missing_recommended = []

    for source, target, forward_pattern, reverse_pattern, required in REQUIRED_BIDIRECTIONAL:
        link_name = f"{source} ↔ {target}"

        # Check forward link
        has_forward = find_forward_link(backend_path, forward_pattern)

        # Check reverse endpoint
        has_reverse, found_in = find_reverse_endpoint(backend_path, reverse_pattern)

        if has_forward and has_reverse:
            complete.append(f"{link_name} (reverse in {found_in})")
        elif has_forward and not has_reverse:
            entry = (
                f"Link: {link_name}\n"
                f"  Forward link: EXISTS\n"
                f"  Reverse endpoint: MISSING\n"
                f"  Expected pattern: {reverse_pattern}\n"
                f"  → Need endpoint to query {source} from {target}"
            )
            if required:
                missing_required.append(entry)
            else:
                missing_recommended.append(entry)
        # If no forward link, no bidirectional needed

    # Report results
    print(f"\nComplete Bidirectional Links: {len(complete)}")
    for c in complete:
        print(f"  ✓ {c}")

    print(f"\nMissing Required Reverse Queries: {len(missing_required)}")
    for m in missing_required:
        print(f"  ✗ {m.split(chr(10))[0]}")

    print(f"\nMissing Recommended Reverse Queries: {len(missing_recommended)}")
    for m in missing_recommended:
        print(f"  ⚠ {m.split(chr(10))[0]}")

    if missing_required:
        print("\n" + "=" * 50)
        print("MISSING REQUIRED REVERSE QUERIES:")
        print("-" * 50)
        for m in missing_required:
            print(m)
            print()

        print("\nBidirectional queries enable navigation in BOTH directions.")
        print("Add the missing reverse endpoints.")
        sys.exit(1)
    else:
        print("\n✓ All required bidirectional queries exist")
        sys.exit(0)


if __name__ == "__main__":
    main()
