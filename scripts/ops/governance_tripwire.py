#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | pre-push | manual
#   Execution: sync
# Role: Detect --no-verify bypasses without exception documentation
# Callers: CI pipeline, pre-push hook, manual verification
# Allowed Imports: L6 (stdlib only)
# Forbidden Imports: app.*, backend.*
# Reference: EXC-2026-01, docs/governance/EXCEPTIONS.md
"""
Governance Tripwire

Detects commits that bypassed pre-commit hooks (via --no-verify) without
documenting a formal exception in docs/governance/EXCEPTIONS.md.

Rules:
1. If a commit bypassed hooks but references an exception (EXC-XXXX), it's valid
2. If a commit bypassed hooks with NO exception reference, it's a violation
3. The exception must exist in EXCEPTIONS.md and be CLOSED

Usage:
    python3 scripts/ops/governance_tripwire.py                    # Check recent commits
    python3 scripts/ops/governance_tripwire.py --commits 10       # Check last 10 commits
    python3 scripts/ops/governance_tripwire.py --range HEAD~5..HEAD  # Check range
    python3 scripts/ops/governance_tripwire.py --ci               # CI mode (exit 1 on fail)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# =============================================================================
# CONSTANTS
# =============================================================================

EXCEPTIONS_FILE = "docs/governance/EXCEPTIONS.md"
EXCEPTION_PATTERN = re.compile(r"EXC-\d{4}-\d{2}")

# Indicators that a commit bypassed hooks
BYPASS_INDICATORS = [
    "--no-verify",
    "pre-commit bypass",
    "hook bypass",
    "governance bypass",
    "scope bypass",
]


# =============================================================================
# COLORS
# =============================================================================


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colored(text: str, color: str) -> str:
    """Apply color if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


# =============================================================================
# EXCEPTION VALIDATION
# =============================================================================


def load_exceptions(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Load exception records from EXCEPTIONS.md.

    Returns:
        (exceptions dict, commit_to_exception dict)
        - exceptions: {exception_id: status}
        - commit_to_exception: {commit_hash_prefix: exception_id}
    """
    exceptions_path = repo_root / EXCEPTIONS_FILE

    if not exceptions_path.exists():
        return {}, {}

    content = exceptions_path.read_text()
    exceptions = {}
    commit_to_exception = {}

    # Parse exception blocks
    current_id = None
    current_status = None

    for line in content.split("\n"):
        # Match exception headers like "## EXC-2026-01"
        if line.startswith("## EXC-"):
            match = EXCEPTION_PATTERN.search(line)
            if match:
                current_id = match.group()

        # Match status lines like "**Status:** CLOSED"
        if current_id and "**Status:**" in line:
            if "CLOSED" in line.upper():
                current_status = "CLOSED"
            elif "OPEN" in line.upper():
                current_status = "OPEN"
            else:
                current_status = "UNKNOWN"

            exceptions[current_id] = current_status

        # Match commit references like "**Commit:** `7a0ae4cf...`"
        if current_id and "**Commit:**" in line:
            # Extract commit hash (looks for backtick-wrapped hash)
            commit_match = re.search(r"`([a-f0-9]{7,40})`", line)
            if commit_match:
                commit_hash = commit_match.group(1)
                commit_to_exception[commit_hash[:8]] = current_id

        # Reset after finding status (end of header block)
        if current_id and current_status and line.strip() == "":
            current_id = None
            current_status = None

    return exceptions, commit_to_exception


def validate_exception(
    exception_id: str, exceptions: dict[str, str]
) -> tuple[bool, str]:
    """Validate that an exception exists and is properly closed."""
    if exception_id not in exceptions:
        return False, f"Exception {exception_id} not found in {EXCEPTIONS_FILE}"

    status = exceptions[exception_id]
    if status != "CLOSED":
        return False, f"Exception {exception_id} has status {status}, expected CLOSED"

    return True, f"Exception {exception_id} is valid and CLOSED"


# =============================================================================
# COMMIT ANALYSIS
# =============================================================================


def get_commits(count: int = 5, commit_range: Optional[str] = None) -> list[dict]:
    """Get recent commits with their messages."""
    if commit_range:
        cmd = ["git", "log", commit_range, "--format=%H|%s|%b", "--no-walk=sorted"]
        # For ranges, we need different approach
        cmd = ["git", "log", commit_range, "--format=%H|||%s|||%b|||END"]
    else:
        cmd = ["git", "log", f"-{count}", "--format=%H|||%s|||%b|||END"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return []

    commits = []
    entries = result.stdout.split("|||END")

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        parts = entry.split("|||")
        if len(parts) >= 2:
            commit_hash = parts[0].strip()
            subject = parts[1].strip() if len(parts) > 1 else ""
            body = parts[2].strip() if len(parts) > 2 else ""

            commits.append(
                {
                    "hash": commit_hash,
                    "subject": subject,
                    "body": body,
                    "full_message": f"{subject}\n\n{body}".strip(),
                }
            )

    return commits


def check_commit_for_bypass(commit: dict) -> tuple[bool, Optional[str]]:
    """
    Check if a commit indicates a hook bypass.

    Returns: (is_bypass, exception_id if found)
    """
    full_message = commit["full_message"].lower()

    # Check for bypass indicators
    is_bypass = any(
        indicator.lower() in full_message for indicator in BYPASS_INDICATORS
    )

    if not is_bypass:
        return False, None

    # If bypass, look for exception reference
    exception_match = EXCEPTION_PATTERN.search(commit["full_message"])
    exception_id = exception_match.group() if exception_match else None

    return True, exception_id


# =============================================================================
# MAIN CHECK
# =============================================================================


def run_check(
    count: int = 5,
    commit_range: Optional[str] = None,
    ci_mode: bool = False,
    quiet: bool = False,
) -> int:
    """
    Run the governance tripwire check.

    Returns: 0 if clean, 1 if violations found
    """
    repo_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    )

    if not quiet:
        print()
        print(
            colored(
                "╔═══════════════════════════════════════════════════════════════╗",
                Colors.CYAN,
            )
        )
        print(
            colored(
                "║              GOVERNANCE TRIPWIRE CHECK                        ║",
                Colors.CYAN,
            )
        )
        print(
            colored(
                "╚═══════════════════════════════════════════════════════════════╝",
                Colors.CYAN,
            )
        )
        print()

    # Load exceptions
    exceptions, commit_to_exception = load_exceptions(repo_root)

    if not quiet:
        print(f"Loaded {len(exceptions)} exception(s) from {EXCEPTIONS_FILE}")
        if commit_to_exception:
            print(
                f"  Commits with documented exceptions: {list(commit_to_exception.keys())}"
            )
        print()

    # Get commits
    commits = get_commits(count=count, commit_range=commit_range)

    if not commits:
        if not quiet:
            print(colored("No commits to check", Colors.YELLOW))
        return 0

    if not quiet:
        print(f"Checking {len(commits)} commit(s)...")
        print()

    # Check each commit
    violations = []
    bypasses_with_exceptions = []

    for commit in commits:
        is_bypass, exception_id = check_commit_for_bypass(commit)

        if not is_bypass:
            continue

        # Check if exception is in commit message
        if exception_id:
            # Validate the exception
            is_valid, reason = validate_exception(exception_id, exceptions)
            if is_valid:
                bypasses_with_exceptions.append((commit, exception_id))
            else:
                violations.append((commit, exception_id, reason))
        else:
            # Check if this commit is documented in an exception record
            commit_prefix = commit["hash"][:8]
            if commit_prefix in commit_to_exception:
                # Commit is referenced in an exception record
                exc_id = commit_to_exception[commit_prefix]
                is_valid, reason = validate_exception(exc_id, exceptions)
                if is_valid:
                    bypasses_with_exceptions.append((commit, f"{exc_id} (retroactive)"))
                else:
                    violations.append((commit, exc_id, reason))
            else:
                # Bypass without exception reference
                violations.append(
                    (commit, None, "Bypass without exception reference (EXC-XXXX)")
                )

    # Report results
    if bypasses_with_exceptions and not quiet:
        print(colored("✅ Valid bypass(es) with documented exceptions:", Colors.GREEN))
        for commit, exc_id in bypasses_with_exceptions:
            print(f"  • {commit['hash'][:8]} - {exc_id}")
            print(f"    {commit['subject'][:60]}")
        print()

    if violations:
        print(
            colored(f"❌ Found {len(violations)} governance violation(s):", Colors.RED)
        )
        print()

        for commit, exc_id, reason in violations:
            print(f"  {colored('✗', Colors.RED)} {commit['hash'][:8]}")
            print(f"    Subject: {commit['subject'][:60]}")
            print(f"    Reason: {reason}")
            print()

        print(colored("━" * 70, Colors.RED))
        print()
        print(colored("Remediation required:", Colors.BOLD))
        print()
        print("  1. Create an exception record in docs/governance/EXCEPTIONS.md")
        print("  2. Follow the exception template in that file")
        print("  3. Reference the exception ID (EXC-XXXX-XX) in future bypasses")
        print()
        print(
            colored(
                "❌ VIOLATION: Pre-commit bypass without governance documentation",
                Colors.RED,
            )
        )
        return 1

    if not quiet:
        print(colored("✅ No governance violations detected", Colors.GREEN))

    return 0


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Check for undocumented pre-commit hook bypasses"
    )
    parser.add_argument(
        "--commits",
        "-n",
        type=int,
        default=5,
        help="Number of recent commits to check (default: 5)",
    )
    parser.add_argument(
        "--range",
        "-r",
        dest="commit_range",
        help="Git commit range to check (e.g., HEAD~5..HEAD)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 on any violation",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output",
    )

    args = parser.parse_args()

    exit_code = run_check(
        count=args.commits,
        commit_range=args.commit_range,
        ci_mode=args.ci,
        quiet=args.quiet,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
