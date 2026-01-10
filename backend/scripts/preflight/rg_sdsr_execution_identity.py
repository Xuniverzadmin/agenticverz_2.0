#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CLI / preflight invocation
#   Execution: sync
# Role: RG-SDSR-01 Execution Identity Guard
# Reference: PIN-379 (SDSR E2E), SDSR_E2E_TESTING_PROTOCOL.md

"""
RG-SDSR-01: Execution Identity Guard (Non-Negotiable)

LOCKED CONTRACT:
- run_id MUST be unique per execution
- Reuse is forbidden
- No auto-fix, no suffixing, no bypass

What it prevents:
- ON CONFLICT DO NOTHING silently skipping trace inserts
- Reuse of archived trace identifiers
- Ambiguous execution provenance

Exit codes:
- 0: run_id is unique, safe to proceed
- 4: run_id already exists (HARD FAIL)

Usage:
    python rg_sdsr_execution_identity.py <run_id>

Integration:
    Called by sdsr_e2e_preflight.sh after SR-1/2/3 and before injection.
    If this guard fails, inject_synthetic.py must NOT run.
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# DB-AUTH-001: Require Neon authority (CRITICAL - execution identity check)
from scripts._db_guard import require_neon
require_neon()

EXIT_PASS = 0
EXIT_IDENTITY_REUSE = 4


def fail(msg: str) -> None:
    """Print failure message and exit with code 4."""
    print(f"[RG-SDSR-01 FAIL] {msg}")
    sys.exit(EXIT_IDENTITY_REUSE)


def main() -> None:
    # Validate arguments
    if len(sys.argv) != 2:
        fail("Expected run_id argument. Usage: python rg_sdsr_execution_identity.py <run_id>")

    run_id = sys.argv[1]

    if not run_id or run_id.strip() == "":
        fail("run_id cannot be empty")

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try loading from alembic.ini
        try:
            from alembic.config import Config

            cfg = Config("alembic.ini")
            database_url = cfg.get_main_option("sqlalchemy.url")
        except Exception:
            pass

    if not database_url:
        fail("DATABASE_URL not configured (env or alembic.ini)")

    # Check for run_id existence
    try:
        from sqlalchemy import create_engine, text

        # database_url is guaranteed non-None at this point
        engine = create_engine(str(database_url), future=True)

        with engine.connect() as conn:
            # Check runs table (any state - active or historical)
            result = conn.execute(text("SELECT 1 FROM runs WHERE id = :run_id LIMIT 1"), {"run_id": run_id}).scalar()

            if result:
                fail(
                    f"run_id '{run_id}' already exists in runs table.\n"
                    f"    LOCKED CONTRACT: run_id must be execution-unique.\n"
                    f"    This is a HARD FAIL. No auto-fix, no bypass.\n"
                    f"    Resolution: Use a different run_id or investigate the duplicate."
                )

            # Also check aos_traces (belt-and-suspenders)
            # A trace might exist even if the run was deleted
            result = conn.execute(
                text("SELECT 1 FROM aos_traces WHERE run_id = :run_id LIMIT 1"), {"run_id": run_id}
            ).scalar()

            if result:
                fail(
                    f"Trace for run_id '{run_id}' already exists (active or archived).\n"
                    f"    LOCKED CONTRACT: run_id must be execution-unique.\n"
                    f"    This would cause silent trace creation failure due to S6 immutability.\n"
                    f"    Resolution: Use a different run_id."
                )

    except SystemExit:
        # Re-raise SystemExit from fail() calls
        raise
    except Exception as e:
        fail(f"Database check failed: {e}")

    print(f"[RG-SDSR-01 PASS] run_id '{run_id}' is unique")
    sys.exit(EXIT_PASS)


if __name__ == "__main__":
    main()
