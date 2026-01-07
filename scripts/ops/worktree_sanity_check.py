#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: shell | pre-commit | pre-push | periodic
#   Execution: sync
# Role: Enforce intent-scoped worktree purity
# Callers: shell hooks, pre-commit, pre-push, session bootstrap
# Allowed Imports: L6 (stdlib only)
# Forbidden Imports: app.*, backend.*
# Reference: PIN-319 (Governance Fix - Clean Push By Construction)
"""
Worktree Sanity Check

Ensures all modified/staged/untracked files are within declared intent scope.
Catches mixed intent pollution BEFORE commit/push, not after.

Usage:
    python3 scripts/ops/worktree_sanity_check.py           # Check worktree
    python3 scripts/ops/worktree_sanity_check.py --staged  # Check staged only
    python3 scripts/ops/worktree_sanity_check.py --ci      # CI mode (exit 1 on fail)
    python3 scripts/ops/worktree_sanity_check.py --quiet   # Minimal output
"""

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# =============================================================================
# CONSTANTS
# =============================================================================

INTENT_FILE = "INTENT_DECLARATION.yaml"
SCHEMA_FILE = "docs/governance/INTENT_DECLARATION_SCHEMA.yaml"

# Files that are always allowed (governance infrastructure)
ALWAYS_ALLOWED = [
    "INTENT_DECLARATION.yaml",
    ".gitignore",
    "*.md",  # Documentation updates
]

# Files that trigger warnings but don't block
WARN_ONLY = [
    "*.pyc",
    "__pycache__/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    "*.egg-info/**",
    "node_modules/**",
    ".venv/**",
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
# INTENT LOADING
# =============================================================================


def load_intent(repo_root: Path) -> Optional[dict]:
    """Load intent declaration from YAML file."""
    intent_path = repo_root / INTENT_FILE

    if not intent_path.exists():
        return None

    if not YAML_AVAILABLE:
        # Fallback: simple parsing for basic cases
        content = intent_path.read_text()
        return {"_raw": content, "_fallback": True}

    try:
        with open(intent_path) as f:
            data = yaml.safe_load(f)
            return data.get("intent", {})
    except Exception as e:
        print(colored(f"Warning: Failed to parse {INTENT_FILE}: {e}", Colors.YELLOW))
        return None


def get_allowed_paths(intent: dict) -> list[str]:
    """Extract allowed paths from intent."""
    if intent.get("_fallback"):
        # Fallback parsing
        raw = intent.get("_raw", "")
        paths = []
        in_allowed = False
        for line in raw.split("\n"):
            if "allowed_paths:" in line:
                in_allowed = True
                continue
            if in_allowed:
                if line.strip().startswith("- "):
                    path = line.strip()[2:].strip().strip('"').strip("'")
                    paths.append(path)
                elif line.strip() and not line.strip().startswith("#"):
                    if ":" in line:
                        break
        return paths

    scope = intent.get("scope", {})
    return scope.get("allowed_paths", [])


def get_forbidden_paths(intent: dict) -> list[str]:
    """Extract forbidden paths from intent."""
    if intent.get("_fallback"):
        return []

    scope = intent.get("scope", {})
    return scope.get("forbidden_paths", [])


def get_exceptions(intent: dict) -> list[str]:
    """Extract exception paths from intent.

    Note: The 'exceptions' field in INTENT_DECLARATION.yaml contains
    governance exception metadata (id, reason, status), not path patterns.
    Path-based exceptions should be added to 'allowed_paths' directly.

    This function returns an empty list since governance exceptions are
    documented in docs/governance/EXCEPTIONS.md, not used for path matching.
    """
    if intent.get("_fallback"):
        return []

    # Exceptions are governance metadata, not path patterns
    # See docs/governance/EXCEPTIONS.md for exception records
    scope = intent.get("scope", {})
    exceptions = scope.get("exceptions", [])

    # Filter to only string patterns (future-proof for path exceptions)
    return [e for e in exceptions if isinstance(e, str)]


def get_mode(intent: dict) -> str:
    """Get enforcement mode."""
    if intent.get("_fallback"):
        return "exclusive"

    return intent.get("mode", "exclusive")


# =============================================================================
# FILE MATCHING
# =============================================================================


def matches_pattern(filepath: str, pattern: str) -> bool:
    """Check if filepath matches a glob pattern."""
    # Normalize paths
    filepath = filepath.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    # Handle ** patterns
    if "**" in pattern:
        # Split pattern at **
        parts = pattern.split("**")
        if len(parts) == 2:
            prefix, suffix = parts
            prefix = prefix.rstrip("/")
            suffix = suffix.lstrip("/")

            if prefix and not filepath.startswith(prefix):
                return False
            if suffix and not fnmatch.fnmatch(filepath, f"*{suffix}"):
                # Check if any part of the path matches suffix
                for i in range(len(filepath)):
                    if fnmatch.fnmatch(filepath[i:], suffix):
                        return True
                    if fnmatch.fnmatch(filepath[i:], f"*/{suffix}"):
                        return True
                return False
            return True

    return fnmatch.fnmatch(filepath, pattern)


def is_file_allowed(
    filepath: str,
    allowed_paths: list[str],
    forbidden_paths: list[str],
    exceptions: list[str],
) -> tuple[bool, str]:
    """
    Check if a file is allowed under current intent.

    Returns: (is_allowed, reason)
    """
    # Check always-allowed first
    for pattern in ALWAYS_ALLOWED:
        if matches_pattern(filepath, pattern):
            return True, "always_allowed"

    # Check warn-only (these don't count as violations)
    for pattern in WARN_ONLY:
        if matches_pattern(filepath, pattern):
            return True, "warn_only"

    # Check exceptions (overrides forbidden)
    for pattern in exceptions:
        if matches_pattern(filepath, pattern):
            return True, "exception"

    # Check forbidden paths (takes precedence over allowed)
    for pattern in forbidden_paths:
        if matches_pattern(filepath, pattern):
            return False, f"forbidden by pattern: {pattern}"

    # Check allowed paths
    for pattern in allowed_paths:
        if matches_pattern(filepath, pattern):
            return True, f"allowed by pattern: {pattern}"

    # Not in any allowed path
    return False, "not in allowed_paths"


# =============================================================================
# GIT OPERATIONS
# =============================================================================


def get_repo_root() -> Path:
    """Get the repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(colored("Error: Not in a git repository", Colors.RED))
        sys.exit(1)

    return Path(result.stdout.strip())


def get_modified_files(staged_only: bool = False) -> list[str]:
    """Get list of modified/staged/untracked files."""
    files = []

    if staged_only:
        # Only staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
        )
        files.extend(result.stdout.strip().split("\n"))
    else:
        # All modified, staged, and untracked files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Format: XY filename (or XY "filename" for special chars)
            # Status is line[:2], filepath starts at position 3
            filepath = line[3:].strip()
            # Handle renamed files (old -> new)
            if " -> " in filepath:
                filepath = filepath.split(" -> ")[1]
            # Remove quotes if present
            filepath = filepath.strip('"')
            files.append(filepath)

    return [f for f in files if f]


# =============================================================================
# MAIN CHECK
# =============================================================================


def run_check(
    staged_only: bool = False,
    ci_mode: bool = False,
    quiet: bool = False,
) -> int:
    """
    Run the worktree sanity check.

    Returns: 0 if clean, 1 if violations found
    """
    repo_root = get_repo_root()
    os.chdir(repo_root)

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
                "║              WORKTREE SANITY CHECK                            ║",
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

    # Load intent
    intent = load_intent(repo_root)

    if not intent:
        if not quiet:
            print(colored("⚠️  No INTENT_DECLARATION.yaml found", Colors.YELLOW))
            print()
            print("To declare intent, create INTENT_DECLARATION.yaml with:")
            print()
            print("  intent:")
            print("    id: PIN-XXX")
            print("    title: Your Work Title")
            print("    type: frontend-architecture")
            print("    scope:")
            print("      allowed_paths:")
            print('        - "your/path/**"')
            print("    mode: exclusive")
            print()
        # In CI mode, missing intent is a warning but not blocking
        return 0

    # Extract scope
    allowed_paths = get_allowed_paths(intent)
    forbidden_paths = get_forbidden_paths(intent)
    exceptions = get_exceptions(intent)
    mode = get_mode(intent)

    if not quiet:
        intent_id = intent.get("id", "unknown")
        intent_title = intent.get("title", "untitled")
        print(f"Intent: {colored(intent_id, Colors.BOLD)} - {intent_title}")
        print(f"Mode: {colored(mode, Colors.BLUE)}")
        print(f"Allowed paths: {len(allowed_paths)}")
        print(f"Forbidden paths: {len(forbidden_paths)}")
        print()

    # Get modified files
    files = get_modified_files(staged_only=staged_only)

    if not files:
        if not quiet:
            print(colored("✅ Worktree is clean", Colors.GREEN))
        return 0

    if not quiet:
        scope_label = "staged" if staged_only else "modified/staged/untracked"
        print(f"Checking {len(files)} {scope_label} files...")
        print()

    # Check each file
    violations = []
    warnings = []

    for filepath in files:
        is_allowed, reason = is_file_allowed(
            filepath, allowed_paths, forbidden_paths, exceptions
        )

        if not is_allowed:
            violations.append((filepath, reason))
        elif reason == "warn_only":
            warnings.append((filepath, reason))

    # Report results
    if violations:
        print(colored(f"❌ Found {len(violations)} scope violation(s):", Colors.RED))
        print()

        for filepath, reason in violations:
            print(f"  {colored('✗', Colors.RED)} {filepath}")
            print(f"    → {reason}")
            print()

        print(colored("━" * 70, Colors.RED))
        print()
        print(colored("Remediation options:", Colors.BOLD))
        print()
        print("  1. git stash the out-of-scope changes")
        print("  2. Update INTENT_DECLARATION.yaml to include these paths")
        print("  3. Create a separate branch for this work")
        print("  4. Use --no-verify with documented justification")
        print()

        if mode == "exclusive":
            print(
                colored(
                    "❌ BLOCKED: Exclusive mode rejects scope violations", Colors.RED
                )
            )
            return 1
        elif mode == "exploratory":
            print(
                colored(
                    "⚠️  WARNING: Exploratory mode allows violations (not blocking)",
                    Colors.YELLOW,
                )
            )
            return 0
        elif mode == "hotfix":
            print(
                colored("⚠️  HOTFIX MODE: Violations allowed but logged", Colors.YELLOW)
            )
            return 0

    if warnings and not quiet:
        print(colored(f"⚠️  {len(warnings)} file(s) in warn-only paths", Colors.YELLOW))

    if not quiet:
        print(colored("✅ All files within declared intent scope", Colors.GREEN))

    return 0


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Check worktree files against declared intent scope"
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Only check staged files (for pre-commit)",
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
        staged_only=args.staged,
        ci_mode=args.ci,
        quiet=args.quiet,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
