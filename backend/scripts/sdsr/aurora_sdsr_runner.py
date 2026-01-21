#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CLI invocation
#   Execution: sync
# Role: SDSR Scenario Runner - Execute scenarios and validate invariants
# Reference: PIN-370, SDSR Layered Architecture

"""
AURORA SDSR Scenario Runner

Executes SDSR scenarios and validates responses against domain invariants.

ARCHITECTURE (3-Layer Model):
    L0 — Transport (synth-owned)     → Endpoint reachable, auth works, response exists
    L1 — Domain (domain-owned)       → policy_context, EvidenceMetadata, etc.
    L2 — Capability (optional)       → Specific business rules

EXECUTION FLOW:
    1. Load scenario YAML
    2. Execute API call (inject)
    3. Look up invariant definitions by ID
    4. Execute each invariant against response
    5. Collect and report results
    6. Check OBSERVED promotion eligibility

PROMOTION RULE (MANDATORY):
    A capability may NOT move to OBSERVED unless:
    - All L0 (transport) invariants pass
    - At least ONE L1 (domain) invariant passes

Usage:
    python aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001
    python aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 --dry-run
    python aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 --verbose

Author: AURORA L2 Automation
Reference: PIN-370, SDSR System Contract
"""

import os
import sys
import json
import yaml
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"
OBSERVATIONS_DIR = REPO_ROOT / "backend/scripts/sdsr/observations"

# Add backend to path for imports
sys.path.insert(0, str(BACKEND_ROOT))

# Import domain invariant system
try:
    from sdsr.invariants import (
        get_invariant_by_id,
        execute_invariant,
        execute_invariants,
        check_observed_promotion_eligible,
        get_transport_invariants,
        load_domain_invariants,
    )
    INVARIANTS_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Could not import domain invariants: {e}", file=sys.stderr)
    print("Ensure backend/sdsr/invariants/ exists and is properly configured.", file=sys.stderr)
    INVARIANTS_AVAILABLE = False


# =============================================================================
# CREDENTIAL RESOLUTION
# =============================================================================


def resolve_credentials(auth_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Resolve credentials based on auth mode.

    Auth Modes:
        OBSERVER - Read-only, uses AOS_OBSERVER_KEY or AOS_API_KEY
        SERVICE  - Service-to-service, uses AOS_API_KEY + tenant ID
        USER     - User context, uses AUTH_TOKEN (Clerk JWT)

    Returns:
        Dict of headers with resolved credentials
    """
    mode = auth_config.get("mode", "OBSERVER")
    headers = {}

    if mode == "OBSERVER":
        # Use observer key if available, fallback to API key
        api_key = os.environ.get("AOS_OBSERVER_KEY") or os.environ.get("AOS_API_KEY")
        if api_key:
            headers["X-AOS-Key"] = api_key
        else:
            print("WARNING: No AOS_OBSERVER_KEY or AOS_API_KEY found", file=sys.stderr)

    elif mode == "SERVICE":
        api_key = os.environ.get("AOS_API_KEY")
        tenant_id = os.environ.get("SDSR_TENANT_ID") or os.environ.get("AOS_TENANT_ID")
        if api_key:
            headers["X-AOS-Key"] = api_key
        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id

    elif mode == "USER":
        auth_token = os.environ.get("AUTH_TOKEN")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            print("WARNING: No AUTH_TOKEN found for USER mode", file=sys.stderr)

    return headers


# =============================================================================
# SCENARIO LOADING
# =============================================================================


def load_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Load scenario YAML by ID."""
    scenario_path = SDSR_SCENARIOS_DIR / f"{scenario_id}.yaml"

    if not scenario_path.exists():
        print(f"ERROR: Scenario not found: {scenario_path}", file=sys.stderr)
        return None

    with open(scenario_path) as f:
        return yaml.safe_load(f)


# =============================================================================
# API EXECUTION
# =============================================================================


def execute_inject(
    inject_config: Dict[str, Any],
    auth_headers: Dict[str, str],
    base_url: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Execute the inject (API call) from scenario.

    Returns:
        Dict with: status_code, response, response_time, error
    """
    endpoint = inject_config.get("endpoint", "")
    method = inject_config.get("method", "GET").upper()
    headers = {**inject_config.get("headers", {}), **auth_headers}
    params = inject_config.get("params", {})
    body = inject_config.get("body")

    # Build full URL
    if endpoint.startswith("http"):
        url = endpoint
    else:
        url = f"{base_url.rstrip('/')}{endpoint}"

    start_time = datetime.now(timezone.utc)

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, headers=headers, params=params, json=body, timeout=timeout)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, params=params, json=body, timeout=timeout)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, params=params, timeout=timeout)
        else:
            return {
                "status_code": None,
                "response": None,
                "response_time": 0,
                "error": f"Unsupported method: {method}",
            }

        end_time = datetime.now(timezone.utc)
        response_time = (end_time - start_time).total_seconds() * 1000  # ms

        # Try to parse JSON response
        try:
            response_data = resp.json()
        except Exception:
            response_data = resp.text

        return {
            "status_code": resp.status_code,
            "response": response_data,
            "response_time": response_time,
            "error": None,
        }

    except requests.exceptions.Timeout:
        return {
            "status_code": None,
            "response": None,
            "response_time": timeout * 1000,
            "error": f"Request timed out after {timeout}s",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status_code": None,
            "response": None,
            "response_time": 0,
            "error": f"Connection error: {e}",
        }
    except Exception as e:
        return {
            "status_code": None,
            "response": None,
            "response_time": 0,
            "error": f"Request failed: {e}",
        }


# =============================================================================
# INVARIANT EXECUTION
# =============================================================================


def execute_scenario_invariants(
    invariant_ids: List[str],
    response: Any,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute invariants by ID against a response.

    Args:
        invariant_ids: List of invariant IDs to execute
        response: API response data
        context: Execution context (status_code, panel_class, etc.)

    Returns:
        Results dict with: total, passed, failed, results
    """
    results = []
    passed_count = 0
    failed_count = 0
    l0_passed = 0
    l0_failed = 0
    l1_passed = 0
    l1_failed = 0

    for inv_id in invariant_ids:
        inv = get_invariant_by_id(inv_id)

        if inv is None:
            # Handle legacy/unknown invariant IDs
            results.append({
                "id": inv_id,
                "name": "unknown",
                "passed": False,
                "message": f"Invariant not found in registry: {inv_id}",
                "required": False,
                "error": "NOT_FOUND",
            })
            failed_count += 1
            continue

        # Execute the invariant
        result = execute_invariant(inv, response, context)
        results.append(result)

        layer = inv.get("layer", "L1")

        if result["passed"]:
            passed_count += 1
            if layer == "L0":
                l0_passed += 1
            else:
                l1_passed += 1
        else:
            failed_count += 1
            if layer == "L0":
                l0_failed += 1
            else:
                l1_failed += 1

    return {
        "total": len(invariant_ids),
        "passed": passed_count,
        "failed": failed_count,
        "l0_passed": l0_passed,
        "l0_failed": l0_failed,
        "l1_passed": l1_passed,
        "l1_failed": l1_failed,
        "results": results,
    }


# =============================================================================
# OBSERVATION EMISSION
# =============================================================================


def emit_observation(
    scenario: Dict[str, Any],
    inject_result: Dict[str, Any],
    invariant_results: Dict[str, Any],
    promotion_eligible: bool,
) -> Path:
    """
    Emit SDSR observation JSON.

    This observation can be consumed by AURORA_L2_apply_sdsr_observations.py
    to update capability status.
    """
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    scenario_id = scenario.get("scenario_id", "unknown")
    observation_id = f"SDSR_OBSERVATION_{scenario_id}_{timestamp}"

    observation = {
        "observation_id": observation_id,
        "scenario_id": scenario_id,
        "capability": scenario.get("capability"),
        "panel_id": scenario.get("panel_id"),
        "domain": scenario.get("domain"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inject": {
            "endpoint": scenario.get("inject", {}).get("endpoint"),
            "method": scenario.get("inject", {}).get("method"),
            "status_code": inject_result.get("status_code"),
            "response_time_ms": inject_result.get("response_time"),
            "error": inject_result.get("error"),
        },
        "invariants": {
            "total": invariant_results.get("total", 0),
            "passed": invariant_results.get("passed", 0),
            "failed": invariant_results.get("failed", 0),
            "l0_passed": invariant_results.get("l0_passed", 0),
            "l0_failed": invariant_results.get("l0_failed", 0),
            "l1_passed": invariant_results.get("l1_passed", 0),
            "l1_failed": invariant_results.get("l1_failed", 0),
            "results": invariant_results.get("results", []),
        },
        "promotion": {
            "eligible": promotion_eligible,
            "rule": "L0_ALL_PASS AND L1_AT_LEAST_ONE",
            "recommendation": "OBSERVED" if promotion_eligible else "KEEP_DECLARED",
        },
        "metadata": {
            "runner_version": "1.0.0",
            "generated_by": "aurora_sdsr_runner.py",
        },
    }

    observation_path = OBSERVATIONS_DIR / f"{observation_id}.json"

    with open(observation_path, "w") as f:
        json.dump(observation, f, indent=2, default=str)

    return observation_path


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def run_scenario(
    scenario_id: str,
    base_url: str = "http://localhost:8000",
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Run a single SDSR scenario.

    Args:
        scenario_id: Scenario ID to run
        base_url: Base URL for API calls
        dry_run: If True, don't execute API call
        verbose: If True, print detailed output

    Returns:
        Execution result dict
    """
    if not INVARIANTS_AVAILABLE:
        return {
            "success": False,
            "scenario_id": scenario_id,
            "error": "Invariant system not available",
        }

    # Load scenario
    scenario = load_scenario(scenario_id)
    if scenario is None:
        return {
            "success": False,
            "scenario_id": scenario_id,
            "error": "Scenario not found",
        }

    print(f"\n{'=' * 70}")
    print(f"SDSR Scenario: {scenario_id}")
    print(f"{'=' * 70}")

    # Show scenario info
    print(f"Capability: {scenario.get('capability')}")
    print(f"Panel: {scenario.get('panel_id')}")
    print(f"Domain: {scenario.get('domain')}")
    print(f"Endpoint: {scenario.get('inject', {}).get('endpoint')}")
    print(f"Method: {scenario.get('inject', {}).get('method')}")

    invariant_ids = scenario.get("invariant_ids", [])
    print(f"Invariants: {len(invariant_ids)}")

    if verbose:
        for inv_id in invariant_ids:
            inv = get_invariant_by_id(inv_id)
            if inv:
                print(f"  - {inv_id}: {inv.get('description', 'No description')}")
            else:
                print(f"  - {inv_id}: [NOT FOUND]")

    if dry_run:
        print("\n[DRY RUN] Would execute API call, skipping...")
        return {
            "success": True,
            "scenario_id": scenario_id,
            "dry_run": True,
        }

    # Resolve credentials
    auth_config = scenario.get("auth", {"mode": "OBSERVER"})
    auth_headers = resolve_credentials(auth_config)

    # Execute inject
    print("\n--- Executing Inject ---")
    inject_config = scenario.get("inject", {})
    inject_result = execute_inject(inject_config, auth_headers, base_url)

    print(f"Status: {inject_result.get('status_code')}")
    print(f"Response Time: {inject_result.get('response_time'):.2f}ms")

    if inject_result.get("error"):
        print(f"Error: {inject_result.get('error')}")

    # Build context for invariant execution
    context = {
        "status_code": inject_result.get("status_code"),
        "response_time": inject_result.get("response_time"),
        "panel_class": scenario.get("metadata", {}).get("panel_class", "execution"),
        "endpoint": inject_config.get("endpoint"),
        "method": inject_config.get("method"),
        "domain": scenario.get("domain"),
        "allow_empty_response": True,
    }

    # Execute invariants
    print("\n--- Executing Invariants ---")
    response = inject_result.get("response")
    invariant_results = execute_scenario_invariants(invariant_ids, response, context)

    print(f"Total: {invariant_results['total']}")
    print(f"Passed: {invariant_results['passed']}")
    print(f"Failed: {invariant_results['failed']}")
    print(f"L0 Passed: {invariant_results['l0_passed']}, Failed: {invariant_results['l0_failed']}")
    print(f"L1 Passed: {invariant_results['l1_passed']}, Failed: {invariant_results['l1_failed']}")

    if verbose:
        print("\nInvariant Details:")
        for result in invariant_results.get("results", []):
            status = "PASS" if result["passed"] else "FAIL"
            print(f"  [{status}] {result['id']}: {result['message']}")

    # Check promotion eligibility
    print("\n--- Promotion Check ---")
    l0_all_pass = invariant_results["l0_failed"] == 0
    l1_at_least_one = invariant_results["l1_passed"] >= 1
    promotion_eligible = l0_all_pass and l1_at_least_one

    print(f"L0 All Pass: {l0_all_pass}")
    print(f"L1 At Least One: {l1_at_least_one}")
    print(f"OBSERVED Eligible: {promotion_eligible}")

    if promotion_eligible:
        print("\n✅ PROMOTION: Capability may be promoted to OBSERVED")
    else:
        if not l0_all_pass:
            print("\n❌ BLOCKED: L0 transport invariants failed")
        elif not l1_at_least_one:
            print("\n❌ BLOCKED: No L1 domain invariants passed")

    # Emit observation
    observation_path = emit_observation(
        scenario, inject_result, invariant_results, promotion_eligible
    )
    print(f"\nObservation: {observation_path.relative_to(REPO_ROOT)}")

    return {
        "success": True,
        "scenario_id": scenario_id,
        "inject_result": {
            "status_code": inject_result.get("status_code"),
            "response_time": inject_result.get("response_time"),
            "error": inject_result.get("error"),
        },
        "invariant_results": {
            "total": invariant_results["total"],
            "passed": invariant_results["passed"],
            "failed": invariant_results["failed"],
        },
        "promotion_eligible": promotion_eligible,
        "observation_path": str(observation_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="AURORA SDSR Scenario Runner - Execute and validate scenarios"
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario ID to execute",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for API calls (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't execute API call, just validate scenario",
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

    result = run_scenario(
        scenario_id=args.scenario,
        base_url=args.base_url,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("success") else 1

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
