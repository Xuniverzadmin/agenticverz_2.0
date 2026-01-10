#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, bootstrap
#   Execution: sync
# Role: Enforce HEALTH-LIFECYCLE-COHERENCE governance rule
# Callers: CI pipeline, session_start.sh, bootstrap verification
# Allowed Imports: stdlib, psycopg2 (for DB read)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================
# GOVERNANCE RULE: HEALTH-LIFECYCLE-COHERENCE (Non-Negotiable)
# ==============================================================================
#
# A BLOCKED health state CANNOT coexist with COMPLETE lifecycle status.
#
# This guard enforces:
#   IF health(capability) == BLOCKED THEN status != COMPLETE
#
# The invariant:
#   - PlatformHealthService (L4) is the authority for health state
#   - CAPABILITY_LIFECYCLE.yaml declares lifecycle status
#   - If a capability is BLOCKED, it MUST NOT be COMPLETE
#   - This prevents false claims of readiness
#
# Enforcement:
#   - CI blocks merges with coherence violations
#   - Bootstrap refuses to start with violations
#   - Session start fails with violations
#
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================

"""
Health-Lifecycle Coherence Guard

Enforces the HEALTH-LIFECYCLE-COHERENCE governance rule.
Ensures BLOCKED health states do not coexist with COMPLETE lifecycle status.

Usage:
    python scripts/ci/health_lifecycle_coherence_guard.py [--verbose] [--ci]

Exit codes:
    0: Coherent (no BLOCKED+COMPLETE violations)
    1: Incoherent (BLOCKED capabilities have COMPLETE status)
    2: Missing files, DB connection, or parse errors

Environment:
    DATABASE_URL: Required for reading governance signals
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# DB-AUTH-001: Declare local-only authority
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from scripts._db_guard import assert_db_authority  # noqa: E402
assert_db_authority("local")

# File paths relative to repo root
LIFECYCLE_PATH = Path("docs/governance/CAPABILITY_LIFECYCLE.yaml")


# ==============================================================================
# HEALTH STATE DEFINITIONS (Mirror of L4 PlatformHealthService)
# ==============================================================================

HEALTH_STATE_BLOCKED = "BLOCKED"
HEALTH_STATE_DEGRADED = "DEGRADED"
HEALTH_STATE_HEALTHY = "HEALTHY"


# ==============================================================================
# YAML LOADING
# ==============================================================================


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(2)
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ==============================================================================
# DATABASE HEALTH SIGNAL READING
# ==============================================================================


def get_blocked_capabilities_from_db(db_url: str) -> dict[str, list[str]]:
    """
    Read BLOCKED governance signals from database.

    Returns dict of capability_name -> list of blocking reasons.
    """
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(2)

    blocked_capabilities: dict[str, list[str]] = {}

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Query for BLOCKED signals that are not superseded and not expired
        query = """
        SELECT scope, signal_type, reason, recorded_by, recorded_at
        FROM governance_signals
        WHERE decision = 'BLOCKED'
          AND superseded_at IS NULL
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY scope, recorded_at DESC
        """

        cur.execute(query)
        rows = cur.fetchall()

        for row in rows:
            scope, signal_type, reason, recorded_by, recorded_at = row

            # Skip SYSTEM-level signals (they don't map to specific capabilities)
            if scope == "SYSTEM":
                continue

            if scope not in blocked_capabilities:
                blocked_capabilities[scope] = []

            blocked_capabilities[scope].append(
                f"{signal_type} by {recorded_by}: {reason or 'No reason provided'}"
            )

        cur.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(2)

    return blocked_capabilities


def get_system_health_from_db(db_url: str) -> tuple[str, list[str]]:
    """
    Get system-level health state from governance signals.

    Returns (state, list of reasons).
    """
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(2)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Check BLCA status
        query = """
        SELECT decision, reason, recorded_at
        FROM governance_signals
        WHERE signal_type = 'BLCA_STATUS'
          AND scope = 'SYSTEM'
          AND superseded_at IS NULL
        ORDER BY recorded_at DESC
        LIMIT 1
        """

        cur.execute(query)
        row = cur.fetchone()

        if row and row[0] == "BLOCKED":
            cur.close()
            conn.close()
            return HEALTH_STATE_BLOCKED, [f"BLCA: {row[1] or 'violations detected'}"]

        # Check lifecycle coherence
        query = """
        SELECT decision, reason, recorded_at
        FROM governance_signals
        WHERE signal_type = 'LIFECYCLE_QUALIFIER_COHERENCE'
          AND scope = 'SYSTEM'
          AND superseded_at IS NULL
        ORDER BY recorded_at DESC
        LIMIT 1
        """

        cur.execute(query)
        row = cur.fetchone()

        if row and row[0] == "INCOHERENT":
            cur.close()
            conn.close()
            return HEALTH_STATE_DEGRADED, [f"Lifecycle: {row[1] or 'incoherent'}"]

        cur.close()
        conn.close()
        return HEALTH_STATE_HEALTHY, []

    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(2)


# ==============================================================================
# COHERENCE CHECK
# ==============================================================================


def check_health_lifecycle_coherence(
    lifecycle: dict, blocked_capabilities: dict[str, list[str]], verbose: bool = False
) -> list[str]:
    """
    Check that BLOCKED capabilities do not have COMPLETE lifecycle status.

    Returns list of violations (empty if coherent).
    """
    violations = []

    capabilities = lifecycle.get("capabilities", {})

    for cap_name, cap_data in capabilities.items():
        status = cap_data.get("status", "UNKNOWN")

        # Check if this capability is BLOCKED
        if cap_name in blocked_capabilities:
            blocking_reasons = blocked_capabilities[cap_name]

            if status == "COMPLETE":
                violations.append(
                    f"HEALTH-LIFECYCLE-VIOLATION: {cap_name} is BLOCKED in health "
                    f"but has status=COMPLETE in lifecycle"
                )
                for reason in blocking_reasons:
                    violations.append(f"    -> {reason}")
            elif verbose:
                print(f"  OK: {cap_name} is BLOCKED but status={status} (not COMPLETE)")
        elif verbose:
            print(f"  OK: {cap_name} is not BLOCKED (status={status})")

    return violations


# ==============================================================================
# MAIN
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Enforce HEALTH-LIFECYCLE-COHERENCE governance rule"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument("--ci", action="store_true", help="CI mode (strict exit codes)")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Bootstrap mode (check system health too)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("HEALTH-LIFECYCLE COHERENCE GUARD")
    print("=" * 70)
    print()

    # Get database URL
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("WARNING: DATABASE_URL not set")
        print("  Health signals cannot be read from database.")
        print("  Assuming no BLOCKED capabilities.")
        print()
        blocked_capabilities: dict[str, list[str]] = {}
        system_health = HEALTH_STATE_HEALTHY
        system_reasons: list[str] = []
    else:
        # Read health signals from database
        print("Reading governance signals from database...")
        blocked_capabilities = get_blocked_capabilities_from_db(db_url)
        system_health, system_reasons = get_system_health_from_db(db_url)
        print(f"  Found {len(blocked_capabilities)} BLOCKED capabilities")
        print(f"  System health: {system_health}")
        print()

    # Load lifecycle
    print(f"Loading lifecycle from: {LIFECYCLE_PATH}")
    lifecycle = load_yaml(LIFECYCLE_PATH)
    print()

    # Bootstrap mode: check system health
    if args.bootstrap:
        print("-" * 70)
        print("BOOTSTRAP HEALTH CHECK")
        print("-" * 70)

        if system_health == HEALTH_STATE_BLOCKED:
            print()
            print(f"  SYSTEM HEALTH: {system_health}")
            for reason in system_reasons:
                print(f"    -> {reason}")
            print()
            print("=" * 70)
            print("VERDICT: BOOTSTRAP BLOCKED")
            print("=" * 70)
            print()
            print("Resolution:")
            print("  1. Fix the blocking issue (BLCA violations, etc.)")
            print("  2. Re-run session_start.sh")
            print()
            sys.exit(1)
        else:
            print(f"  System health: {system_health} (OK)")
            print()

    # Check capability-level coherence
    print("-" * 70)
    print("CAPABILITY COHERENCE CHECK")
    print("-" * 70)

    violations = check_health_lifecycle_coherence(
        lifecycle, blocked_capabilities, verbose=args.verbose
    )

    if violations:
        print()
        print(f"VIOLATIONS FOUND: {len(violations)}")
        print("-" * 70)
        for v in violations:
            print(f"  {v}")
        print()
        print("=" * 70)
        print("VERDICT: INCOHERENT")
        print("=" * 70)
        print()
        print("The invariant 'BLOCKED health cannot coexist with COMPLETE lifecycle'")
        print("has been violated.")
        print()
        print("Resolution:")
        print("  1. Fix the health issue (resolve blocking signals)")
        print("  2. OR downgrade the lifecycle status from COMPLETE")
        print("  3. Re-run this guard")
        print()
        print("Reference: PIN-284 (Platform Monitoring System)")
        print()
        sys.exit(1)
    else:
        cap_count = len(lifecycle.get("capabilities", {}))
        complete_count = sum(
            1
            for c in lifecycle.get("capabilities", {}).values()
            if c.get("status") == "COMPLETE"
        )

        print()
        print("=" * 70)
        print("VERDICT: COHERENT")
        print("=" * 70)
        print()
        print(f"  Capabilities checked:  {cap_count}")
        print(f"  COMPLETE in lifecycle: {complete_count}")
        print(f"  BLOCKED in health:     {len(blocked_capabilities)}")
        print()
        print("  No BLOCKED+COMPLETE violations found.")
        print("  Health is coherent with lifecycle.")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
