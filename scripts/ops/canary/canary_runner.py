#!/usr/bin/env python3
"""
AOS Canary Runner - Feature flag toggle, smoke test, Prometheus monitoring, rollback.

Usage:
    python scripts/ops/canary/canary_runner.py --config scripts/ops/canary/configs/m4_canary.yaml
    python scripts/ops/canary/canary_runner.py --config scripts/ops/canary/configs/m4_canary.yaml --dry-run
    python scripts/ops/canary/canary_runner.py --config scripts/ops/canary/configs/m4_canary.yaml --watch 300

Features:
    - File-based feature flag toggle with atomic writes + flock (matches AOS config structure)
    - Runs smoke script with timeout
    - Queries Prometheus for metrics with proper baseline windows
    - Compares metrics against baseline thresholds
    - Auto-rollback on threshold breach with alerting
    - JSON report generation with provenance (git sha, config hash, timestamps)
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# File locking for atomic operations
try:
    from fcntl import flock, LOCK_EX, LOCK_UN

    HAS_FLOCK = True
except ImportError:
    HAS_FLOCK = False  # Windows fallback

# Try to import yaml, fall back to json config if not available
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_FLAGS_PATH = PROJECT_ROOT / "backend/app/config/feature_flags.json"
DEFAULT_PROMETHEUS_URL = "http://127.0.0.1:9090"
DEFAULT_API_BASE = "http://127.0.0.1:8000"


@dataclass
class CanaryReport:
    """Structured canary run report with full provenance."""

    name: str
    start_time: str
    end_time: Optional[str] = None
    config_path: str = ""
    dry_run: bool = False

    # Provenance (for audit trail)
    git_sha: str = ""
    git_branch: str = ""
    config_hash: str = ""
    hostname: str = ""
    user: str = ""

    # Flag operations
    flags_enabled: List[str] = field(default_factory=list)
    flag_enable_status: str = ""
    flag_enable_error: str = ""

    # Smoke test results
    smoke_script: str = ""
    smoke_returncode: int = -1
    smoke_stdout: str = ""
    smoke_stderr: str = ""
    smoke_duration_seconds: float = 0.0

    # Prometheus metrics
    prometheus_url: str = ""
    metrics_baseline: Dict[str, float] = field(default_factory=dict)
    metrics_current: Dict[str, float] = field(default_factory=dict)
    metrics_delta: Dict[str, float] = field(default_factory=dict)
    baseline_window_seconds: int = 300  # 5 min default

    # Rollback decision
    rollback_triggered: bool = False
    rollback_reason: str = ""
    rollback_status: str = ""
    alert_sent: bool = False
    alert_error: str = ""

    # Overall
    success: bool = False
    errors: List[str] = field(default_factory=list)


def load_config(path: str) -> Dict[str, Any]:
    """Load canary config from YAML or JSON."""
    with open(path) as f:
        if path.endswith(".yaml") or path.endswith(".yml"):
            if not HAS_YAML:
                raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")
            return yaml.safe_load(f)
        else:
            return json.load(f)


def log(level: str, msg: str):
    """Simple colored logging."""
    colors = {
        "INFO": "\033[0;32m",
        "WARN": "\033[1;33m",
        "ERROR": "\033[0;31m",
        "STEP": "\033[0;34m",
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{level}]{reset} {msg}")


def get_git_info() -> Tuple[str, str]:
    """Get current git SHA and branch for provenance."""
    sha, branch = "", ""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=PROJECT_ROOT,
        ).stdout.strip()[:12]
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=PROJECT_ROOT,
        ).stdout.strip()
    except Exception:
        pass
    return sha, branch


def get_config_hash(config: Dict[str, Any]) -> str:
    """Generate a hash of the config for provenance."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def get_hostname_user() -> Tuple[str, str]:
    """Get hostname and user for provenance."""
    import socket

    hostname = socket.gethostname()
    user = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
    return hostname, user


def read_feature_flags(path: Path = DEFAULT_FLAGS_PATH) -> Dict[str, Any]:
    """Read current feature flags with file locking."""
    with open(path) as f:
        if HAS_FLOCK:
            flock(f.fileno(), LOCK_EX)  # Exclusive lock for read consistency
        try:
            return json.load(f)
        finally:
            if HAS_FLOCK:
                flock(f.fileno(), LOCK_UN)


def write_feature_flags(flags: Dict[str, Any], path: Path = DEFAULT_FLAGS_PATH):
    """Write feature flags atomically with flock + temp-rename pattern.

    This prevents:
    - Partial writes (atomic rename)
    - Concurrent modifications (flock)
    - Data corruption on crash (fsync)
    """
    path = Path(path)
    dir_path = path.parent

    # Open existing file for locking (if it exists)
    lock_fd = None
    if path.exists() and HAS_FLOCK:
        lock_fd = open(path, "r")
        flock(lock_fd.fileno(), LOCK_EX)

    try:
        # Write to temp file in same directory (required for atomic rename)
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(flags, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure data hits disk

            # Atomic rename (POSIX guarantees atomicity)
            os.replace(tmp_path, str(path))
            log("INFO", f"Atomically updated {path}")
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    finally:
        if lock_fd:
            flock(lock_fd.fileno(), LOCK_UN)
            lock_fd.close()


def backup_feature_flags(path: Path = DEFAULT_FLAGS_PATH) -> Optional[str]:
    """Create a timestamped backup of feature_flags.json before modification.

    Returns backup path on success, None on failure.
    """
    if not path.exists():
        return None

    try:
        timestamp = int(time.time())
        backup_path = path.with_suffix(f".{timestamp}.bak")
        import shutil

        shutil.copy2(path, backup_path)
        log("INFO", f"Backup created: {backup_path}")

        # Rotate old backups (keep last 10)
        rotate_backups(path.parent, max_backups=10)

        return str(backup_path)
    except Exception as e:
        log("WARN", f"Failed to create backup: {e}")
        return None


def rotate_backups(directory: Path, max_backups: int = 10) -> int:
    """Rotate old backup files, keeping only the most recent N backups.

    Risk mitigation 4.4: Prevent unbounded .bak file growth.

    Args:
        directory: Directory containing backup files
        max_backups: Maximum number of backups to keep (default 10)

    Returns:
        Number of backups deleted
    """
    try:
        import glob

        pattern = str(directory / "feature_flags.*.bak")
        backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

        deleted = 0
        for old_backup in backups[max_backups:]:
            try:
                os.unlink(old_backup)
                deleted += 1
                log("INFO", f"Rotated old backup: {old_backup}")
            except Exception as e:
                log("WARN", f"Failed to delete old backup {old_backup}: {e}")

        return deleted
    except Exception as e:
        log("WARN", f"Backup rotation failed: {e}")
        return 0


def check_filesystem_type(path: Path) -> str:
    """Check if path is on NFS/network filesystem (risk mitigation 4.1).

    flock may not work reliably on NFS. Returns filesystem type.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["df", "-T", str(path)], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 2:
                    fstype = parts[1].lower()
                    if fstype in ("nfs", "nfs4", "cifs", "glusterfs", "ceph"):
                        log(
                            "WARN",
                            f"Feature flags on network filesystem ({fstype}) - flock may not be reliable!",
                        )
                    return fstype
    except Exception:
        pass
    return "unknown"


def write_incident_fallback(
    report: "CanaryReport", fallback_dir: Path = None
) -> Optional[str]:
    """Write incident report to fallback location when webhook fails (risk 4.3).

    Provides persistent record even if Slack/webhook is unreachable.
    """
    if fallback_dir is None:
        fallback_dir = PROJECT_ROOT / "scripts/ops/canary/incidents"

    try:
        fallback_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        incident_path = fallback_dir / f"incident_{timestamp}_{report.name}.json"

        incident_data = {
            "timestamp": timestamp,
            "canary_name": report.name,
            "rollback_triggered": report.rollback_triggered,
            "rollback_reason": report.rollback_reason,
            "errors": report.errors,
            "metrics_delta": report.metrics_delta,
            "git_sha": report.git_sha,
            "hostname": report.hostname,
        }

        with open(incident_path, "w") as f:
            json.dump(incident_data, f, indent=2)

        log("INFO", f"Incident fallback written: {incident_path}")
        return str(incident_path)
    except Exception as e:
        log("ERROR", f"Failed to write incident fallback: {e}")
        return None


def toggle_flag(
    flag_name: str,
    enable: bool,
    env: str = "staging",
    dry_run: bool = False,
    create_backup: bool = True,
) -> Tuple[bool, str]:
    """Toggle a feature flag in the config file.

    Args:
        flag_name: Name of the flag to toggle
        enable: True to enable, False to disable
        env: Environment (staging, production, etc.)
        dry_run: If True, don't actually modify the file
        create_backup: If True, backup before modification (default True)
    """
    try:
        flags = read_feature_flags()

        # Check if flag exists
        if flag_name not in flags.get("flags", {}):
            return False, f"Flag '{flag_name}' not found in config"

        # Check signoff requirement
        flag_cfg = flags["flags"][flag_name]
        if enable and flag_cfg.get("requires_m4_signoff", False):
            signoff_path = PROJECT_ROOT / ".m4_signoff"
            if not signoff_path.exists():
                return False, f"Flag '{flag_name}' requires .m4_signoff artifact"

        current_value = flags["environments"].get(env, {}).get(flag_name, False)

        if dry_run:
            log(
                "INFO",
                f"[DRY-RUN] Would set {flag_name}={enable} in {env} (current={current_value})",
            )
            return True, "dry-run"

        # Create backup before modification
        if create_backup:
            backup_feature_flags()

        # Update flag
        if env not in flags["environments"]:
            flags["environments"][env] = {}
        flags["environments"][env][flag_name] = enable

        # Also update the main flags section for immediate effect
        flags["flags"][flag_name]["enabled"] = enable

        write_feature_flags(flags)
        log("INFO", f"Set {flag_name}={enable} in {env}")
        return True, "success"

    except Exception as e:
        return False, str(e)


def run_smoke_script(
    script_path: str, timeout: int = 60
) -> Tuple[int, str, str, float]:
    """Run smoke test script with timeout."""
    start = time.time()
    try:
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
        )
        duration = time.time() - start
        return result.returncode, result.stdout, result.stderr, duration
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout after {timeout}s", time.time() - start
    except Exception as e:
        return -1, "", str(e), time.time() - start


def query_prometheus(prom_url: str, query: str) -> Optional[float]:
    """Execute a Prometheus instant query and return scalar result."""
    try:
        params = urllib.parse.urlencode({"query": query})
        url = f"{prom_url.rstrip('/')}/api/v1/query?{params}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)

        if data.get("status") != "success":
            log("WARN", f"Prometheus query returned status: {data.get('status')}")
            return None

        result = data.get("data", {}).get("result", [])
        if not result:
            return 0.0

        # Return first result value
        value = result[0].get("value", [None, None])[1]
        return float(value) if value is not None else None

    except Exception as e:
        log("WARN", f"Prometheus query failed: {e}")
        return None


def query_prometheus_range(
    prom_url: str, query: str, window_seconds: int = 300
) -> Optional[float]:
    """Execute a Prometheus range query and return avg over window.

    This provides a proper baseline by averaging metrics over a time window,
    rather than just taking a point-in-time instant value.
    """
    try:
        # Use avg_over_time to get average over the window
        range_query = f"avg_over_time(({query})[{window_seconds}s:])"
        params = urllib.parse.urlencode({"query": range_query})
        url = f"{prom_url.rstrip('/')}/api/v1/query?{params}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)

        if data.get("status") != "success":
            # Fallback to instant query if range query fails
            log("WARN", "Range query failed, falling back to instant query")
            return query_prometheus(prom_url, query)

        result = data.get("data", {}).get("result", [])
        if not result:
            # Fallback to instant query
            return query_prometheus(prom_url, query)

        value = result[0].get("value", [None, None])[1]
        return float(value) if value is not None else None

    except Exception as e:
        log("WARN", f"Prometheus range query failed: {e}, falling back to instant")
        return query_prometheus(prom_url, query)


def get_baseline_metrics(
    prom_url: str, metrics_config: Dict[str, str], window_seconds: int = 300
) -> Dict[str, float]:
    """Query baseline metrics from Prometheus using range averaging.

    Args:
        prom_url: Prometheus server URL
        metrics_config: Dict of metric_name -> PromQL query
        window_seconds: Time window for baseline averaging (default 5 minutes)
    """
    baseline = {}
    for name, query in metrics_config.items():
        # Use range query for proper baseline
        value = query_prometheus_range(prom_url, query, window_seconds)
        if value is not None:
            baseline[name] = value
            log("INFO", f"Baseline {name}: {value:.4f} (avg over {window_seconds}s)")
        else:
            baseline[name] = 0.0
            log("WARN", f"Baseline {name}: 0.0 (metric not available)")
    return baseline


def get_current_metrics(
    prom_url: str, metrics_config: Dict[str, str]
) -> Dict[str, float]:
    """Query current instant metrics from Prometheus."""
    current = {}
    for name, query in metrics_config.items():
        value = query_prometheus(prom_url, query)
        if value is not None:
            current[name] = value
            log("INFO", f"Current {name}: {value:.4f}")
        else:
            current[name] = 0.0
    return current


def check_thresholds(
    baseline: Dict[str, float], current: Dict[str, float], thresholds: Dict[str, Any]
) -> Tuple[bool, str]:
    """Check if current metrics exceed thresholds compared to baseline."""

    # Golden mismatch - any increase is fatal
    if "golden_mismatch" in current:
        if current["golden_mismatch"] > baseline.get("golden_mismatch", 0):
            return (
                True,
                f"golden_mismatch increased: {baseline.get('golden_mismatch', 0)} -> {current['golden_mismatch']}",
            )

    # Error rate delta
    error_delta_pct = thresholds.get("error_rate_delta_pct", 50.0)
    if "error_rate" in current and "error_rate" in baseline:
        if baseline["error_rate"] > 0:
            delta_pct = (
                (current["error_rate"] - baseline["error_rate"])
                / baseline["error_rate"]
            ) * 100
            if delta_pct > error_delta_pct:
                return (
                    True,
                    f"error_rate increased {delta_pct:.1f}% (threshold: {error_delta_pct}%)",
                )

    # Latency p95 delta
    latency_delta_ms = thresholds.get("latency_p95_delta_ms", 200.0)
    if "latency_p95" in current and "latency_p95" in baseline:
        delta = current["latency_p95"] - baseline["latency_p95"]
        if delta > latency_delta_ms:
            return (
                True,
                f"latency_p95 increased {delta:.1f}ms (threshold: {latency_delta_ms}ms)",
            )

    return False, ""


def check_metric_uptime(
    prom_url: str, min_uptime_seconds: int = 300
) -> Tuple[bool, float]:
    """Check if Prometheus has been up long enough for stable metrics.

    Returns (is_ready, uptime_seconds).
    Prevents false positives from cold-start metric noise.
    """
    try:
        # Query target uptime (any target with process_start_time_seconds)
        # First try prometheus job, then fallback to any available metric
        uptime_query = "max(time() - process_start_time_seconds)"
        uptime = query_prometheus(prom_url, uptime_query)

        if uptime is None:
            # Fallback: check if we can query at all
            test_query = "up"
            test_result = query_prometheus(prom_url, test_query)
            if test_result is not None:
                log("WARN", "Could not determine metric uptime, assuming ready")
                return True, -1
            return False, 0

        if uptime < min_uptime_seconds:
            log(
                "WARN",
                f"Prometheus uptime {uptime:.0f}s < required {min_uptime_seconds}s",
            )
            return False, uptime

        log(
            "INFO",
            f"Prometheus uptime: {uptime:.0f}s (required: {min_uptime_seconds}s)",
        )
        return True, uptime

    except Exception as e:
        log("WARN", f"Failed to check metric uptime: {e}")
        return True, -1  # Proceed with warning


def send_alert_with_retry(
    webhook_url: str,
    report: "CanaryReport",
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Tuple[bool, str]:
    """Send rollback alert with exponential backoff retry.

    Args:
        webhook_url: Webhook URL
        report: Canary report
        max_retries: Maximum retry attempts (default 3)
        base_delay: Base delay in seconds (doubles each retry)
    """
    if not webhook_url:
        return True, "no webhook configured"

    last_error = ""
    for attempt in range(max_retries):
        success, msg = send_alert(webhook_url, report)
        if success:
            return True, msg

        last_error = msg
        if attempt < max_retries - 1:
            delay = base_delay * (2**attempt)
            log("WARN", f"Alert attempt {attempt + 1} failed, retrying in {delay}s...")
            time.sleep(delay)

    log("ERROR", f"All {max_retries} alert attempts failed: {last_error}")

    # Risk mitigation 4.3: Write to incident fallback when webhook fails
    if report.rollback_triggered:
        fallback_path = write_incident_fallback(report)
        if fallback_path:
            log("INFO", f"Incident recorded to fallback: {fallback_path}")

    return False, f"failed after {max_retries} attempts: {last_error}"


def send_alert(webhook_url: str, report: "CanaryReport") -> Tuple[bool, str]:
    """Send rollback alert to webhook (Slack/Teams/Discord compatible).

    Expects webhook_url to accept JSON payload with 'text' or 'content' field.
    """
    if not webhook_url:
        return True, "no webhook configured"

    try:
        # Build alert message
        alert_text = f"""🚨 **CANARY ROLLBACK TRIGGERED**

**Canary:** {report.name}
**Reason:** {report.rollback_reason}
**Environment:** staging
**Time:** {report.end_time or datetime.now(timezone.utc).isoformat()}
**Git SHA:** {report.git_sha or 'unknown'}
**Config:** {report.config_path}

**Flags Rolled Back:** {', '.join(report.flags_enabled)}

**Metrics Delta:**
{json.dumps(report.metrics_delta, indent=2)}

**Smoke Test:** {'PASSED' if report.smoke_returncode == 0 else f'FAILED (code {report.smoke_returncode})'}

[View Report]({report.config_path})
"""
        # Try Slack format first, then fallback to generic
        payload = {
            "text": alert_text,  # Slack
            "content": alert_text,  # Discord
            "message": alert_text,  # Generic
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status < 300:
                log("INFO", "Alert sent successfully")
                return True, "sent"
            else:
                return False, f"HTTP {resp.status}"

    except Exception as e:
        log("WARN", f"Failed to send alert: {e}")
        return False, str(e)


def execute_rollback(
    flags_to_disable: List[str], env: str = "staging", webhook_url: str = ""
) -> Tuple[bool, str]:
    """Execute rollback by disabling flags and optionally running rollback script."""
    errors = []

    # Disable all enabled flags
    for flag in flags_to_disable:
        success, msg = toggle_flag(flag, enable=False, env=env)
        if not success:
            errors.append(f"Failed to disable {flag}: {msg}")

    # Run rollback script if it exists
    rollback_script = PROJECT_ROOT / "scripts/rollback_failure_catalog.sh"
    if rollback_script.exists():
        log("STEP", "Running rollback script...")
        try:
            result = subprocess.run(
                [str(rollback_script), "--force"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=PROJECT_ROOT,
            )
            if result.returncode != 0:
                errors.append(f"Rollback script failed: {result.stderr}")
        except Exception as e:
            errors.append(f"Rollback script error: {e}")

    if errors:
        return False, "; ".join(errors)
    return True, "success"


def run_canary(
    config: Dict[str, Any], dry_run: bool = False, watch_seconds: int = 0
) -> CanaryReport:
    """Execute the full canary workflow."""

    # Get provenance info
    git_sha, git_branch = get_git_info()
    hostname, user = get_hostname_user()
    config_hash = get_config_hash(config)

    report = CanaryReport(
        name=config.get("name", "canary"),
        start_time=datetime.now(timezone.utc).isoformat(),
        config_path=config.get("_config_path", ""),
        dry_run=dry_run,
        git_sha=git_sha,
        git_branch=git_branch,
        config_hash=config_hash,
        hostname=hostname,
        user=user,
    )

    log("INFO", f"Provenance: git={git_sha}@{git_branch} host={hostname} user={user}")

    # Risk mitigation 4.1: Check for network filesystem
    fstype = check_filesystem_type(DEFAULT_FLAGS_PATH)
    if fstype not in ("unknown", "ext4", "ext3", "xfs", "btrfs", "tmpfs"):
        log(
            "WARN",
            f"Feature flags on {fstype} filesystem - atomic operations may be unreliable",
        )

    env = config.get("environment", "staging")
    flags_to_enable = config.get("feature_flags", [])
    report.flags_enabled = flags_to_enable

    prom_url = config.get("prometheus", {}).get("url", DEFAULT_PROMETHEUS_URL)
    report.prometheus_url = prom_url

    # Baseline window configuration
    baseline_window = config.get("prometheus", {}).get("baseline_window_seconds", 300)
    report.baseline_window_seconds = baseline_window

    # Alert webhook configuration
    webhook_url = config.get("alerting", {}).get("webhook_url", "")
    webhook_url = webhook_url or os.environ.get("CANARY_WEBHOOK_URL", "")

    metrics_queries = config.get("prometheus", {}).get("metrics", {})
    thresholds = config.get("thresholds", {})

    smoke_cfg = config.get("smoke", {})
    smoke_script = smoke_cfg.get(
        "script", str(PROJECT_ROOT / "scripts/ops/canary_smoke_test.sh")
    )
    smoke_timeout = smoke_cfg.get("timeout_seconds", 60)
    report.smoke_script = smoke_script

    # Check if metric uptime guard is required
    require_metric_uptime = config.get("prometheus", {}).get(
        "require_metric_uptime", True
    )

    try:
        # Step 0: Check Prometheus metric uptime (cold-start guard)
        # Risk mitigation 4.2: Option to wait instead of hard-fail on Prometheus restart
        wait_for_uptime = config.get("prometheus", {}).get(
            "wait_for_metric_uptime", False
        )
        if require_metric_uptime and not dry_run:
            log(
                "STEP",
                f"Checking Prometheus metric uptime (min: {baseline_window}s)...",
            )
            is_ready, uptime = check_metric_uptime(prom_url, baseline_window)
            if not is_ready and uptime >= 0:
                if wait_for_uptime:
                    wait_time = int(baseline_window - uptime) + 10  # Add 10s buffer
                    log(
                        "WARN",
                        f"Prometheus uptime {uptime:.0f}s < required {baseline_window}s",
                    )
                    log("INFO", f"Waiting {wait_time}s for metrics to stabilize...")
                    time.sleep(wait_time)
                    is_ready, uptime = check_metric_uptime(prom_url, baseline_window)

                if not is_ready and uptime >= 0:
                    report.errors.append(
                        f"Prometheus uptime {uptime:.0f}s < required {baseline_window}s"
                    )
                    report.success = False
                    log(
                        "ERROR",
                        f"Aborting: metrics not stable (uptime {uptime:.0f}s < {baseline_window}s)",
                    )
                    return report

        # Step 1: Get baseline metrics with range averaging
        log("STEP", f"Collecting baseline metrics (avg over {baseline_window}s)...")
        report.metrics_baseline = get_baseline_metrics(
            prom_url, metrics_queries, baseline_window
        )

        # Step 2: Enable feature flags
        log("STEP", f"Enabling flags: {flags_to_enable}")
        for flag in flags_to_enable:
            success, msg = toggle_flag(flag, enable=True, env=env, dry_run=dry_run)
            if not success:
                report.flag_enable_error = msg
                report.errors.append(f"Failed to enable {flag}: {msg}")
                report.rollback_triggered = True
                report.rollback_reason = "flag_enable_failed"
                return report
        report.flag_enable_status = "success"

        # Step 3: Run smoke test
        log("STEP", f"Running smoke test: {smoke_script}")
        if not dry_run:
            rc, stdout, stderr, duration = run_smoke_script(smoke_script, smoke_timeout)
            report.smoke_returncode = rc
            report.smoke_stdout = (
                stdout[-2000:] if len(stdout) > 2000 else stdout
            )  # Truncate
            report.smoke_stderr = stderr[-2000:] if len(stderr) > 2000 else stderr
            report.smoke_duration_seconds = duration

            if rc != 0:
                log("ERROR", f"Smoke test failed with code {rc}")
                report.rollback_triggered = True
                report.rollback_reason = f"smoke_failed_code_{rc}"
        else:
            log("INFO", "[DRY-RUN] Would run smoke test")
            report.smoke_returncode = 0

        # Step 4: Watch mode - monitor metrics over time
        if watch_seconds > 0 and not dry_run and not report.rollback_triggered:
            log("STEP", f"Watching metrics for {watch_seconds}s...")
            end_time = time.time() + watch_seconds
            check_interval = min(30, watch_seconds // 10)

            while time.time() < end_time:
                time.sleep(check_interval)
                current = get_current_metrics(prom_url, metrics_queries)
                should_rollback, reason = check_thresholds(
                    report.metrics_baseline, current, thresholds
                )
                if should_rollback:
                    report.metrics_current = current
                    report.rollback_triggered = True
                    report.rollback_reason = reason
                    break
                log("INFO", f"Metrics OK, {int(end_time - time.time())}s remaining...")

        # Step 5: Final metrics check
        if not report.rollback_triggered and not dry_run:
            log("STEP", "Final metrics check...")
            report.metrics_current = get_current_metrics(prom_url, metrics_queries)

            # Calculate deltas
            for key in report.metrics_baseline:
                if key in report.metrics_current:
                    report.metrics_delta[key] = (
                        report.metrics_current[key] - report.metrics_baseline[key]
                    )

            should_rollback, reason = check_thresholds(
                report.metrics_baseline, report.metrics_current, thresholds
            )
            if should_rollback:
                report.rollback_triggered = True
                report.rollback_reason = reason

        # Step 6: Rollback if needed
        if report.rollback_triggered and flags_to_enable:
            log("WARN", f"Triggering rollback: {report.rollback_reason}")
            if not dry_run:
                success, msg = execute_rollback(flags_to_enable, env)
                report.rollback_status = "success" if success else f"failed: {msg}"

                # Send alert on rollback (with retry)
                if webhook_url:
                    log("STEP", "Sending rollback alert (with retry)...")
                    alert_ok, alert_msg = send_alert_with_retry(webhook_url, report)
                    report.alert_sent = alert_ok
                    report.alert_error = "" if alert_ok else alert_msg
            else:
                log("INFO", "[DRY-RUN] Would execute rollback")
                report.rollback_status = "dry-run"

        # Success if no rollback needed
        report.success = not report.rollback_triggered

    except Exception as e:
        report.errors.append(str(e))
        report.success = False
        log("ERROR", f"Canary failed: {e}")

    report.end_time = datetime.now(timezone.utc).isoformat()
    return report


def write_report(report: CanaryReport, output_path: str):
    """Write report to JSON file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)
        f.write("\n")
    log("INFO", f"Report written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AOS Canary Runner - Feature flag, smoke test, metrics monitoring"
    )
    parser.add_argument(
        "--config", required=True, help="Path to canary config (YAML/JSON)"
    )
    parser.add_argument(
        "--report",
        default="scripts/ops/canary/reports/latest_report.json",
        help="Output report path",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would happen without changes"
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Watch metrics for N seconds after smoke test",
    )
    args = parser.parse_args()

    log("INFO", "=" * 60)
    log("INFO", "         AOS Canary Runner")
    log("INFO", "=" * 60)

    # Load config
    config = load_config(args.config)
    config["_config_path"] = args.config

    log("INFO", f"Config: {args.config}")
    log("INFO", f"Dry-run: {args.dry_run}")
    log("INFO", f"Watch: {args.watch}s")
    print()

    # Run canary
    report = run_canary(config, dry_run=args.dry_run, watch_seconds=args.watch)

    # Write report
    write_report(report, args.report)

    # Print summary
    print()
    log("INFO", "=" * 60)
    if report.success:
        log("INFO", "         CANARY PASSED")
    else:
        log("ERROR", "         CANARY FAILED")
        if report.rollback_triggered:
            log("WARN", f"         Rollback reason: {report.rollback_reason}")
    log("INFO", "=" * 60)

    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    main()
