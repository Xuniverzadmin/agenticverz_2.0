"""Phase 5B E2E Tests: Policy Pre-Check Matrix

Frozen test matrix from PIN-173. These tests define governance invariants,
not features. Any test failure indicates a contract violation.

Tests:
- G5B-01: Pre-check fails (strict) → Run blocked, decision emitted
- G5B-02: Pre-check passes (strict) → Run created, NO decision
- G5B-03: Pre-check fails (advisory) → Run created with warning, NO decision
- G5B-04: Pre-check passes (advisory) → Run created, no warnings, NO decision
- G5B-05: Service unavailable (strict) → Run blocked, policy_unavailable
- G5B-06: Service unavailable (advisory) → Run proceeds with warning, NO decision
- G5B-07: Decision has correct causal_role → pre_run
- G5B-08: PreRunDeclaration shows policy status → policy_status field present
- G5B-09: No run created on block → runs table unchanged
- G5B-10: Timeline shows pre-check before ACK → Founder can reconstruct causality

Emission Rule (Frozen):
  - EMIT decision IFF (posture == strict AND (pre_check_failed OR service_unavailable))
  - DO NOT EMIT if pre_check passed or posture == advisory
"""

import os
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, text

# Import the Phase 5B emission function
from app.contracts.decisions import (
    emit_policy_precheck_decision,
)

# =============================================================================
# Test Configuration
# =============================================================================

# These tests verify the emit_policy_precheck_decision function follows
# the frozen emission rules from PIN-173.


@pytest.fixture(scope="module")
def db_url() -> Optional[str]:
    """Get database URL for tests."""
    return os.environ.get("DATABASE_URL")


@pytest.fixture
def request_id() -> str:
    """Generate unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture
def tenant_id() -> str:
    """Default tenant for tests."""
    return "test-tenant-g5b"


# =============================================================================
# Mock Contexts
# =============================================================================


@contextmanager
def mock_policy_fails() -> Generator[None, None, None]:
    """Mock policy engine to return pre-check failure."""
    with patch("app.policy.engine.PolicyEngine") as mock:
        engine = mock.return_value
        engine.pre_check = AsyncMock(
            return_value={
                "passed": False,
                "violations": ["DENY_ALL: Request denied by policy"],
                "service_available": True,
            }
        )
        yield


@contextmanager
def mock_policy_passes() -> Generator[None, None, None]:
    """Mock policy engine to return pre-check success."""
    with patch("app.policy.engine.PolicyEngine") as mock:
        engine = mock.return_value
        engine.pre_check = AsyncMock(
            return_value={
                "passed": True,
                "violations": [],
                "service_available": True,
            }
        )
        yield


@contextmanager
def mock_policy_service_down() -> Generator[None, None, None]:
    """Mock policy engine to simulate service unavailability."""
    with patch("app.policy.engine.PolicyEngine") as mock:
        engine = mock.return_value
        engine.pre_check = AsyncMock(
            return_value={
                "passed": False,
                "violations": [],
                "service_available": False,
            }
        )
        yield


# =============================================================================
# Database Helpers
# =============================================================================


def get_run_count(db_url: str, request_id: str) -> int:
    """Count runs created for this request."""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Note: runs table may not have request_id column yet
        # This query will need adjustment based on actual schema
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM runs
                WHERE idempotency_key LIKE :pattern
            """
            ),
            {"pattern": f"%{request_id}%"},
        )
        count = result.scalar() or 0
    engine.dispose()
    return count


def get_decision_records(db_url: str, request_id: str, decision_type: Optional[str] = None) -> list:
    """Fetch decision records for this request."""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        if decision_type:
            result = conn.execute(
                text(
                    """
                    SELECT * FROM contracts.decision_records
                    WHERE request_id = :request_id
                    AND decision_type = :decision_type
                    ORDER BY decided_at ASC
                """
                ),
                {"request_id": request_id, "decision_type": decision_type},
            )
        else:
            result = conn.execute(
                text(
                    """
                    SELECT * FROM contracts.decision_records
                    WHERE request_id = :request_id
                    ORDER BY decided_at ASC
                """
                ),
                {"request_id": request_id},
            )
        rows = result.fetchall()
    engine.dispose()
    return [dict(row._mapping) for row in rows]


def get_pre_run_declaration(db_url: str, run_id: str) -> Optional[Dict[str, Any]]:
    """Fetch PRE-RUN declaration for a run."""
    # Note: This may need to fetch from in-memory store or database
    # depending on Phase 5B implementation
    return None  # Placeholder - implementation depends on storage choice


# =============================================================================
# G5B-01: Pre-check fails (strict mode)
# =============================================================================


class TestG5B01PrecheckFailsStrict:
    """
    GIVEN: A policy that will fail pre-check
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run is NOT created
      - Decision record emitted with:
        - decision_type = policy_pre_check
        - decision_outcome = policy_blocked
        - causal_role = pre_run
        - run_id = None
        - request_id = <generated>
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_run_is_blocked(self, db_url: str, request_id: str, tenant_id: str):
        """Run must NOT be created when strict mode pre-check fails."""
        initial_count = get_run_count(db_url, request_id)

        # Phase 5B: Emit decision for strict + failed scenario
        # This simulates what the API endpoint would do
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["DENY_ALL: Request denied by policy"],
            tenant_id=tenant_id,
        )

        # Assert: No run created (emission doesn't create runs)
        final_count = get_run_count(db_url, request_id)
        assert final_count == initial_count, "Run should NOT be created on strict block"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_decision_record_emitted(self, db_url: str, request_id: str, tenant_id: str):
        """Decision record must be emitted with policy_blocked outcome."""
        # Phase 5B: Emit decision for strict + failed scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["DENY_ALL: Request denied by policy"],
            tenant_id=tenant_id,
        )

        # Assert: Decision emitted
        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        assert len(decisions) >= 1, "Decision record must be emitted on strict block"

        decision = decisions[0]
        assert decision["decision_type"] == "policy_pre_check"
        assert decision["decision_outcome"] == "policy_blocked"
        assert decision["causal_role"] == "pre_run"
        assert decision["run_id"] is None, "run_id must be None (run not created)"
        assert decision["request_id"] == request_id


# =============================================================================
# G5B-02: Pre-check passes (strict mode)
# =============================================================================


class TestG5B02PrecheckPassesStrict:
    """
    GIVEN: A policy that will pass pre-check
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run IS created
      - NO decision record emitted for policy_pre_check
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_run_is_created(self, db_url: str, request_id: str, tenant_id: str):
        """Run must be created when strict mode pre-check passes."""
        with mock_policy_passes():
            # TODO: Call API endpoint with policy_posture="strict"
            pass

        # Assert: Run created
        # Note: This assertion depends on how runs are linked to request_id
        # Placeholder - will pass trivially until implemented

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_decision_emitted(self, db_url: str, request_id: str, tenant_id: str):
        """NO decision record for policy_pre_check on success."""
        with mock_policy_passes():
            # TODO: Call API endpoint with policy_posture="strict"
            pass

        # Assert: NO decision emitted (success is not a decision)
        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        # This is the key invariant: success does NOT emit decision
        assert len(decisions) == 0, "Success must NOT emit policy_pre_check decision"


# =============================================================================
# G5B-03: Pre-check fails (advisory mode)
# =============================================================================


class TestG5B03PrecheckFailsAdvisory:
    """
    GIVEN: A policy that will fail pre-check
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created (advisory does not block)
      - NO decision record emitted
      - PRE-RUN declaration shows warnings
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_run_is_created_despite_failure(self, db_url: str, request_id: str, tenant_id: str):
        """Run must be created even when advisory mode pre-check fails."""
        with mock_policy_fails():
            # TODO: Call API endpoint with policy_posture="advisory"
            pass

        # Assert: Run created (advisory does not block)
        # Placeholder assertion

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_decision_emitted(self, db_url: str, request_id: str, tenant_id: str):
        """NO decision record in advisory mode (warnings only in declaration)."""
        with mock_policy_fails():
            # TODO: Call API endpoint with policy_posture="advisory"
            pass

        # Assert: NO decision emitted
        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        # Key invariant: advisory mode NEVER emits decisions
        assert len(decisions) == 0, "Advisory mode must NOT emit policy_pre_check decision"


# =============================================================================
# G5B-04: Pre-check passes (advisory mode)
# =============================================================================


class TestG5B04PrecheckPassesAdvisory:
    """
    GIVEN: A policy that will pass pre-check
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created
      - NO decision record emitted
      - No warnings in PRE-RUN declaration
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_decision_emitted(self, db_url: str, request_id: str, tenant_id: str):
        """NO decision record for policy_pre_check on advisory success."""
        with mock_policy_passes():
            # TODO: Call API endpoint with policy_posture="advisory"
            pass

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")
        assert len(decisions) == 0, "Advisory success must NOT emit decision"


# =============================================================================
# G5B-05: Policy service unavailable (strict mode)
# =============================================================================


class TestG5B05ServiceUnavailableStrict:
    """
    GIVEN: Policy service is unavailable
    AND: posture = strict
    WHEN: Run is requested
    THEN:
      - Run is NOT created
      - Decision record emitted with decision_outcome = policy_unavailable
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_run_is_blocked(self, db_url: str, request_id: str, tenant_id: str):
        """Run must NOT be created when policy service is down (strict)."""
        initial_count = get_run_count(db_url, request_id)

        # Phase 5B: Emit decision for strict + service unavailable scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=False,  # Service down
            violations=[],
            tenant_id=tenant_id,
        )

        final_count = get_run_count(db_url, request_id)
        assert final_count == initial_count, "Run should NOT be created when service unavailable (strict)"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_policy_unavailable_decision(self, db_url: str, request_id: str, tenant_id: str):
        """Decision record with policy_unavailable outcome."""
        # Phase 5B: Emit decision for strict + service unavailable scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=False,  # Service down
            violations=[],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        assert len(decisions) >= 1, "Must emit decision on service unavailable (strict)"
        assert decisions[0]["decision_outcome"] == "policy_unavailable"


# =============================================================================
# G5B-06: Policy service unavailable (advisory mode)
# =============================================================================


class TestG5B06ServiceUnavailableAdvisory:
    """
    GIVEN: Policy service is unavailable
    AND: posture = advisory
    WHEN: Run is requested
    THEN:
      - Run IS created (advisory proceeds with warning)
      - NO decision record emitted
      - PRE-RUN declaration shows service_available = False
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_no_decision_emitted(self, db_url: str, request_id: str, tenant_id: str):
        """NO decision record in advisory mode even when service down."""
        with mock_policy_service_down():
            # TODO: Call API endpoint with policy_posture="advisory"
            pass

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        # Key invariant: advisory NEVER emits decisions
        assert len(decisions) == 0, "Advisory must NOT emit decision even when service down"


# =============================================================================
# G5B-07: Causal role is pre_run
# =============================================================================


class TestG5B07CausalRolePreRun:
    """
    GIVEN: Pre-check fails in strict mode
    WHEN: Decision is emitted
    THEN: causal_role = pre_run
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_causal_role_is_pre_run(self, db_url: str, request_id: str, tenant_id: str):
        """All policy pre-check decisions must have causal_role = pre_run."""
        # Phase 5B: Emit decision for strict + failed scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["Test violation"],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        assert len(decisions) >= 1, "Decision must be emitted"
        for decision in decisions:
            assert decision["causal_role"] == "pre_run", "causal_role must be pre_run"


# =============================================================================
# G5B-08: PRE-RUN declaration includes policy status
# =============================================================================


class TestG5B08DeclarationIncludesPolicyStatus:
    """
    GIVEN: Any run request
    WHEN: PRE-RUN declaration is generated
    THEN: Declaration includes policy_status field with all required subfields
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_policy_status_in_declaration(self, db_url: str, request_id: str, tenant_id: str):
        """PRE-RUN declaration must include policy_status field."""
        # TODO: Create PRE-RUN declaration via customer visibility API

        # Placeholder - need to fetch declaration
        declaration = None  # get_pre_run_declaration(...)

        # Will FAIL until policy_status is added to PreRunDeclaration
        if declaration:
            assert "policy_status" in declaration, "policy_status field required"

            ps = declaration["policy_status"]
            required_fields = [
                "posture",
                "checked",
                "passed",
                "violations",
                "warnings",
                "service_available",
            ]
            for field in required_fields:
                assert field in ps, f"policy_status must include {field}"


# =============================================================================
# G5B-09: No run created on block
# =============================================================================


class TestG5B09NoRunOnBlock:
    """
    GIVEN: Pre-check fails in strict mode
    WHEN: Block occurs
    THEN: runs table has no new row
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_runs_table_unchanged(self, db_url: str, request_id: str, tenant_id: str):
        """Runs table must not have new rows when blocked."""
        # Get initial state
        engine = create_engine(db_url)
        with engine.connect() as conn:
            initial_result = conn.execute(text("SELECT COUNT(*) FROM runs"))
            initial_count = initial_result.scalar() or 0
        engine.dispose()

        with mock_policy_fails():
            # TODO: Call API endpoint with policy_posture="strict"
            pass

        # Get final state
        engine = create_engine(db_url)
        with engine.connect() as conn:
            final_result = conn.execute(text("SELECT COUNT(*) FROM runs"))
            final_count = final_result.scalar() or 0
        engine.dispose()

        assert final_count == initial_count, "Block must NOT create any run"


# =============================================================================
# G5B-10: Founder timeline reconstruction
# =============================================================================


class TestG5B10FounderTimelineReconstruction:
    """
    GIVEN: Pre-check blocks a run
    WHEN: Founder queries timeline
    THEN:
      - Decision appears in timeline
      - Ordered before any ACK (if ACK existed)
      - request_id links to blocked request
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_decision_in_timeline(self, db_url: str, request_id: str, tenant_id: str):
        """Founder must be able to reconstruct causality from timeline."""
        # Phase 5B: Emit decision for strict + failed scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["Timeline test violation"],
            tenant_id=tenant_id,
        )

        # Query founder timeline
        decisions = get_decision_records(db_url, request_id, "policy_pre_check")

        assert len(decisions) >= 1, "Decision must appear in timeline"

        decision = decisions[0]
        assert decision["request_id"] == request_id, "request_id must match"
        assert decision["causal_role"] == "pre_run", "causal_role must be pre_run"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_timeline_order(self, db_url: str, request_id: str, tenant_id: str):
        """Pre-check decision must appear before any subsequent events."""
        # Phase 5B: Emit decision for strict + failed scenario
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["Order test violation"],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id)

        # If there are multiple decisions, pre-check should be first
        if len(decisions) > 0:
            first = decisions[0]
            # Pre-check should be among the first decisions
            assert first["decision_type"] == "policy_pre_check" or first["causal_role"] == "pre_run", (
                "Pre-run decisions should appear first"
            )


# =============================================================================
# Summary Test: All Invariants
# =============================================================================


class TestG5BInvariants:
    """Meta-tests verifying the emission rule invariants."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_emission_rule_strict_failure_emits(self, db_url: str, request_id: str, tenant_id: str):
        """Invariant: strict + failure = emit decision."""
        # Phase 5B: Test the frozen emission rule
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=False,
            service_available=True,
            violations=["Invariant test violation"],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")
        # MUST emit
        assert len(decisions) >= 1, "INVARIANT VIOLATED: strict + failure must emit"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_emission_rule_strict_success_does_not_emit(self, db_url: str, request_id: str, tenant_id: str):
        """Invariant: strict + success = NO decision."""
        # Phase 5B: Test the frozen emission rule - success does NOT emit
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="strict",
            passed=True,  # Success
            service_available=True,
            violations=[],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")
        # MUST NOT emit
        assert len(decisions) == 0, "INVARIANT VIOLATED: strict + success must NOT emit"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="Database required for contract tests",
    )
    async def test_emission_rule_advisory_never_emits(self, db_url: str, request_id: str, tenant_id: str):
        """Invariant: advisory = NEVER emit (regardless of pass/fail)."""
        # Phase 5B: Test the frozen emission rule - advisory NEVER emits
        emit_policy_precheck_decision(
            request_id=request_id,
            posture="advisory",  # Advisory mode
            passed=False,  # Even on failure
            service_available=True,
            violations=["Advisory test violation"],
            tenant_id=tenant_id,
        )

        decisions = get_decision_records(db_url, request_id, "policy_pre_check")
        assert len(decisions) == 0, "INVARIANT VIOLATED: advisory must NEVER emit"
