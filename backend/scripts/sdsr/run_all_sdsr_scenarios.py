#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Batch SDSR Runner - Execute all scenarios systematically by domain order.
# artifact_class: CODE
"""
Batch SDSR Runner - Execute all scenarios systematically by domain order.

This script:
1. Discovers all SDSR scenarios
2. Runs them sequentially by domain (OVR → ACT → INC → POL → LOG → ANL)
3. Collects results
4. Applies passing observations

Usage:
    python run_all_sdsr_scenarios.py --dry-run   # Show what would run
    python run_all_sdsr_scenarios.py --run       # Execute and apply observations
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
OBSERVATIONS_DIR = Path(__file__).parent / "observations"
AURORA_RUNNER = Path(__file__).parent.parent.parent / "aurora_l2/tools/aurora_sdsr_runner.py"
AURORA_APPLY = Path(__file__).parent.parent.parent / "aurora_l2/tools/aurora_apply_observation.py"

# Domain order for systematic execution
DOMAIN_ORDER = ["OVR", "ACT", "INC", "POL", "LOG", "ANL", "ANA"]


def get_domain_prefix(panel_id: str) -> str:
    """Extract domain prefix from panel ID."""
    return panel_id.split("-")[0]


def sort_by_domain(scenarios: list) -> list:
    """Sort scenarios by domain order."""
    def domain_key(s):
        prefix = get_domain_prefix(s)
        try:
            return DOMAIN_ORDER.index(prefix)
        except ValueError:
            return len(DOMAIN_ORDER)
    return sorted(scenarios, key=lambda s: (domain_key(s), s))


def discover_scenarios():
    """Find all SDSR scenarios for panels."""
    scenarios = []
    for yaml_file in SCENARIOS_DIR.glob("SDSR-*-O?-001.yaml"):
        # Extract panel ID: SDSR-ACT-LLM-COMP-O1-001.yaml -> ACT-LLM-COMP-O1
        name = yaml_file.stem  # SDSR-ACT-LLM-COMP-O1-001
        parts = name.split("-")
        # Remove SDSR- prefix and -001 suffix
        if parts[0] == "SDSR" and parts[-1] == "001":
            panel_id = "-".join(parts[1:-1])
            scenarios.append(panel_id)
    return sort_by_domain(scenarios)


def run_scenario(panel_id: str) -> dict:
    """Run SDSR scenario for a panel."""
    result = {
        "panel_id": panel_id,
        "status": None,
        "response_code": None,
        "error": None,
    }

    try:
        cmd = ["python3", str(AURORA_RUNNER), "--panel", panel_id]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = proc.stdout + proc.stderr

        # Parse result
        if "✅ SDSR PASSED" in output:
            result["status"] = "PASS"
        elif "❌ SDSR FAILED" in output:
            result["status"] = "FAIL"
        else:
            result["status"] = "ERROR"
            result["error"] = output[:200]

        # Extract response code
        for line in output.split("\n"):
            if "Response Code:" in line:
                result["response_code"] = line.split(":")[-1].strip()
                break

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = "Scenario timed out after 60s"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    return result


def apply_observation(capability_id: str) -> bool:
    """Apply observation for a capability."""
    try:
        cmd = ["python3", str(AURORA_APPLY), "--capability", capability_id]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return "✅ Observation applied successfully" in proc.stdout
    except Exception:
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch SDSR Runner")
    parser.add_argument("--dry-run", action="store_true", help="Show scenarios without running")
    parser.add_argument("--run", action="store_true", help="Execute scenarios and apply observations")
    parser.add_argument("--domain", help="Run only specific domain (OVR, ACT, INC, POL, LOG)")
    args = parser.parse_args()

    print("=" * 70)
    print("BATCH SDSR RUNNER")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Discover scenarios
    scenarios = discover_scenarios()

    # Filter by domain if specified
    if args.domain:
        scenarios = [s for s in scenarios if get_domain_prefix(s) == args.domain.upper()]

    print(f"\nDiscovered {len(scenarios)} scenarios\n")

    if args.dry_run:
        print("DRY RUN - Scenarios to execute:\n")
        current_domain = None
        for panel_id in scenarios:
            domain = get_domain_prefix(panel_id)
            if domain != current_domain:
                print(f"\n=== {domain} Domain ===")
                current_domain = domain
            print(f"  {panel_id}")
        return

    if not args.run:
        parser.print_help()
        return

    # Execute scenarios
    results = {"pass": [], "fail": [], "error": []}
    current_domain = None

    for i, panel_id in enumerate(scenarios, 1):
        domain = get_domain_prefix(panel_id)
        if domain != current_domain:
            print(f"\n{'=' * 70}")
            print(f"=== {domain} Domain ===")
            print("=" * 70)
            current_domain = domain

        print(f"\n[{i}/{len(scenarios)}] Running: {panel_id}")
        result = run_scenario(panel_id)

        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"  {status_icon} Status: {result['status']}, HTTP: {result['response_code']}")

        if result["status"] == "PASS":
            results["pass"].append(panel_id)
        elif result["status"] == "FAIL":
            results["fail"].append(panel_id)
        else:
            results["error"].append(panel_id)
            if result["error"]:
                print(f"  ⚠️  Error: {result['error'][:100]}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total scenarios: {len(scenarios)}")
    print(f"  ✅ PASSED: {len(results['pass'])}")
    print(f"  ❌ FAILED: {len(results['fail'])}")
    print(f"  ⚠️  ERRORS: {len(results['error'])}")

    if results["fail"]:
        print(f"\nFailed panels ({len(results['fail'])}):")
        for p in results["fail"]:
            print(f"  - {p}")

    if results["error"]:
        print(f"\nError panels ({len(results['error'])}):")
        for p in results["error"]:
            print(f"  - {p}")

    # Save results
    results_file = OBSERVATIONS_DIR / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(scenarios),
            "pass": results["pass"],
            "fail": results["fail"],
            "error": results["error"],
        }, f, indent=2)
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
