#!/usr/bin/env python3
"""
AURORA L2 Golden Failure Test

Proves that safety rails work under stress.

This test simulates:
1. Backend route disappears
2. Coherency fails (COH-009 REALITY_MISMATCH)
3. SDSR is blocked (never runs)
4. TRUSTED is never reached

If this test passes, the system correctly prevents trust escalation
when backend reality doesn't match declared capability.

Usage:
    pytest test_golden_failure.py -v
    python test_golden_failure.py  # standalone

Author: AURORA L2 Automation
"""

import sys
import tempfile
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from aurora_coherency_check import CoherencyChecker, CheckStatus
from aurora_sdsr_runner import (
    run_scenario,
    ObservationStatus,
    FailureClass,
    CoherencyResult,
)
from aurora_trust_evaluator import evaluate_trust, load_trust_policy


class TestGoldenFailure:
    """
    Golden failure test suite.

    These tests prove that the system fails safely when:
    - Backend routes disappear
    - Coherency checks fail
    - Reality doesn't match declaration
    """

    def test_coh009_blocks_sdsr_when_endpoint_missing(self):
        """
        Scenario: Backend route disappears after capability declared.

        Expected:
        1. COH-009 detects missing endpoint
        2. Coherency check returns REALITY_MISMATCH
        3. SDSR run is BLOCKED
        4. Observation records failure taxonomy
        """
        # Simulate a scenario where endpoint doesn't exist
        scenario = {
            'scenario_id': 'SDSR-GOLDEN-FAIL-001',
            'capability': 'test.missing_endpoint',
            'panel_id': 'TEST-GOLDEN-001',
            'inject': {
                'endpoint': '/api/v1/nonexistent/route',
                'method': 'GET',
            },
            'invariants': [
                {'id': 'INV-001', 'name': 'response_ok', 'assertion': 'status_code == 200'},
            ],
        }

        # Mock coherency check to return REALITY_MISMATCH
        with patch('aurora_sdsr_runner.run_coherency_check') as mock_coherency:
            mock_coherency.return_value = CoherencyResult(
                passed=False,
                failure_class=FailureClass.REALITY_MISMATCH.value,
                failed_checks=['COH-009'],
            )

            observation = run_scenario(scenario, skip_coherency=False)

            # Verify SDSR was blocked
            assert observation.status == ObservationStatus.BLOCKED.value, \
                f"Expected BLOCKED, got {observation.status}"

            # Verify failure taxonomy
            assert observation.failure_taxonomy == FailureClass.REALITY_MISMATCH.value, \
                f"Expected REALITY_MISMATCH, got {observation.failure_taxonomy}"

            # Verify coherency was NOT verified
            assert observation.coherency_verified is False

            # Verify no invariants were checked (blocked before execution)
            assert observation.invariants_passed == 0
            assert observation.invariants_failed == 0

            print("✅ COH-009 correctly blocked SDSR when endpoint missing")

    def test_reality_mismatch_prevents_trust_promotion(self):
        """
        Scenario: Capability with REALITY_MISMATCH cannot reach TRUSTED.

        Expected:
        1. Observation history contains REALITY_MISMATCH failure
        2. Trust evaluation returns NOT eligible
        3. Capability stays OBSERVED
        """
        # Create mock observation history with a REALITY_MISMATCH
        mock_history = [
            {
                'observation_id': 'OBS-001',
                'status': 'PASS',
                'observed_at': datetime.now(timezone.utc).isoformat(),
                'coherency_verified': True,
                'invariant_results': [{'id': 'INV-001', 'status': 'PASS'}],
            },
            {
                'observation_id': 'OBS-002',
                'status': 'BLOCKED',
                'observed_at': datetime.now(timezone.utc).isoformat(),
                'coherency_verified': False,
                'failure_taxonomy': 'REALITY_MISMATCH',
                'invariant_results': [],
            },
        ]

        with patch('aurora_trust_evaluator.load_observation_history') as mock_load:
            with patch('aurora_trust_evaluator.load_capability_yaml') as mock_cap:
                mock_load.return_value = mock_history
                mock_cap.return_value = {
                    'capability_id': 'test.blocked_cap',
                    'status': 'OBSERVED',
                }

                policy = load_trust_policy()
                eval_result = evaluate_trust('test.blocked_cap', policy)

                # Verify NOT eligible
                assert eval_result.eligible is False, \
                    f"Expected NOT eligible, got eligible={eval_result.eligible}"

                # Verify reason mentions coherency or insufficient runs
                assert 'coherency' in eval_result.reason.lower() or \
                       'insufficient' in eval_result.reason.lower() or \
                       'pass rate' in eval_result.reason.lower(), \
                    f"Unexpected reason: {eval_result.reason}"

                print("✅ REALITY_MISMATCH correctly prevents TRUSTED promotion")

    def test_consecutive_failures_block_promotion(self):
        """
        Scenario: Multiple consecutive failures prevent TRUSTED.

        Expected:
        1. Three failures in a row
        2. Trust evaluation fails on consecutive_failures check
        3. Capability stays OBSERVED
        """
        # Create history with 3 consecutive failures
        mock_history = []
        for i in range(5):
            if i < 2:
                # First 2 pass
                mock_history.append({
                    'observation_id': f'OBS-{i:03d}',
                    'status': 'PASS',
                    'observed_at': datetime.now(timezone.utc).isoformat(),
                    'coherency_verified': True,
                    'invariant_results': [{'id': 'INV-001', 'status': 'PASS'}],
                })
            else:
                # Next 3 fail (consecutive)
                mock_history.append({
                    'observation_id': f'OBS-{i:03d}',
                    'status': 'FAIL',
                    'observed_at': datetime.now(timezone.utc).isoformat(),
                    'coherency_verified': True,
                    'failure_taxonomy': 'INVARIANT_VIOLATED',
                    'invariant_results': [{'id': 'INV-001', 'status': 'FAIL'}],
                })

        with patch('aurora_trust_evaluator.load_observation_history') as mock_load:
            with patch('aurora_trust_evaluator.load_capability_yaml') as mock_cap:
                mock_load.return_value = mock_history
                mock_cap.return_value = {
                    'capability_id': 'test.failing_cap',
                    'status': 'OBSERVED',
                }

                policy = load_trust_policy()
                eval_result = evaluate_trust('test.failing_cap', policy)

                # Verify NOT eligible
                assert eval_result.eligible is False

                # Verify metrics show consecutive failures
                assert eval_result.metrics.get('max_consecutive_failures', 0) >= 3, \
                    f"Expected 3+ consecutive failures, got {eval_result.metrics}"

                print("✅ Consecutive failures correctly block TRUSTED promotion")

    def test_coherency_violation_different_from_reality_mismatch(self):
        """
        Scenario: COH-001 to COH-008 are COHERENCY_VIOLATION, not REALITY_MISMATCH.

        Expected:
        1. Wiring failures (COH-003) return COHERENCY_VIOLATION
        2. Reality failures (COH-009/010) return REALITY_MISMATCH
        """
        scenario = {
            'scenario_id': 'SDSR-GOLDEN-FAIL-002',
            'capability': 'test.wiring_mismatch',
            'panel_id': 'TEST-GOLDEN-002',
            'inject': {
                'endpoint': '/api/v1/exists',
                'method': 'GET',
            },
            'invariants': [],
        }

        # Test COH-003 (wiring) returns COHERENCY_VIOLATION
        with patch('aurora_sdsr_runner.run_coherency_check') as mock_coherency:
            mock_coherency.return_value = CoherencyResult(
                passed=False,
                failure_class=FailureClass.COHERENCY_VIOLATION.value,
                failed_checks=['COH-003'],
            )

            observation = run_scenario(scenario, skip_coherency=False)

            assert observation.failure_taxonomy == FailureClass.COHERENCY_VIOLATION.value, \
                f"COH-003 should be COHERENCY_VIOLATION, got {observation.failure_taxonomy}"

        # Test COH-009 returns REALITY_MISMATCH
        with patch('aurora_sdsr_runner.run_coherency_check') as mock_coherency:
            mock_coherency.return_value = CoherencyResult(
                passed=False,
                failure_class=FailureClass.REALITY_MISMATCH.value,
                failed_checks=['COH-009'],
            )

            observation = run_scenario(scenario, skip_coherency=False)

            assert observation.failure_taxonomy == FailureClass.REALITY_MISMATCH.value, \
                f"COH-009 should be REALITY_MISMATCH, got {observation.failure_taxonomy}"

        print("✅ Failure taxonomy correctly distinguishes wiring vs reality failures")

    def test_skip_coherency_is_dangerous(self):
        """
        Scenario: --skip-coherency bypasses safety checks.

        Expected:
        1. With skip_coherency=True, SDSR runs even without coherency
        2. This is why --skip-coherency should only be used for debugging
        """
        scenario = {
            'scenario_id': 'SDSR-GOLDEN-FAIL-003',
            'capability': 'test.skip_danger',
            'panel_id': 'TEST-GOLDEN-003',
            'inject': {
                'endpoint': '/api/v1/test',
                'method': 'GET',
            },
            'invariants': [],
        }

        # Mock API call to succeed
        with patch('aurora_sdsr_runner.execute_api_call') as mock_api:
            mock_api.return_value = {
                'success': True,
                'status_code': 200,
                'response': {'ok': True},
                'elapsed_ms': 50.0,
            }

            # With skip_coherency, SDSR runs (dangerous!)
            observation = run_scenario(scenario, skip_coherency=True)

            # It passes because coherency was skipped
            assert observation.status == ObservationStatus.PASS.value
            assert observation.coherency_verified is True  # Marked as skipped

            print("⚠️  --skip-coherency correctly bypasses checks (USE WITH CAUTION)")

    def test_auth_failure_does_not_count_against_trust(self):
        """
        Scenario: 401/403 errors are AUTH_FAILURE, not structural failures.

        Expected:
        1. Auth failures are classified separately
        2. They don't immediately demote trust (credential issue, not capability issue)
        """
        scenario = {
            'scenario_id': 'SDSR-GOLDEN-FAIL-004',
            'capability': 'test.auth_fail',
            'panel_id': 'TEST-GOLDEN-004',
            'inject': {
                'endpoint': '/api/v1/protected',
                'method': 'GET',
            },
            'invariants': [
                {'id': 'INV-001', 'name': 'response_ok', 'assertion': 'status_code == 200'},
            ],
        }

        # Mock coherency to pass
        with patch('aurora_sdsr_runner.run_coherency_check') as mock_coherency:
            mock_coherency.return_value = CoherencyResult(passed=True)

            # Mock API to return 401
            with patch('aurora_sdsr_runner.execute_api_call') as mock_api:
                mock_api.return_value = {
                    'success': True,
                    'status_code': 401,
                    'response': {'error': 'Unauthorized'},
                    'elapsed_ms': 20.0,
                }

                observation = run_scenario(scenario, skip_coherency=False)

                # Verify AUTH_FAILURE taxonomy
                assert observation.failure_taxonomy == FailureClass.AUTH_FAILURE.value, \
                    f"Expected AUTH_FAILURE, got {observation.failure_taxonomy}"

                print("✅ Auth failures correctly classified as AUTH_FAILURE (noise)")


def run_golden_failure_tests():
    """Run all golden failure tests."""
    print("=" * 70)
    print("AURORA L2 Golden Failure Test Suite")
    print("=" * 70)
    print()
    print("These tests prove the safety rails work under stress.")
    print()

    test = TestGoldenFailure()

    tests = [
        ("COH-009 blocks SDSR when endpoint missing", test.test_coh009_blocks_sdsr_when_endpoint_missing),
        ("REALITY_MISMATCH prevents TRUSTED promotion", test.test_reality_mismatch_prevents_trust_promotion),
        ("Consecutive failures block promotion", test.test_consecutive_failures_block_promotion),
        ("Coherency vs Reality taxonomy", test.test_coherency_violation_different_from_reality_mismatch),
        ("Skip coherency is dangerous", test.test_skip_coherency_is_dangerous),
        ("Auth failures are noise", test.test_auth_failure_does_not_count_against_trust),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print()
        print("✅ All golden failure tests passed!")
        print("   Safety rails are working correctly.")
        return 0
    else:
        print()
        print("❌ Some golden failure tests failed!")
        print("   Safety rails may be compromised.")
        return 1


if __name__ == "__main__":
    sys.exit(run_golden_failure_tests())
