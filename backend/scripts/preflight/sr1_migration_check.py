#!/usr/bin/env python3
"""
SR-1 Migration Consistency Check (Canonical Implementation)

Reference: docs/governance/SDSR_E2E_TESTING_PROTOCOL.md

This script is the ONLY authority for SR-1 verification.
DO NOT use shell parsing of `alembic current` or `alembic heads`.

Exit codes:
    0 = SR-1 PASS (current == head, single head)
    1 = SR-1 FAIL (any failure condition)

Design principles:
    - Machine-readable (no parsing human CLI output)
    - Deterministic (same result every time)
    - Fast (single DB connection, O(1))
    - Alembic-native (uses Alembic internals, not shell wrappers)
    - Governance-safe (explicit failures, no fallbacks)
"""

import os
import sys

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect


def fail(reason: str) -> None:
    """Print failure reason and exit with code 1."""
    print(f"[SR-1 FAIL] {reason}")
    sys.exit(1)


def main() -> None:
    """Execute SR-1 migration consistency check."""

    # Determine paths relative to backend directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    if not os.path.exists(alembic_ini):
        fail(f"alembic.ini not found at {alembic_ini}")

    cfg = Config(alembic_ini)

    # Get DATABASE_URL from environment (overrides alembic.ini)
    db_url: str | None = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = cfg.get_main_option("sqlalchemy.url")

    if not db_url:
        fail("DATABASE_URL not configured (not in env or alembic.ini)")
        return  # Never reached, but helps type checker

    # Initialize variables for type checker
    current_rev: str | None = None
    heads: list[str] = []

    # 1. Connect to DB (fast, single connection)
    try:
        engine = create_engine(db_url, future=True)
        with engine.connect() as conn:
            # 2. Ensure alembic_version table exists
            inspector = inspect(conn)
            if "alembic_version" not in inspector.get_table_names():
                fail("alembic_version table missing - DB not initialized with Alembic")

            # 3. Read current revision from DB
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

    except Exception as e:
        fail(f"Database or Alembic context error: {e}")

    if not current_rev:
        fail("No current revision found in DB - alembic_version table is empty")
        return  # Never reached, but helps type checker

    # 4. Load migration script graph
    try:
        script = ScriptDirectory.from_config(cfg)
        heads = list(script.get_heads())
    except Exception as e:
        fail(f"Failed to load migration scripts: {e}")

    # 5. Enforce single-head invariant
    if len(heads) == 0:
        fail("No migration heads found in script directory")

    if len(heads) != 1:
        fail(f"Multiple migration heads detected (multi-head chaos): {heads}")

    head = heads[0]

    # 6. Compare DB vs code
    if current_rev != head:
        fail(f"Migration mismatch: DB={current_rev}, CODE={head}")

    print(f"[SR-1 PASS] Migration state clean at revision {current_rev}")
    sys.exit(0)


if __name__ == "__main__":
    main()
