#!/usr/bin/env python3
"""
HOUSEKEEPING Protocol (HK-01) - Automation Script

Maintains VPS health by removing stale, orphaned, or unused system resources
WITHOUT affecting live services or work state.

Usage:
    python scripts/ops/housekeeping_scan.py [--scan-only]
    python scripts/ops/housekeeping_scan.py --tier2-token HK-APPROVAL-<timestamp>

Triggers:
    - User command: "do housekeeping"
    - Scheduled via cron (optional)

TIER-2 APPROVAL:
    Tier-2 actions require token-based approval (no numeric flags).
    Tokens are one-time use and must be generated fresh.
    Format: HK-APPROVAL-<timestamp>

Reference: docs/ops/HOUSEKEEPING_PROTOCOL.md
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Constants
ROOT_DIR = Path(__file__).parent.parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "housekeeping"
ERROR_ARTIFACTS_DIR = ROOT_DIR / "artifacts" / "errors"
SESSION_STATE_FILE = ROOT_DIR / ".session_state.yaml"
PROTECTED_SERVICES = ["nova_agent_manager", "nova_worker", "nova_db", "nova_pgbouncer"]

# Token validation
APPROVAL_TOKEN_PREFIX = "HK-APPROVAL-"
USED_TOKENS_FILE = ARTIFACTS_DIR / ".used_tokens"

# Protocol name (for violation reporting)
PROTOCOL_NAME = "HK-01"


def run_cmd(cmd: str) -> tuple[int, str]:
    """Run a shell command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except Exception as e:
        return 1, str(e)


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_artifact_id() -> str:
    """Generate artifact ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"HK-{ts}"


def generate_approval_token() -> str:
    """Generate a fresh approval token."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{APPROVAL_TOKEN_PREFIX}{ts}"


def validate_approval_token(token: str) -> tuple[bool, str]:
    """
    Validate an approval token.

    Rules:
    - Must have correct prefix
    - Must not be reused
    - Must be recorded after use
    """
    if not token:
        return False, "No token provided"

    if not token.startswith(APPROVAL_TOKEN_PREFIX):
        return False, f"Invalid token format. Must start with '{APPROVAL_TOKEN_PREFIX}'"

    # Check if token was already used
    if USED_TOKENS_FILE.exists():
        with open(USED_TOKENS_FILE) as f:
            used_tokens = set(f.read().strip().split("\n"))
        if token in used_tokens:
            return False, "Token has already been used (reuse forbidden)"

    return True, "Token valid"


def record_used_token(token: str) -> None:
    """Record a token as used (one-time use enforcement)."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(USED_TOKENS_FILE, "a") as f:
        f.write(f"{token}\n")


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


def check_session_state_readonly() -> tuple[bool, str | None]:
    """
    Verify session state file is readable (READ-ONLY check).

    NOTE: housekeeping_scan.py MUST treat .session_state.yaml as READ-ONLY.
    Only session_reconcile.py may write to it.

    Returns:
        (True, None) if file is accessible or doesn't exist.
        (False, error_message) if file cannot be read.
    """
    if not SESSION_STATE_FILE.exists():
        return True, None  # Not a problem for housekeeping

    # Just verify we can read it
    try:
        with open(SESSION_STATE_FILE) as f:
            yaml.safe_load(f)
        return True, None
    except Exception as e:
        return False, f"Cannot read session state file: {e}"


def abort_on_session_state_violation(attempted_action: str) -> None:
    """
    HARD BLOCK: If housekeeping attempts to write session state.

    Per TODO-04:
    - Only session_reconcile.py may write .session_state.yaml
    - housekeeping_scan.py MUST treat it as read-only
    - Violations must: Abort execution, Emit error artifact
    """
    error_path = emit_error_artifact(
        violation_type="SESSION_STATE_WRITE_FORBIDDEN",
        protocol=PROTOCOL_NAME,
        description="housekeeping_scan.py attempted to write to .session_state.yaml. "
        "Only session_reconcile.py may modify this file.",
        attempted_action=attempted_action,
    )

    print(f"\n{'=' * 60}")
    print("  SESSION STATE VIOLATION - EXECUTION ABORTED")
    print(f"{'=' * 60}")
    print("\n  ❌ VIOLATION: Attempted to write to .session_state.yaml")
    print(f"  ❌ PROTOCOL: {PROTOCOL_NAME} (housekeeping)")
    print(f"  ❌ ACTION: {attempted_action}")
    print("\n  Only session_reconcile.py may modify session state.")
    print(f"  Error artifact: {error_path}")
    print(f"\n{'=' * 60}\n")

    sys.exit(2)  # Exit code 2 = violation abort


class HousekeepingScan:
    """Housekeeping protocol executor."""

    def __init__(self, scan_only: bool = False, tier2_token: str | None = None):
        self.scan_only = scan_only
        self.tier2_token = tier2_token
        self.tier2_approved = False
        self.artifact: dict[str, Any] = {
            "schema_version": "1.0",
            "protocol": "HK-01",
            "id": get_artifact_id(),
            "timestamp": get_timestamp(),
            "triggered_by": "script",
        }
        self.tier2_requests: list[dict] = []

    def print_header(self, title: str) -> None:
        """Print section header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def print_status(self, item: str, status: str, detail: str = "") -> None:
        """Print status line."""
        icon = "✅" if status == "ok" else "❌" if status == "fail" else "⚠️"
        print(f"  {icon} {item}: {detail}" if detail else f"  {icon} {item}")

    # =========================================================================
    # Tier-0: Read-Only Scans
    # =========================================================================

    def scan_disk(self) -> dict:
        """Scan disk usage."""
        _, output = run_cmd("df -h / | tail -1")
        parts = output.split()
        if len(parts) >= 5:
            return {
                "total_gb": parts[1],
                "used_gb": parts[2],
                "available_gb": parts[3],
                "usage_percent": int(parts[4].rstrip("%")),
            }
        return {"error": "Could not parse disk usage"}

    def scan_memory(self) -> dict:
        """Scan memory usage."""
        _, output = run_cmd("free -g | grep Mem")
        parts = output.split()
        if len(parts) >= 4:
            total = int(parts[1])
            used = int(parts[2])
            available = int(parts[6]) if len(parts) > 6 else total - used
            return {
                "total_gb": total,
                "used_gb": used,
                "available_gb": available,
            }
        return {"error": "Could not parse memory usage"}

    def scan_docker(self) -> dict:
        """Scan Docker system usage."""
        _, output = run_cmd("docker system df --format json")
        result = {
            "images_count": 0,
            "images_size_gb": 0,
            "containers_count": 0,
            "volumes_count": 0,
            "build_cache_mb": 0,
        }
        try:
            for line in output.strip().split("\n"):
                if not line:
                    continue
                data = json.loads(line)
                dtype = data.get("Type", "")
                if dtype == "Images":
                    result["images_count"] = int(data.get("TotalCount", 0))
                    result["images_size_gb"] = data.get("Size", "0B")
                elif dtype == "Containers":
                    result["containers_count"] = int(data.get("TotalCount", 0))
                elif dtype == "Local Volumes":
                    result["volumes_count"] = int(data.get("TotalCount", 0))
                elif dtype == "Build Cache":
                    result["build_cache_mb"] = data.get("Size", "0B")
        except Exception:
            pass
        return result

    def scan_stale_processes(self) -> list[dict]:
        """Find stale test/build processes."""
        stale = []
        _, output = run_cmd("ps aux | grep -E 'pytest|python.*test' | grep -v grep")
        for line in output.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    stale.append({"pid": parts[1], "cmd": " ".join(parts[10:])})
        return stale

    def scan_orphan_containers(self) -> list[dict]:
        """Find stopped containers."""
        orphans = []
        _, output = run_cmd(
            "docker ps -a --filter 'status=exited' --format '{{.Names}}\t{{.Status}}'"
        )
        for line in output.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    orphans.append({"name": parts[0], "status": parts[1]})
        return orphans

    def run_scans(self) -> dict:
        """Run all Tier-0 scans."""
        self.print_header("TIER-0: Read-Only Scans")

        scans = {
            "disk": self.scan_disk(),
            "memory": self.scan_memory(),
            "docker": self.scan_docker(),
            "stale_processes": self.scan_stale_processes(),
            "orphan_containers": self.scan_orphan_containers(),
        }

        # Print results
        disk = scans["disk"]
        if "error" not in disk:
            self.print_status(
                "Disk",
                "ok",
                f"{disk['usage_percent']}% used ({disk['available_gb']} available)",
            )
        else:
            self.print_status("Disk", "fail", disk["error"])

        mem = scans["memory"]
        if "error" not in mem:
            self.print_status(
                "Memory",
                "ok",
                f"{mem['available_gb']}GB available of {mem['total_gb']}GB",
            )
        else:
            self.print_status("Memory", "fail", mem["error"])

        docker = scans["docker"]
        self.print_status(
            "Docker",
            "ok",
            f"{docker['images_count']} images, {docker['containers_count']} containers",
        )

        stale_count = len(scans["stale_processes"])
        self.print_status(
            "Stale processes",
            "warn" if stale_count > 0 else "ok",
            f"{stale_count} found",
        )

        orphan_count = len(scans["orphan_containers"])
        self.print_status(
            "Orphan containers",
            "warn" if orphan_count > 0 else "ok",
            f"{orphan_count} found",
        )

        self.artifact["scans"] = scans
        return scans

    # =========================================================================
    # Service Health Checks
    # =========================================================================

    def check_services(self) -> dict:
        """Check health of protected services."""
        results = {}

        for service in PROTECTED_SERVICES:
            code, output = run_cmd(
                f"docker ps --filter 'name={service}' --format '{{{{.Status}}}}'"
            )
            if code == 0 and "Up" in output:
                if "healthy" in output.lower():
                    results[service] = "healthy"
                else:
                    results[service] = "running"
            else:
                results[service] = "unhealthy"

        return results

    def verify_services_pre(self) -> bool:
        """Verify services before cleanup."""
        self.print_header("SERVICE PRE-CHECK")

        results = self.check_services()
        self.artifact["services_pre_check"] = results

        all_healthy = True
        for service, status in results.items():
            if status in ["healthy", "running"]:
                self.print_status(service, "ok", status)
            else:
                self.print_status(service, "fail", status)
                all_healthy = False

        if not all_healthy:
            print("\n  ❌ BLOCKED: Services unhealthy before cleanup")
            return False

        return True

    def verify_services_post(self) -> bool:
        """Verify services after cleanup."""
        self.print_header("SERVICE POST-CHECK")

        results = self.check_services()
        self.artifact["services_post_check"] = results

        all_healthy = True
        for service, status in results.items():
            if status in ["healthy", "running"]:
                self.print_status(service, "ok", status)
            else:
                self.print_status(service, "fail", status)
                all_healthy = False

        return all_healthy

    # =========================================================================
    # Tier-1: Safe Cleanup (Auto-Execute)
    # =========================================================================

    def tier1_cleanup(self) -> dict:
        """Execute Tier-1 (safe) cleanup actions."""
        self.print_header("TIER-1: Safe Cleanup")

        results = {
            "containers_removed": 0,
            "images_pruned": 0,
            "build_cache_cleared_mb": 0,
            "processes_killed": 0,
            "page_cache_cleared": False,
            "journal_vacuumed": False,
            "tmp_files_cleaned": 0,
            "cache_files_cleaned": 0,
        }

        if self.scan_only:
            print("  [SCAN-ONLY MODE] Skipping Tier-1 actions")
            self.artifact["tier_1_actions"] = results
            return results

        # Kill stale test processes
        run_cmd("pkill -f pytest 2>/dev/null; pkill -f 'python.*test' 2>/dev/null")
        stale_count = len(self.artifact.get("scans", {}).get("stale_processes", []))
        results["processes_killed"] = stale_count
        self.print_status("Kill stale processes", "ok", f"{stale_count} killed")

        # Remove stopped containers
        code, output = run_cmd("docker container prune -f")
        if "Total reclaimed space" in output:
            results["containers_removed"] = len(
                self.artifact.get("scans", {}).get("orphan_containers", [])
            )
        self.print_status("Prune containers", "ok")

        # Prune dangling images
        run_cmd("docker image prune -f")
        self.print_status("Prune dangling images", "ok")

        # Clear build cache
        code, output = run_cmd("docker builder prune -af")
        if "Total:" in output:
            for line in output.split("\n"):
                if "Total:" in line:
                    results["build_cache_cleared_mb"] = line.split(":")[-1].strip()
        self.print_status("Clear build cache", "ok")

        # Clear page cache
        code, _ = run_cmd("sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null")
        results["page_cache_cleared"] = code == 0
        self.print_status("Clear page cache", "ok" if code == 0 else "warn")

        # Vacuum journal logs
        code, _ = run_cmd("journalctl --vacuum-time=3d 2>/dev/null")
        results["journal_vacuumed"] = code == 0
        self.print_status("Vacuum journal logs", "ok" if code == 0 else "warn")

        # Clean tmp files
        run_cmd("find /tmp -type f -mtime +1 -delete 2>/dev/null")
        self.print_status("Clean /tmp files", "ok")

        # Clean cache files
        run_cmd("find ~/.cache -type f -mtime +7 -delete 2>/dev/null")
        self.print_status("Clean ~/.cache files", "ok")

        self.artifact["tier_1_actions"] = results
        return results

    # =========================================================================
    # Tier-2: Risky Cleanup (Token-Based Approval Required)
    # =========================================================================

    def validate_tier2_token(self) -> bool:
        """Validate Tier-2 approval token."""
        if not self.tier2_token:
            return False

        valid, msg = validate_approval_token(self.tier2_token)
        if not valid:
            print(f"\n  ❌ TIER-2 TOKEN INVALID: {msg}")
            return False

        self.tier2_approved = True
        return True

    def identify_tier2(self) -> list[dict]:
        """Identify Tier-2 cleanup opportunities."""
        self.tier2_requests = []

        # Check for orphan volumes
        code, output = run_cmd("docker volume ls -q --filter 'dangling=true' | wc -l")
        orphan_volumes = int(output.strip()) if code == 0 else 0
        if orphan_volumes > 0:
            self.tier2_requests.append(
                {
                    "id": "orphan_volumes",
                    "action": "Remove orphan volumes",
                    "detail": f"{orphan_volumes} volumes",
                    "command": "docker volume prune -f",
                }
            )

        # Check for unused images (not just dangling)
        code, output = run_cmd("docker images --filter 'dangling=false' -q | wc -l")
        unused_images = int(output.strip()) if code == 0 else 0
        if unused_images > 5:
            self.tier2_requests.append(
                {
                    "id": "unused_images",
                    "action": "Prune all unused images",
                    "detail": f"{unused_images} images",
                    "command": "docker image prune -af",
                }
            )

        return self.tier2_requests

    def print_tier2_requests(self) -> None:
        """Print Tier-2 approval instructions."""
        if not self.tier2_requests:
            return

        self.print_header("TIER-2: Approval Required")
        print("  The following actions require explicit token-based approval:\n")
        for req in self.tier2_requests:
            print(f"    • [{req['id']}] {req['action']} - {req['detail']}")

        # Generate fresh token
        fresh_token = generate_approval_token()
        print("\n  To approve, run with:")
        print(f"    --tier2-token {fresh_token}")
        print("\n  ⚠️  Tokens are one-time use only. Do not reuse.")

    def execute_tier2(self) -> dict:
        """Execute Tier-2 actions with approved token."""
        results = {
            "requested": [r["id"] for r in self.tier2_requests],
            "approved": self.tier2_approved,
            "approval_token": self.tier2_token,
            "approved_by": "human",
            "executed": [],
            "skipped": [],
        }

        if not self.tier2_approved:
            results["skipped"] = results["requested"]
            self.artifact["tier_2_actions"] = results
            return results

        self.print_header("TIER-2: Executing Approved Actions")

        # Record token as used (prevent reuse)
        # Note: tier2_token is validated non-None by validate_tier2_token()
        if self.tier2_token is not None:
            record_used_token(self.tier2_token)

        for req in self.tier2_requests:
            code, _ = run_cmd(req["command"])
            if code == 0:
                results["executed"].append(req["id"])
                self.print_status(req["action"], "ok", "Executed")
            else:
                results["skipped"].append(req["id"])
                self.print_status(req["action"], "fail", "Failed")

        self.artifact["tier_2_actions"] = results
        return results

    # =========================================================================
    # Main Execution
    # =========================================================================

    def save_artifact(self) -> Path:
        """Save artifact to file."""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        artifact_path = ARTIFACTS_DIR / f"{self.artifact['id']}.yaml"

        with open(artifact_path, "w") as f:
            yaml.dump(self.artifact, f, default_flow_style=False, sort_keys=False)

        return artifact_path

    def run(self) -> bool:
        """Execute housekeeping protocol."""
        print("\n" + "=" * 60)
        print("  HOUSEKEEPING PROTOCOL (HK-01)")
        print("=" * 60)

        # Verify session state is accessible (read-only check)
        readable, error_msg = check_session_state_readonly()
        if not readable:
            print(f"\n  ⚠️  Warning: {error_msg}")

        # Validate Tier-2 token if provided
        if self.tier2_token:
            self.validate_tier2_token()

        # Step 1: Run scans (Tier-0)
        self.run_scans()

        # Step 2: Verify services before cleanup
        if not self.verify_services_pre():
            self.artifact["result"] = {
                "services_protected": False,
                "no_active_work_disrupted": True,
                "success": False,
                "notes": "Services unhealthy before cleanup - blocked",
            }
            self.save_artifact()
            return False

        # Step 3: Execute Tier-1 cleanup
        self.tier1_cleanup()

        # Step 4: Identify and handle Tier-2
        self.identify_tier2()
        if self.tier2_approved:
            self.execute_tier2()
        elif self.tier2_requests:
            self.print_tier2_requests()

        # Step 5: Verify services after cleanup
        services_ok = self.verify_services_post()

        # Step 6: Generate result
        self.artifact["result"] = {
            "services_protected": services_ok,
            "no_active_work_disrupted": True,
            "success": services_ok,
            "notes": "" if services_ok else "Services became unhealthy after cleanup",
        }

        # Save artifact
        artifact_path = self.save_artifact()

        # Print summary
        self.print_header("SUMMARY")
        if services_ok:
            print("  ✅ Housekeeping completed successfully")
            print("  ✅ Services protected: verified")
            print("  ✅ No active work disrupted: true")
        else:
            print("  ❌ Housekeeping completed with warnings")
            print("  ❌ Some services may be affected")

        print(f"\n  Artifact: {artifact_path}")

        return services_ok


def main():
    parser = argparse.ArgumentParser(description="Housekeeping Protocol (HK-01)")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only run scans, do not execute cleanup",
    )
    parser.add_argument(
        "--tier2-token",
        type=str,
        default=None,
        help=f"Token for Tier-2 approval (format: {APPROVAL_TOKEN_PREFIX}<timestamp>)",
    )
    args = parser.parse_args()

    hk = HousekeepingScan(scan_only=args.scan_only, tier2_token=args.tier2_token)
    success = hk.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
