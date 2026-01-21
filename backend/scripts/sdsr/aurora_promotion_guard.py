#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI / CLI invocation
#   Execution: sync
# Role: SDSR Promotion Guard - Enforce capability status transitions
# Reference: PIN-370, CAP-E2E-001

"""
AURORA SDSR Promotion Guard

Enforces the OBSERVED promotion rule:
    A capability may NOT move to OBSERVED unless:
    - SDSR scenario was executed
    - All L0 (transport) invariants passed
    - At least ONE L1 (domain) invariant passed
    - Observation JSON exists and was applied

CAPABILITY LIFECYCLE:
    DECLARED → OBSERVED → TRUSTED → DEPRECATED
         ↑
         └── This guard controls this transition

Usage:
    # Validate a single capability
    python aurora_promotion_guard.py --capability CAP-ACT-LLM-RUNS-LIVE

    # Validate all capabilities
    python aurora_promotion_guard.py --all

    # CI mode (exit 1 on violations)
    python aurora_promotion_guard.py --all --ci

    # Show detailed report
    python aurora_promotion_guard.py --all --verbose

Author: AURORA L2 Automation
Reference: PIN-370, CAP-E2E-001 (Capability Status Gate)
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
OBSERVATIONS_DIR = REPO_ROOT / "backend/scripts/sdsr/observations"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"


# =============================================================================
# CAPABILITY STATUS DEFINITIONS
# =============================================================================

VALID_STATUSES = {"DECLARED", "OBSERVED", "TRUSTED", "DEPRECATED"}

# Status transitions that are allowed
ALLOWED_TRANSITIONS = {
    "DECLARED": {"OBSERVED", "DEPRECATED"},
    "OBSERVED": {"TRUSTED", "DEPRECATED"},
    "TRUSTED": {"DEPRECATED"},
    "DEPRECATED": set(),
}


# =============================================================================
# CAPABILITY LOADING
# =============================================================================


def load_capability(capability_id: str) -> Optional[Dict[str, Any]]:
    """Load capability YAML from registry."""
    cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"

    if not cap_path.exists():
        return None

    with open(cap_path) as f:
        return yaml.safe_load(f)


def list_all_capabilities() -> List[str]:
    """List all capability IDs in the registry."""
    if not CAPABILITY_REGISTRY.exists():
        return []

    capabilities = []
    for cap_file in CAPABILITY_REGISTRY.glob("AURORA_L2_CAPABILITY_*.yaml"):
        # Extract capability ID from filename
        # AURORA_L2_CAPABILITY_CAP-ACT-LLM-RUNS-LIVE.yaml → CAP-ACT-LLM-RUNS-LIVE
        cap_id = cap_file.stem.replace("AURORA_L2_CAPABILITY_", "")
        capabilities.append(cap_id)

    return sorted(capabilities)


# =============================================================================
# OBSERVATION LOADING
# =============================================================================


def find_observation_for_capability(capability_id: str) -> Optional[Dict[str, Any]]:
    """
    Find the most recent observation for a capability.

    Returns the observation JSON if found, None otherwise.
    """
    if not OBSERVATIONS_DIR.exists():
        return None

    # Find all observations for this capability
    observations = []
    for obs_file in OBSERVATIONS_DIR.glob("SDSR_OBSERVATION_*.json"):
        try:
            with open(obs_file) as f:
                obs = json.load(f)
                if obs.get("capability") == capability_id:
                    observations.append((obs_file, obs))
        except (json.JSONDecodeError, IOError):
            continue

    if not observations:
        return None

    # Return most recent by timestamp
    observations.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
    return observations[0][1]


# =============================================================================
# PROMOTION VALIDATION
# =============================================================================


def validate_promotion_eligibility(
    capability: Dict[str, Any],
    observation: Optional[Dict[str, Any]],
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate if a capability is eligible for its current status.

    Returns:
        Tuple of (is_valid, reason, details)
    """
    capability_id = capability.get("id", "unknown")
    status = capability.get("status", "DECLARED")

    details = {
        "capability_id": capability_id,
        "status": status,
        "has_observation": observation is not None,
    }

    # DECLARED status is always valid (no observation required)
    if status == "DECLARED":
        return True, "DECLARED status requires no validation", details

    # DEPRECATED status is always valid (governance decision)
    if status == "DEPRECATED":
        return True, "DEPRECATED status requires no validation", details

    # For OBSERVED or TRUSTED, we need an observation
    if observation is None:
        return (
            False,
            f"Status is {status} but no SDSR observation found",
            details,
        )

    # Check observation results
    promotion = observation.get("promotion", {})
    invariants = observation.get("invariants", {})

    details["observation_id"] = observation.get("observation_id")
    details["observation_timestamp"] = observation.get("timestamp")
    details["l0_passed"] = invariants.get("l0_passed", 0)
    details["l0_failed"] = invariants.get("l0_failed", 0)
    details["l1_passed"] = invariants.get("l1_passed", 0)
    details["l1_failed"] = invariants.get("l1_failed", 0)
    details["promotion_eligible"] = promotion.get("eligible", False)

    # Check if observation showed eligibility
    if not promotion.get("eligible", False):
        l0_all_pass = invariants.get("l0_failed", 1) == 0
        l1_at_least_one = invariants.get("l1_passed", 0) >= 1

        if not l0_all_pass:
            return (
                False,
                f"Status is {status} but L0 transport invariants failed in observation",
                details,
            )
        if not l1_at_least_one:
            return (
                False,
                f"Status is {status} but no L1 domain invariants passed in observation",
                details,
            )
        return (
            False,
            f"Status is {status} but observation shows not eligible for promotion",
            details,
        )

    # TRUSTED requires additional validation (production usage)
    if status == "TRUSTED":
        # For now, just require an observation marked as eligible
        # Future: add production usage metrics check
        details["note"] = "TRUSTED validation: observation eligible, production metrics not checked"

    return True, f"Status {status} is valid based on observation", details


# =============================================================================
# GUARD ENFORCEMENT
# =============================================================================


def run_promotion_guard(
    capability_ids: List[str],
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Run promotion guard validation on capabilities.

    Returns:
        Results dict with: total, valid, violations, results
    """
    results = []
    valid_count = 0
    violation_count = 0

    for cap_id in capability_ids:
        capability = load_capability(cap_id)

        if capability is None:
            results.append({
                "capability_id": cap_id,
                "valid": False,
                "reason": "Capability not found in registry",
                "details": {},
            })
            violation_count += 1
            continue

        observation = find_observation_for_capability(cap_id)
        is_valid, reason, details = validate_promotion_eligibility(capability, observation)

        results.append({
            "capability_id": cap_id,
            "valid": is_valid,
            "reason": reason,
            "details": details,
        })

        if is_valid:
            valid_count += 1
        else:
            violation_count += 1

    return {
        "total": len(capability_ids),
        "valid": valid_count,
        "violations": violation_count,
        "results": results,
    }


def print_results(
    results: Dict[str, Any],
    verbose: bool = False,
    ci_mode: bool = False,
) -> None:
    """Print guard results to console."""
    print(f"\n{'=' * 70}")
    print("SDSR PROMOTION GUARD RESULTS")
    print(f"{'=' * 70}")

    print(f"\nTotal Capabilities: {results['total']}")
    print(f"Valid: {results['valid']}")
    print(f"Violations: {results['violations']}")

    if results['violations'] > 0 or verbose:
        print("\n--- Capability Status ---")

        for result in results['results']:
            status = "VALID" if result['valid'] else "VIOLATION"
            cap_id = result['capability_id']
            reason = result['reason']

            if result['valid']:
                if verbose:
                    print(f"  [OK] {cap_id}")
                    print(f"       {reason}")
            else:
                print(f"  [!!] {cap_id}")
                print(f"       {reason}")

                if verbose and result.get('details'):
                    details = result['details']
                    if details.get('observation_id'):
                        print(f"       Observation: {details['observation_id']}")
                    if 'l0_passed' in details:
                        print(f"       L0: {details['l0_passed']} passed, {details['l0_failed']} failed")
                        print(f"       L1: {details['l1_passed']} passed, {details['l1_failed']} failed")

    if results['violations'] > 0:
        print(f"\n{'=' * 70}")
        print("CAP-E2E-001 VIOLATION: Capability status requires E2E validation")
        print("=" * 70)
        print("\nCapabilities cannot be OBSERVED without passing SDSR scenarios.")
        print("To fix:")
        print("  1. Create SDSR scenario for the capability")
        print("  2. Run: python aurora_sdsr_runner.py --scenario <scenario_id>")
        print("  3. Apply observation: python AURORA_L2_apply_sdsr_observations.py")
        print("  4. Re-run this guard to verify")

        if ci_mode:
            print("\nCI MODE: Failing build due to promotion violations")
    else:
        print("\n✅ All capability statuses are valid")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="AURORA SDSR Promotion Guard - Enforce capability status transitions"
    )

    parser.add_argument(
        "--capability",
        help="Capability ID to validate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all capabilities in registry",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode - exit 1 on violations",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    # Determine which capabilities to validate
    if args.capability:
        capability_ids = [args.capability]
    elif args.all:
        capability_ids = list_all_capabilities()
        if not capability_ids:
            print("No capabilities found in registry", file=sys.stderr)
            return 1
    else:
        print("ERROR: Specify --capability <ID> or --all", file=sys.stderr)
        return 1

    # Run validation
    results = run_promotion_guard(capability_ids, verbose=args.verbose)

    # Output results
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_results(results, verbose=args.verbose, ci_mode=args.ci)

    # Exit code
    if args.ci and results['violations'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
