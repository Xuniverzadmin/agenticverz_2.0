#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: CAP-001 - Capability Must Match Endpoint
# artifact_class: CODE
"""
GUARDRAIL: CAP-001 - Capability Must Match Endpoint
Rule: Every declared capability MUST have an implemented endpoint.

This script validates that capabilities are backed by actual API endpoints.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set
import yaml


def find_declared_capabilities(registry_path: Path) -> Dict[str, Dict]:
    """Find all declared capabilities in the registry."""
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
                    'domain': content.get('domain', 'UNKNOWN'),
                    'api_endpoints': content.get('api_endpoints', []),
                    'required_endpoints': content.get('required_endpoints', []),
                }
        except Exception as e:
            print(f"Warning: Could not parse {yaml_file}: {e}")

    return capabilities


def find_implemented_endpoints(api_path: Path) -> Set[str]:
    """Find all implemented API endpoints."""
    endpoints = set()

    if not api_path.exists():
        return endpoints

    for py_file in api_path.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()

        # Find FastAPI route decorators
        patterns = [
            r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                endpoints.add(f"{method} {path}")

    return endpoints


def check_capability_coverage(
    capabilities: Dict[str, Dict],
    implemented: Set[str]
) -> tuple[List[str], List[str]]:
    """Check if capabilities have matching endpoints."""
    violations = []
    warnings = []

    for cap_id, cap_info in capabilities.items():
        # Skip non-active capabilities
        if cap_info['status'] in ['DEPRECATED', 'DEFERRED']:
            continue

        required = cap_info.get('required_endpoints', [])
        declared = cap_info.get('api_endpoints', [])

        all_expected = set(required + declared)

        if not all_expected:
            warnings.append(
                f"Capability: {cap_id}\n"
                f"  Status: {cap_info['status']}\n"
                f"  → No endpoints declared for this capability\n"
                f"  → Consider adding api_endpoints or required_endpoints"
            )
            continue

        missing = []
        for endpoint in all_expected:
            # Normalize endpoint format
            endpoint_normalized = endpoint.strip()

            # Check if endpoint exists (fuzzy match)
            found = False
            for impl in implemented:
                if endpoint_normalized in impl or impl in endpoint_normalized:
                    found = True
                    break

            if not found:
                missing.append(endpoint_normalized)

        if missing and cap_info['status'] in ['OBSERVED', 'TRUSTED']:
            violations.append(
                f"Capability: {cap_id}\n"
                f"  Status: {cap_info['status']}\n"
                f"  File: {cap_info['file']}\n"
                f"  Missing endpoints: {missing}\n"
                f"  → Capability claims OBSERVED but endpoints not found"
            )
        elif missing and cap_info['status'] == 'DECLARED':
            warnings.append(
                f"Capability: {cap_id}\n"
                f"  Status: {cap_info['status']}\n"
                f"  Missing endpoints: {missing}\n"
                f"  → DECLARED capability needs implementation"
            )

    return violations, warnings


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent.parent

    # Paths to check
    registry_path = base_path / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
    api_path = base_path / "backend" / "app" / "api"

    print("CAP-001: Capability-Endpoint Match Check")
    print("=" * 50)

    # Find capabilities
    capabilities = find_declared_capabilities(registry_path)
    print(f"Declared capabilities: {len(capabilities)}")

    # Find endpoints
    implemented = find_implemented_endpoints(api_path)
    print(f"Implemented endpoints: {len(implemented)}")

    # Check coverage
    violations, warnings = check_capability_coverage(capabilities, implemented)

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

        print("\nCapabilities must match endpoints!")
        print("If a capability is OBSERVED or TRUSTED:")
        print("  - All declared endpoints must exist")
        print("  - Missing endpoints = broken capability")
        print("  - Either implement endpoint or demote status")
        sys.exit(1)
    else:
        print("✓ All OBSERVED/TRUSTED capabilities have matching endpoints")
        sys.exit(0)


if __name__ == "__main__":
    main()
