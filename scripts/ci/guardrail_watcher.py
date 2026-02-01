#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL WATCHER - Event-driven pre-diagnosis system.
# artifact_class: CODE
"""
GUARDRAIL WATCHER - Event-driven pre-diagnosis system.

Watches for file changes and runs relevant guardrails BEFORE commit.
Uses inotify (low memory) with debouncing (batch changes).

Usage:
    python guardrail_watcher.py              # Watch mode
    python guardrail_watcher.py --daemon     # Background daemon
    python guardrail_watcher.py --check FILE # Check single file
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import defaultdict

# Configuration
DEBOUNCE_SECONDS = 3  # Wait this long after last change before running
MAX_BATCH_SIZE = 20   # Run after this many files regardless of debounce
WATCH_EXTENSIONS = {'.py', '.yaml', '.yml'}
IGNORE_PATTERNS = {'__pycache__', '.git', 'node_modules', '.pytest_cache', 'dist', 'build'}

# Map file patterns to relevant guardrails
FILE_TO_GUARDRAILS: Dict[str, List[str]] = {
    # API routes
    'api/*.py': ['DOMAIN-001', 'DATA-002', 'API-001', 'API-002'],
    'api/aos_accounts.py': ['DOMAIN-002'],
    'api/overview.py': ['DOMAIN-003'],

    # Services
    'services/*.py': ['DOMAIN-001', 'CROSS-001', 'API-001'],
    'services/limit*.py': ['LIMITS-001', 'LIMITS-002', 'LIMITS-003'],
    'services/policy*.py': ['LIMITS-003', 'AUDIT-001'],
    'services/incident*.py': ['CROSS-001', 'AUDIT-001'],

    # Models
    'models/*.py': ['DATA-001', 'LIMITS-001'],

    # Worker
    'worker/*.py': ['LIMITS-002', 'DOMAIN-001'],

    # Capabilities
    'AURORA_L2_CAPABILITY_REGISTRY/*.yaml': ['CAP-001', 'CAP-002', 'CAP-003'],

    # Intents
    'intents/*.yaml': ['CAP-002'],
}

# Guardrail scripts
GUARDRAIL_SCRIPTS = {
    'DOMAIN-001': 'check_domain_writes.py',
    'DOMAIN-002': 'check_account_boundaries.py',
    'DOMAIN-003': 'check_overview_readonly.py',
    'DATA-001': 'check_foreign_keys.py',
    'DATA-002': 'check_tenant_queries.py',
    'CROSS-001': 'check_cross_domain_propagation.py',
    'CROSS-002': 'check_bidirectional_queries.py',
    'LIMITS-001': 'check_limit_tables.py',
    'LIMITS-002': 'check_limit_enforcement.py',
    'LIMITS-003': 'check_limit_audit.py',
    'AUDIT-001': 'check_governance_audit.py',
    'AUDIT-002': 'check_audit_completeness.py',
    'CAP-001': 'check_capability_endpoints.py',
    'CAP-002': 'check_console_boundaries.py',
    'CAP-003': 'check_capability_status.py',
    'API-001': 'check_facade_usage.py',
    'API-002': 'check_response_envelopes.py',
}


class GuardrailWatcher:
    """Event-driven guardrail checker with debouncing."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.script_dir = base_path / "scripts" / "ci"
        self.pending_files: Set[Path] = set()
        self.last_change_time: float = 0
        self.lock = threading.Lock()
        self.running = False
        self.check_thread: Optional[threading.Thread] = None

    def match_file_to_guardrails(self, file_path: Path) -> Set[str]:
        """Determine which guardrails apply to a file."""
        guardrails = set()

        # Get relative path from backend/app or design/l2_1
        rel_path = str(file_path)

        for pattern, rules in FILE_TO_GUARDRAILS.items():
            # Simple glob matching
            if self._matches_pattern(rel_path, pattern):
                guardrails.update(rules)

        return guardrails

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching."""
        import fnmatch
        # Check if any part of path matches pattern
        parts = pattern.split('/')
        path_parts = path.split('/')

        for i in range(len(path_parts) - len(parts) + 1):
            match = True
            for j, p in enumerate(parts):
                if not fnmatch.fnmatch(path_parts[i + j], p):
                    match = False
                    break
            if match:
                return True
        return False

    def on_file_changed(self, file_path: Path):
        """Called when a file is created/modified."""
        # Skip ignored patterns
        for ignore in IGNORE_PATTERNS:
            if ignore in str(file_path):
                return

        # Skip non-watched extensions
        if file_path.suffix not in WATCH_EXTENSIONS:
            return

        with self.lock:
            self.pending_files.add(file_path)
            self.last_change_time = time.time()

            # Check if we should run immediately (batch size reached)
            if len(self.pending_files) >= MAX_BATCH_SIZE:
                self._trigger_check()

    def _trigger_check(self):
        """Trigger guardrail check for pending files."""
        if self.check_thread and self.check_thread.is_alive():
            return  # Already running

        self.check_thread = threading.Thread(target=self._run_checks)
        self.check_thread.start()

    def _run_checks(self):
        """Run guardrail checks for pending files."""
        with self.lock:
            files = self.pending_files.copy()
            self.pending_files.clear()

        if not files:
            return

        # Collect all applicable guardrails
        guardrails_to_run: Set[str] = set()
        for f in files:
            guardrails_to_run.update(self.match_file_to_guardrails(f))

        if not guardrails_to_run:
            return

        # Print header
        print()
        print("=" * 60)
        print(f"  GUARDRAIL PRE-CHECK ({len(files)} files changed)")
        print(f"  {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"  Files: {[f.name for f in list(files)[:5]]}{'...' if len(files) > 5 else ''}")
        print(f"  Guardrails: {sorted(guardrails_to_run)}")
        print("-" * 60)

        # Run each guardrail
        failures = []
        for rule_id in sorted(guardrails_to_run):
            script = GUARDRAIL_SCRIPTS.get(rule_id)
            if not script:
                continue

            script_path = self.script_dir / script
            if not script_path.exists():
                continue

            print(f"  {rule_id}...", end=" ", flush=True)

            try:
                result = subprocess.run(
                    ['python3', str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    print("✅")
                else:
                    print("❌")
                    failures.append((rule_id, result.stdout + result.stderr))
            except subprocess.TimeoutExpired:
                print("⏱️ TIMEOUT")
            except Exception as e:
                print(f"⚠️ ERROR: {e}")

        # Summary
        print("-" * 60)
        if failures:
            print(f"  ❌ {len(failures)} VIOLATIONS DETECTED")
            print()
            for rule_id, output in failures[:2]:  # Show first 2
                print(f"  [{rule_id}]")
                # Show first few lines of output
                lines = output.strip().split('\n')
                for line in lines[:5]:
                    print(f"    {line}")
                if len(lines) > 5:
                    print(f"    ... ({len(lines) - 5} more lines)")
                print()
            print("  ⚠️  FIX BEFORE COMMIT")
        else:
            print(f"  ✅ All {len(guardrails_to_run)} checks passed")
        print("=" * 60)
        print()

    def debounce_loop(self):
        """Background loop that triggers checks after debounce period."""
        while self.running:
            time.sleep(0.5)  # Check every 500ms

            with self.lock:
                if not self.pending_files:
                    continue

                elapsed = time.time() - self.last_change_time
                if elapsed >= DEBOUNCE_SECONDS:
                    self._trigger_check()

    def start_watching(self):
        """Start watching for file changes using inotify."""
        try:
            import inotify.adapters
        except ImportError:
            print("Installing inotify...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'inotify'],
                          capture_output=True)
            import inotify.adapters

        self.running = True

        # Start debounce thread
        debounce_thread = threading.Thread(target=self.debounce_loop, daemon=True)
        debounce_thread.start()

        # Watch paths
        watch_paths = [
            self.base_path / "backend" / "app",
            self.base_path / "backend" / "AURORA_L2_CAPABILITY_REGISTRY",
            self.base_path / "design" / "l2_1" / "intents",
        ]

        i = inotify.adapters.InotifyTrees([str(p) for p in watch_paths if p.exists()])

        print("=" * 60)
        print("  GUARDRAIL WATCHER ACTIVE")
        print("=" * 60)
        print(f"  Watching: {len([p for p in watch_paths if p.exists()])} directories")
        print(f"  Debounce: {DEBOUNCE_SECONDS}s | Batch size: {MAX_BATCH_SIZE}")
        print(f"  Extensions: {WATCH_EXTENSIONS}")
        print()
        print("  Waiting for file changes... (Ctrl+C to stop)")
        print("=" * 60)
        print()

        try:
            for event in i.event_gen(yield_nones=False):
                (_, type_names, path, filename) = event

                # Only care about modifications and creates
                if not any(t in type_names for t in ['IN_MODIFY', 'IN_CREATE', 'IN_MOVED_TO']):
                    continue

                file_path = Path(path) / filename
                self.on_file_changed(file_path)

        except KeyboardInterrupt:
            print("\n  Watcher stopped.")
            self.running = False


def check_single_file(file_path: Path, base_path: Path):
    """Check guardrails for a single file."""
    watcher = GuardrailWatcher(base_path)
    guardrails = watcher.match_file_to_guardrails(file_path)

    if not guardrails:
        print(f"No guardrails apply to: {file_path}")
        return

    print(f"File: {file_path}")
    print(f"Applicable guardrails: {sorted(guardrails)}")
    print()

    watcher.pending_files.add(file_path)
    watcher._run_checks()


def main():
    base_path = Path(__file__).parent.parent.parent

    if '--check' in sys.argv:
        # Single file check mode
        idx = sys.argv.index('--check')
        if idx + 1 < len(sys.argv):
            file_path = Path(sys.argv[idx + 1])
            check_single_file(file_path, base_path)
        else:
            print("Usage: guardrail_watcher.py --check <file>")
            sys.exit(1)

    elif '--daemon' in sys.argv:
        # Daemon mode - fork to background
        if os.fork() > 0:
            print("Guardrail watcher started in background")
            sys.exit(0)

        # Child process
        os.setsid()
        watcher = GuardrailWatcher(base_path)
        watcher.start_watching()

    else:
        # Interactive watch mode
        watcher = GuardrailWatcher(base_path)
        watcher.start_watching()


if __name__ == "__main__":
    main()
