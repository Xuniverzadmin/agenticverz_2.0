#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: CAP-002 - Console Capability Boundaries
# artifact_class: CODE
"""
GUARDRAIL: CAP-002 - Console Capability Boundaries
Rule: Capabilities must bind to correct console type.

This script validates that capabilities are bound to the appropriate console.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List
import yaml

# Console types and their allowed domains
CONSOLE_DOMAINS = {
    'customer': {
        'allowed_domains': [
            'Activity',
            'Incidents',
            'Policies',
            'Logs',
            'Analytics',
            'Overview',
            'Connectivity',
            'Accounts',
        ],
        'forbidden_domains': [
            'Admin',
            'System',
            'Founder',
            'Ops',
            'Internal',
        ],
    },
    'founder': {
        'allowed_domains': [
            'CrossTenant',
            'SystemHealth',
            'Platform',
            'Admin',
        ],
        'forbidden_domains': [],  # Founder can see everything
    },
    'ops': {
        'allowed_domains': [
            'Infrastructure',
            'Monitoring',
            'Debugging',
        ],
        'forbidden_domains': [
            'CustomerData',
            'Billing',
        ],
    },
}


def find_capabilities(registry_path: Path) -> List[Dict]:
    """Find all capabilities with console bindings."""
    capabilities = []

    if not registry_path.exists():
        return capabilities

    for yaml_file in registry_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)

            if content and isinstance(content, dict):
                capabilities.append({
                    'id': content.get('capability_id', yaml_file.stem),
                    'file': yaml_file.name,
                    'domain': content.get('domain', 'UNKNOWN'),
                    'console': content.get('console', 'customer'),
                    'status': content.get('status', 'UNKNOWN'),
                    'visibility': content.get('visibility', 'private'),
                })
        except Exception as e:
            print(f"Warning: Could not parse {yaml_file}: {e}")

    return capabilities


def check_intent_files(intents_path: Path) -> List[Dict]:
    """Find intents with console bindings."""
    intents = []

    if not intents_path.exists():
        return intents

    for yaml_file in intents_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)

            if content and isinstance(content, dict):
                intents.append({
                    'id': content.get('panel_id', yaml_file.stem),
                    'file': yaml_file.name,
                    'domain': content.get('domain', 'UNKNOWN'),
                    'console': content.get('console', 'customer'),
                    'subdomain': content.get('subdomain', ''),
                })
        except Exception as e:
            print(f"Warning: Could not parse {yaml_file}: {e}")

    return intents


def check_console_boundaries(
    capabilities: List[Dict],
    intents: List[Dict]
) -> tuple[List[str], List[str]]:
    """Check if capabilities and intents respect console boundaries."""
    violations = []
    warnings = []

    # Check capabilities
    for cap in capabilities:
        console = cap['console'].lower()
        domain = cap['domain']

        if console not in CONSOLE_DOMAINS:
            warnings.append(
                f"Capability: {cap['id']}\n"
                f"  → Unknown console type: {console}\n"
                f"  → Valid consoles: {list(CONSOLE_DOMAINS.keys())}"
            )
            continue

        console_config = CONSOLE_DOMAINS[console]

        # Check forbidden domains
        for forbidden in console_config['forbidden_domains']:
            if forbidden.lower() in domain.lower():
                violations.append(
                    f"Capability: {cap['id']}\n"
                    f"  Console: {console}\n"
                    f"  Domain: {domain}\n"
                    f"  → FORBIDDEN: {console} console cannot have {forbidden} capabilities\n"
                    f"  → Move to appropriate console or change domain"
                )

        # Check if domain is in allowed list
        allowed = console_config['allowed_domains']
        if allowed:  # Empty means "all allowed"
            matched = False
            for allowed_domain in allowed:
                if allowed_domain.lower() in domain.lower():
                    matched = True
                    break
            if not matched:
                warnings.append(
                    f"Capability: {cap['id']}\n"
                    f"  Console: {console}\n"
                    f"  Domain: {domain}\n"
                    f"  → Domain not in standard list for {console} console\n"
                    f"  → Allowed: {allowed}"
                )

    # Check intents
    for intent in intents:
        console = intent['console'].lower()
        domain = intent['domain']

        if console not in CONSOLE_DOMAINS:
            continue

        console_config = CONSOLE_DOMAINS[console]

        # Check forbidden domains
        for forbidden in console_config['forbidden_domains']:
            if forbidden.lower() in domain.lower():
                violations.append(
                    f"Intent: {intent['id']}\n"
                    f"  Console: {console}\n"
                    f"  Domain: {domain}\n"
                    f"  → FORBIDDEN: {console} console cannot have {forbidden} panels\n"
                    f"  → File: {intent['file']}"
                )

    return violations, warnings


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent.parent

    # Paths to check
    registry_path = base_path / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
    intents_path = base_path / "design" / "l2_1" / "intents"

    print("CAP-002: Console Capability Boundaries Check")
    print("=" * 50)

    # Find capabilities and intents
    capabilities = find_capabilities(registry_path)
    intents = check_intent_files(intents_path)

    print(f"Capabilities: {len(capabilities)}")
    print(f"Intents: {len(intents)}")

    # Check boundaries
    violations, warnings = check_console_boundaries(capabilities, intents)

    print(f"\nViolations: {len(violations)}")
    print(f"Warnings: {len(warnings)}")
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

        print("\nConsole boundaries must be respected!")
        print("Customer console: Only customer domains")
        print("Founder console: Cross-tenant visibility")
        print("Ops console: Infrastructure only")
        print()
        print("Mixing domains across consoles is a security risk.")
        sys.exit(1)
    else:
        print("✓ All capabilities respect console boundaries")
        sys.exit(0)


if __name__ == "__main__":
    main()
