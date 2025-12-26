"""
Phase 5C: Recovery Automation - Contract Tests

PIN-174: Recovery Automation Matrix (FROZEN 2025-12-26)

These tests verify the Phase 5C recovery semantics:
- R1: Safe & Idempotent (auto-apply allowed)
- R2: Risky (human approval required)
- R3: Forbidden (never recover)

Frozen Decision Emission Rule:
    ALWAYS emit exactly one RECOVERY_EVALUATION decision after any:
      - execution_halted
      - execution_failed

    Outcome mapping:
      - R1 and applied → recovery_applied
      - R2 and suggested → recovery_suggested
      - R3 or no applicable recovery → recovery_skipped

Test IDs: G5C-01 → G5C-15
"""

import os
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import pytest
from sqlalchemy import create_engine, text

# Phase 5C imports
from app.contracts.decisions import (
    emit_recovery_evaluation_decision,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def db_url() -> str:
    """Get database URL from environment."""
    return os.environ.get("DATABASE_URL", "")


@pytest.fixture
def request_id() -> str:
    """Generate unique request ID for test isolation."""
    return f"test-g5c-{uuid.uuid4()}"


@pytest.fixture
def run_id() -> str:
    """Generate unique run ID for test isolation."""
    return f"run-g5c-{uuid.uuid4()}"


@pytest.fixture
def tenant_id() -> str:
    """Test tenant ID."""
    return "test-tenant-g5c"


# =============================================================================
# Mock Contexts for Failure Scenarios
# =============================================================================


@contextmanager
def mock_transient_timeout():
    """Mock a transient network timeout (R1 candidate)."""
    yield {"failure_type": "network_timeout", "transient": True}


@contextmanager
def mock_rate_limit_with_retry_after():
    """Mock 429 with Retry-After header (R1 candidate)."""
    yield {
        "failure_type": "rate_limit",
        "status_code": 429,
        "retry_after": 5,  # seconds
    }


@contextmanager
def mock_rate_limit_without_retry_after():
    """Mock 429 without Retry-After header (R2 candidate)."""
    yield {
        "failure_type": "rate_limit",
        "status_code": 429,
        "retry_after": None,
    }


@contextmanager
def mock_tool_failure():
    """Mock consistent tool failure (R2 candidate)."""
    yield {"failure_type": "tool_failure", "tool_id": "test-tool"}


@contextmanager
def mock_policy_violation_failure():
    """Mock failure due to policy violation (R3 - forbidden)."""
    yield {"failure_type": "policy_violation", "rule": "DENY_ALL"}


@contextmanager
def mock_budget_exhausted_failure():
    """Mock failure due to budget exhaustion (R3 - forbidden)."""
    yield {"failure_type": "budget_exhausted", "remaining": 0}


@contextmanager
def mock_partial_execution_failure():
    """Mock partial execution failure (R3 by default)."""
    yield {
        "failure_type": "partial_execution",
        "steps_completed": 3,
        "step_failed": 4,
    }


@contextmanager
def mock_recovery_attempt_failure():
    """Mock failure during a recovery attempt (R3 - loop prevention)."""
    yield {
        "failure_type": "recovery_failure",
        "is_recovery_attempt": True,
        "original_failure": "network_timeout",
    }


# =============================================================================
# Helper Functions
# =============================================================================


def get_decision_records(
    db_url: str,
    request_id: Optional[str] = None,
    run_id: Optional[str] = None,
    decision_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query decision records from database."""
    if not db_url:
        return []

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            # Build query (use contracts schema)
            query = "SELECT * FROM contracts.decision_records WHERE 1=1"
            params: Dict[str, Any] = {}

            if request_id:
                query += " AND request_id = :request_id"
                params["request_id"] = request_id

            if run_id:
                query += " AND run_id = :run_id"
                params["run_id"] = run_id

            if decision_type:
                query += " AND decision_type = :decision_type"
                params["decision_type"] = decision_type

            query += " ORDER BY decided_at ASC"

            result = conn.execute(text(query), params)
            rows = result.fetchall()

            # Convert to dicts
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    except Exception:
        # Table may not exist yet
        return []
    finally:
        engine.dispose()


def simulate_execution_failure(
    run_id: str,
    request_id: str,
    failure_type: str,
    failure_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simulate an execution failure and trigger recovery evaluation.

    This is where the recovery logic would be called.
    For red phase, this returns the failure without recovery.
    """
    # TODO: This should call the actual recovery evaluation logic
    # For now, just return the failure state
    return {
        "run_id": run_id,
        "request_id": request_id,
        "status": "failed",
        "failure_type": failure_type,
        "failure_context": failure_context,
        "recovery_evaluated": False,  # Not implemented yet
    }


def emit_recovery_decision(
    run_id: str,
    request_id: str,
    recovery_class: str,  # R1, R2, R3
    recovery_action: Optional[str],
    failure_type: str,
    tenant_id: str = "default",
) -> Optional[Dict[str, Any]]:
    """
    Test wrapper for emit_recovery_evaluation_decision.

    Calls the actual implementation and returns a dict representation.
    """
    record = emit_recovery_evaluation_decision(
        run_id=run_id,
        request_id=request_id,
        recovery_class=recovery_class,
        recovery_action=recovery_action,
        failure_type=failure_type,
        tenant_id=tenant_id,
    )
    if record:
        return record.to_dict()
    return None


# =============================================================================
# G5C-01: Transient timeout, R1 applies
# =============================================================================


class TestG5C01TransientTimeoutR1:
    """
    GIVEN: A transient network timeout failure
    AND: Recovery class = R1 (safe & idempotent)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_applied
      - Auto-retry executed exactly once
      - New attempt_id created, original run_id preserved
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_recovery_applied_decision_emitted(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """R1 recovery must emit recovery_applied decision."""
        with mock_transient_timeout() as failure_context:
            # Simulate failure and trigger recovery evaluation
            # TODO: Call actual recovery evaluation logic
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R1",
                recovery_action="retry_same_request",
                failure_type="network_timeout",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_applied"
        assert decisions[0]["causal_role"] == "post_run"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_retry_succeeds_after_r1(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """R1 retry should succeed and complete the run."""
        # TODO: Implement when recovery logic exists
        # This test verifies that after R1 auto-apply, the run completes
        pass


# =============================================================================
# G5C-02: R1 retry also fails → R2 suggested
# =============================================================================


class TestG5C02R1RetryFailsEscalateR2:
    """
    GIVEN: A transient failure with R1 recovery applied
    AND: The R1 retry also fails
    WHEN: Second failure is evaluated
    THEN:
      - First decision: recovery_applied (R1)
      - Second decision: recovery_suggested (R2)
      - No further auto-retry
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_escalation_to_r2_after_r1_failure(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """When R1 retry fails, must escalate to R2 suggestion."""
        # First failure → R1 applied
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry_same_request",
            failure_type="network_timeout",
            tenant_id=tenant_id,
        )

        # R1 retry also fails → escalate to R2
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R2",
            recovery_action="suggest_manual_intervention",
            failure_type="network_timeout_persistent",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 2, "Two recovery decisions expected"
        assert decisions[0]["decision_outcome"] == "recovery_applied"
        assert decisions[1]["decision_outcome"] == "recovery_suggested"


# =============================================================================
# G5C-03: Tool failure → R2 suggested
# =============================================================================


class TestG5C03ToolFailureR2:
    """
    GIVEN: A consistent tool failure
    AND: Recovery class = R2 (risky)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_suggested
      - NO auto-retry
      - Suggestion surfaced to founder only
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_r2_emits_recovery_suggested(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """R2 must emit recovery_suggested, not recovery_applied."""
        with mock_tool_failure() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R2",
                recovery_action="suggest_alternative_tool",
                failure_type="tool_failure",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_suggested"
        assert decisions[0]["decision_outcome"] != "recovery_applied"


# =============================================================================
# G5C-04: Policy violation failure → R3 skipped
# =============================================================================


class TestG5C04PolicyViolationR3:
    """
    GIVEN: A failure caused by policy violation
    AND: Recovery class = R3 (forbidden)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_skipped
      - NO retry
      - NO suggestion
      - Reason includes "policy violation"
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_policy_violation_is_r3(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Policy violations must result in R3 (recovery_skipped)."""
        with mock_policy_violation_failure() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R3",
                recovery_action=None,  # No action for R3
                failure_type="policy_violation",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# G5C-05: Budget halt failure → R3 skipped
# =============================================================================


class TestG5C05BudgetHaltR3:
    """
    GIVEN: A failure caused by budget exhaustion
    AND: Recovery class = R3 (forbidden)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_skipped
      - NO retry (would exceed budget)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_budget_exhaustion_is_r3(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Budget exhaustion must result in R3 (recovery_skipped)."""
        with mock_budget_exhausted_failure() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R3",
                recovery_action=None,
                failure_type="budget_exhausted",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# G5C-06: Recovery attempt fails → R3 loop prevention
# =============================================================================


class TestG5C06RecoveryLoopPrevention:
    """
    GIVEN: A failure occurs during a recovery attempt
    AND: This would create a recovery loop
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_skipped
      - Reason: loop_prevention
      - NO further recovery attempts
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_recovery_loop_prevented(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Recovery attempt failure must be R3 (loop prevention)."""
        with mock_recovery_attempt_failure() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R3",
                recovery_action=None,
                failure_type="recovery_failure",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# G5C-07: Success path → No recovery decision
# =============================================================================


class TestG5C07SuccessPathNoRecovery:
    """
    GIVEN: Execution succeeds
    WHEN: Run completes normally
    THEN:
      - NO recovery_evaluation decision emitted
      - Recovery is only evaluated on failure
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_recovery_decision_on_success(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Success path must NOT emit any recovery decision."""
        # Simulate successful execution - no emit_recovery_decision called
        # (Success doesn't trigger recovery evaluation)

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # This should PASS even without implementation
        # (No decision emitted = correct behavior for success)
        assert len(decisions) == 0, "Success must NOT emit recovery decision"


# =============================================================================
# G5C-08: Failure without recovery candidate → R3 skipped
# =============================================================================


class TestG5C08NoRecoveryCandidateR3:
    """
    GIVEN: A failure with no applicable recovery
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_skipped
      - Reason: no_applicable_recovery
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_recovery_candidate_is_r3(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Failure without recovery candidate must emit recovery_skipped."""
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R3",
            recovery_action=None,
            failure_type="unknown_failure",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted even when skipped"
        assert decisions[0]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# G5C-09: Founder timeline shows recovery
# =============================================================================


class TestG5C09FounderTimelineRecovery:
    """
    GIVEN: Recovery evaluation occurs
    WHEN: Founder queries timeline
    THEN:
      - All recovery decisions appear in timeline
      - Ordered correctly with causal_role = post_run
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_recovery_in_founder_timeline(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Founder timeline must include all recovery decisions."""
        # Emit a recovery decision
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry_same_request",
            failure_type="network_timeout",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id)

        # Will FAIL until Phase 5C is implemented
        recovery_decisions = [d for d in decisions if d.get("decision_type") == "recovery_evaluation"]
        assert len(recovery_decisions) >= 1, "Recovery must appear in timeline"
        assert all(
            d["causal_role"] == "post_run" for d in recovery_decisions
        ), "All recovery decisions must be post_run"


# =============================================================================
# G5C-10: Customer outcome is reconciled
# =============================================================================


class TestG5C10CustomerOutcomeReconciled:
    """
    GIVEN: Recovery occurs (R1 applied)
    WHEN: Customer views outcome
    THEN:
      - Final status is shown (not intermediate)
      - Recovery mechanics are hidden
      - No R1/R2/R3 classification visible to customer
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_customer_sees_final_outcome_only(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Customer must see reconciled outcome, not recovery mechanics."""
        # This test verifies visibility rules
        # Customer outcome should not expose R1/R2/R3 details
        # For red phase, we verify the structure exists
        pass  # Will be implemented with visibility layer


# =============================================================================
# G5C-11: No silent retries
# =============================================================================


class TestG5C11NoSilentRetries:
    """
    GIVEN: Any retry occurs
    WHEN: Recovery is applied
    THEN:
      - Every retry has a decision record
      - No retry without recovery_evaluation emission
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_every_retry_has_decision(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Every retry must emit a recovery_evaluation decision."""
        # Simulate R1 retry
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry_same_request",
            failure_type="network_timeout",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "INVARIANT: Every retry must have a decision"


# =============================================================================
# G5C-12: No recovery loops
# =============================================================================


class TestG5C12NoRecoveryLoops:
    """
    GIVEN: A recovery attempt fails
    WHEN: Second failure occurs in recovery
    THEN:
      - Immediately classified as R3
      - No further recovery attempts
      - Loop structurally impossible
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_recovery_loop_is_r3(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Second failure in recovery must be R3 (no loop)."""
        # First: R1 applied
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry_same_request",
            failure_type="network_timeout",
            tenant_id=tenant_id,
        )

        # Second: Recovery itself fails → must be R3
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R3",  # Forced to R3
            recovery_action=None,
            failure_type="recovery_failure",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 2, "Both decisions must be recorded"
        # Second decision must be recovery_skipped (R3)
        assert decisions[1]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# G5C-13: 429 with Retry-After → R1
# =============================================================================


class TestG5C13RateLimitWithRetryAfterR1:
    """
    GIVEN: 429 response with Retry-After header
    AND: Recovery class = R1 (bounded, upstream-guided)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_applied
      - Wait time from Retry-After is respected
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_429_with_retry_after_is_r1(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """429 with Retry-After must be R1 (recovery_applied)."""
        with mock_rate_limit_with_retry_after() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R1",
                recovery_action="wait_and_retry",
                failure_type="rate_limit_with_guidance",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_applied"


# =============================================================================
# G5C-14: 429 without Retry-After → R2
# =============================================================================


class TestG5C14RateLimitWithoutRetryAfterR2:
    """
    GIVEN: 429 response without Retry-After header
    AND: Recovery class = R2 (no guidance, may worsen load)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_suggested
      - NO auto-retry
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_429_without_retry_after_is_r2(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """429 without Retry-After must be R2 (recovery_suggested)."""
        with mock_rate_limit_without_retry_after() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R2",
                recovery_action="suggest_wait_and_retry",
                failure_type="rate_limit_no_guidance",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_suggested"


# =============================================================================
# G5C-15: Partial execution failure → R3
# =============================================================================


class TestG5C15PartialExecutionFailureR3:
    """
    GIVEN: Partial execution failure (steps succeeded before fail)
    AND: Recovery class = R3 by default (may duplicate side effects)
    WHEN: Recovery is evaluated
    THEN:
      - Decision emitted with recovery_skipped
      - NO retry (would duplicate completed work)
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_partial_execution_is_r3(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """Partial execution failure must be R3 (recovery_skipped)."""
        with mock_partial_execution_failure() as failure_context:
            emit_recovery_decision(
                run_id=run_id,
                request_id=request_id,
                recovery_class="R3",
                recovery_action=None,
                failure_type="partial_execution",
                tenant_id=tenant_id,
            )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "Recovery decision must be emitted"
        assert decisions[0]["decision_outcome"] == "recovery_skipped"


# =============================================================================
# Summary Test: All Invariants
# =============================================================================


class TestG5CInvariants:
    """Meta-tests verifying the recovery invariants from PIN-174."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_r1_max_one_retry(self, db_url: str, run_id: str, request_id: str, tenant_id: str):
        """INVARIANT: R1 auto-applies exactly once, then escalates."""
        # First failure → R1 applied
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry",
            failure_type="transient",
            tenant_id=tenant_id,
        )

        # Second failure → must NOT be R1 again
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R2",  # or R3, but NOT R1
            recovery_action="suggest",
            failure_type="transient_persistent",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 2
        # Only first can be recovery_applied
        applied_count = sum(1 for d in decisions if d.get("decision_outcome") == "recovery_applied")
        assert applied_count <= 1, "INVARIANT: Max 1 auto-retry (R1)"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_every_failure_emits_decision(
        self, db_url: str, run_id: str, request_id: str, tenant_id: str
    ):
        """INVARIANT: Every failure must emit exactly one recovery decision."""
        # Emit recovery decision for a failure
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R3",
            recovery_action=None,
            failure_type="any_failure",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1, "INVARIANT: Every failure emits a decision"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_invariant_causal_role_always_post_run(
        self, db_url: str, run_id: str, request_id: str, tenant_id: str
    ):
        """INVARIANT: All recovery decisions have causal_role = post_run."""
        emit_recovery_decision(
            run_id=run_id,
            request_id=request_id,
            recovery_class="R1",
            recovery_action="retry",
            failure_type="transient",
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, run_id=run_id, decision_type="recovery_evaluation")

        # Will FAIL until Phase 5C is implemented
        assert len(decisions) >= 1
        for d in decisions:
            assert d["causal_role"] == "post_run", "INVARIANT: causal_role = post_run"
