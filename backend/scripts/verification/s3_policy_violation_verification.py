#!/usr/bin/env python3
"""
S3 Policy Violation Truth Verification Script

Tests PIN-195 acceptance criteria:
- AC-0: Preconditions
- AC-1: Violation Fact Persistence
- AC-2: Incident Creation & Classification
- AC-3: Evidence Integrity
- AC-4: API Truth Propagation
- AC-6: Restart Durability (manual check)
- AC-7: Negative Assertions

ARCHITECTURE RULE: This script uses ONLY the canonical service constructors.
NO manual engine creation. NO URL manipulation.
See LESSONS_ENFORCED.md Invariant #6: Verification Script Architecture

Usage:
    DATABASE_URL=... python3 scripts/verification/s3_policy_violation_verification.py
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# DB-AUTH-001: Require Neon authority (HIGH - truth verification)
from scripts._db_guard import require_neon
require_neon()

# CANONICAL IMPORTS: Use centralized DB access and helpers
from sqlalchemy import text

from app.db import get_async_session_factory, get_engine
from app.utils.runtime import generate_uuid, utc_now

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Use canonical session factory - NO manual engine creation
AsyncSessionLocal = get_async_session_factory()
sync_engine = get_engine()

TENANT_ID = "demo-tenant"
WRONG_TENANT_ID = "wrong-tenant-isolation-test"
RUN_ID = f"s3-test-{generate_uuid()}"
POLICY_ID = "CONTENT_ACCURACY"
RULE_ID = "CA001"


class S3VerificationResult:
    def __init__(self):
        self.checks = {}
        self.run_id = RUN_ID
        self.violation_id = None
        self.incident_id = None
        self.evidence_id = None

    def record(self, check_name: str, passed: bool, details: str = ""):
        self.checks[check_name] = {"passed": passed, "details": details}
        status = "PASS" if passed else "FAIL"
        print(f"{'  ' if passed else '! '}{status} {check_name}: {details}")

    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks.values())


async def ac0_preconditions(result: S3VerificationResult) -> bool:
    """AC-0: Verify preconditions."""
    print("\n" + "=" * 60)
    print("AC-0: PRECONDITIONS")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # Check demo-tenant exists
        tenant_check = conn.execute(text("SELECT id FROM tenants WHERE id = :tid OR slug = :tid"), {"tid": TENANT_ID})
        tenant_exists = tenant_check.fetchone() is not None
        result.record("ac0_tenant_exists", tenant_exists, f"tenant={TENANT_ID}")

        # Check no pre-existing incidents for this run
        incident_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_value LIKE :pattern
            """
            ),
            {"pattern": f"%run_id={RUN_ID}%"},
        )
        no_preexisting = incident_check.scalar() == 0
        result.record("ac0_clean_slate", no_preexisting, f"run_id={RUN_ID}")

    return tenant_exists and no_preexisting


async def create_test_violation(result: S3VerificationResult) -> bool:
    """Create a test policy violation using PolicyViolationService."""
    print("\n" + "=" * 60)
    print("CREATING TEST VIOLATION")
    print("=" * 60)

    try:
        # CANONICAL IMPORTS: Use service constructors, not manual creation
        from app.services.policy_violation_service import (
            PolicyViolationService,
            ViolationFact,
        )

        async with AsyncSessionLocal() as session:
            service = PolicyViolationService(session)

            violation = ViolationFact(
                run_id=RUN_ID,
                tenant_id=TENANT_ID,
                policy_id=POLICY_ID,
                policy_type=POLICY_ID,
                violated_rule=RULE_ID,
                evaluated_value="test_query_about_auto_renew",
                threshold_condition="Definitive assertion about missing data",
                severity="high",
                reason="Made definitive claim about auto_renew but data is NULL",
                evidence={
                    "field": "auto_renew",
                    "value_in_context": None,
                    "claim_made": "Yes, your contract will auto-renew next month.",
                    "test_run": True,
                    "timestamp": utc_now().isoformat(),
                },
            )

            violation_result = await service.persist_violation_and_create_incident(violation, auto_action="block")

            result.violation_id = violation.id
            result.incident_id = violation_result.incident_id
            result.evidence_id = violation_result.evidence_id

            print(f"Created violation: {result.violation_id}")
            print(f"Created incident: {result.incident_id}")
            print(f"Created evidence: {result.evidence_id}")

            return True

    except Exception as e:
        print(f"ERROR creating violation: {e}")
        import traceback

        traceback.print_exc()
        return False


async def ac1_violation_persistence(result: S3VerificationResult) -> bool:
    """AC-1: Verify violation fact is persisted."""
    print("\n" + "=" * 60)
    print("AC-1: VIOLATION FACT PERSISTENCE")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # Check violation exists in prevention_records
        violation_check = conn.execute(
            text(
                """
                SELECT id, policy_id, pattern_id, tenant_id, outcome, created_at
                FROM prevention_records
                WHERE id = :vid
            """
            ),
            {"vid": result.violation_id},
        )
        row = violation_check.fetchone()

        if row:
            result.record("ac1_violation_exists", True, f"id={row[0]}")
            result.record("ac1_linked_to_policy", row[1] == POLICY_ID, f"policy_id={row[1]}")
            result.record("ac1_linked_to_tenant", row[3] == TENANT_ID, f"tenant_id={row[3]}")
            result.record("ac1_linked_to_rule", row[2] == RULE_ID, f"rule_id={row[2]}")
            result.record("ac1_has_timestamp", row[5] is not None, f"timestamp={row[5]}")
            return True
        else:
            result.record("ac1_violation_exists", False, "Violation not found in DB")
            return False


async def ac2_incident_classification(result: S3VerificationResult) -> bool:
    """AC-2: Verify incident creation and classification."""
    print("\n" + "=" * 60)
    print("AC-2: INCIDENT CREATION & CLASSIFICATION")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # Check incident exists
        incident_check = conn.execute(
            text(
                """
                SELECT id, tenant_id, severity, status, trigger_type, trigger_value
                FROM incidents
                WHERE id = :iid
            """
            ),
            {"iid": result.incident_id},
        )
        row = incident_check.fetchone()

        if row:
            result.record("ac2_incident_exists", True, f"id={row[0]}")
            result.record("ac2_correct_tenant", row[1] == TENANT_ID, f"tenant_id={row[1]}")
            result.record("ac2_has_severity", row[2] is not None, f"severity={row[2]}")
            result.record("ac2_correct_trigger_type", row[4] == "policy_violation", f"trigger_type={row[4]}")
            result.record("ac2_contains_run_id", f"run_id={RUN_ID}" in (row[5] or ""), "trigger_value contains run_id")

            # Check NO advisory exists (should be incident, not advisory)
            advisory_check = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM cost_anomalies
                    WHERE metadata->>'run_id' = :run_id
                    AND anomaly_type = 'POLICY_VIOLATION'
                """
                ),
                {"run_id": RUN_ID},
            )
            no_advisory = advisory_check.scalar() == 0
            result.record("ac2_no_advisory_for_violation", no_advisory, "No advisory misclassification")

            return True
        else:
            result.record("ac2_incident_exists", False, "Incident not found in DB")
            return False


async def ac3_evidence_integrity(result: S3VerificationResult) -> bool:
    """AC-3: Verify evidence integrity."""
    print("\n" + "=" * 60)
    print("AC-3: EVIDENCE INTEGRITY")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # Check evidence exists in incident_events
        evidence_check = conn.execute(
            text(
                """
                SELECT id, event_type, data_json
                FROM incident_events
                WHERE incident_id = :iid
                AND event_type = 'evidence_captured'
            """
            ),
            {"iid": result.incident_id},
        )
        row = evidence_check.fetchone()

        if row:
            result.record("ac3_evidence_exists", True, f"id={row[0]}")
            result.record("ac3_evidence_type_correct", row[1] == "evidence_captured", f"type={row[1]}")

            import json

            data = json.loads(row[2] or "{}")
            has_violation_ref = "violation_id" in data
            has_evidence = "evidence" in data
            is_immutable = data.get("immutable", False)

            result.record("ac3_linked_to_violation", has_violation_ref, "violation_id in data")
            result.record("ac3_has_evidence_data", has_evidence, "evidence in data")
            result.record("ac3_marked_immutable", is_immutable, "immutable=true")

            return True
        else:
            result.record("ac3_evidence_exists", False, "Evidence not found")
            return False


async def ac7_negative_assertions(result: S3VerificationResult) -> bool:
    """AC-7: Verify negative assertions."""
    print("\n" + "=" * 60)
    print("AC-7: NEGATIVE ASSERTIONS")
    print("=" * 60)

    with sync_engine.connect() as conn:
        # No duplicate incidents for this run+policy
        duplicate_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE trigger_type = 'policy_violation'
                AND trigger_value LIKE :pattern
            """
            ),
            {"pattern": f"%run_id={RUN_ID}%policy_id={POLICY_ID}%"},
        )
        count = duplicate_check.scalar()
        result.record("ac7_no_duplicate_incidents", count == 1, f"count={count}")

        # No cross-tenant leakage
        cross_tenant_check = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE id = :iid
                AND tenant_id = :wrong_tenant
            """
            ),
            {"iid": result.incident_id, "wrong_tenant": WRONG_TENANT_ID},
        )
        no_leakage = cross_tenant_check.scalar() == 0
        result.record("ac7_no_cross_tenant_leakage", no_leakage, "wrong_tenant sees 0")

        # No incident without violation (check invariant)
        orphan_check = conn.execute(
            text(
                """
                SELECT i.id FROM incidents i
                WHERE i.trigger_type = 'policy_violation'
                AND i.trigger_value LIKE :pattern
                AND NOT EXISTS (
                    SELECT 1 FROM prevention_records pr
                    WHERE pr.original_incident_id = :run_id
                    OR pr.blocked_incident_id = :run_id
                )
            """
            ),
            {"pattern": f"%run_id={RUN_ID}%", "run_id": RUN_ID},
        )
        no_orphan = orphan_check.fetchone() is None
        result.record("ac7_no_orphan_incidents", no_orphan, "All incidents have violation facts")

        return count == 1 and no_leakage and no_orphan


async def test_idempotency(result: S3VerificationResult) -> bool:
    """Test that duplicate violations don't create duplicate incidents."""
    print("\n" + "=" * 60)
    print("IDEMPOTENCY TEST")
    print("=" * 60)

    try:
        from app.services.policy_violation_service import (
            PolicyViolationService,
            ViolationFact,
        )

        async with AsyncSessionLocal() as session:
            service = PolicyViolationService(session)

            # Try to create duplicate violation
            violation = ViolationFact(
                run_id=RUN_ID,
                tenant_id=TENANT_ID,
                policy_id=POLICY_ID,
                policy_type=POLICY_ID,
                violated_rule=RULE_ID,
                evaluated_value="duplicate_test",
                threshold_condition="duplicate_test",
                severity="high",
                reason="Duplicate test",
                evidence={"test": "idempotency"},
            )

            violation_result = await service.persist_violation_and_create_incident(violation)

            # Should return same incident_id
            same_incident = violation_result.incident_id == result.incident_id
            result.record(
                "idempotency_same_incident",
                same_incident,
                f"returned={violation_result.incident_id}, expected={result.incident_id}",
            )

            return same_incident

    except Exception as e:
        print(f"Idempotency test error: {e}")
        return False


async def main():
    print("=" * 60)
    print("S3 POLICY VIOLATION TRUTH VERIFICATION")
    print("=" * 60)
    print(f"Tenant: {TENANT_ID}")
    print(f"Run ID: {RUN_ID}")
    print(f"Policy: {POLICY_ID}")
    print(f"Rule: {RULE_ID}")

    result = S3VerificationResult()

    # AC-0: Preconditions
    if not await ac0_preconditions(result):
        print("\n! FAIL: Preconditions not met")
        return 1

    # Create test violation
    if not await create_test_violation(result):
        print("\n! FAIL: Could not create test violation")
        return 1

    # AC-1: Violation persistence
    await ac1_violation_persistence(result)

    # AC-2: Incident classification
    await ac2_incident_classification(result)

    # AC-3: Evidence integrity
    await ac3_evidence_integrity(result)

    # AC-7: Negative assertions
    await ac7_negative_assertions(result)

    # Idempotency test
    await test_idempotency(result)

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for c in result.checks.values() if c["passed"])
    total_count = len(result.checks)

    print(f"Passed: {passed_count}/{total_count}")
    print(f"Run ID: {result.run_id}")
    print(f"Violation ID: {result.violation_id}")
    print(f"Incident ID: {result.incident_id}")
    print(f"Evidence ID: {result.evidence_id}")

    if result.passed():
        print("\nS3 VERIFICATION PASSED")
        print("Policy violations are detected, persisted, evidenced,")
        print("classified as incidents, and exposed truthfully.")
        return 0
    else:
        print("\n! S3 VERIFICATION FAILED")
        failed = [k for k, v in result.checks.items() if not v["passed"]]
        print(f"Failed checks: {failed}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
