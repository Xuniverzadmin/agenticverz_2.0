#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI / pre-commit
#   Execution: sync
# Role: CI guard for Activity Domain V2 deprecation enforcement
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: standard library only
# Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md (Phase 5 - Lockdown)

"""
Activity Domain V2 Deprecation Guard

This script enforces the deprecation of the /runs endpoint by checking:
1. No new capability registry bindings to /runs (except detail endpoints)
2. No new UI references to /runs list endpoint
3. Registry locks are respected

Exit codes:
- 0: No violations found
- 1: Violations found (blocks CI)

Usage:
    python check_activity_deprecation.py [--strict]

    --strict: Also warn about existing deprecated references (non-blocking)
"""

import argparse
import glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# =============================================================================
# Configuration
# =============================================================================

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent

CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
ACTIVITY_REGISTRY = REPO_ROOT / "docs" / "architecture" / "activity" / "ACTIVITY_CAPABILITY_REGISTRY.yaml"
FRONTEND_SRC = REPO_ROOT / "website" / "app-shell" / "src"
REGISTRY_LOCKS = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY" / "REGISTRY_LOCKS.yaml"

# Deprecated endpoint pattern (list endpoint, not detail)
DEPRECATED_PATTERN = re.compile(r"/api/v1/activity/runs(?![/{])")

# Allowed detail endpoints (not deprecated)
ALLOWED_PATTERNS = [
    re.compile(r"/api/v1/activity/runs/\{run_id\}"),
    re.compile(r"/api/v1/activity/runs/[^/]+/evidence"),
    re.compile(r"/api/v1/activity/runs/[^/]+/proof"),
    re.compile(r"/api/v1/activity/live/by-dimension"),
    re.compile(r"/api/v1/activity/completed/by-dimension"),
]


# =============================================================================
# Violation Types
# =============================================================================


@dataclass
class Violation:
    """A deprecation violation."""

    file: str
    line: int
    content: str
    violation_type: str
    severity: str  # ERROR or WARNING


# =============================================================================
# Checkers
# =============================================================================


def check_capability_registry_bindings() -> list[Violation]:
    """Check for new capability bindings to deprecated endpoint."""
    violations = []

    # Check individual capability files
    capability_files = glob.glob(
        str(CAPABILITY_REGISTRY_DIR / "AURORA_L2_CAPABILITY_activity.*.yaml")
    )

    for filepath in capability_files:
        with open(filepath) as f:
            content = f.read()
            lines = content.split("\n")

        # Skip if file is marked DEPRECATED
        if "status: DEPRECATED" in content:
            continue

        # Check the canonical endpoint field first
        # If the endpoint is a detail endpoint (contains {run_id}), skip the file
        canonical_endpoint = None
        for line in lines:
            if line.startswith("endpoint:"):
                canonical_endpoint = line
                break

        if canonical_endpoint:
            # If canonical endpoint is a detail endpoint, skip entirely
            is_detail_endpoint = any(p.search(canonical_endpoint) for p in ALLOWED_PATTERNS)
            if is_detail_endpoint:
                continue

        for i, line in enumerate(lines, start=1):
            if DEPRECATED_PATTERN.search(line):
                # Check if it's an allowed pattern
                is_allowed = any(p.search(line) for p in ALLOWED_PATTERNS)
                if not is_allowed:
                    violations.append(
                        Violation(
                            file=filepath,
                            line=i,
                            content=line.strip(),
                            violation_type="CAPABILITY_BINDING_TO_DEPRECATED_ENDPOINT",
                            severity="ERROR",
                        )
                    )

    return violations


def check_panel_bindings() -> list[Violation]:
    """Check panel_bindings section for deprecated endpoint references."""
    violations = []

    if not ACTIVITY_REGISTRY.exists():
        return violations

    with open(ACTIVITY_REGISTRY) as f:
        content = f.read()
        lines = content.split("\n")

    in_panel_bindings = False
    for i, line in enumerate(lines, start=1):
        if "panel_bindings:" in line:
            in_panel_bindings = True
            continue

        if in_panel_bindings:
            # Exit panel_bindings section on next top-level key
            if line and not line.startswith(" ") and ":" in line:
                break

            if DEPRECATED_PATTERN.search(line):
                is_allowed = any(p.search(line) for p in ALLOWED_PATTERNS)
                if not is_allowed:
                    violations.append(
                        Violation(
                            file=str(ACTIVITY_REGISTRY),
                            line=i,
                            content=line.strip(),
                            violation_type="PANEL_BINDING_TO_DEPRECATED_ENDPOINT",
                            severity="ERROR",
                        )
                    )

    return violations


def check_frontend_references() -> list[Violation]:
    """Check frontend for references to deprecated endpoint."""
    violations = []

    if not FRONTEND_SRC.exists():
        return violations

    # Check TypeScript/JavaScript files
    for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
        for filepath in FRONTEND_SRC.rglob(ext):
            with open(filepath) as f:
                try:
                    content = f.read()
                    lines = content.split("\n")
                except UnicodeDecodeError:
                    continue

            for i, line in enumerate(lines, start=1):
                # Check for API calls to deprecated endpoint
                if "/activity/runs" in line and "/activity/runs/" not in line:
                    # Skip if it's a V2 endpoint
                    if any(
                        v2 in line
                        for v2 in [
                            "/activity/live",
                            "/activity/completed",
                            "/activity/signals",
                            "/activity/metrics",
                            "/activity/threshold-signals",
                        ]
                    ):
                        continue

                    # This is likely a reference to the deprecated list endpoint
                    violations.append(
                        Violation(
                            file=str(filepath),
                            line=i,
                            content=line.strip()[:100],
                            violation_type="FRONTEND_REFERENCE_TO_DEPRECATED_ENDPOINT",
                            severity="WARNING",  # Warning because frontend needs migration
                        )
                    )

    return violations


def check_registry_locks() -> list[Violation]:
    """Check that /runs is locked in REGISTRY_LOCKS.yaml."""
    violations = []

    if not REGISTRY_LOCKS.exists():
        violations.append(
            Violation(
                file=str(REGISTRY_LOCKS),
                line=0,
                content="File does not exist",
                violation_type="MISSING_REGISTRY_LOCKS",
                severity="ERROR",
            )
        )
        return violations

    with open(REGISTRY_LOCKS) as f:
        content = f.read()

    if "/api/v1/activity/runs" not in content:
        violations.append(
            Violation(
                file=str(REGISTRY_LOCKS),
                line=0,
                content="/runs endpoint not found in locks",
                violation_type="ENDPOINT_NOT_LOCKED",
                severity="ERROR",
            )
        )

    return violations


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Activity Domain V2 Deprecation Guard"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also report warnings as errors",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip frontend checks (for backend-only validation)",
    )
    parser.add_argument(
        "--skip-locks",
        action="store_true",
        help="Skip registry locks check (for incremental validation)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ACTIVITY DOMAIN V2 DEPRECATION GUARD")
    print("Phase 5 - Lockdown Enforcement")
    print("=" * 60)
    print()

    all_violations: list[Violation] = []

    # Run checks
    print("Checking capability registry bindings...")
    all_violations.extend(check_capability_registry_bindings())

    print("Checking panel bindings...")
    all_violations.extend(check_panel_bindings())

    if not args.skip_frontend:
        print("Checking frontend references...")
        all_violations.extend(check_frontend_references())

    if not args.skip_locks:
        print("Checking registry locks...")
        all_violations.extend(check_registry_locks())

    print()

    # Report results
    errors = [v for v in all_violations if v.severity == "ERROR"]
    warnings = [v for v in all_violations if v.severity == "WARNING"]

    if errors:
        print("=" * 60)
        print(f"ERRORS ({len(errors)})")
        print("=" * 60)
        for v in errors:
            print(f"\n{v.violation_type}")
            print(f"  File: {v.file}:{v.line}")
            print(f"  Content: {v.content}")
        print()

    if warnings:
        print("=" * 60)
        print(f"WARNINGS ({len(warnings)})")
        print("=" * 60)
        for v in warnings:
            print(f"\n{v.violation_type}")
            print(f"  File: {v.file}:{v.line}")
            print(f"  Content: {v.content}")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors or (args.strict and warnings):
        print("\nRESULT: FAILED")
        print("\nTo fix:")
        print("- Remove deprecated /runs bindings from capability registry")
        print("- Use /activity/live, /activity/completed, or /activity/signals instead")
        print("- Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md")
        return 1

    print("\nRESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
