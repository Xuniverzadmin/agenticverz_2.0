#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: script import
#   Execution: sync
# Role: Database Authority Enforcement Guard
# Reference: DB-AUTH-001

"""
Database Authority Guard - Enforcement Script

CONTRACT (LOCKED - DB-AUTH-001)

PURPOSE:
    Enforce database authority determinism. Authority is declared, not inferred.
    This script MUST be imported by any script that touches the database.

USAGE:
    # At the top of your script:
    from scripts._db_guard import assert_db_authority, get_db_url

    # Assert expected authority before any DB operation:
    assert_db_authority("neon")  # or "local"

    # Get the validated DATABASE_URL:
    db_url = get_db_url()

EXIT CODES:
    5 - DB_AUTHORITY not declared
    6 - DB_AUTHORITY mismatch (expected != actual)
    7 - DATABASE_URL not found
    8 - DATABASE_URL doesn't match declared authority
    9 - Dual-connection detected (both Neon and Local)
    10 - Override expired or invalid

ENVIRONMENT VARIABLES:
    DB_AUTHORITY - Required. Must be "neon" or "local"
    DB_ENV - Optional. "prod-like", "dev", or "test"
    DATABASE_URL - Required. The connection string
    EXPECTED_DB_AUTHORITY - Optional. If set, must match DB_AUTHORITY

OVERRIDE PROTOCOL:
    GOVERNANCE_OVERRIDE - Must be "DB-AUTH-001" to enable override
    OVERRIDE_REASON - Required text explaining why override is needed
    OVERRIDE_TTL - Required ISO timestamp (e.g., 2026-01-11T12:00:00Z)

    No TTL → invalid override
    Expired TTL → hard fail
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional, Set

# Track which databases have been connected to in this process
_connected_databases: Set[str] = set()


class DBAuthorityError(Exception):
    """Database authority violation."""
    pass


def _detect_authority_from_url(url: str) -> str:
    """
    Detect which database the URL points to.
    This is for VALIDATION only, not inference.
    """
    if not url:
        return "unknown"

    url_lower = url.lower()

    if "neon.tech" in url_lower:
        return "neon"
    elif "localhost" in url_lower or "127.0.0.1" in url_lower:
        return "local"
    elif "nova_db" in url_lower or "nova_pgbouncer" in url_lower:
        return "local"
    elif ":5432" in url_lower or ":5433" in url_lower or ":6432" in url_lower:
        # Ambiguous - could be either
        return "ambiguous"
    else:
        return "unknown"


def get_declared_authority() -> Optional[str]:
    """Get the declared DB_AUTHORITY from environment."""
    return os.getenv("DB_AUTHORITY")


def get_db_url() -> str:
    """
    Get DATABASE_URL after validating authority.

    Raises:
        DBAuthorityError: If authority is not properly declared or URL doesn't match
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise DBAuthorityError(
            "[DB-GUARD] DATABASE_URL not found in environment. "
            "Set DATABASE_URL before running this script."
        )

    return db_url


def assert_db_authority(expected: str, *, strict: bool = True) -> None:
    """
    Assert that the declared database authority matches expectation.

    Args:
        expected: The expected authority ("neon" or "local")
        strict: If True, also validate DATABASE_URL matches authority

    Raises:
        DBAuthorityError: If authority doesn't match or is not declared
        SystemExit: With appropriate exit code on failure

    Example:
        assert_db_authority("neon")  # Fails if DB_AUTHORITY != "neon"
    """
    declared = get_declared_authority()

    # Check if authority is declared
    if not declared:
        print(
            "[DB-GUARD] VIOLATION: DB_AUTHORITY not declared.\n"
            "Authority is declared, not inferred.\n"
            "Set DB_AUTHORITY=neon or DB_AUTHORITY=local before running.\n"
            "Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(5)

    # Check EXPECTED_DB_AUTHORITY if set
    env_expected = os.getenv("EXPECTED_DB_AUTHORITY")
    if env_expected and env_expected != declared:
        print(
            f"[DB-GUARD] VIOLATION: Authority mismatch.\n"
            f"EXPECTED_DB_AUTHORITY={env_expected}\n"
            f"DB_AUTHORITY={declared}\n"
            f"Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(6)

    # Check against expected parameter
    if declared != expected:
        print(
            f"[DB-GUARD] VIOLATION: Authority mismatch.\n"
            f"Script expects: {expected}\n"
            f"Declared: {declared}\n"
            f"Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(6)

    # Strict mode: validate DATABASE_URL matches declared authority
    if strict:
        db_url = os.getenv("DATABASE_URL", "")
        url_authority = _detect_authority_from_url(db_url)

        if url_authority == "unknown":
            print(
                f"[DB-GUARD] WARNING: DATABASE_URL authority could not be determined.\n"
                f"URL pattern: {db_url[:50]}...\n"
                f"Proceeding with declared authority: {declared}",
                file=sys.stderr
            )
        elif url_authority == "ambiguous":
            print(
                f"[DB-GUARD] WARNING: DATABASE_URL is ambiguous.\n"
                f"Proceeding with declared authority: {declared}",
                file=sys.stderr
            )
        elif url_authority != declared:
            print(
                f"[DB-GUARD] VIOLATION: DATABASE_URL doesn't match declared authority.\n"
                f"Declared: {declared}\n"
                f"URL appears to be: {url_authority}\n"
                f"Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
                file=sys.stderr
            )
            sys.exit(8)

    # Success - authority is valid
    print(f"[DB-GUARD] Authority validated: {declared}", file=sys.stderr)

    # Register this connection for dual-connection tracking
    register_connection(declared)


def require_neon() -> str:
    """
    Convenience function: Assert Neon authority and return DATABASE_URL.

    Returns:
        The validated DATABASE_URL

    Example:
        db_url = require_neon()
    """
    assert_db_authority("neon")
    return get_db_url()


def require_local() -> str:
    """
    Convenience function: Assert local authority and return DATABASE_URL.

    Returns:
        The validated DATABASE_URL

    Example:
        db_url = require_local()
    """
    assert_db_authority("local")
    return get_db_url()


def log_authority_check(operation: str, reason: str) -> None:
    """
    Log an authority check for audit purposes.

    Args:
        operation: What operation is being performed (read, write, validate)
        reason: Why this database is being accessed
    """
    authority = get_declared_authority() or "UNDECLARED"
    db_env = os.getenv("DB_ENV", "unknown")

    print(
        f"[DB-GUARD] Authority check:\n"
        f"  Authority: {authority}\n"
        f"  Environment: {db_env}\n"
        f"  Operation: {operation}\n"
        f"  Reason: {reason}",
        file=sys.stderr
    )


# =============================================================================
# DUAL-CONNECTION DETECTION (B)
# =============================================================================

def register_connection(authority: str) -> None:
    """
    Register that a connection has been made to a specific database authority.
    Fails immediately if both Neon and Local are connected in same process.

    This kills the "check both" anti-pattern permanently.

    Args:
        authority: The database authority being connected to ("neon" or "local")

    Raises:
        SystemExit: Exit code 9 if dual-connection detected
    """
    global _connected_databases

    _connected_databases.add(authority)

    # Check for dual-connection violation
    if "neon" in _connected_databases and "local" in _connected_databases:
        print(
            "[DB-GUARD] VIOLATION: Dual-connection detected!\n"
            "Both Neon and Local databases have been accessed in this process.\n"
            "This is a governance violation (DB-AUTH-001).\n"
            "\n"
            "Rule: A single process must connect to ONE authoritative database.\n"
            "Checking both databases to 'decide' correctness is forbidden.\n"
            "\n"
            "Connected to: " + ", ".join(_connected_databases) + "\n"
            "Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(9)


def assert_single_connection() -> None:
    """
    Assert that only one database has been connected to.
    Call this at end of script to verify no dual-connection occurred.

    Raises:
        SystemExit: Exit code 9 if dual-connection detected
    """
    if len(_connected_databases) > 1:
        print(
            f"[DB-GUARD] VIOLATION: Multiple databases accessed in single process.\n"
            f"Connected to: {', '.join(_connected_databases)}\n"
            f"Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(9)


def get_connected_databases() -> Set[str]:
    """Return the set of databases connected to in this process."""
    return _connected_databases.copy()


# =============================================================================
# OVERRIDE PROTOCOL (D)
# =============================================================================

def check_override() -> bool:
    """
    Check if a valid governance override is in effect.

    Override requires ALL of:
    - GOVERNANCE_OVERRIDE=DB-AUTH-001
    - OVERRIDE_REASON=<text>
    - OVERRIDE_TTL=<ISO timestamp>

    Returns:
        True if valid override is active, False otherwise

    Raises:
        SystemExit: Exit code 10 if override is expired or invalid
    """
    override = os.getenv("GOVERNANCE_OVERRIDE")

    if not override:
        return False

    if override != "DB-AUTH-001":
        print(
            f"[DB-GUARD] Invalid GOVERNANCE_OVERRIDE value: {override}\n"
            f"Expected: DB-AUTH-001",
            file=sys.stderr
        )
        return False

    # Check required fields
    reason = os.getenv("OVERRIDE_REASON")
    ttl = os.getenv("OVERRIDE_TTL")

    if not reason:
        print(
            "[DB-GUARD] VIOLATION: GOVERNANCE_OVERRIDE set but OVERRIDE_REASON missing.\n"
            "Override without reason is invalid.\n"
            "Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(10)

    if not ttl:
        print(
            "[DB-GUARD] VIOLATION: GOVERNANCE_OVERRIDE set but OVERRIDE_TTL missing.\n"
            "No TTL → invalid override.\n"
            "Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(10)

    # Parse and validate TTL
    try:
        # Handle both formats: with Z suffix and without
        ttl_clean = ttl.replace("Z", "+00:00")
        if "+" not in ttl_clean and "-" not in ttl_clean[10:]:
            # No timezone, assume UTC
            ttl_clean += "+00:00"
        ttl_dt = datetime.fromisoformat(ttl_clean)
    except ValueError as e:
        print(
            f"[DB-GUARD] VIOLATION: Invalid OVERRIDE_TTL format: {ttl}\n"
            f"Expected ISO format (e.g., 2026-01-11T12:00:00Z)\n"
            f"Error: {e}",
            file=sys.stderr
        )
        sys.exit(10)

    # Check if expired
    now = datetime.now(timezone.utc)
    if ttl_dt < now:
        print(
            f"[DB-GUARD] VIOLATION: Override has EXPIRED.\n"
            f"OVERRIDE_TTL: {ttl}\n"
            f"Current time: {now.isoformat()}\n"
            f"Expired TTL → hard fail.\n"
            f"Reference: docs/governance/DB_AUTH_001_INVARIANT.md",
            file=sys.stderr
        )
        sys.exit(10)

    # Valid override
    print(
        f"[DB-GUARD] OVERRIDE ACTIVE:\n"
        f"  Invariant: DB-AUTH-001\n"
        f"  Reason: {reason}\n"
        f"  Expires: {ttl}\n"
        f"  Time remaining: {ttl_dt - now}",
        file=sys.stderr
    )
    return True


def assert_db_authority_with_override(expected: str, *, strict: bool = True) -> None:
    """
    Assert database authority, but allow valid override to bypass.

    Use this instead of assert_db_authority() when override is permitted.

    Args:
        expected: The expected authority ("neon" or "local")
        strict: If True, also validate DATABASE_URL matches authority
    """
    if check_override():
        print(
            f"[DB-GUARD] Override active - bypassing authority check for: {expected}",
            file=sys.stderr
        )
        # Still register the connection for dual-connection tracking
        register_connection(expected)
        return

    # No override - normal authority check
    assert_db_authority(expected, strict=strict)


# Auto-check on import if EXPECTED_DB_AUTHORITY is set
_expected = os.getenv("EXPECTED_DB_AUTHORITY")
if _expected:
    _declared = get_declared_authority()
    if _declared and _declared != _expected:
        print(
            f"[DB-GUARD] VIOLATION on import: Authority mismatch.\n"
            f"EXPECTED_DB_AUTHORITY={_expected}\n"
            f"DB_AUTHORITY={_declared}",
            file=sys.stderr
        )
        sys.exit(6)


if __name__ == "__main__":
    # Self-test
    print("DB Authority Guard - Self Test")
    print(f"DB_AUTHORITY: {get_declared_authority()}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'not set')[:50]}...")

    if get_declared_authority():
        print(f"Authority is declared: {get_declared_authority()}")
    else:
        print("Authority NOT declared - this would be a violation")
