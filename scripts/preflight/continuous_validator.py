#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Continuous file validation daemon
# Reference: docs/architecture/contracts/

"""
Continuous Validator Daemon

Watches the codebase for file changes and runs contract checks in real-time.
Provides immediate feedback while coding, not just at commit time.

Usage:
    python continuous_validator.py              # Run in foreground
    python continuous_validator.py --daemon     # Run as background daemon
    python continuous_validator.py --status     # Show current status
    python continuous_validator.py --stop       # Stop the daemon
"""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

# Try to import watchdog, install if missing
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    print("Installing watchdog...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog", "-q"])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_PATH = REPO_ROOT / "backend"
STATUS_FILE = REPO_ROOT / ".validator_status.json"
PID_FILE = REPO_ROOT / ".validator.pid"
LOG_FILE = REPO_ROOT / ".validator.log"

# Debounce settings (avoid running checks multiple times for rapid saves)
DEBOUNCE_SECONDS = 1.0

# Check configurations: pattern -> checks to run
CHECK_CONFIG = {
    # Schema files
    "app/schemas/**/*.py": ["naming"],
    # Model files
    "app/models/**/*.py": ["naming"],
    # API files
    "app/api/**/*.py": ["naming", "router", "boundary"],
    # Migration files
    "alembic/versions/*.py": ["migration"],
    # Main.py
    "app/main.py": ["router"],
    # Registry
    "app/api/registry.py": ["router"],
}

# Individual check functions
CHECKS = {}


# =============================================================================
# Status Management
# =============================================================================

class ValidatorStatus:
    """Manages the status file for real-time feedback."""

    def __init__(self, status_file: Path):
        self.status_file = status_file
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = self._default()
        else:
            self.data = self._default()

    def _default(self):
        return {
            "status": "UNKNOWN",
            "last_check": None,
            "violations": [],
            "files_watched": 0,
            "checks_run": 0,
            "started_at": None,
            "pid": None,
        }

    def _save(self):
        with open(self.status_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def update(self, **kwargs):
        with self.lock:
            self.data.update(kwargs)
            self.data["last_check"] = datetime.now().isoformat()
            self._save()

    def add_violation(self, violation: dict):
        with self.lock:
            # Keep only last 50 violations
            self.data["violations"] = self.data.get("violations", [])[-49:] + [violation]
            self.data["status"] = "VIOLATIONS"
            self._save()

    def clear_violations(self):
        with self.lock:
            self.data["violations"] = []
            self.data["status"] = "CLEAN"
            self._save()

    def set_clean(self):
        with self.lock:
            if not self.data.get("violations"):
                self.data["status"] = "CLEAN"
                self._save()

    def increment_checks(self):
        with self.lock:
            self.data["checks_run"] = self.data.get("checks_run", 0) + 1
            self._save()

    def get(self):
        with self.lock:
            return self.data.copy()


# =============================================================================
# Logging
# =============================================================================

class Logger:
    """Simple logger that writes to file and optionally stdout."""

    def __init__(self, log_file: Path, verbose: bool = True):
        self.log_file = log_file
        self.verbose = verbose
        self.lock = threading.Lock()

    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"

        with self.lock:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")

            if self.verbose:
                color = {"INFO": "\033[0m", "WARN": "\033[33m", "ERROR": "\033[31m", "PASS": "\033[32m"}.get(level, "")
                reset = "\033[0m" if color else ""
                print(f"{color}{line}{reset}")

    def info(self, msg): self.log("INFO", msg)
    def warn(self, msg): self.log("WARN", msg)
    def error(self, msg): self.log("ERROR", msg)
    def passed(self, msg): self.log("PASS", msg)


# =============================================================================
# Check Implementations
# =============================================================================

def run_check(check_name: str, file_path: Path, logger: Logger) -> list[dict]:
    """Run a specific check and return violations."""
    violations = []

    if check_name == "naming":
        violations = check_naming_inline(file_path)
    elif check_name == "migration":
        violations = check_migration_inline(file_path)
    elif check_name == "router":
        violations = check_router_inline(file_path)
    elif check_name == "boundary":
        violations = check_boundary_inline(file_path)

    return violations


def check_naming_inline(file_path: Path) -> list[dict]:
    """Inline naming check for a single file."""
    import re
    violations = []

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    # Check for context suffixes in schema files
    if "/schemas/" in str(file_path):
        context_patterns = [
            (r":\s*\w+.*#.*_remaining", "NC-001", "Context suffix '_remaining' in schema"),
            (r":\s*\w+.*#.*_current", "NC-001", "Context suffix '_current' in schema"),
            (r"(\w+_remaining)\s*:", "NC-001", "Context suffix '_remaining' in field name"),
            (r"(\w+_current)\s*:", "NC-001", "Context suffix '_current' in field name"),
            (r"(\w+_total)\s*:", "NC-001", "Context suffix '_total' in field name"),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, rule, message in context_patterns:
                if re.search(pattern, line):
                    violations.append({
                        "file": str(file_path),
                        "line": line_num,
                        "rule": rule,
                        "message": message,
                        "code": line.strip()[:60],
                    })

    # Check for camelCase in model files
    if "/models/" in str(file_path):
        camel_pattern = re.compile(r"^\s+(\w+[a-z][A-Z]\w*)\s*:")
        for line_num, line in enumerate(lines, 1):
            match = camel_pattern.search(line)
            if match and not match.group(1).startswith("_"):
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": "NC-003",
                    "message": f"camelCase field '{match.group(1)}' in model",
                    "code": line.strip()[:60],
                })

    return violations


def check_migration_inline(file_path: Path) -> list[dict]:
    """Inline migration check for a single file."""
    import re
    violations = []

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    # Check for MIGRATION_CONTRACT header
    if "MIGRATION_CONTRACT:" not in content:
        violations.append({
            "file": str(file_path),
            "line": 1,
            "rule": "MIG-001",
            "message": "Missing MIGRATION_CONTRACT header",
            "code": "",
        })
        return violations

    # Extract contract parent and down_revision
    contract_match = re.search(r"#\s*parent:\s*(\S+)", content)
    down_rev_match = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)

    if contract_match and down_rev_match:
        contract_parent = contract_match.group(1)
        down_revision = down_rev_match.group(1)

        if contract_parent != down_revision:
            violations.append({
                "file": str(file_path),
                "line": down_rev_match.start(),
                "rule": "MIG-002",
                "message": f"Contract parent '{contract_parent}' != down_revision '{down_revision}'",
                "code": "",
            })

    return violations


def check_router_inline(file_path: Path) -> list[dict]:
    """Inline router wiring check."""
    import re
    violations = []

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    # If this is main.py, check for router imports
    if file_path.name == "main.py":
        for line_num, line in enumerate(lines, 1):
            # Check for router imports (but allow registry)
            if re.search(r"from\s+\.?app\.api\.", line) or re.search(r"from\s+\.api\.", line):
                if "registry" not in line:
                    violations.append({
                        "file": str(file_path),
                        "line": line_num,
                        "rule": "RW-001",
                        "message": "Router import in main.py (use registry.py)",
                        "code": line.strip()[:60],
                    })

            # Check for include_router
            if "include_router" in line and not line.strip().startswith("#"):
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": "RW-002",
                    "message": "include_router in main.py (use registry.py)",
                    "code": line.strip()[:60],
                })

    return violations


def check_boundary_inline(file_path: Path) -> list[dict]:
    """Inline runtime/API boundary check."""
    import re
    violations = []

    # Skip adapters
    if "_adapters" in str(file_path):
        return violations

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    # Patterns for direct runtime access
    runtime_patterns = [
        (r"\.headroom\.tokens\b", "RAB-001", "Direct access to .headroom.tokens"),
        (r"\.headroom\.runs\b", "RAB-001", "Direct access to .headroom.runs"),
        (r"\.headroom\.cost_cents\b", "RAB-001", "Direct access to .headroom.cost_cents"),
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern, rule, message in runtime_patterns:
            if re.search(pattern, line):
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": rule,
                    "message": message + " (use adapter)",
                    "code": line.strip()[:60],
                })

    return violations


# =============================================================================
# File Watcher
# =============================================================================

class ContractEventHandler(FileSystemEventHandler):
    """Handles file system events and triggers appropriate checks."""

    def __init__(self, status: ValidatorStatus, logger: Logger):
        self.status = status
        self.logger = logger
        self.pending_checks = {}
        self.lock = threading.Lock()
        self.debounce_timer = None

    def _get_checks_for_file(self, file_path: Path) -> list[str]:
        """Determine which checks to run for a given file."""
        import fnmatch

        try:
            rel_path = str(file_path.relative_to(BACKEND_PATH))
        except ValueError:
            return []

        checks = set()

        for pattern, check_list in CHECK_CONFIG.items():
            # Try both with and without leading path
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, f"**/{pattern}"):
                checks.update(check_list)

            # Also check simple contains for paths like "app/schemas"
            pattern_base = pattern.replace("**/*.py", "").replace("/*.py", "").rstrip("/")
            if pattern_base in rel_path:
                checks.update(check_list)

        return list(checks)

    def _schedule_check(self, file_path: Path):
        """Schedule a check with debouncing."""
        with self.lock:
            self.pending_checks[str(file_path)] = time.time()

            # Cancel existing timer
            if self.debounce_timer:
                self.debounce_timer.cancel()

            # Schedule new timer
            self.debounce_timer = threading.Timer(DEBOUNCE_SECONDS, self._run_pending_checks)
            self.debounce_timer.start()

    def _run_pending_checks(self):
        """Run all pending checks."""
        with self.lock:
            files_to_check = list(self.pending_checks.keys())
            self.pending_checks.clear()

        all_violations = []

        for file_str in files_to_check:
            file_path = Path(file_str)
            if not file_path.exists():
                continue

            checks = self._get_checks_for_file(file_path)
            if not checks:
                continue

            self.logger.info(f"Checking: {file_path.name} [{', '.join(checks)}]")

            for check in checks:
                violations = run_check(check, file_path, self.logger)
                all_violations.extend(violations)

            self.status.increment_checks()

        # Update status
        if all_violations:
            for v in all_violations:
                self.status.add_violation(v)
                self.logger.warn(f"  ✗ {v['rule']}: {v['message']} ({v['file']}:{v['line']})")
        else:
            self.status.set_clean()
            if files_to_check:
                self.logger.passed(f"  ✓ All checks passed")

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".py"):
            return

        file_path = Path(event.src_path)
        if file_path.is_relative_to(BACKEND_PATH):
            self._schedule_check(file_path)

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".py"):
            return

        file_path = Path(event.src_path)
        if file_path.is_relative_to(BACKEND_PATH):
            self.logger.info(f"New file: {file_path.name}")
            self._schedule_check(file_path)


# =============================================================================
# Daemon Management
# =============================================================================

def start_daemon(verbose: bool = False):
    """Start the continuous validator daemon."""
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            print(f"Daemon already running (PID {pid})")
            return
        except OSError:
            PID_FILE.unlink()  # Stale PID file

    # Write PID
    PID_FILE.write_text(str(os.getpid()))

    # Initialize
    status = ValidatorStatus(STATUS_FILE)
    logger = Logger(LOG_FILE, verbose=verbose)

    status.update(
        status="STARTING",
        started_at=datetime.now().isoformat(),
        pid=os.getpid(),
        violations=[],
    )

    logger.info("=" * 60)
    logger.info("Continuous Validator Started")
    logger.info(f"Watching: {BACKEND_PATH}")
    logger.info(f"Status file: {STATUS_FILE}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)

    # Set up file watcher
    event_handler = ContractEventHandler(status, logger)
    observer = Observer()
    observer.schedule(event_handler, str(BACKEND_PATH), recursive=True)

    # Handle shutdown
    def shutdown(signum, frame):
        logger.info("Shutting down...")
        observer.stop()
        status.update(status="STOPPED")
        if PID_FILE.exists():
            PID_FILE.unlink()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Start watching
    observer.start()
    status.update(status="WATCHING", files_watched=sum(1 for _ in BACKEND_PATH.rglob("*.py")))

    logger.info("Watching for changes... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


def stop_daemon():
    """Stop the daemon."""
    if not PID_FILE.exists():
        print("Daemon not running")
        return

    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped daemon (PID {pid})")
    except OSError:
        print("Daemon not running (stale PID)")

    if PID_FILE.exists():
        PID_FILE.unlink()


def show_status():
    """Show current validator status."""
    if not STATUS_FILE.exists():
        print("No status file found. Daemon may not have run yet.")
        return

    status = ValidatorStatus(STATUS_FILE)
    data = status.get()

    # Status header
    status_color = {
        "CLEAN": "\033[32m",      # Green
        "VIOLATIONS": "\033[31m", # Red
        "WATCHING": "\033[34m",   # Blue
        "STOPPED": "\033[33m",    # Yellow
    }.get(data.get("status", ""), "")
    reset = "\033[0m"

    print("╔════════════════════════════════════════════════════════════╗")
    print(f"║  CONTINUOUS VALIDATOR STATUS                               ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Status:       {status_color}{data.get('status', 'UNKNOWN'):12}{reset}                         ║")
    print(f"║  PID:          {str(data.get('pid', '-')):12}                         ║")
    print(f"║  Last Check:   {str(data.get('last_check', '-'))[:19]:19}              ║")
    print(f"║  Checks Run:   {data.get('checks_run', 0):<12}                         ║")
    print(f"║  Files Watched:{data.get('files_watched', 0):<12}                         ║")
    print("╚════════════════════════════════════════════════════════════╝")

    violations = data.get("violations", [])
    if violations:
        print(f"\n⚠ {len(violations)} VIOLATION(S):\n")
        for v in violations[-10:]:  # Show last 10
            print(f"  [{v.get('rule')}] {v.get('file')}:{v.get('line')}")
            print(f"    {v.get('message')}")
            if v.get('code'):
                print(f"    Code: {v.get('code')}")
            print()
    else:
        print("\n✓ No violations")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Continuous Validator Daemon")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    parser.add_argument("--status", "-s", action="store_true", help="Show status")
    parser.add_argument("--stop", action="store_true", help="Stop daemon")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.stop:
        stop_daemon()
    elif args.status:
        show_status()
    else:
        start_daemon(verbose=not args.daemon or args.verbose)


if __name__ == "__main__":
    main()
