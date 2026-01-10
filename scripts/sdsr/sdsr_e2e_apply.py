#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CLI invocation
#   Execution: sync
# Role: SDSR End-to-End Orchestrator (LEAK-3 + LEAK-4 fix)
# Reference: AURORA_L2 Mechanical Truth Bridge

"""
SDSR End-to-End Apply Orchestrator

PURPOSE:
    Orchestrate the complete SDSR → AURORA_L2 → UI pipeline.
    This is the SINGLE EXPLICIT entry point for E2E scenario application.

PIPELINE:
    1. inject_synthetic.py --wait
       └─ Injects scenario, waits for execution, materializes truth, emits observation
    2. AURORA_L2_apply_sdsr_observations.py
       └─ Records truth: Capability YAML → OBSERVED, Intent YAML → observation_trace
    3. run_aurora_l2_pipeline.sh
       └─ Recompiles UI projection with updated binding status

WHAT THIS IS:
    - Explicit orchestration (not hidden automation)
    - Auditable sequence
    - CI-friendly entry point
    - Single command for full E2E

WHAT THIS IS NOT:
    - NOT a watcher
    - NOT auto-triggered
    - NOT hidden side effects
    - NOT bypassing boundaries

EXIT CODES:
    0 → Full pipeline success
    1 → Injection failed
    2 → Observation file not found
    3 → Applier failed
    4 → Pipeline failed

USAGE:
    python3 scripts/sdsr/sdsr_e2e_apply.py --scenario <path>
    python3 scripts/sdsr/sdsr_e2e_apply.py --scenario <path> --case CASE-A
    python3 scripts/sdsr/sdsr_e2e_apply.py --scenario <path> --dry-run
    python3 scripts/sdsr/sdsr_e2e_apply.py --observation <path>  # Skip injection
"""

import argparse
import subprocess
import sys
from pathlib import Path

# =============================================================================
# EXIT CODES
# =============================================================================
EXIT_SUCCESS = 0
EXIT_INJECTION_FAILED = 1
EXIT_OBSERVATION_NOT_FOUND = 2
EXIT_APPLIER_FAILED = 3
EXIT_PIPELINE_FAILED = 4

# =============================================================================
# PATHS
# =============================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INJECT_SCRIPT = REPO_ROOT / "backend/scripts/sdsr/inject_synthetic.py"
APPLIER_SCRIPT = REPO_ROOT / "scripts/tools/AURORA_L2_apply_sdsr_observations.py"
PIPELINE_SCRIPT = REPO_ROOT / "scripts/tools/run_aurora_l2_pipeline.sh"
OBSERVATIONS_DIR = REPO_ROOT / "sdsr/observations"


# =============================================================================
# HELPERS
# =============================================================================

def log_step(step_num: int, total: int, message: str):
    """Print a step header."""
    print()
    print("=" * 70)
    print(f"[{step_num}/{total}] {message}")
    print("=" * 70)


def log_ok(message: str):
    """Print success message."""
    print(f"  [OK] {message}")


def log_error(message: str):
    """Print error message."""
    print(f"  [ERROR] {message}", file=sys.stderr)


def log_info(message: str):
    """Print info message."""
    print(f"  [INFO] {message}")


def run_command(cmd: list, description: str, dry_run: bool = False) -> tuple[int, str]:
    """
    Run a command and return exit code and output.

    Returns:
        (exit_code, output)
    """
    if dry_run:
        log_info(f"[DRY RUN] Would run: {' '.join(cmd)}")
        return 0, "[dry run]"

    log_info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        # Print output
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")

        if result.stderr and result.returncode != 0:
            for line in result.stderr.strip().split("\n"):
                print(f"    [stderr] {line}", file=sys.stderr)

        return result.returncode, result.stdout

    except Exception as e:
        log_error(f"Command failed: {e}")
        return 1, str(e)


def find_observation_file(scenario_id: str) -> Path | None:
    """Find the observation file for a scenario."""
    # Pattern: SDSR_OBSERVATION_<scenario_id>.json
    pattern = f"SDSR_OBSERVATION_{scenario_id}.json"

    for obs_file in OBSERVATIONS_DIR.glob("SDSR_OBSERVATION_*.json"):
        if obs_file.name == pattern:
            return obs_file

    return None


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def orchestrate_e2e(
    scenario_path: Path | None,
    observation_path: Path | None,
    case_id: str | None,
    timeout: int,
    dry_run: bool,
) -> int:
    """
    Orchestrate the full SDSR → AURORA_L2 → UI pipeline.

    Returns exit code.
    """
    total_steps = 3 if observation_path else 3  # Always 3 steps

    print()
    print("=" * 70)
    print("SDSR END-TO-END ORCHESTRATOR")
    print("=" * 70)
    print(f"  Mode: {'DRY RUN' if dry_run else 'FULL RUN'}")
    if scenario_path:
        print(f"  Scenario: {scenario_path}")
    if observation_path:
        print(f"  Observation: {observation_path}")
    if case_id:
        print(f"  Case: {case_id}")

    # Track scenario_id for observation lookup
    scenario_id = None
    final_observation_path = observation_path

    # =========================================================================
    # STEP 1: Inject and materialize (skip if observation provided)
    # =========================================================================
    if scenario_path and not observation_path:
        log_step(1, total_steps, "INJECT + MATERIALIZE + EMIT")

        cmd = [
            "python3", str(INJECT_SCRIPT),
            "--scenario", str(scenario_path),
            "--wait",
            "--timeout", str(timeout),
        ]
        if case_id:
            cmd.extend(["--case", case_id])

        exit_code, output = run_command(cmd, "inject_synthetic.py", dry_run)

        if exit_code != 0:
            log_error(f"Injection failed with exit code {exit_code}")
            return EXIT_INJECTION_FAILED

        log_ok("Injection + materialization + emission complete")

        # Extract scenario_id from scenario file to find observation
        import yaml
        with open(scenario_path) as f:
            spec = yaml.safe_load(f)
            scenario_id = spec.get("scenario_id")

        if scenario_id:
            final_observation_path = find_observation_file(scenario_id)
            if final_observation_path:
                log_ok(f"Observation file: {final_observation_path}")
            else:
                log_error(f"Observation file not found for scenario {scenario_id}")
                log_info(f"Expected: {OBSERVATIONS_DIR}/SDSR_OBSERVATION_{scenario_id}.json")
                return EXIT_OBSERVATION_NOT_FOUND

    elif observation_path:
        log_step(1, total_steps, "SKIP INJECTION (observation provided)")
        log_info(f"Using provided observation: {observation_path}")
        final_observation_path = observation_path

    else:
        log_error("Either --scenario or --observation must be provided")
        return EXIT_INJECTION_FAILED

    # =========================================================================
    # STEP 2: Apply observation (LEAK-3 fix)
    # =========================================================================
    log_step(2, total_steps, "APPLY OBSERVATION → AURORA_L2")

    if not final_observation_path or not final_observation_path.exists():
        log_error(f"Observation file not found: {final_observation_path}")
        return EXIT_OBSERVATION_NOT_FOUND

    cmd = [
        "python3", str(APPLIER_SCRIPT),
        "--observation", str(final_observation_path),
    ]

    exit_code, _ = run_command(cmd, "AURORA_L2_apply_sdsr_observations.py", dry_run)

    if exit_code != 0:
        log_error(f"Applier failed with exit code {exit_code}")
        return EXIT_APPLIER_FAILED

    log_ok("Observation applied: Capability YAML + Intent YAML updated")

    # =========================================================================
    # STEP 3: Run UI pipeline (LEAK-4 fix)
    # =========================================================================
    log_step(3, total_steps, "RECOMPILE UI PROJECTION")

    cmd = [str(PIPELINE_SCRIPT)]

    exit_code, _ = run_command(cmd, "run_aurora_l2_pipeline.sh", dry_run)

    if exit_code != 0:
        log_error(f"Pipeline failed with exit code {exit_code}")
        return EXIT_PIPELINE_FAILED

    log_ok("UI projection recompiled")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print("ORCHESTRATION COMPLETE")
    print("=" * 70)
    if dry_run:
        print("  [DRY RUN] No files were modified")
    else:
        print("  [OK] Full pipeline executed successfully")
        print()
        print("  Truth has been:")
        print("    1. Materialized (ScenarioSDSROutput)")
        print("    2. Witnessed (SDSR_OBSERVATION_*.json)")
        print("    3. Recorded (Capability YAML → OBSERVED)")
        print("    4. Traced (Intent YAML → observation_trace)")
        print("    5. Reflected (UI projection recompiled)")

    return EXIT_SUCCESS


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SDSR End-to-End Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline:
  1. inject_synthetic.py --wait → Materialize + Emit
  2. AURORA_L2_apply_sdsr_observations.py → Record truth
  3. run_aurora_l2_pipeline.sh → Reflect in UI

Examples:
  # Full E2E from scenario
  python3 scripts/sdsr/sdsr_e2e_apply.py --scenario backend/scripts/sdsr/scenarios/SDSR-E2E-001.yaml

  # With case selection
  python3 scripts/sdsr/sdsr_e2e_apply.py --scenario scenarios/multi.yaml --case CASE-A

  # Skip injection, apply existing observation
  python3 scripts/sdsr/sdsr_e2e_apply.py --observation sdsr/observations/SDSR_OBSERVATION_E2E_001.json

  # Dry run
  python3 scripts/sdsr/sdsr_e2e_apply.py --scenario scenarios/test.yaml --dry-run
        """,
    )

    parser.add_argument(
        "--scenario",
        type=Path,
        help="Path to SDSR scenario YAML file",
    )

    parser.add_argument(
        "--observation",
        type=Path,
        help="Path to existing SDSR observation JSON (skips injection)",
    )

    parser.add_argument(
        "--case",
        type=str,
        help="Case ID for multi-case scenarios",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for execution wait (default: 120)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without executing",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.scenario and not args.observation:
        parser.error("Either --scenario or --observation must be provided")

    if args.scenario and args.observation:
        parser.error("Cannot specify both --scenario and --observation")

    if args.scenario and not args.scenario.exists():
        parser.error(f"Scenario file not found: {args.scenario}")

    if args.observation and not args.observation.exists():
        parser.error(f"Observation file not found: {args.observation}")

    # Run orchestration
    exit_code = orchestrate_e2e(
        scenario_path=args.scenario,
        observation_path=args.observation,
        case_id=args.case,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
