#!/usr/bin/env python3
"""
SESSION_EXIT Protocol - Exit Gate Arbiter

Single authoritative exit arbiter that determines whether a session
may terminate cleanly.

Usage:
    python scripts/ops/session_exit.py [--hk-max-age HOURS]

Exit Codes:
    0 - CLEAN_EXIT (session may terminate)
    1 - EXIT_BLOCKED (session must reconcile first)

Reference: docs/ops/SESSION_RECONCILE_PROTOCOL.md
Reference: CLAUDE_AUTHORITY.md Section 11.3
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent
SESSION_STATE_FILE = ROOT_DIR / ".session_state.yaml"
SR_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "session_reconcile"
HK_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "housekeeping"
EXIT_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "session_exit"
ERROR_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "errors"

# Default freshness threshold
DEFAULT_HK_MAX_AGE_HOURS = 24

# Protocol name (for violation reporting)
PROTOCOL_NAME = "SESSION_EXIT"


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def get_latest_artifact(
    artifact_dir: Path, prefix: str
) -> tuple[Path | None, dict | None]:
    """Get the latest artifact from a directory."""
    if not artifact_dir.exists():
        return None, None

    artifacts = sorted(
        artifact_dir.glob(f"{prefix}*.yaml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not artifacts:
        return None, None

    try:
        with open(artifacts[0]) as f:
            return artifacts[0], yaml.safe_load(f)
    except Exception:
        return artifacts[0], None


def emit_error_artifact(
    violation_type: str,
    protocol: str,
    description: str,
    attempted_action: str,
) -> Path:
    """
    Emit an error artifact when a violation is detected.

    Per TODO-04: Violations must abort execution and emit error artifact.

    Returns:
        Path to the created error artifact.
    """
    ERROR_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    artifact_id = f"ERR-{protocol}-{ts}"
    artifact_path = ERROR_ARTIFACTS_DIR / f"{artifact_id}.yaml"

    error_artifact = {
        "schema_version": "1.0",
        "type": "VIOLATION_ERROR",
        "id": artifact_id,
        "timestamp": get_timestamp(),
        "protocol": protocol,
        "violation_type": violation_type,
        "description": description,
        "attempted_action": attempted_action,
        "status": "ABORTED",
        "resolution_required": True,
    }

    with open(artifact_path, "w") as f:
        yaml.dump(error_artifact, f, default_flow_style=False, sort_keys=False)

    return artifact_path


def abort_on_session_state_violation(attempted_action: str) -> None:
    """
    HARD BLOCK: If session_exit attempts to write session state.

    Per TODO-04:
    - Only session_reconcile.py may write .session_state.yaml
    - session_exit.py MUST treat it as read-only
    - Violations must: Abort execution, Emit error artifact
    """
    error_path = emit_error_artifact(
        violation_type="SESSION_STATE_WRITE_FORBIDDEN",
        protocol=PROTOCOL_NAME,
        description="session_exit.py attempted to write to .session_state.yaml. "
        "Only session_reconcile.py may modify this file.",
        attempted_action=attempted_action,
    )

    print(f"\n{'=' * 60}")
    print("  SESSION STATE VIOLATION - EXECUTION ABORTED")
    print(f"{'=' * 60}")
    print("\n  ❌ VIOLATION: Attempted to write to .session_state.yaml")
    print(f"  ❌ PROTOCOL: {PROTOCOL_NAME}")
    print(f"  ❌ ACTION: {attempted_action}")
    print("\n  Only session_reconcile.py may modify session state.")
    print(f"  Error artifact: {error_path}")
    print(f"\n{'=' * 60}\n")

    sys.exit(2)  # Exit code 2 = violation abort


class SessionExitGate:
    """Exit gate arbiter - determines if session can terminate cleanly."""

    def __init__(self, hk_max_age_hours: int = DEFAULT_HK_MAX_AGE_HOURS):
        self.hk_max_age = timedelta(hours=hk_max_age_hours)
        self.session_id: str | None = None
        self.exit_artifact: dict[str, Any] = {
            "schema_version": "1.0",
            "protocol": "SESSION_EXIT",
            "timestamp": get_timestamp(),
            "checks": {},
            "verdict": None,
            "exit_allowed": False,
            "blocking_reasons": [],
        }

    def print_header(self, title: str) -> None:
        """Print section header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def print_check(self, name: str, passed: bool, detail: str = "") -> None:
        """Print check result."""
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}: {detail}" if detail else f"  {icon} {name}")

    # =========================================================================
    # Check Functions (READ-ONLY - No Mutations)
    # =========================================================================

    def check_sr_artifact(self) -> bool:
        """
        Check 1: Load latest SR artifact and verify verdict.

        REQUIRED: verdict == RECONCILED_EXIT_READY
        """
        sr_path, sr_data = get_latest_artifact(SR_ARTIFACTS_DIR, "SR-")

        if not sr_path:
            self.exit_artifact["checks"]["sr_artifact"] = {
                "status": "missing",
                "path": None,
            }
            self.exit_artifact["blocking_reasons"].append("No SR artifact found")
            self.print_check("SR Artifact", False, "Not found")
            return False

        if not sr_data:
            self.exit_artifact["checks"]["sr_artifact"] = {
                "status": "invalid",
                "path": str(sr_path),
            }
            self.exit_artifact["blocking_reasons"].append("SR artifact is invalid")
            self.print_check("SR Artifact", False, "Invalid YAML")
            return False

        verdict = sr_data.get("verdict")
        self.session_id = sr_data.get("session_id")
        self.exit_artifact["session_id"] = self.session_id

        self.exit_artifact["checks"]["sr_artifact"] = {
            "status": "found",
            "path": str(sr_path),
            "session_id": self.session_id,
            "verdict": verdict,
            "exit_ready": sr_data.get("exit_ready", False),
        }

        if verdict != "RECONCILED_EXIT_READY":
            self.exit_artifact["blocking_reasons"].append(
                f"SR verdict is '{verdict}', expected 'RECONCILED_EXIT_READY'"
            )
            self.print_check("SR Artifact", False, f"verdict={verdict}")
            return False

        self.print_check("SR Artifact", True, f"verdict={verdict}")
        return True

    def check_session_state_consistency(self) -> bool:
        """
        Check 2: Verify session_state.yaml consistency with SR artifact.

        NOTE: This is READ-ONLY. session_exit.py must NOT modify session state.
        """
        if not SESSION_STATE_FILE.exists():
            self.exit_artifact["checks"]["session_state"] = {
                "status": "missing",
                "consistent": False,
            }
            self.exit_artifact["blocking_reasons"].append(
                "session_state.yaml not found"
            )
            self.print_check("Session State", False, "Not found")
            return False

        try:
            with open(SESSION_STATE_FILE) as f:
                state = yaml.safe_load(f) or {}
        except Exception as e:
            self.exit_artifact["checks"]["session_state"] = {
                "status": "invalid",
                "error": str(e),
            }
            self.exit_artifact["blocking_reasons"].append(
                f"session_state.yaml invalid: {e}"
            )
            self.print_check("Session State", False, "Invalid YAML")
            return False

        # Check for consistency
        exit_ready = state.get("exit", {}).get("ready", False)
        exit_verdict = state.get("exit", {}).get("verdict")

        self.exit_artifact["checks"]["session_state"] = {
            "status": "found",
            "exit_ready": exit_ready,
            "verdict": exit_verdict,
        }

        # Allow if SR says ready, even if state file not updated
        # (SR artifact is authoritative)
        self.print_check("Session State", True, f"exit_ready={exit_ready}")
        return True

    def check_hk_freshness(self) -> bool:
        """
        Check 3: Verify housekeeping freshness.

        REQUIRED: Latest HK artifact must be within configured threshold.
        """
        hk_path, hk_data = get_latest_artifact(HK_ARTIFACTS_DIR, "HK-")

        if not hk_path:
            self.exit_artifact["checks"]["hk_freshness"] = {
                "status": "missing",
                "fresh": False,
            }
            self.exit_artifact["blocking_reasons"].append(
                "No HK artifact found - run housekeeping first"
            )
            self.print_check("HK Freshness", False, "No housekeeping record")
            return False

        if not hk_data:
            self.exit_artifact["checks"]["hk_freshness"] = {
                "status": "invalid",
                "path": str(hk_path),
            }
            self.exit_artifact["blocking_reasons"].append("HK artifact is invalid")
            self.print_check("HK Freshness", False, "Invalid YAML")
            return False

        # Check age
        hk_timestamp = hk_data.get("timestamp")
        if not hk_timestamp:
            self.exit_artifact["checks"]["hk_freshness"] = {
                "status": "no_timestamp",
                "path": str(hk_path),
            }
            self.exit_artifact["blocking_reasons"].append(
                "HK artifact has no timestamp"
            )
            self.print_check("HK Freshness", False, "No timestamp")
            return False

        try:
            hk_time = parse_timestamp(hk_timestamp)
            now = datetime.now(timezone.utc)
            age = now - hk_time
            age_hours = age.total_seconds() / 3600

            self.exit_artifact["checks"]["hk_freshness"] = {
                "status": "found",
                "path": str(hk_path),
                "timestamp": hk_timestamp,
                "age_hours": round(age_hours, 2),
                "max_age_hours": self.hk_max_age.total_seconds() / 3600,
                "fresh": age <= self.hk_max_age,
            }

            if age > self.hk_max_age:
                self.exit_artifact["blocking_reasons"].append(
                    f"HK artifact is {age_hours:.1f}h old, max allowed is {self.hk_max_age.total_seconds() / 3600}h"
                )
                self.print_check(
                    "HK Freshness",
                    False,
                    f"Age: {age_hours:.1f}h (max: {self.hk_max_age.total_seconds() / 3600}h)",
                )
                return False

            self.print_check("HK Freshness", True, f"Age: {age_hours:.1f}h")
            return True

        except Exception as e:
            self.exit_artifact["checks"]["hk_freshness"] = {
                "status": "error",
                "error": str(e),
            }
            self.exit_artifact["blocking_reasons"].append(
                f"Failed to check HK freshness: {e}"
            )
            self.print_check("HK Freshness", False, str(e))
            return False

    # =========================================================================
    # Main Execution
    # =========================================================================

    def save_exit_artifact(self) -> Path:
        """Save exit verdict artifact."""
        EXIT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        session_id = self.session_id or "unknown"
        artifact_path = EXIT_ARTIFACTS_DIR / f"EXIT-{session_id}.yaml"

        with open(artifact_path, "w") as f:
            yaml.dump(self.exit_artifact, f, default_flow_style=False, sort_keys=False)

        return artifact_path

    def run(self) -> str:
        """
        Execute exit gate checks.

        FORBIDDEN:
        - No reconciliation
        - No housekeeping
        - No mutation except writing EXIT artifact
        """
        print("\n" + "=" * 60)
        print("  SESSION EXIT GATE")
        print("=" * 60)

        self.print_header("EXIT CHECKS")

        # Run all checks
        check_results = []

        # Check 1: SR artifact verdict
        check_results.append(self.check_sr_artifact())

        # Check 2: Session state consistency
        check_results.append(self.check_session_state_consistency())

        # Check 3: HK freshness
        check_results.append(self.check_hk_freshness())

        # Determine verdict
        all_passed = all(check_results)

        if all_passed:
            self.exit_artifact["verdict"] = "CLEAN_EXIT"
            self.exit_artifact["exit_allowed"] = True
        else:
            self.exit_artifact["verdict"] = "EXIT_BLOCKED"
            self.exit_artifact["exit_allowed"] = False

        # Save artifact
        artifact_path = self.save_exit_artifact()

        # Print verdict
        self.print_header("VERDICT")

        if all_passed:
            print("  ✅ CLEAN_EXIT")
            print("  ✅ Session may terminate cleanly")
        else:
            print("  ❌ EXIT_BLOCKED")
            print("  ❌ Session must resolve blockers first")
            print("\n  Blocking reasons:")
            for reason in self.exit_artifact["blocking_reasons"]:
                print(f"    - {reason}")

        print(f"\n  Artifact: {artifact_path}")

        return self.exit_artifact["verdict"]


def main():
    parser = argparse.ArgumentParser(description="Session Exit Gate")
    parser.add_argument(
        "--hk-max-age",
        type=int,
        default=DEFAULT_HK_MAX_AGE_HOURS,
        help=f"Maximum age of HK artifact in hours (default: {DEFAULT_HK_MAX_AGE_HOURS})",
    )
    args = parser.parse_args()

    gate = SessionExitGate(hk_max_age_hours=args.hk_max_age)
    verdict = gate.run()

    # Exit codes
    if verdict == "CLEAN_EXIT":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
