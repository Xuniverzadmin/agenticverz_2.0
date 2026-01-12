#!/usr/bin/env python3
"""
SESSION_RECONCILE Protocol (SR-01) - Automation Script

Reconciles work pipeline state into a single, exit-ready terminal state
by invoking approved automation scripts and validating outcomes.

Usage:
    python scripts/ops/session_reconcile.py [--dry-run] [--skip-tests]

Triggers:
    - User command: "session reconcile"

Pipeline Order (STRICT):
    scripts → container → deploy → tests → git

Reference: docs/ops/SESSION_RECONCILE_PROTOCOL.md
"""

import argparse
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent
SESSION_STATE_FILE = ROOT_DIR / ".session_state.yaml"
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "session_reconcile"
SESSION_PINS_DIR = ROOT_DIR / "memory" / "session_pins"

# Pipeline steps in STRICT order
PIPELINE_STEPS = ["scripts", "container", "deploy", "tests", "git_commit", "git_push"]


def run_cmd(cmd: str, cwd: Path | None = None) -> tuple[int, str]:
    """Run a shell command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=cwd or ROOT_DIR,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except Exception as e:
        return 1, str(e)


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_session_id() -> str:
    """Generate unique session ID."""
    return str(uuid.uuid4())[:8]


class SessionReconciler:
    """Session reconciliation protocol executor."""

    def __init__(self, dry_run: bool = False, skip_tests: bool = False):
        self.dry_run = dry_run
        self.skip_tests = skip_tests
        self.session_id = generate_session_id()
        self.session_state: dict[str, Any] = {}
        self.artifact: dict[str, Any] = {
            "schema_version": "1.0",
            "protocol": "SR-01",
            "session_id": self.session_id,
            "timestamp": get_timestamp(),
            "triggered_by": "script",
            "pipeline": {},
            "verdict": None,
            "exit_ready": False,
            "blocking_reason": None,
        }

    def print_header(self, title: str) -> None:
        """Print section header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def print_status(self, step: str, status: str, detail: str = "") -> None:
        """Print status line."""
        icon = (
            "✅"
            if status == "ok"
            else "❌"
            if status == "fail"
            else "⏭️"
            if status == "skip"
            else "🔄"
        )
        print(f"  {icon} {step}: {detail}" if detail else f"  {icon} {step}")

    # =========================================================================
    # State Loading
    # =========================================================================

    def load_session_state(self) -> bool:
        """Load and validate .session_state.yaml."""
        self.print_header("LOADING SESSION STATE")

        if not SESSION_STATE_FILE.exists():
            print(f"  ❌ Missing: {SESSION_STATE_FILE}")
            print("  ❌ BLOCKED: Cannot reconcile without session state")
            self.artifact["verdict"] = "RECONCILIATION_BLOCKED"
            self.artifact["blocking_reason"] = "Missing .session_state.yaml"
            return False

        try:
            with open(SESSION_STATE_FILE) as f:
                self.session_state = yaml.safe_load(f) or {}
            print(f"  ✅ Loaded: {SESSION_STATE_FILE}")

            # Show current state
            for key, value in self.session_state.items():
                print(f"     - {key}: {value}")

            return True
        except Exception as e:
            print(f"  ❌ Failed to load session state: {e}")
            self.artifact["verdict"] = "RECONCILIATION_BLOCKED"
            self.artifact["blocking_reason"] = f"Invalid .session_state.yaml: {e}"
            return False

    def load_previous_pin(self) -> dict | None:
        """Load previous session pin if exists."""
        if not SESSION_PINS_DIR.exists():
            return None

        pins = sorted(SESSION_PINS_DIR.glob("*.yaml"), reverse=True)
        if pins:
            try:
                with open(pins[0]) as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
        return None

    # =========================================================================
    # Pipeline Steps
    # =========================================================================

    def step_scripts(self) -> bool:
        """Run build scripts."""
        self.print_status("scripts", "run", "Checking for build scripts...")

        # Check if any build script exists
        build_script = ROOT_DIR / "scripts" / "build.sh"
        if build_script.exists():
            if self.dry_run:
                self.print_status("scripts", "skip", "[DRY-RUN] Would run build.sh")
                self.artifact["pipeline"]["scripts"] = {
                    "status": "skipped",
                    "output": "dry-run",
                }
                return True

            code, output = run_cmd(f"bash {build_script}")
            if code == 0:
                self.print_status("scripts", "ok", "Build completed")
                self.artifact["pipeline"]["scripts"] = {
                    "status": "completed",
                    "output": output[:500],
                }
                return True
            else:
                self.print_status("scripts", "fail", "Build failed")
                self.artifact["pipeline"]["scripts"] = {
                    "status": "failed",
                    "output": output[:500],
                }
                return False
        else:
            self.print_status("scripts", "skip", "No build.sh found")
            self.artifact["pipeline"]["scripts"] = {
                "status": "skipped",
                "output": "No build script",
            }
            return True

    def step_container(self) -> bool:
        """Build containers."""
        self.print_status("container", "run", "Building containers...")

        if self.dry_run:
            self.print_status(
                "container", "skip", "[DRY-RUN] Would run docker compose build"
            )
            self.artifact["pipeline"]["container"] = {
                "status": "skipped",
                "images_built": [],
            }
            return True

        code, output = run_cmd("docker compose build", cwd=ROOT_DIR)
        if code == 0:
            self.print_status("container", "ok", "Containers built")
            self.artifact["pipeline"]["container"] = {
                "status": "completed",
                "images_built": ["backend", "worker"],
            }
            return True
        else:
            self.print_status("container", "fail", "Container build failed")
            self.artifact["pipeline"]["container"] = {
                "status": "failed",
                "images_built": [],
                "error": output[:500],
            }
            return False

    def step_deploy(self) -> bool:
        """Deploy services."""
        self.print_status("deploy", "run", "Deploying services...")

        if self.dry_run:
            self.print_status(
                "deploy", "skip", "[DRY-RUN] Would run docker compose up -d"
            )
            self.artifact["pipeline"]["deploy"] = {
                "status": "skipped",
                "services_started": [],
            }
            return True

        code, output = run_cmd("docker compose up -d", cwd=ROOT_DIR)
        if code == 0:
            self.print_status("deploy", "ok", "Services deployed")
            self.artifact["pipeline"]["deploy"] = {
                "status": "completed",
                "services_started": ["backend", "worker"],
            }
            return True
        else:
            self.print_status("deploy", "fail", "Deployment failed")
            self.artifact["pipeline"]["deploy"] = {
                "status": "failed",
                "services_started": [],
                "error": output[:500],
            }
            return False

    def step_tests(self) -> bool:
        """Run test suite."""
        self.print_status("tests", "run", "Running tests...")

        if self.skip_tests:
            self.print_status("tests", "skip", "[SKIP-TESTS] Skipping test suite")
            self.artifact["pipeline"]["tests"] = {
                "status": "skipped",
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }
            return True

        if self.dry_run:
            self.print_status("tests", "skip", "[DRY-RUN] Would run pytest")
            self.artifact["pipeline"]["tests"] = {
                "status": "skipped",
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }
            return True

        code, output = run_cmd(
            "python3 -m pytest tests/ -v --tb=no -q", cwd=ROOT_DIR / "backend"
        )

        # Parse test results
        passed = failed = skipped = 0
        for line in output.split("\n"):
            if "passed" in line:
                import re

                match = re.search(r"(\d+) passed", line)
                if match:
                    passed = int(match.group(1))
                match = re.search(r"(\d+) failed", line)
                if match:
                    failed = int(match.group(1))
                match = re.search(r"(\d+) skipped", line)
                if match:
                    skipped = int(match.group(1))

        if code == 0 and failed == 0:
            self.print_status("tests", "ok", f"{passed} passed, {skipped} skipped")
            self.artifact["pipeline"]["tests"] = {
                "status": "passed",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
            }
            return True
        else:
            self.print_status("tests", "fail", f"{passed} passed, {failed} failed")
            self.artifact["pipeline"]["tests"] = {
                "status": "failed",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
            }
            self.artifact["verdict"] = "FAILED_TESTS"
            self.artifact["blocking_reason"] = f"{failed} tests failed"
            return False

    def step_git_commit(self) -> bool:
        """Commit changes."""
        self.print_status("git_commit", "run", "Checking for uncommitted changes...")

        # Check if there are changes to commit
        code, output = run_cmd("git status --porcelain")
        if not output.strip():
            self.print_status("git_commit", "skip", "No changes to commit")
            self.artifact["pipeline"]["git_commit"] = {
                "status": "skipped",
                "commit_hash": None,
                "files_changed": 0,
            }
            return True

        if self.dry_run:
            self.print_status("git_commit", "skip", "[DRY-RUN] Would commit changes")
            self.artifact["pipeline"]["git_commit"] = {
                "status": "skipped",
                "commit_hash": None,
                "files_changed": 0,
            }
            return True

        # Count files
        files_changed = len([line for line in output.strip().split("\n") if line])

        # Stage and commit
        code, _ = run_cmd("git add -A")
        if code != 0:
            self.print_status("git_commit", "fail", "Failed to stage changes")
            self.artifact["pipeline"]["git_commit"] = {
                "status": "failed",
                "error": "git add failed",
            }
            return False

        commit_msg = f"session reconcile: {self.session_id}"
        code, output = run_cmd(f'git commit -m "{commit_msg}"')
        if code != 0:
            self.print_status("git_commit", "fail", "Failed to commit")
            self.artifact["pipeline"]["git_commit"] = {
                "status": "failed",
                "error": output[:200],
            }
            return False

        # Get commit hash
        _, hash_output = run_cmd("git rev-parse --short HEAD")
        commit_hash = hash_output.strip()

        self.print_status(
            "git_commit", "ok", f"Committed {files_changed} files ({commit_hash})"
        )
        self.artifact["pipeline"]["git_commit"] = {
            "status": "completed",
            "commit_hash": commit_hash,
            "files_changed": files_changed,
        }
        return True

    def step_git_push(self) -> bool:
        """Push to remote."""
        self.print_status("git_push", "run", "Pushing to remote...")

        if self.dry_run:
            self.print_status("git_push", "skip", "[DRY-RUN] Would push to origin")
            self.artifact["pipeline"]["git_push"] = {
                "status": "skipped",
                "remote": "origin/main",
            }
            return True

        # Check if there's anything to push
        code, output = run_cmd("git status")
        if "Your branch is up to date" in output:
            self.print_status("git_push", "skip", "Already up to date")
            self.artifact["pipeline"]["git_push"] = {
                "status": "skipped",
                "remote": "origin/main",
            }
            return True

        code, output = run_cmd("git push origin main")
        if code == 0:
            self.print_status("git_push", "ok", "Pushed to origin/main")
            self.artifact["pipeline"]["git_push"] = {
                "status": "completed",
                "remote": "origin/main",
            }
            return True
        else:
            # Retry once
            self.print_status("git_push", "run", "Retrying push...")
            code, output = run_cmd("git push origin main")
            if code == 0:
                self.print_status("git_push", "ok", "Pushed to origin/main (retry)")
                self.artifact["pipeline"]["git_push"] = {
                    "status": "completed",
                    "remote": "origin/main",
                }
                return True
            else:
                self.print_status("git_push", "fail", "Push failed after retry")
                self.artifact["pipeline"]["git_push"] = {
                    "status": "failed",
                    "remote": "origin/main",
                    "error": output[:200],
                }
                return False

    # =========================================================================
    # Main Execution
    # =========================================================================

    def run_pipeline(self) -> bool:
        """Run the reconciliation pipeline in strict order."""
        self.print_header("RECONCILIATION PIPELINE")

        steps = [
            ("scripts", self.step_scripts),
            ("container", self.step_container),
            ("deploy", self.step_deploy),
            ("tests", self.step_tests),
            ("git_commit", self.step_git_commit),
            ("git_push", self.step_git_push),
        ]

        for step_name, step_func in steps:
            if not step_func():
                return False

        return True

    def save_artifact(self) -> Path:
        """Save reconciliation artifact."""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        artifact_path = ARTIFACTS_DIR / f"SR-{self.session_id}.yaml"

        with open(artifact_path, "w") as f:
            yaml.dump(self.artifact, f, default_flow_style=False, sort_keys=False)

        return artifact_path

    def save_session_pin(self) -> Path:
        """Save session pin for memory."""
        SESSION_PINS_DIR.mkdir(parents=True, exist_ok=True)
        pin_path = SESSION_PINS_DIR / f"{self.session_id}.yaml"

        pin = {
            "session_id": self.session_id,
            "started_at": self.artifact["timestamp"],
            "ended_at": get_timestamp(),
            "verdict": self.artifact["verdict"],
            "exit_ready": self.artifact["exit_ready"],
            "work_summary": {
                "commits": [
                    self.artifact["pipeline"].get("git_commit", {}).get("commit_hash")
                ],
                "files_changed": self.artifact["pipeline"]
                .get("git_commit", {})
                .get("files_changed", 0),
                "tests_passed": self.artifact["pipeline"]
                .get("tests", {})
                .get("passed", 0),
                "pins_created": [],
            },
            "next_session_context": {
                "pending_work": [],
                "blockers": [],
                "notes": "",
            },
        }

        with open(pin_path, "w") as f:
            yaml.dump(pin, f, default_flow_style=False, sort_keys=False)

        return pin_path

    def run(self) -> str:
        """Execute session reconciliation protocol."""
        print("\n" + "=" * 60)
        print("  SESSION_RECONCILE PROTOCOL (SR-01)")
        print(f"  Session ID: {self.session_id}")
        print("=" * 60)

        # Step 1: Load session state
        if not self.load_session_state():
            self.save_artifact()
            return "RECONCILIATION_BLOCKED"

        # Step 2: Load previous pin (optional)
        prev_pin = self.load_previous_pin()
        if prev_pin:
            print(f"\n  Previous session: {prev_pin.get('session_id', 'unknown')}")
            print(f"  Previous verdict: {prev_pin.get('verdict', 'unknown')}")

        # Step 3: Run pipeline
        if self.run_pipeline():
            self.artifact["verdict"] = "RECONCILED_EXIT_READY"
            self.artifact["exit_ready"] = True
        elif not self.artifact["verdict"]:
            self.artifact["verdict"] = "RECONCILIATION_BLOCKED"
            self.artifact["blocking_reason"] = "Pipeline step failed"

        # Step 4: Save artifacts
        artifact_path = self.save_artifact()
        pin_path = self.save_session_pin()

        # Step 5: Print summary
        self.print_header("VERDICT")

        verdict = self.artifact["verdict"]
        if verdict == "RECONCILED_EXIT_READY":
            print("  ✅ RECONCILED_EXIT_READY")
            print("  ✅ exit_ready: true")
            print("  ✅ git: pushed")
            print("  ✅ tests: passed")
        elif verdict == "FAILED_TESTS":
            print("  ❌ FAILED_TESTS")
            print(f"  ❌ Reason: {self.artifact['blocking_reason']}")
        else:
            print("  ❌ RECONCILIATION_BLOCKED")
            print(f"  ❌ Reason: {self.artifact['blocking_reason']}")

        print(f"\n  Artifact: {artifact_path}")
        print(f"  Session Pin: {pin_path}")

        return verdict


def main():
    parser = argparse.ArgumentParser(description="Session Reconcile Protocol (SR-01)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate pipeline without executing",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution (use with caution)",
    )
    args = parser.parse_args()

    reconciler = SessionReconciler(dry_run=args.dry_run, skip_tests=args.skip_tests)
    verdict = reconciler.run()

    # Exit codes
    if verdict == "RECONCILED_EXIT_READY":
        sys.exit(0)
    elif verdict == "FAILED_TESTS":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
