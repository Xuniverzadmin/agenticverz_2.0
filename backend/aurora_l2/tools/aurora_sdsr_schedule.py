#!/usr/bin/env python3
"""
AURORA L2 SDSR Scheduler

Runs SDSR verification for all capabilities on a schedule.
Can be invoked manually or via cron.

Usage:
    # Run all SDSR scenarios
    python aurora_sdsr_schedule.py --all

    # Run and auto-promote eligible
    python aurora_sdsr_schedule.py --all --promote

    # Run specific capability
    python aurora_sdsr_schedule.py --capability overview.activity_snapshot

    # Dry run (show what would execute)
    python aurora_sdsr_schedule.py --all --dry-run

Cron Example (run nightly at 3am):
    0 3 * * * cd /path/to/repo && python backend/aurora_l2/tools/aurora_sdsr_schedule.py --all >> /var/log/aurora_sdsr.log 2>&1

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
TOOLS_DIR = Path(__file__).parent
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"
SCHEDULE_LOG_DIR = REPO_ROOT / "backend/scripts/sdsr/schedule_logs"


def get_capabilities_by_status(status: str) -> List[str]:
    """Get all capabilities with given status."""
    capabilities = []
    if not CAPABILITY_REGISTRY.exists():
        return capabilities

    for cap_file in CAPABILITY_REGISTRY.glob("AURORA_L2_CAPABILITY_*.yaml"):
        with open(cap_file) as f:
            cap = yaml.safe_load(f)
            if cap and cap.get('status') == status:
                capabilities.append(cap.get('capability_id'))

    return capabilities


def get_scenarios_for_capability(capability_id: str) -> List[str]:
    """Find scenarios that test a capability."""
    scenarios = []
    if not SDSR_SCENARIOS_DIR.exists():
        return scenarios

    for scenario_file in SDSR_SCENARIOS_DIR.glob("SDSR-*.yaml"):
        with open(scenario_file) as f:
            scenario = yaml.safe_load(f)
            if scenario and scenario.get('capability') == capability_id:
                scenarios.append(scenario.get('scenario_id'))

    return scenarios


def get_all_scenarios() -> List[str]:
    """Get all scenario IDs."""
    scenarios = []
    if not SDSR_SCENARIOS_DIR.exists():
        return scenarios

    for scenario_file in SDSR_SCENARIOS_DIR.glob("SDSR-*.yaml"):
        with open(scenario_file) as f:
            scenario = yaml.safe_load(f)
            if scenario:
                scenarios.append(scenario.get('scenario_id'))

    return scenarios


def run_sdsr_scenario(scenario_id: str, skip_coherency: bool = False) -> Dict:
    """Run a single SDSR scenario."""
    cmd = [
        sys.executable,
        str(TOOLS_DIR / "aurora_sdsr_runner.py"),
        "--scenario", scenario_id,
    ]
    if skip_coherency:
        cmd.append("--skip-coherency")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(TOOLS_DIR),
        )
        return {
            'scenario_id': scenario_id,
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            'scenario_id': scenario_id,
            'success': False,
            'returncode': -1,
            'error': 'Timeout',
        }
    except Exception as e:
        return {
            'scenario_id': scenario_id,
            'success': False,
            'returncode': -1,
            'error': str(e),
        }


def run_trust_evaluation(promote: bool = False) -> Dict:
    """Run trust evaluation."""
    cmd = [
        sys.executable,
        str(TOOLS_DIR / "aurora_trust_evaluator.py"),
        "--all",
    ]
    if promote:
        cmd.append("--promote")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(TOOLS_DIR),
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def run_staleness_check() -> Dict:
    """Run intent staleness check."""
    cmd = [
        sys.executable,
        str(TOOLS_DIR / "aurora_intent_registry_sync.py"),
        "--verify",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(TOOLS_DIR),
        )
        return {
            'success': result.returncode == 0,
            'stale_count': result.returncode,  # Non-zero = stale intents
            'stdout': result.stdout,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def write_schedule_log(results: Dict):
    """Write schedule run log."""
    SCHEDULE_LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc)
    log_id = timestamp.strftime("%Y%m%d-%H%M%S")
    log_file = SCHEDULE_LOG_DIR / f"SDSR_SCHEDULE_{log_id}.json"

    log_entry = {
        'log_id': log_id,
        'timestamp': timestamp.isoformat(),
        **results,
    }

    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)

    return log_file


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 SDSR Scheduler - Run verification on schedule"
    )
    parser.add_argument("--all", action="store_true", help="Run all SDSR scenarios")
    parser.add_argument("--capability", help="Run scenarios for specific capability")
    parser.add_argument("--promote", action="store_true",
                        help="Auto-promote eligible capabilities to TRUSTED")
    parser.add_argument("--skip-coherency", action="store_true",
                        help="Skip coherency checks (use with caution)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if not args.all and not args.capability:
        parser.print_help()
        return 1

    print("=" * 70)
    print("AURORA L2 SDSR Scheduled Run")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # Determine scenarios to run
    scenarios_to_run = []
    if args.all:
        scenarios_to_run = get_all_scenarios()
    elif args.capability:
        scenarios_to_run = get_scenarios_for_capability(args.capability)

    if not scenarios_to_run:
        print("\nNo scenarios found to run.")
        return 0

    print(f"\nScenarios to run: {len(scenarios_to_run)}")
    for s in scenarios_to_run:
        print(f"  - {s}")

    if args.dry_run:
        print("\n[DRY RUN] Would execute above scenarios")
        return 0

    # Run SDSR scenarios
    print("\n" + "-" * 70)
    print("Phase 1: SDSR Verification")
    print("-" * 70)

    sdsr_results = []
    passed = 0
    failed = 0
    blocked = 0

    for scenario_id in scenarios_to_run:
        print(f"\n>>> {scenario_id}")
        result = run_sdsr_scenario(scenario_id, skip_coherency=args.skip_coherency)
        sdsr_results.append(result)

        if result['success']:
            print("    PASS")
            passed += 1
        elif result.get('returncode') == 2:
            print("    BLOCKED (coherency)")
            blocked += 1
        else:
            print("    FAIL")
            failed += 1

        if args.verbose and result.get('stdout'):
            for line in result['stdout'].split('\n')[:10]:
                print(f"    {line}")

    print(f"\nSDSR Results: {passed} passed, {failed} failed, {blocked} blocked")

    # Run trust evaluation
    print("\n" + "-" * 70)
    print("Phase 2: Trust Evaluation")
    print("-" * 70)

    trust_result = run_trust_evaluation(promote=args.promote)
    if trust_result.get('stdout'):
        print(trust_result['stdout'])

    # Run staleness check
    print("\n" + "-" * 70)
    print("Phase 3: Intent Staleness Check")
    print("-" * 70)

    staleness_result = run_staleness_check()
    if staleness_result.get('stdout'):
        print(staleness_result['stdout'])

    # Write log
    log_file = write_schedule_log({
        'sdsr_results': sdsr_results,
        'sdsr_summary': {
            'total': len(scenarios_to_run),
            'passed': passed,
            'failed': failed,
            'blocked': blocked,
        },
        'trust_evaluation': trust_result,
        'staleness_check': staleness_result,
        'promote_enabled': args.promote,
    })

    print("\n" + "=" * 70)
    print("Schedule Run Complete")
    print(f"Log: {log_file.relative_to(REPO_ROOT)}")
    print("=" * 70)

    # Exit code: 0 if all passed, 1 if any failed
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
