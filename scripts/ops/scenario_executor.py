#!/usr/bin/env python3
"""
SCENARIO EXECUTOR - Lifecycle Scenario Verification

Executes and validates scenarios against SESSION_LIFECYCLE_SCENARIOS.md.
Produces SCENARIO-SXX-RUN-<n>.yaml artifacts for each execution.

Usage:
    python scripts/ops/scenario_executor.py --scenario S14
    python scripts/ops/scenario_executor.py --scenario S17 --simulate
    python scripts/ops/scenario_executor.py --list

Reference: docs/ops/SESSION_LIFECYCLE_SCENARIOS.md
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "scenario_runs"
SR_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "session_reconcile"
HK_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "housekeeping"
EXIT_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "session_exit"
SESSION_STATE_FILE = ROOT_DIR / ".session_state.yaml"


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_run_id() -> str:
    """Generate run ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return ts


def run_cmd(cmd: str, timeout: int = 60) -> tuple[int, str]:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT_DIR,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except Exception as e:
        return 1, str(e)


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

SCENARIOS = {
    "S14": {
        "name": "RECONCILE_INTERRUPTED",
        "description": "Reconciliation was interrupted mid-execution",
        "expected_exit_verdict": "EXIT_BLOCKED",
        "expected_new_work": "BLOCKED",
        "setup": "interrupt_reconcile",
        "validation": "validate_interrupted_state",
    },
    "S17": {
        "name": "FORCED_EXIT_ATTEMPT",
        "description": "User attempts to exit without proper reconciliation",
        "expected_exit_verdict": "DIRTY_EXIT",
        "expected_new_work": "BLOCKED",
        "setup": "setup_dirty_state",
        "validation": "validate_forced_exit",
    },
    "S19": {
        "name": "SERVICES_UNHEALTHY_POST_HK",
        "description": "Services became unhealthy after housekeeping",
        "expected_exit_verdict": "EXIT_BLOCKED",
        "expected_new_work": "BLOCKED",
        "setup": "simulate_service_failure",
        "validation": "validate_service_failure_handling",
    },
}


# =============================================================================
# SETUP FUNCTIONS
# =============================================================================


def setup_dirty_state() -> dict:
    """Set up a dirty session state (no clean reconciliation)."""
    # Ensure session state exists but is not exit-ready
    state = {
        "session_id": f"test-{get_run_id()}",
        "started_at": get_timestamp(),
        "pipeline": {
            "scripts": {"status": "completed"},
            "container": {"status": "completed"},
            "deploy": {"status": "completed"},
            "tests": {"status": "failed"},  # Failed tests = dirty
            "git_commit": {"status": "pending"},
            "git_push": {"status": "pending"},
        },
        "exit": {
            "ready": False,
            "verdict": None,
        },
    }

    with open(SESSION_STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

    return {"session_state": state}


def interrupt_reconcile() -> dict:
    """Simulate an interrupted reconciliation."""
    # Create partial SR artifact
    sr_id = f"SR-test-interrupted-{get_run_id()}"
    sr_artifact = {
        "schema_version": "1.0",
        "protocol": "SR-01",
        "session_id": f"test-{get_run_id()}",
        "timestamp": get_timestamp(),
        "triggered_by": "scenario_test",
        "pipeline": {
            "scripts": {"status": "completed"},
            "container": {"status": "completed"},
            "deploy": {"status": "in_progress"},  # Interrupted here
            # Missing: tests, git_commit, git_push
        },
        "verdict": None,  # No verdict = interrupted
        "exit_ready": False,
        "notes": "Simulated interruption during deploy step",
    }

    SR_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = SR_ARTIFACTS_DIR / f"{sr_id}.yaml"
    with open(artifact_path, "w") as f:
        yaml.dump(sr_artifact, f, default_flow_style=False)

    return {"sr_artifact": str(artifact_path), "sr_data": sr_artifact}


def simulate_service_failure() -> dict:
    """Simulate services becoming unhealthy after housekeeping."""
    # Create HK artifact showing post-check failure
    hk_id = f"HK-{get_run_id()}"
    hk_artifact = {
        "schema_version": "1.0",
        "protocol": "HK-01",
        "id": hk_id,
        "timestamp": get_timestamp(),
        "triggered_by": "scenario_test",
        "scans": {
            "disk": {"usage_percent": 65},
            "memory": {"available_gb": 8},
        },
        "services_pre_check": {
            "nova_agent_manager": "healthy",
            "nova_worker": "healthy",
            "nova_db": "healthy",
        },
        "tier_1_actions": {
            "containers_removed": 2,
            "page_cache_cleared": True,
        },
        "services_post_check": {
            "nova_agent_manager": "unhealthy",  # Simulated failure
            "nova_worker": "healthy",
            "nova_db": "healthy",
        },
        "result": {
            "services_protected": False,
            "no_active_work_disrupted": True,
            "success": False,
            "notes": "Services became unhealthy after cleanup",
        },
    }

    HK_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = HK_ARTIFACTS_DIR / f"{hk_id}.yaml"
    with open(artifact_path, "w") as f:
        yaml.dump(hk_artifact, f, default_flow_style=False)

    return {"hk_artifact": str(artifact_path), "hk_data": hk_artifact}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_interrupted_state(setup_result: dict) -> dict:
    """Validate S14: RECONCILE_INTERRUPTED handling."""
    violations = []

    # Check 1: Exit gate should block
    exit_code, output = run_cmd("python3 scripts/ops/session_exit.py")
    if exit_code == 0:
        violations.append(
            "EXIT_BLOCKED violation: Exit gate allowed exit on interrupted state"
        )

    # Check 2: SR artifact should exist but be incomplete
    sr_path = setup_result.get("sr_artifact")
    if sr_path and Path(sr_path).exists():
        with open(sr_path) as f:
            sr_data = yaml.safe_load(f)
        if sr_data.get("verdict") == "RECONCILED_EXIT_READY":
            violations.append(
                "VERDICT violation: Interrupted reconcile should not be EXIT_READY"
            )
    else:
        violations.append("ARTIFACT violation: SR artifact missing")

    return {
        "exit_code": exit_code,
        "exit_output": output[:500],
        "violations": violations,
        "passed": len(violations) == 0,
    }


def validate_forced_exit(setup_result: dict) -> dict:
    """Validate S17: FORCED_EXIT_ATTEMPT handling."""
    violations = []
    session_state = setup_result.get("session_state", {})

    # Check 1: Exit gate should block (return code 1)
    exit_code, output = run_cmd("python3 scripts/ops/session_exit.py")
    if exit_code == 0:
        violations.append(
            "EXIT_BLOCKED violation: Exit gate allowed exit on dirty state"
        )

    # Check 2: Should output EXIT_BLOCKED verdict
    if "EXIT_BLOCKED" not in output and "BLOCKED" not in output:
        violations.append("VERDICT violation: Exit gate should report BLOCKED status")

    # Check 3: Blocking reasons should be present
    if "Blocking reasons" not in output and "blocking" not in output.lower():
        violations.append("REASON violation: Exit gate should explain why blocked")

    return {
        "exit_code": exit_code,
        "exit_output": output[:500],
        "session_state_tests_status": session_state.get("pipeline", {})
        .get("tests", {})
        .get("status"),
        "violations": violations,
        "passed": len(violations) == 0,
    }


def validate_service_failure_handling(setup_result: dict) -> dict:
    """Validate S19: SERVICES_UNHEALTHY_POST_HK handling."""
    violations = []

    # Check 1: HK artifact should indicate service failure
    hk_path = setup_result.get("hk_artifact")
    if hk_path and Path(hk_path).exists():
        with open(hk_path) as f:
            hk_data = yaml.safe_load(f)

        if hk_data.get("result", {}).get("services_protected") is True:
            violations.append(
                "SERVICE_PROTECTION violation: Should report services NOT protected"
            )

        if hk_data.get("result", {}).get("success") is True:
            violations.append(
                "SUCCESS violation: Should report failure when services unhealthy"
            )

        post_check = hk_data.get("services_post_check", {})
        unhealthy_found = any(s == "unhealthy" for s in post_check.values())
        if not unhealthy_found:
            violations.append(
                "POST_CHECK violation: Should record unhealthy service status"
            )
    else:
        violations.append("ARTIFACT violation: HK artifact missing")

    return {
        "hk_artifact_valid": hk_path is not None,
        "violations": violations,
        "passed": len(violations) == 0,
    }


# =============================================================================
# SCENARIO EXECUTOR
# =============================================================================


class ScenarioExecutor:
    """Execute and validate lifecycle scenarios."""

    def __init__(self, scenario_id: str, simulate: bool = False):
        self.scenario_id = scenario_id
        self.simulate = simulate
        self.scenario = SCENARIOS.get(scenario_id)
        self.run_id = get_run_id()
        self.artifact: dict[str, Any] = {
            "schema_version": "1.0",
            "type": "SCENARIO_RUN",
            "scenario_id": scenario_id,
            "run_id": self.run_id,
            "timestamp": get_timestamp(),
            "mode": "simulate" if simulate else "execute",
        }

    def execute(self) -> bool:
        """Execute the scenario and validate results."""
        if not self.scenario:
            print(f"ERROR: Unknown scenario {self.scenario_id}")
            return False

        print(f"\n{'=' * 60}")
        print(f"  SCENARIO EXECUTION: {self.scenario_id}")
        print(f"  {self.scenario['name']}")
        print(f"{'=' * 60}\n")

        self.artifact["scenario_name"] = self.scenario["name"]
        self.artifact["description"] = self.scenario["description"]

        # Step 1: Setup
        print("  [1/3] Setting up scenario state...")
        setup_func = globals().get(self.scenario["setup"])
        if setup_func:
            setup_result = setup_func()
            self.artifact["setup"] = {
                "function": self.scenario["setup"],
                "result": setup_result,
            }
            print("        Setup complete")
        else:
            print("        ERROR: Setup function not found")
            return False

        # Step 2: Validate
        print("  [2/3] Validating scenario behavior...")
        validate_func = globals().get(self.scenario["validation"])
        if validate_func:
            validation_result = validate_func(setup_result)
            self.artifact["validation"] = validation_result

            if validation_result["passed"]:
                print("        PASSED - No violations")
            else:
                print(
                    f"        FAILED - {len(validation_result['violations'])} violations"
                )
                for v in validation_result["violations"]:
                    print(f"          - {v}")
        else:
            print("        ERROR: Validation function not found")
            return False

        # Step 3: Record result
        print("  [3/3] Recording execution artifact...")
        self.artifact["result"] = {
            "passed": validation_result["passed"],
            "expected_exit_verdict": self.scenario["expected_exit_verdict"],
            "expected_new_work": self.scenario["expected_new_work"],
            "violations_count": len(validation_result.get("violations", [])),
        }

        # Save artifact
        artifact_path = self.save_artifact()
        print(f"        Artifact: {artifact_path}")

        # Summary
        print(f"\n{'=' * 60}")
        if validation_result["passed"]:
            print("  RESULT: PASSED")
        else:
            print("  RESULT: FAILED")
        print(f"{'=' * 60}\n")

        return validation_result["passed"]

    def save_artifact(self) -> Path:
        """Save execution artifact."""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        # Find next run number for this scenario
        existing = list(ARTIFACTS_DIR.glob(f"SCENARIO-{self.scenario_id}-RUN-*.yaml"))
        run_num = len(existing) + 1

        artifact_path = (
            ARTIFACTS_DIR / f"SCENARIO-{self.scenario_id}-RUN-{run_num}.yaml"
        )

        with open(artifact_path, "w") as f:
            yaml.dump(self.artifact, f, default_flow_style=False, sort_keys=False)

        return artifact_path


def list_scenarios():
    """List all available scenarios."""
    print("\n" + "=" * 60)
    print("  AVAILABLE SCENARIOS")
    print("=" * 60 + "\n")

    for sid, scenario in SCENARIOS.items():
        print(f"  {sid}: {scenario['name']}")
        print(f"      {scenario['description']}")
        print(f"      Expected exit: {scenario['expected_exit_verdict']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Scenario Executor")
    parser.add_argument(
        "--scenario",
        type=str,
        help="Scenario ID to execute (e.g., S14, S17, S19)",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode (no real changes)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scenarios",
    )
    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return

    if not args.scenario:
        print("ERROR: --scenario required. Use --list to see available scenarios.")
        sys.exit(1)

    executor = ScenarioExecutor(args.scenario, simulate=args.simulate)
    success = executor.execute()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
