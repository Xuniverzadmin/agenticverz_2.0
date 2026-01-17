#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Real-time validator status dashboard
# Reference: docs/architecture/contracts/

"""
Validator Dashboard

Real-time terminal dashboard showing contract validation status.
Updates automatically when violations are detected or cleared.

Usage:
    python validator_dashboard.py           # Live dashboard
    python validator_dashboard.py --watch   # Watch mode (compact)
    python validator_dashboard.py --notify  # Desktop notifications
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
STATUS_FILE = REPO_ROOT / ".validator_status.json"
LOG_FILE = REPO_ROOT / ".validator.log"


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def get_status() -> dict:
    """Load current status from file."""
    if not STATUS_FILE.exists():
        return {"status": "NOT_RUNNING", "violations": [], "checks_run": 0}

    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"status": "ERROR", "violations": [], "checks_run": 0}


def send_notification(title: str, message: str, urgency: str = "normal"):
    """Send desktop notification (Linux)."""
    try:
        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message],
            capture_output=True,
            timeout=2
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # notify-send not available


def get_recent_log_lines(n: int = 10) -> list[str]:
    """Get recent log lines."""
    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
            return [l.strip() for l in lines[-n:]]
    except IOError:
        return []


def colorize(text: str, color: str) -> str:
    """Add ANSI color codes."""
    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def render_dashboard(status: dict):
    """Render the full dashboard."""
    clear_screen()

    # Header
    print(colorize("╔══════════════════════════════════════════════════════════════════╗", "cyan"))
    print(colorize("║           CONTINUOUS VALIDATOR DASHBOARD                         ║", "cyan"))
    print(colorize("╚══════════════════════════════════════════════════════════════════╝", "cyan"))
    print()

    # Status box
    status_text = status.get("status", "UNKNOWN")
    status_color = {
        "CLEAN": "green",
        "VIOLATIONS": "red",
        "WATCHING": "blue",
        "STARTING": "yellow",
        "STOPPED": "yellow",
        "NOT_RUNNING": "yellow",
        "ERROR": "red",
    }.get(status_text, "white")

    print(f"  Status:        {colorize(status_text, status_color)}")
    print(f"  PID:           {status.get('pid', '-')}")
    print(f"  Started:       {status.get('started_at', '-')}")
    print(f"  Last Check:    {status.get('last_check', '-')}")
    print(f"  Checks Run:    {status.get('checks_run', 0)}")
    print(f"  Files Watched: {status.get('files_watched', 0)}")
    print()

    # Violations section
    violations = status.get("violations", [])
    if violations:
        print(colorize("┌─────────────────────────────────────────────────────────────────┐", "red"))
        print(colorize(f"│  ⚠ {len(violations)} VIOLATION(S)                                              │", "red"))
        print(colorize("└─────────────────────────────────────────────────────────────────┘", "red"))
        print()

        for v in violations[-5:]:  # Show last 5
            rule = colorize(f"[{v.get('rule', '?')}]", "yellow")
            file_info = f"{v.get('file', '?')}:{v.get('line', '?')}"
            print(f"  {rule} {file_info}")
            print(f"       {v.get('message', '')}")
            if v.get('code'):
                print(f"       {colorize(v.get('code'), 'cyan')}")
            print()
    else:
        print(colorize("┌─────────────────────────────────────────────────────────────────┐", "green"))
        print(colorize("│  ✓ NO VIOLATIONS                                                │", "green"))
        print(colorize("└─────────────────────────────────────────────────────────────────┘", "green"))
        print()

    # Recent activity
    print(colorize("─── Recent Activity ───────────────────────────────────────────────", "cyan"))
    log_lines = get_recent_log_lines(8)
    for line in log_lines:
        # Color based on log level
        if "[PASS]" in line:
            print(f"  {colorize(line, 'green')}")
        elif "[WARN]" in line or "[ERROR]" in line:
            print(f"  {colorize(line, 'red')}")
        else:
            print(f"  {line}")

    if not log_lines:
        print("  (no recent activity)")

    print()
    print(colorize("─── Controls ─────────────────────────────────────────────────────", "cyan"))
    print("  q: Quit  |  r: Refresh  |  c: Clear violations  |  f: Full check")
    print()
    print(f"  Auto-refresh: 2s | {datetime.now().strftime('%H:%M:%S')}")


def render_compact(status: dict, prev_status: dict):
    """Render compact watch mode output."""
    status_text = status.get("status", "?")
    violations = len(status.get("violations", []))
    checks = status.get("checks_run", 0)

    # Only print if something changed
    if status_text != prev_status.get("status") or violations != len(prev_status.get("violations", [])):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_color = "green" if status_text == "CLEAN" else "red" if violations > 0 else "blue"
        status_str = colorize(f"[{status_text}]", status_color)
        violations_str = colorize(f"{violations} violations", "red") if violations else colorize("clean", "green")

        print(f"{timestamp} {status_str} {violations_str} ({checks} checks)")


def run_full_check():
    """Run full preflight checks."""
    script = REPO_ROOT / "scripts" / "preflight" / "run_all_checks.sh"
    if script.exists():
        subprocess.run(["bash", str(script)])
    else:
        print("Full check script not found")


def dashboard_mode():
    """Run interactive dashboard."""
    import select
    import sys
    import termios
    import tty

    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        # Set terminal to raw mode for key input
        tty.setcbreak(sys.stdin.fileno())

        last_status = {}
        while True:
            status = get_status()
            render_dashboard(status)

            # Check for input with timeout
            if select.select([sys.stdin], [], [], 2)[0]:
                key = sys.stdin.read(1)
                if key == 'q':
                    break
                elif key == 'r':
                    continue  # Refresh
                elif key == 'c':
                    # Clear violations in status file
                    status["violations"] = []
                    status["status"] = "CLEAN"
                    with open(STATUS_FILE, "w") as f:
                        json.dump(status, f)
                elif key == 'f':
                    clear_screen()
                    run_full_check()
                    input("\nPress Enter to continue...")

            last_status = status

    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        clear_screen()


def watch_mode():
    """Run compact watch mode."""
    print(colorize("Validator Watch Mode (Ctrl+C to stop)", "cyan"))
    print("-" * 50)

    last_status = {}
    try:
        while True:
            status = get_status()
            render_compact(status, last_status)
            last_status = status
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped")


def notify_mode():
    """Run with desktop notifications."""
    print(colorize("Validator Notification Mode (Ctrl+C to stop)", "cyan"))
    print("Will send desktop notifications on status changes")
    print("-" * 50)

    last_violations = 0
    last_status = ""

    try:
        while True:
            status = get_status()
            current_violations = len(status.get("violations", []))
            current_status = status.get("status", "")

            # Notify on new violations
            if current_violations > last_violations:
                new_count = current_violations - last_violations
                v = status.get("violations", [])[-1] if status.get("violations") else {}
                send_notification(
                    f"⚠ {new_count} New Violation(s)",
                    f"[{v.get('rule')}] {v.get('message', '')}",
                    urgency="critical"
                )
                print(f"  ⚠ Notified: {new_count} new violation(s)")

            # Notify when clean
            if current_status == "CLEAN" and last_status == "VIOLATIONS":
                send_notification(
                    "✓ All Clean",
                    "All contract violations resolved",
                    urgency="normal"
                )
                print("  ✓ Notified: All clean")

            last_violations = current_violations
            last_status = current_status
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped")


def main():
    parser = argparse.ArgumentParser(description="Validator Dashboard")
    parser.add_argument("--watch", "-w", action="store_true", help="Compact watch mode")
    parser.add_argument("--notify", "-n", action="store_true", help="Desktop notification mode")
    parser.add_argument("--once", "-1", action="store_true", help="Show status once and exit")
    args = parser.parse_args()

    if args.once:
        status = get_status()
        render_dashboard(status)
    elif args.watch:
        watch_mode()
    elif args.notify:
        notify_mode()
    else:
        try:
            dashboard_mode()
        except Exception:
            # Fallback for non-interactive terminals
            watch_mode()


if __name__ == "__main__":
    main()
