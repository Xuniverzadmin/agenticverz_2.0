#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, bootstrap
#   Execution: sync
# Role: Verify backend structure matches frozen declaration
# Callers: CI pipeline, session_start.sh
# Allowed Imports: stdlib, yaml
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================
# GOVERNANCE RULE: BACKEND STRUCTURE FREEZE
# ==============================================================================
#
# Frozen directories and files must not drift from declaration.
# This guard verifies the structure matches BACKEND_STRUCTURE_FREEZE.yaml.
#
# Enforcement:
#   - CI blocks merges if frozen files are missing
#   - CI warns if unexpected files are added to frozen directories
#
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================

"""
Backend Structure Guard

Verifies that the backend structure matches the frozen declaration.
Prevents accidental erosion of critical system components.

Usage:
    python scripts/ci/backend_structure_guard.py [--verbose] [--strict]

Exit codes:
    0: Structure matches declaration
    1: Structure drift detected (missing or unexpected files)
    2: Declaration file not found or parse error
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


# Paths
FREEZE_FILE = Path("docs/governance/BACKEND_STRUCTURE_FREEZE.yaml")


def load_freeze_declaration() -> dict[str, Any]:
    """Load the structure freeze declaration."""
    if not FREEZE_FILE.exists():
        print(f"ERROR: Structure freeze file not found: {FREEZE_FILE}")
        sys.exit(2)

    with open(FREEZE_FILE, "r") as f:
        return yaml.safe_load(f)


def check_frozen_directory(
    name: str, config: dict[str, Any], verbose: bool = False
) -> tuple[list[str], list[str]]:
    """
    Check a frozen directory for drift.

    Returns (missing_files, unexpected_files).
    """
    path = Path(config["path"])
    missing = []
    unexpected = []

    if not path.exists():
        return [f"Directory missing: {path}"], []

    # Check for required files
    frozen_files = config.get("files", []) + config.get("frozen_files", [])
    existing_files = {f.name for f in path.iterdir() if f.is_file()}

    for required in frozen_files:
        if required not in existing_files:
            missing.append(f"{path}/{required}")
        elif verbose:
            print(f"  OK: {path}/{required}")

    # Check for unexpected files (warning only, not error)
    for existing in existing_files:
        if existing not in frozen_files and not existing.startswith("__pycache__"):
            if existing != "__pycache__" and not existing.endswith(".pyc"):
                unexpected.append(f"{path}/{existing}")

    return missing, unexpected


def main():
    parser = argparse.ArgumentParser(
        description="Verify backend structure matches frozen declaration"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unexpected files as errors (not just warnings)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("BACKEND STRUCTURE GUARD")
    print("=" * 70)
    print()

    # Load declaration
    print(f"Loading structure freeze: {FREEZE_FILE}")
    declaration = load_freeze_declaration()
    print(f"  Version: {declaration.get('version', 'unknown')}")
    print(f"  Frozen at: {declaration.get('frozen_at', 'unknown')}")
    print()

    # Check frozen directories
    all_missing = []
    all_unexpected = []

    frozen_dirs = declaration.get("frozen_directories", {})

    print("-" * 70)
    print("CHECKING FROZEN DIRECTORIES")
    print("-" * 70)

    for name, config in frozen_dirs.items():
        print(f"\n  [{name}]")
        print(f"  Path: {config['path']}")

        missing, unexpected = check_frozen_directory(name, config, args.verbose)

        if missing:
            print(f"  MISSING: {len(missing)} files")
            for f in missing:
                print(f"    - {f}")
            all_missing.extend(missing)
        elif args.verbose:
            print("  All required files present")

        if unexpected:
            print(f"  UNEXPECTED: {len(unexpected)} files")
            for f in unexpected:
                print(f"    - {f}")
            all_unexpected.extend(unexpected)

    # Summary
    print()
    print("=" * 70)

    if all_missing:
        print("VERDICT: STRUCTURE DRIFT DETECTED")
        print("=" * 70)
        print()
        print(f"Missing files: {len(all_missing)}")
        for f in all_missing:
            print(f"  - {f}")
        print()
        print("Resolution:")
        print("  1. Restore missing files")
        print("  2. OR update BACKEND_STRUCTURE_FREEZE.yaml with governance approval")
        print()
        sys.exit(1)

    if all_unexpected and args.strict:
        print("VERDICT: UNEXPECTED FILES (STRICT MODE)")
        print("=" * 70)
        print()
        print(f"Unexpected files: {len(all_unexpected)}")
        for f in all_unexpected:
            print(f"  - {f}")
        print()
        print("Resolution:")
        print("  1. Remove unexpected files")
        print("  2. OR add to BACKEND_STRUCTURE_FREEZE.yaml with governance approval")
        print()
        sys.exit(1)

    print("VERDICT: STRUCTURE INTACT")
    print("=" * 70)
    print()
    print(f"  Directories checked: {len(frozen_dirs)}")
    print("  Missing files: 0")
    if all_unexpected:
        print(f"  Unexpected files: {len(all_unexpected)} (warning)")
    print()
    print("  Backend structure matches frozen declaration.")
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
