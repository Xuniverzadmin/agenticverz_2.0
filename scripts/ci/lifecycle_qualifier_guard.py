#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Enforce LIFECYCLE-DERIVED-FROM-QUALIFIER governance rule
# Callers: CI pipeline, bootstrap verification
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L7
# Reference: PIN-283 (LIFECYCLE-DERIVED-FROM-QUALIFIER Rule)
#
# GOVERNANCE RULE:
# status: COMPLETE is DERIVED from qualifier evaluation.
# This guard enforces coherence between:
#   - CAPABILITY_LIFECYCLE.yaml (projection)
#   - QUALIFIER_EVALUATION.yaml (authoritative source)
#
# A capability MUST NOT have status: COMPLETE unless:
#   QUALIFIER_EVALUATION.yaml → capability.state == QUALIFIED
#

"""
Lifecycle-Qualifier Coherence Guard

Enforces the LIFECYCLE-DERIVED-FROM-QUALIFIER governance rule.
Ensures CAPABILITY_LIFECYCLE.yaml is a faithful projection of
QUALIFIER_EVALUATION.yaml.

Usage:
    python scripts/ci/lifecycle_qualifier_guard.py [--verbose] [--fix]

Exit codes:
    0: Coherent (all bindings valid)
    1: Incoherent (bindings violated)
    2: Missing files or parse errors
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# File paths relative to repo root
LIFECYCLE_PATH = Path("docs/governance/CAPABILITY_LIFECYCLE.yaml")
QUALIFIER_PATH = Path("docs/governance/QUALIFIER_EVALUATION.yaml")


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(2)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def check_coherence(
    lifecycle: dict, qualifier: dict, verbose: bool = False
) -> list[str]:
    """
    Check coherence between lifecycle and qualifier evaluation.

    Returns list of violations (empty if coherent).
    """
    violations = []

    capabilities_lifecycle = lifecycle.get("capabilities", {})
    capabilities_qualifier = qualifier.get("capabilities", {})

    for cap_name, cap_data in capabilities_lifecycle.items():
        status = cap_data.get("status", "UNKNOWN")
        qualifier_state = cap_data.get("qualifier_state", "UNKNOWN")

        # Check if qualifier binding exists
        if "qualifier" not in cap_data:
            violations.append(f"BINDING-MISSING: {cap_name} has no qualifier binding")
            continue

        if "qualifier_state" not in cap_data:
            violations.append(
                f"BINDING-MISSING: {cap_name} has no qualifier_state binding"
            )
            continue

        # Cross-reference with qualifier evaluation
        if cap_name in capabilities_qualifier:
            eval_state = capabilities_qualifier[cap_name].get("state", "UNKNOWN")

            # Check qualifier_state matches evaluation
            if qualifier_state != eval_state:
                violations.append(
                    f"STATE-MISMATCH: {cap_name} lifecycle.qualifier_state={qualifier_state} "
                    f"but evaluation.state={eval_state}"
                )

            # Enforce derivation rule
            if status == "COMPLETE" and eval_state != "QUALIFIED":
                violations.append(
                    f"DERIVATION-VIOLATION: {cap_name} has status=COMPLETE "
                    f"but qualifier is {eval_state} (must be QUALIFIED)"
                )

            if status != "COMPLETE" and eval_state == "QUALIFIED":
                violations.append(
                    f"PROMOTION-MISSING: {cap_name} is QUALIFIED "
                    f"but status is {status} (should be COMPLETE)"
                )
        else:
            violations.append(
                f"EVAL-MISSING: {cap_name} not found in QUALIFIER_EVALUATION.yaml"
            )

        if verbose and not violations:
            print(
                f"  OK: {cap_name} (status={status}, qualifier_state={qualifier_state})"
            )

    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Enforce LIFECYCLE-DERIVED-FROM-QUALIFIER governance rule"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument("--ci", action="store_true", help="CI mode (strict exit codes)")
    args = parser.parse_args()

    print("=" * 70)
    print("LIFECYCLE-QUALIFIER COHERENCE GUARD")
    print("=" * 70)
    print()

    # Load files
    lifecycle = load_yaml(LIFECYCLE_PATH)
    qualifier = load_yaml(QUALIFIER_PATH)

    print(f"Lifecycle source: {LIFECYCLE_PATH}")
    print(f"Qualifier source: {QUALIFIER_PATH}")
    print()

    # Check schema versions
    lifecycle_version = lifecycle.get("schema_version", "unknown")
    qualifier_version = qualifier.get("schema_version", "unknown")
    print(f"Lifecycle schema version: {lifecycle_version}")
    print(f"Qualifier schema version: {qualifier_version}")
    print()

    # Check coherence
    print("Checking coherence...")
    violations = check_coherence(lifecycle, qualifier, verbose=args.verbose)

    if violations:
        print()
        print("-" * 70)
        print(f"VIOLATIONS FOUND: {len(violations)}")
        print("-" * 70)
        for v in violations:
            print(f"  {v}")
        print()
        print("=" * 70)
        print("VERDICT: INCOHERENT")
        print("=" * 70)
        print()
        print("Resolution:")
        print("  1. Run: python scripts/ops/evaluate_qualifiers.py --generate")
        print("  2. Verify all QUALIFIED capabilities have status: COMPLETE")
        print("  3. Re-run this guard")
        print()
        sys.exit(1)
    else:
        cap_count = len(lifecycle.get("capabilities", {}))
        complete_count = sum(
            1
            for c in lifecycle.get("capabilities", {}).values()
            if c.get("status") == "COMPLETE"
        )
        qualified_count = qualifier.get("summary", {}).get("qualified", 0)

        print()
        print("=" * 70)
        print("VERDICT: COHERENT")
        print("=" * 70)
        print()
        print(f"  Capabilities checked:  {cap_count}")
        print(f"  COMPLETE in lifecycle: {complete_count}")
        print(f"  QUALIFIED in eval:     {qualified_count}")
        print()
        print("  All bindings valid.")
        print("  Lifecycle is a faithful projection of qualifier evaluation.")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
