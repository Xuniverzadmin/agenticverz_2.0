#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI pipeline
#   Execution: sync
# Role: Enforce M10 contract - no function overloads
# Reference: M10_OUTBOX_CONTRACT.md, PIN-276

"""
M10 Function Overload Guard

This CI check enforces the "ONE SIGNATURE ONLY" rule from M10_OUTBOX_CONTRACT.md.

If any M10 function has more than one signature (overload), CI fails.
This prevents accidental regression of the canonical function signatures.

Usage:
    python3 scripts/ci/check_m10_overloads.py

Exit codes:
    0 = All functions have exactly one signature
    1 = CONTRACT VIOLATION - overloads detected
    2 = Cannot connect to database
"""

import os
import sys

# Protected functions that must have exactly ONE signature
PROTECTED_FUNCTIONS = [
    "claim_outbox_events",
    "complete_outbox_event",
    "publish_outbox",
    "claim_work",
    "complete_work",
]


def check_overloads() -> int:
    """Check for function overloads in m10_recovery schema."""
    import psycopg2

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 2

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        violations = []

        for func_name in PROTECTED_FUNCTIONS:
            cur.execute(
                """
                SELECT COUNT(*), array_agg(pg_get_function_arguments(p.oid))
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'm10_recovery'
                AND p.proname = %s
                """,
                (func_name,),
            )
            count, signatures = cur.fetchone()

            if count == 0:
                # Function doesn't exist yet - that's OK
                continue
            elif count == 1:
                print(f"✓ {func_name}: 1 signature (canonical)")
            else:
                violations.append(
                    {
                        "function": func_name,
                        "count": count,
                        "signatures": signatures,
                    }
                )
                print(f"✗ {func_name}: {count} signatures (VIOLATION)")
                for sig in signatures:
                    print(f"    - {func_name}({sig})")

        cur.close()
        conn.close()

        if violations:
            print("\n" + "=" * 60)
            print("CONTRACT VIOLATION: M10 function overloads detected")
            print("=" * 60)
            print("\nReference: M10_OUTBOX_CONTRACT.md - ONE SIGNATURE ONLY rule")
            print("\nTo fix, drop the non-canonical overloads:")
            print()
            for v in violations:
                print(f"  -- Fix {v['function']}:")
                print("  -- Keep canonical signature, drop others")
            print()
            return 1

        print("\n✓ All M10 functions have exactly one signature")
        return 0

    except Exception as e:
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(check_overloads())
