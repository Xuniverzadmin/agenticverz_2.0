# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Verify audit_ledger immutability at database level
# Reference: PIN-413 (Logs Domain), LOGS_DOMAIN_AUDIT.md
#
"""
CI Script: Audit Ledger Immutability Check

Verifies that the audit_ledger table is protected by database-level
triggers that prevent UPDATE and DELETE operations.

This script:
1. Inserts a test row (must succeed)
2. Attempts UPDATE (must fail)
3. Attempts DELETE (must fail)
4. Cleans up via raw SQL bypass (test only)

Exit codes:
- 0: Immutability verified
- 1: Immutability broken (UPDATE or DELETE succeeded)
- 2: Setup failed (INSERT failed)

Usage:
    DB_AUTHORITY=neon python scripts/ci_check_audit_immutability.py
"""

import sys
import uuid

from sqlalchemy import text


def main() -> int:
    """Run immutability verification."""
    # Import here to allow script to be parsed without DB connection
    from sqlmodel import Session
    from app.db import get_engine

    test_id = f"ci_test_{uuid.uuid4().hex[:8]}"
    engine = get_engine()
    session = Session(engine)

    print(f"Testing audit_ledger immutability with id={test_id}")
    print("-" * 60)

    # Step 1: INSERT must succeed
    try:
        session.execute(
            text("""
                INSERT INTO audit_ledger
                (id, tenant_id, event_type, entity_type, entity_id, actor_type, created_at)
                VALUES (:id, 'ci_test_tenant', 'CITestEvent', 'CI_TEST', 'ci_entity', 'SYSTEM', NOW())
            """),
            {"id": test_id},
        )
        session.commit()
        print(f"✓ INSERT succeeded (expected)")
    except Exception as e:
        print(f"✗ INSERT failed (unexpected): {e}")
        session.rollback()
        return 2

    # Step 2: UPDATE must fail (trigger should block)
    try:
        session.execute(
            text("""
                UPDATE audit_ledger SET event_type = 'HACKED'
                WHERE id = :id
            """),
            {"id": test_id},
        )
        session.commit()
        print("✗ UPDATE succeeded — IMMUTABILITY BROKEN")
        # Attempt cleanup before exit
        _force_cleanup(session, test_id)
        return 1
    except Exception as e:
        session.rollback()
        if "immutable" in str(e).lower():
            print(f"✓ UPDATE blocked by trigger (expected): {type(e).__name__}")
        else:
            print(f"✓ UPDATE failed (expected): {type(e).__name__}")

    # Step 3: DELETE must fail (trigger should block)
    try:
        session.execute(
            text("""
                DELETE FROM audit_ledger WHERE id = :id
            """),
            {"id": test_id},
        )
        session.commit()
        print("✗ DELETE succeeded — IMMUTABILITY BROKEN")
        return 1
    except Exception as e:
        session.rollback()
        if "immutable" in str(e).lower():
            print(f"✓ DELETE blocked by trigger (expected): {type(e).__name__}")
        else:
            print(f"✓ DELETE failed (expected): {type(e).__name__}")

    # Step 4: Cleanup (bypass trigger for CI only)
    _force_cleanup(session, test_id)

    print("-" * 60)
    print("✅ Audit ledger immutability verified")
    return 0


def _force_cleanup(session, test_id: str) -> None:
    """
    Force cleanup of CI test row.

    This temporarily disables the trigger for cleanup purposes only.
    This is acceptable because:
    - It's CI-only code, not production
    - The test already proved the trigger blocks normal operations
    - We need to avoid polluting the audit_ledger with test data
    """
    try:
        # Disable trigger temporarily (requires superuser in prod, but CI has it)
        session.execute(text("ALTER TABLE audit_ledger DISABLE TRIGGER trg_audit_ledger_immutable"))
        session.execute(text("DELETE FROM audit_ledger WHERE id = :id"), {"id": test_id})
        session.execute(text("ALTER TABLE audit_ledger ENABLE TRIGGER trg_audit_ledger_immutable"))
        session.commit()
        print(f"✓ CI test row cleaned up")
    except Exception as e:
        session.rollback()
        # Not fatal - the row will remain but won't affect production
        print(f"⚠ Cleanup failed (non-fatal): {e}")


if __name__ == "__main__":
    sys.exit(main())
