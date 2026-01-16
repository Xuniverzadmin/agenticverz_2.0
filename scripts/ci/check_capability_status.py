#!/usr/bin/env python3
"""
GUARDRAIL: CAP-003 - Capability Status Progression
Rule: Capability status must follow valid progression.

Valid progression: DECLARED → OBSERVED → TRUSTED
Invalid: DECLARED → TRUSTED (skipping observation)
Invalid: OBSERVED → DECLARED (regression without reason)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

# Valid status values
VALID_STATUSES = ['DECLARED', 'OBSERVED', 'TRUSTED', 'DEPRECATED', 'DEFERRED']

# Valid status transitions
VALID_TRANSITIONS = {
    'DECLARED': ['OBSERVED', 'DEPRECATED', 'DEFERRED'],  # Can only go to OBSERVED, or be deprecated
    'OBSERVED': ['TRUSTED', 'DECLARED', 'DEPRECATED'],   # Can progress to TRUSTED or regress with reason
    'TRUSTED': ['DEPRECATED', 'OBSERVED'],               # Can be deprecated or demoted with reason
    'DEPRECATED': ['DECLARED'],                          # Can be revived
    'DEFERRED': ['DECLARED'],                            # Can be undeferred
}

# Transitions that require explicit reason
TRANSITIONS_REQUIRING_REASON = [
    ('OBSERVED', 'DECLARED'),  # Demotion
    ('TRUSTED', 'OBSERVED'),   # Demotion
]

# Forbidden transitions
FORBIDDEN_TRANSITIONS = [
    ('DECLARED', 'TRUSTED'),   # Must observe first
]


def find_capabilities(registry_path: Path) -> Dict[str, Dict]:
    """Find all capabilities with their status."""
    capabilities = {}

    if not registry_path.exists():
        return capabilities

    for yaml_file in registry_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)

            if content and isinstance(content, dict):
                cap_id = content.get('capability_id', yaml_file.stem)
                capabilities[cap_id] = {
                    'file': yaml_file.name,
                    'status': content.get('status', 'UNKNOWN'),
                    'previous_status': content.get('previous_status'),
                    'status_reason': content.get('status_reason'),
                    'observation_trace': content.get('observation_trace'),
                    'domain': content.get('domain', 'UNKNOWN'),
                }
        except Exception as e:
            print(f"Warning: Could not parse {yaml_file}: {e}")

    return capabilities


def check_status_validity(capabilities: Dict[str, Dict]) -> Tuple[List[str], List[str]]:
    """Check for invalid status values and transitions."""
    violations = []
    warnings = []

    for cap_id, cap_info in capabilities.items():
        status = cap_info['status']
        previous = cap_info.get('previous_status')

        # Check valid status
        if status not in VALID_STATUSES and status != 'UNKNOWN':
            violations.append(
                f"Capability: {cap_id}\n"
                f"  Status: {status}\n"
                f"  → INVALID status value\n"
                f"  → Valid: {VALID_STATUSES}"
            )
            continue

        # Check if OBSERVED/TRUSTED has observation trace
        if status in ['OBSERVED', 'TRUSTED']:
            if not cap_info.get('observation_trace'):
                warnings.append(
                    f"Capability: {cap_id}\n"
                    f"  Status: {status}\n"
                    f"  → Missing observation_trace\n"
                    f"  → {status} status should have SDSR observation evidence"
                )

        # Check transition validity if previous status is recorded
        if previous and previous in VALID_STATUSES:
            transition = (previous, status)

            # Check forbidden transitions
            if transition in FORBIDDEN_TRANSITIONS:
                violations.append(
                    f"Capability: {cap_id}\n"
                    f"  Transition: {previous} → {status}\n"
                    f"  → FORBIDDEN transition\n"
                    f"  → Cannot skip from DECLARED to TRUSTED\n"
                    f"  → Must observe capability first via SDSR"
                )
                continue

            # Check if transition is valid
            if status not in VALID_TRANSITIONS.get(previous, []):
                violations.append(
                    f"Capability: {cap_id}\n"
                    f"  Transition: {previous} → {status}\n"
                    f"  → INVALID transition\n"
                    f"  → From {previous}, valid next: {VALID_TRANSITIONS.get(previous, [])}"
                )
                continue

            # Check if demotion has reason
            if transition in TRANSITIONS_REQUIRING_REASON:
                if not cap_info.get('status_reason'):
                    violations.append(
                        f"Capability: {cap_id}\n"
                        f"  Transition: {previous} → {status}\n"
                        f"  → DEMOTION without reason\n"
                        f"  → status_reason REQUIRED for this transition"
                    )

    return violations, warnings


def check_declared_without_binding(capabilities: Dict[str, Dict]) -> List[str]:
    """Find capabilities stuck in DECLARED without progress."""
    stale = []

    for cap_id, cap_info in capabilities.items():
        if cap_info['status'] == 'DECLARED':
            # Check if it has any implementation evidence
            if not cap_info.get('observation_trace'):
                stale.append(
                    f"Capability: {cap_id}\n"
                    f"  Domain: {cap_info['domain']}\n"
                    f"  File: {cap_info['file']}\n"
                    f"  → Stuck in DECLARED status\n"
                    f"  → Needs SDSR scenario to observe"
                )

    return stale


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent.parent

    # Paths to check
    registry_path = base_path / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"

    print("CAP-003: Capability Status Progression Check")
    print("=" * 50)

    # Find capabilities
    capabilities = find_capabilities(registry_path)
    print(f"Capabilities found: {len(capabilities)}")

    # Status distribution
    status_counts = {}
    for cap in capabilities.values():
        status = cap['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Check validity
    violations, warnings = check_status_validity(capabilities)

    # Check stale DECLARED
    stale = check_declared_without_binding(capabilities)

    print(f"\nViolations: {len(violations)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Stale DECLARED: {len(stale)}")
    print()

    if stale:
        print("STALE DECLARED (need SDSR observation):")
        print("-" * 50)
        for s in stale[:5]:
            print(s)
            print()
        if len(stale) > 5:
            print(f"  ... and {len(stale) - 5} more stale capabilities")
            print()

    if warnings:
        print("WARNINGS:")
        print("-" * 50)
        for w in warnings[:5]:
            print(w)
            print()
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings")
            print()

    if violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in violations:
            print(v)
            print()

        print("\nCapability status progression rules:")
        print("  DECLARED → OBSERVED → TRUSTED")
        print("  - Cannot skip OBSERVED (must have SDSR evidence)")
        print("  - Demotions require status_reason")
        print("  - OBSERVED/TRUSTED require observation_trace")
        sys.exit(1)
    else:
        print("✓ All capability status progressions are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
