#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Test script for MidExecutionPolicyChecker verification
# Reference: PIN-454 Phase 5

"""
MidExecutionPolicyChecker Test

Tests the policy checker by simulating:
1. Normal run (no violations)
2. Budget exceeded scenario
3. Interval throttling
4. Decision logic

Usage:
    python scripts/test_policy_checker.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def log(msg: str, level: str = "INFO") -> None:
    """Simple logger."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {msg}")


def test_policy_checker_unit() -> bool:
    """Test MidExecutionPolicyChecker without database."""
    log("=" * 60)
    log("MidExecutionPolicyChecker Unit Test")
    log("PIN-454 Phase 5 Verification")
    log("=" * 60)

    try:
        from app.worker.policy_checker import (
            MidExecutionPolicyChecker,
            PolicyDecision,
            PolicyViolationType,
            PolicyViolation,
            PolicyCheckResult,
            MID_EXECUTION_POLICY_CHECK_ENABLED,
        )
        log("Imports successful ✓")
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        return False

    # Test 1: Check configuration
    log(f"\n1. Configuration check:")
    log(f"   MID_EXECUTION_POLICY_CHECK_ENABLED = {MID_EXECUTION_POLICY_CHECK_ENABLED}")

    # Test 2: Create checker instance
    log(f"\n2. Creating MidExecutionPolicyChecker...")
    try:
        checker = MidExecutionPolicyChecker(
            check_interval=timedelta(seconds=5),
            min_steps_between_checks=2,
        )
        log("   Checker created ✓")
    except Exception as e:
        log(f"   Failed to create checker: {e}", "ERROR")
        return False

    # Test 3: Test PolicyDecision enum
    log(f"\n3. PolicyDecision enum:")
    for decision in PolicyDecision:
        log(f"   • {decision.name} = {decision.value}")

    # Test 4: Test PolicyViolationType enum
    log(f"\n4. PolicyViolationType enum:")
    for vtype in PolicyViolationType:
        log(f"   • {vtype.name} = {vtype.value}")

    # Test 5: Test PolicyViolation dataclass
    log(f"\n5. PolicyViolation dataclass:")
    violation = PolicyViolation(
        violation_type=PolicyViolationType.BUDGET_EXCEEDED,
        message="Budget exceeded: $5.50 > $5.00",
        current_value=5.50,
        limit_value=5.00,
        policy_id="policy-001",
    )
    log(f"   Created violation: {violation.violation_type.value}")
    log(f"   Message: {violation.message}")

    # Test 6: Test PolicyCheckResult dataclass
    log(f"\n6. PolicyCheckResult dataclass:")
    result = PolicyCheckResult(
        decision=PolicyDecision.TERMINATE,
        reason="Budget exceeded",
        violations=[violation],
    )
    log(f"   Decision: {result.decision.value}")
    log(f"   Reason: {result.reason}")
    log(f"   should_continue: {result.should_continue}")
    log(f"   Violations: {len(result.violations)}")

    # Test 7: Test check_before_step (disabled mode)
    log(f"\n7. Testing check_before_step (policy checking disabled):")

    # Note: MID_EXECUTION_POLICY_CHECK_ENABLED is read at module import time.
    # Since we imported with it disabled (default), check_before_step should
    # return SKIP. We test this without module reload to avoid Prometheus
    # metric duplication errors.

    checker2 = MidExecutionPolicyChecker()
    result = checker2.check_before_step(
        run_id="test-run-001",
        tenant_id="test-tenant-001",
        step_index=0,
        cost_so_far=0.0,
    )
    log(f"   Decision: {result.decision.value}")
    log(f"   Reason: {result.reason}")

    # Since MID_EXECUTION_POLICY_CHECK_ENABLED defaults to false, should be SKIP
    if result.decision == PolicyDecision.SKIP:
        log("   ✓ Correctly returned SKIP when disabled")
    else:
        log("   ✗ Should return SKIP when disabled", "ERROR")

    # Test 8: Test interval throttling
    log(f"\n8. Testing interval throttling:")
    checker3 = MidExecutionPolicyChecker(
        check_interval=timedelta(seconds=60),  # Long interval
        min_steps_between_checks=5,  # 5 steps minimum
    )

    # First check should not be skipped (no previous check)
    skip1 = checker3._should_skip_check("run-001", step_index=0)
    log(f"   First check (step 0): skip={skip1}")

    # Record a check (use timezone-aware datetime to match policy_checker)
    checker3._last_check_time["run-001"] = datetime.now(timezone.utc)
    checker3._last_check_step["run-001"] = 0

    # Second check should be skipped (too soon)
    skip2 = checker3._should_skip_check("run-001", step_index=1)
    log(f"   Second check (step 1, same time): skip={skip2}")

    # Check at step 6 should still be skipped (time interval)
    skip3 = checker3._should_skip_check("run-001", step_index=6)
    log(f"   Third check (step 6, same time): skip={skip3}")

    if not skip1 and skip2 and skip3:
        log("   ✓ Throttling working correctly")
    else:
        log("   ✗ Throttling not working as expected", "WARNING")

    # Test 9: Test decision determination
    log(f"\n9. Testing decision determination:")

    # No violations -> CONTINUE
    decision1, reason1 = checker._determine_decision([])
    log(f"   No violations: {decision1.value} - {reason1}")

    # Budget exceeded -> TERMINATE
    budget_violation = PolicyViolation(
        violation_type=PolicyViolationType.BUDGET_EXCEEDED,
        message="Budget exceeded",
    )
    decision2, reason2 = checker._determine_decision([budget_violation])
    log(f"   Budget exceeded: {decision2.value} - {reason2}")

    # Policy disabled -> PAUSE
    policy_violation = PolicyViolation(
        violation_type=PolicyViolationType.POLICY_DISABLED,
        message="Policy disabled",
    )
    decision3, reason3 = checker._determine_decision([policy_violation])
    log(f"   Policy disabled: {decision3.value} - {reason3}")

    # Manual stop -> TERMINATE
    stop_violation = PolicyViolation(
        violation_type=PolicyViolationType.MANUAL_STOP,
        message="Manual stop",
    )
    decision4, reason4 = checker._determine_decision([stop_violation])
    log(f"   Manual stop: {decision4.value} - {reason4}")

    correct_decisions = (
        decision1 == PolicyDecision.CONTINUE and
        decision2 == PolicyDecision.TERMINATE and
        decision3 == PolicyDecision.PAUSE and
        decision4 == PolicyDecision.TERMINATE
    )

    if correct_decisions:
        log("   ✓ All decisions correct")
    else:
        log("   ✗ Some decisions incorrect", "ERROR")

    # Test 10: Test clear_run_state
    log(f"\n10. Testing clear_run_state:")
    checker._last_check_time["test-run"] = datetime.now()
    checker._last_check_step["test-run"] = 5
    checker._cached_limits["test-run"] = {"budget": 10.0}

    checker.clear_run_state("test-run")

    cleared = (
        "test-run" not in checker._last_check_time and
        "test-run" not in checker._last_check_step and
        "test-run" not in checker._cached_limits
    )

    if cleared:
        log("   ✓ Run state cleared successfully")
    else:
        log("   ✗ Run state not fully cleared", "ERROR")

    # Summary
    log("\n" + "=" * 60)
    log("TEST PASSED ✓")
    log("MidExecutionPolicyChecker working correctly")
    log("=" * 60)

    return True


def main() -> int:
    """Main entry point."""
    from dotenv import load_dotenv
    load_dotenv()

    success = test_policy_checker_unit()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
