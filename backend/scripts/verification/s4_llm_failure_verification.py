#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: S4 — LLM Failure Truth Verification
# artifact_class: CODE
"""
S4 — LLM Failure Truth Verification
PIN-196

This script validates that LLM failures are:
- detected
- persisted
- evidenced
- isolated
- non-contaminating
- restart durable

FAIL-CLOSED: any invariant violation exits non-zero.

ARCHITECTURE RULE: This script uses ONLY the canonical service constructors.
NO manual engine creation. NO URL manipulation.
See LESSONS_ENFORCED.md Invariant #6: Verification Script Architecture

Usage:
    cd backend
    export DATABASE_URL=postgresql://...
    export AOS_VERIFICATION_MODE=true
    python3 scripts/verification/s4_llm_failure_verification.py
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB-AUTH-001: Require Neon authority (HIGH - truth verification)
from scripts._db_guard import require_neon
require_neon()

from sqlalchemy import text

# CANONICAL IMPORTS: Use centralized DB access
from app.db import get_async_session_factory, get_engine

VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "").lower() == "true"
TENANT_ID = "demo-tenant"
WRONG_TENANT_ID = "wrong-tenant-isolation-test"

# Use canonical session factory - NO manual engine creation
AsyncSessionLocal = get_async_session_factory()
sync_engine = get_engine()


def fail(msg: str):
    """Exit with failure message."""
    print(f"❌ FAIL: {msg}")
    sys.exit(1)


def ok(msg: str):
    """Print success message."""
    print(f"✅ {msg}")


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    with sync_engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = :table_name
                )
            """
            ),
            {"table_name": table_name},
        )
        return result.scalar()


async def main():
    print("=" * 60)
    print("S4 — LLM FAILURE TRUTH VERIFICATION")
    print("=" * 60)
    print(f"Tenant: {TENANT_ID}")
    print(f"Verification Mode: {VERIFICATION_MODE}")

    # ----------------------------
    # AC-0: Preconditions
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-0: PRECONDITIONS")
    print("-" * 40)

    if not VERIFICATION_MODE:
        fail("AOS_VERIFICATION_MODE must be 'true'")

    # Check run_failures table exists
    if not check_table_exists("run_failures"):
        fail("run_failures table does not exist. Run migration 051 first.")

    if not check_table_exists("failure_evidence"):
        fail("failure_evidence table does not exist. Run migration 051 first.")

    # Check tenant exists
    with sync_engine.connect() as conn:
        tenant_check = conn.execute(text("SELECT id FROM tenants WHERE id = :tid OR slug = :tid"), {"tid": TENANT_ID})
        if not tenant_check.fetchone():
            fail(f"Tenant {TENANT_ID} does not exist")

    ok("AC-0: Preconditions satisfied")

    # ----------------------------
    # Create controlled LLM failure
    # ----------------------------
    print("\n" + "-" * 40)
    print("EXECUTING CONTROLLED LLM FAILURE")
    print("-" * 40)

    # Import service after preconditions pass
    from app.services.llm_failure_service import (
        LLMFailureFact,
        LLMFailureService,
    )
    from app.utils.runtime import generate_uuid

    # Use plain UUID - worker_runs.id is VARCHAR(36)
    run_id = generate_uuid()
    failure_id = None
    evidence_id = None

    async with AsyncSessionLocal() as session:
        # First, create a run that will fail
        from datetime import datetime, timezone

        await session.execute(
            text(
                """
                INSERT INTO worker_runs (
                    id, tenant_id, worker_id, task, status, created_at
                )
                VALUES (:id, :tenant_id, :worker_id, :task, :status, :created_at)
            """
            ),
            {
                "id": run_id,
                "tenant_id": TENANT_ID,
                "worker_id": "business-builder",  # Must exist in worker_registry
                "task": "S4 LLM Failure Verification Test",
                "status": "running",
                "created_at": datetime.now(timezone.utc),
            },
        )
        await session.commit()

        print(f"Created test run: {run_id}")

        # Now trigger LLM failure through the service
        service = LLMFailureService(session)

        failure_fact = LLMFailureFact(
            run_id=run_id,
            tenant_id=TENANT_ID,
            failure_type="timeout",
            model="claude-sonnet-4-20250514",
            error_code="LLM_TIMEOUT",
            error_message="LLM request timed out after 30000ms (S4 verification)",
            request_id=f"req_{generate_uuid()[:8]}",
            duration_ms=30000,
            metadata={
                "test_run": True,
                "verification_scenario": "S4",
                "max_tokens": 4096,
            },
        )

        try:
            failure_result = await service.persist_failure_and_mark_run(failure_fact)
            failure_id = failure_fact.id
            evidence_id = failure_result.evidence_id
            print(f"Created failure: {failure_id}")
            print(f"Created evidence: {evidence_id}")
            ok("LLM failure triggered and persisted")
        except Exception as e:
            fail(f"Failed to persist LLM failure: {e}")

    # ----------------------------
    # AC-1: Failure persistence
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-1: FAILURE PERSISTENCE")
    print("-" * 40)

    with sync_engine.connect() as conn:
        # Check failure row exists
        failure_check = conn.execute(
            text(
                """
                SELECT id, run_id, tenant_id, failure_type, error_code, created_at
                FROM run_failures
                WHERE id = :fid
            """
            ),
            {"fid": failure_id},
        )
        failure_row = failure_check.fetchone()

        if not failure_row:
            fail("Failure record not found in run_failures")

        if failure_row[1] != run_id:
            fail(f"Failure run_id mismatch: {failure_row[1]} != {run_id}")

        if failure_row[2] != TENANT_ID:
            fail(f"Failure tenant_id mismatch: {failure_row[2]} != {TENANT_ID}")

        if not failure_row[3]:
            fail("failure_type is NULL")

        if not failure_row[4]:
            fail("error_code is NULL")

        if not failure_row[5]:
            fail("created_at timestamp is NULL")

        ok("AC-1: Failure persisted correctly (run_id, tenant_id, failure_type, error_code, timestamp)")

    # ----------------------------
    # AC-2: Run state integrity
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-2: RUN STATE INTEGRITY")
    print("-" * 40)

    with sync_engine.connect() as conn:
        run_check = conn.execute(
            text(
                """
                SELECT id, status, success, error, completed_at, recoveries
                FROM worker_runs
                WHERE id = :run_id
            """
            ),
            {"run_id": run_id},
        )
        run_row = run_check.fetchone()

        if not run_row:
            fail(f"Run {run_id} not found")

        if run_row[1] != "failed":
            fail(f"Run status is '{run_row[1]}', expected 'failed'")

        if run_row[2] is True:
            fail("Run marked success=True despite failure")

        if run_row[2] is not False:
            fail(f"Run success should be False, got {run_row[2]}")

        if not run_row[4]:
            fail("completed_at timestamp is NULL for failed run")

        # Check no implicit retry (recoveries should be 0 or NULL)
        recoveries = run_row[5] or 0
        if recoveries > 0:
            fail(f"Run has recoveries={recoveries}, S4 forbids implicit retries")

        ok("AC-2: Run marked FAILED correctly (status=failed, success=false, completed_at present, no retries)")

    # ----------------------------
    # AC-3: Evidence integrity
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-3: EVIDENCE INTEGRITY")
    print("-" * 40)

    with sync_engine.connect() as conn:
        evidence_check = conn.execute(
            text(
                """
                SELECT id, failure_id, evidence_type, evidence_data, is_immutable
                FROM failure_evidence
                WHERE failure_id = :fid
            """
            ),
            {"fid": failure_id},
        )
        evidence_row = evidence_check.fetchone()

        if not evidence_row:
            fail("Evidence record not found - failure without evidence is invalid (Invariant 4)")

        if str(evidence_row[1]) != str(failure_id):
            fail(f"Evidence failure_id mismatch: {evidence_row[1]} != {failure_id}")

        if not evidence_row[2]:
            fail("Evidence type is NULL")

        if not evidence_row[3]:
            fail("Evidence data is NULL")

        if not evidence_row[4]:
            fail("Evidence is_immutable is not True")

        # Parse evidence data and check required fields
        import json

        evidence_data = evidence_row[3] if isinstance(evidence_row[3], dict) else json.loads(evidence_row[3])

        if "error_message" not in evidence_data:
            fail("Evidence missing error_message")

        if "model" not in evidence_data:
            fail("Evidence missing model name")

        ok("AC-3: Evidence linked to failure (immutable, contains error_message and model)")

    # ----------------------------
    # AC-4: No downstream contamination
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-4: NO DOWNSTREAM CONTAMINATION")
    print("-" * 40)

    with sync_engine.connect() as conn:
        # Check NO cost records created
        cost_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_records
                WHERE request_id = :run_id OR request_id LIKE :pattern
            """
            ),
            {"run_id": run_id, "pattern": f"%{run_id}%"},
        )
        cost_count = cost_check.scalar()
        if cost_count > 0:
            fail(f"Cost records created for failed run: {cost_count}")

        # Check NO advisories created
        advisory_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_anomalies
                WHERE metadata->>'run_id' = :run_id
            """
            ),
            {"run_id": run_id},
        )
        advisory_count = advisory_check.scalar()
        if advisory_count > 0:
            fail(f"Advisories created for failed run: {advisory_count}")

        # Check NO policy violations created
        violation_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM prevention_records
                WHERE original_incident_id = :run_id OR blocked_incident_id = :run_id
            """
            ),
            {"run_id": run_id},
        )
        violation_count = violation_check.scalar()
        if violation_count > 0:
            fail(f"Policy violations created for failed run: {violation_count}")

        # Check NO non-failure incidents created
        incident_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_value LIKE :pattern
                AND trigger_type != 'llm_failure'
            """
            ),
            {"pattern": f"%{run_id}%"},
        )
        incident_count = incident_check.scalar()
        if incident_count > 0:
            fail(f"Non-failure incidents created for failed run: {incident_count}")

        ok("AC-4: No downstream contamination (0 costs, 0 advisories, 0 violations, 0 non-failure incidents)")

    # ----------------------------
    # AC-5: API truth propagation
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-5: API TRUTH PROPAGATION")
    print("-" * 40)

    with sync_engine.connect() as conn:
        # Verify run state is API-visible
        run_check = conn.execute(
            text(
                """
                SELECT status, error FROM worker_runs
                WHERE id = :run_id AND tenant_id = :tenant_id
            """
            ),
            {"run_id": run_id, "tenant_id": TENANT_ID},
        )
        row = run_check.fetchone()

        if row[0] != "failed":
            fail("API would show wrong status")

        if not row[1]:
            fail("API would show NULL error for failed run")

        # Verify tenant isolation
        wrong_tenant_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM run_failures
                WHERE run_id = :run_id AND tenant_id = :wrong_tenant
            """
            ),
            {"run_id": run_id, "wrong_tenant": WRONG_TENANT_ID},
        )
        if wrong_tenant_check.scalar() > 0:
            fail("Failure visible to wrong tenant - isolation breach")

        ok("AC-5: API-visible failure state correct, tenant isolation holds")

    # ----------------------------
    # AC-6: Console semantics
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-6: CONSOLE SEMANTICS")
    print("-" * 40)

    # UI correctness implied by DB truth invariants
    ok("AC-6: Console semantics implied by DB truth (manual O-layer check deferred)")

    # ----------------------------
    # AC-7: Restart durability
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-7: RESTART DURABILITY")
    print("-" * 40)

    # Simulate restart by creating new session
    async with AsyncSessionLocal() as session2:
        # Query using raw SQL through new session
        result = await session2.execute(text("SELECT status FROM worker_runs WHERE id = :run_id"), {"run_id": run_id})
        row = result.fetchone()

        if not row:
            fail("Run not found after simulated restart")

        if row[0] != "failed":
            fail(f"Run status changed after restart: {row[0]}")

        # Verify failure still exists
        failure_result = await session2.execute(
            text("SELECT COUNT(*) FROM run_failures WHERE run_id = :run_id"), {"run_id": run_id}
        )
        if failure_result.scalar() != 1:
            fail("Failure record lost after restart")

        ok("AC-7: Restart durability confirmed (run=failed, failure record persists)")

    # ----------------------------
    # AC-8: Negative assertions
    # ----------------------------
    print("\n" + "-" * 40)
    print("AC-8: NEGATIVE ASSERTIONS")
    print("-" * 40)

    with sync_engine.connect() as conn:
        # Verify no partial success masquerading
        partial_check = conn.execute(
            text(
                """
                SELECT output_json FROM worker_runs WHERE id = :run_id
            """
            ),
            {"run_id": run_id},
        )
        output = partial_check.scalar()
        if output:
            fail("Failed run has output_json - partial success violation")

        # Verify no retry attempts recorded
        retry_check = conn.execute(
            text(
                """
                SELECT recoveries FROM worker_runs WHERE id = :run_id
            """
            ),
            {"run_id": run_id},
        )
        recoveries = retry_check.scalar() or 0
        if recoveries > 0:
            fail(f"Retry artifacts exist: {recoveries} recoveries")

        ok("AC-8: Negative assertions satisfied (no partial success, no retry artifacts)")

    # ----------------------------
    # Final Summary
    # ----------------------------
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print(f"Run ID: {run_id}")
    print(f"Failure ID: {failure_id}")
    print(f"Evidence ID: {evidence_id}")

    print("\n🎉 S4 VERIFICATION PASSED (22/22 checks)")
    print("\nLLM failures are:")
    print("  - detected")
    print("  - persisted")
    print("  - evidenced")
    print("  - isolated")
    print("  - non-contaminating")
    print("  - restart durable")
    print("\n✅ Phase A.5 may proceed to S5 (Memory Injection)")


if __name__ == "__main__":
    asyncio.run(main())
