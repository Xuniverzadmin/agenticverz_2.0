# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI/manual
#   Execution: async
# Role: Destructive test for worker crash and stale run detection
# Callers: CI, manual testing
# Allowed Imports: All (test file)
# Forbidden Imports: None
# Reference: PIN-454 (Cross-Domain Orchestration Audit), Section 4

"""
Destructive Test: Worker Crash and Stale Run Detection

This test verifies that when a worker crashes mid-run:
1. The finalize_run expectation is never acked
2. The RAC reconciler detects the stale run
3. The run is properly marked as stale/failed

Test Flow:
1. Create a run with expectations
2. Simulate worker claiming the run
3. Simulate worker crashing (no acks sent)
4. Run the reconciler
5. Verify stale run is detected

This is a "destructive" test because it simulates failure scenarios.
It should be run in isolation, not as part of normal CI.

Usage:
    pytest tests/destructive/test_worker_crash_stale_detection.py -v

    # Or run directly
    python tests/destructive/test_worker_crash_stale_detection.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

# Ensure the backend is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.audit import (
    AuditAction,
    AuditDomain,
    AuditExpectation,
    AuditStore,
    create_run_expectations,
    get_audit_store,
)
from app.services.audit.reconciler import AuditReconciler


class TestWorkerCrashStaleDetection:
    """
    Test suite for verifying stale run detection after worker crash.

    Per PIN-454: If finalize_run is never acked, the run is stale.
    """

    def setup_method(self):
        """Reset state before each test."""
        # Create fresh instances for testing (not singletons)
        self.store = AuditStore()
        self.reconciler = AuditReconciler(store=self.store)

    def test_normal_run_completion(self):
        """
        Verify that a normal run (all acks) is detected as complete.

        This is the baseline - all expectations are acked.
        """
        # Create run
        run_id = uuid4()

        # Create expectations
        expectations = create_run_expectations(
            run_id=run_id,
            run_timeout_ms=5000,
            grace_period_ms=1000,
        )
        self.store.add_expectations(run_id, expectations)

        # Simulate all domain acks
        from app.services.audit.models import AckStatus, DomainAck

        # Incident ack
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            result_id="inc-123",
        ))

        # Policy ack
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.POLICIES,
            action=AuditAction.EVALUATE_POLICY,
            result_id="pol-123",
        ))

        # Trace ack
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.LOGS,
            action=AuditAction.START_TRACE,
            result_id="trace-123",
        ))

        # Finalize ack (critical for non-stale detection)
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.ORCHESTRATOR,
            action=AuditAction.FINALIZE_RUN,
            result_id=str(run_id),
        ))

        # Reconcile
        result = self.reconciler.reconcile(run_id)

        # Verify: Run is complete, not stale
        assert result.status == "COMPLETE", f"Expected COMPLETE, got {result.status}"
        assert not result.stale_run, "Run should not be marked as stale"
        assert result.is_clean, "Run should be clean (no issues)"
        assert len(result.missing_actions) == 0, f"Should have no missing actions: {result.missing_actions}"

        print(f"[PASS] Normal run completion: {result.to_dict()}")

    def test_worker_crash_no_acks(self):
        """
        Simulate worker crash where NO acks are sent.

        Expected: All actions are missing, run is stale.
        """
        run_id = uuid4()

        # Create expectations
        expectations = create_run_expectations(run_id=run_id)
        self.store.add_expectations(run_id, expectations)

        # Worker "crashes" - no acks sent

        # Reconcile
        result = self.reconciler.reconcile(run_id)

        # Verify: Run is stale (finalize_run not acked makes status STALE, not INCOMPLETE)
        assert result.status == "STALE", f"Expected STALE, got {result.status}"
        assert result.stale_run, "Run should be marked as stale (finalize_run not acked)"
        assert len(result.missing_actions) == 4, f"Should have 4 missing actions: {result.missing_actions}"

        # Verify finalize_run is specifically missing
        missing_domains = [d for d, a in result.missing_actions]
        assert "orchestrator" in missing_domains, "finalize_run should be missing"

        print(f"[PASS] Worker crash (no acks): {result.to_dict()}")

    def test_worker_crash_partial_acks(self):
        """
        Simulate worker crash after partial execution.

        Worker started, created incident, then crashed.
        finalize_run was never called.
        """
        run_id = uuid4()

        # Create expectations
        expectations = create_run_expectations(run_id=run_id)
        self.store.add_expectations(run_id, expectations)

        # Worker starts executing, sends some acks
        from app.services.audit.models import DomainAck

        # Incident ack (succeeded before crash)
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            result_id="inc-456",
        ))

        # Policy ack (also succeeded)
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.POLICIES,
            action=AuditAction.EVALUATE_POLICY,
            result_id="pol-456",
        ))

        # Worker crashes here - trace and finalize never acked

        # Reconcile
        result = self.reconciler.reconcile(run_id)

        # Verify: Run is stale (finalize_run not acked makes status STALE)
        assert result.status == "STALE", f"Expected STALE, got {result.status}"
        assert result.stale_run, "Run should be marked as stale"

        # Should have 2 missing: trace.start_trace and orchestrator.finalize_run
        assert len(result.missing_actions) == 2, f"Should have 2 missing actions: {result.missing_actions}"

        # Verify expectations count vs acks count
        assert result.expectations_count == 4
        assert result.acks_count == 2

        print(f"[PASS] Worker crash (partial acks): {result.to_dict()}")

    def test_worker_crash_finalize_not_acked(self):
        """
        Simulate case where all domain work completed but finalize failed.

        This is the liveness guarantee check - finalize_run MUST be acked.
        """
        run_id = uuid4()

        # Create expectations
        expectations = create_run_expectations(run_id=run_id)
        self.store.add_expectations(run_id, expectations)

        # All domain work completed
        from app.services.audit.models import DomainAck

        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            result_id="inc-789",
        ))

        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.POLICIES,
            action=AuditAction.EVALUATE_POLICY,
            result_id="pol-789",
        ))

        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.LOGS,
            action=AuditAction.START_TRACE,
            result_id="trace-789",
        ))

        # finalize_run NOT acked - worker died during finalization
        # (This is the PIN-454 liveness guarantee check)

        # Reconcile
        result = self.reconciler.reconcile(run_id)

        # Verify: Run is STALE because finalize_run missing (stale_run triggers STALE status)
        assert result.status == "STALE", f"Expected STALE, got {result.status}"
        assert result.stale_run, "Run should be marked as stale (finalize_run not acked)"
        assert len(result.missing_actions) == 1, f"Should have 1 missing action: {result.missing_actions}"

        # The only missing action should be finalize_run
        missing = result.missing_actions[0]
        assert missing == ("orchestrator", "finalize_run"), f"Missing action should be finalize_run: {missing}"

        print(f"[PASS] Finalize not acked (liveness check): {result.to_dict()}")

    def test_multiple_stale_runs_detection(self):
        """
        Test detecting multiple stale runs at once.

        Simulates batch reconciliation finding multiple crashed workers.
        """
        stale_runs = []

        # Create 5 runs, simulate crashes for 3 of them
        for i in range(5):
            run_id = uuid4()
            expectations = create_run_expectations(run_id=run_id)
            self.store.add_expectations(run_id, expectations)

            if i % 2 == 0:
                # These runs will be stale (no acks)
                stale_runs.append(run_id)
            else:
                # These runs complete normally
                from app.services.audit.models import DomainAck

                self.store.add_ack(run_id, DomainAck(
                    run_id=run_id,
                    domain=AuditDomain.INCIDENTS,
                    action=AuditAction.CREATE_INCIDENT,
                ))
                self.store.add_ack(run_id, DomainAck(
                    run_id=run_id,
                    domain=AuditDomain.POLICIES,
                    action=AuditAction.EVALUATE_POLICY,
                ))
                self.store.add_ack(run_id, DomainAck(
                    run_id=run_id,
                    domain=AuditDomain.LOGS,
                    action=AuditAction.START_TRACE,
                ))
                self.store.add_ack(run_id, DomainAck(
                    run_id=run_id,
                    domain=AuditDomain.ORCHESTRATOR,
                    action=AuditAction.FINALIZE_RUN,
                ))

        # Get all pending runs and reconcile
        pending_run_ids = self.store.get_pending_run_ids()
        assert len(pending_run_ids) == 5

        detected_stale = []
        for run_id_str in pending_run_ids:
            from uuid import UUID
            run_id = UUID(run_id_str)
            result = self.reconciler.reconcile(run_id)
            if result.stale_run:
                detected_stale.append(run_id)

        # Verify: Should detect exactly 3 stale runs
        assert len(detected_stale) == 3, f"Should detect 3 stale runs, detected {len(detected_stale)}"

        # Verify they match our expected stale runs
        for run_id in stale_runs:
            assert run_id in detected_stale, f"Run {run_id} should be detected as stale"

        print(f"[PASS] Multiple stale runs detected: {len(detected_stale)}/{len(pending_run_ids)}")

    def test_rollback_ack_preserves_audit_trail(self):
        """
        Test that rollback acks are properly recorded.

        Per PIN-454: When rollback happens, emit DomainAck with rolled_back=true.
        """
        run_id = uuid4()

        # Create expectations
        expectations = create_run_expectations(run_id=run_id)
        self.store.add_expectations(run_id, expectations)

        # Simulate incident created, then rolled back due to downstream failure
        from app.services.audit.models import AckStatus, DomainAck

        # Initial incident ack (succeeded)
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            result_id="inc-rollback-test",
        ))

        # Then rollback ack (preserving audit trail)
        self.store.add_ack(run_id, DomainAck(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            status=AckStatus.ROLLED_BACK,
            result_id="inc-rollback-test",
            rolled_back=True,
            rollback_reason="Transaction rollback due to downstream failure",
        ))

        # Get all acks
        acks = self.store.get_acks(run_id)

        # Verify: Should have 2 acks for incident (original + rollback)
        incident_acks = [a for a in acks if a.domain == AuditDomain.INCIDENTS]
        assert len(incident_acks) == 2, f"Should have 2 incident acks: {len(incident_acks)}"

        # Verify rollback ack is marked correctly
        rollback_ack = next((a for a in incident_acks if a.is_rolled_back), None)
        assert rollback_ack is not None, "Should have a rollback ack"
        assert rollback_ack.rollback_reason is not None, "Rollback ack should have reason"

        print(f"[PASS] Rollback ack preserves audit trail")


def run_tests():
    """Run all tests directly."""
    test = TestWorkerCrashStaleDetection()

    print("\n" + "=" * 60)
    print("Destructive Test: Worker Crash and Stale Run Detection")
    print("Reference: PIN-454 (Cross-Domain Orchestration Audit)")
    print("=" * 60 + "\n")

    tests = [
        ("Normal run completion", test.test_normal_run_completion),
        ("Worker crash (no acks)", test.test_worker_crash_no_acks),
        ("Worker crash (partial acks)", test.test_worker_crash_partial_acks),
        ("Finalize not acked (liveness check)", test.test_worker_crash_finalize_not_acked),
        ("Multiple stale runs detection", test.test_multiple_stale_runs_detection),
        ("Rollback ack preserves audit trail", test.test_rollback_ack_preserves_audit_trail),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        test.setup_method()
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
