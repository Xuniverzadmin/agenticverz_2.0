# Layer: L8 — Catalyst / Verification Tests
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: pytest
#   Execution: sync
# Role: Invariant tests for Rollout Projection Service
# Callers: CI/CD, developers
# Reference: PIN-296, part2-design-v1

"""
Part-2 Rollout Projection Service Invariant Tests

Tests for the rollout projection layer.

This is the FINAL layer of Part-2 governance workflow.

Invariants tested:
- ROLLOUT-001: Projection is read-only
- ROLLOUT-002: Stage advancement requires audit PASS
- ROLLOUT-003: Stage advancement requires stabilization
- ROLLOUT-004: No health degradation during rollout
- ROLLOUT-005: Stages are monotonic
- ROLLOUT-006: Customer sees only current stage facts

Reference: PIN-296, part2-design-v1
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.services.governance.rollout_projection import (
    PROJECTION_VERSION,
    STAGE_ORDER,
    AuditSummary,
    BlastRadius,
    ContractSummary,
    ExecutionSummary,
    RolloutProjectionService,
    RolloutStage,
    StabilizationWindow,
    completion_report_to_dict,
    founder_view_to_dict,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def projection_service():
    """Create rollout projection service for testing."""
    return RolloutProjectionService()


@pytest.fixture
def contract_summary():
    """Create a sample contract summary."""
    return ContractSummary(
        contract_id=uuid4(),
        issue_id=uuid4(),
        title="Enable capability X",
        eligibility_verdict="MAY",
        approved_by="founder_123",
        approved_at=datetime.now(timezone.utc) - timedelta(hours=2),
        affected_capabilities=["capability_x"],
    )


@pytest.fixture
def execution_summary():
    """Create a sample execution summary."""
    now = datetime.now(timezone.utc)
    return ExecutionSummary(
        job_id=uuid4(),
        status="COMPLETED",
        started_at=now - timedelta(hours=1),
        completed_at=now - timedelta(minutes=30),
        steps_executed=3,
        steps_succeeded=3,
    )


@pytest.fixture
def audit_summary_pass():
    """Create a sample passing audit summary."""
    return AuditSummary(
        audit_id=uuid4(),
        verdict="PASS",
        checks_passed=["A-001", "A-002", "A-003", "A-004", "A-005", "A-006", "A-007"],
        checks_failed=[],
        audited_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )


@pytest.fixture
def audit_summary_fail():
    """Create a sample failing audit summary."""
    return AuditSummary(
        audit_id=uuid4(),
        verdict="FAIL",
        checks_passed=["A-001", "A-002", "A-004", "A-005", "A-006", "A-007"],
        checks_failed=["A-003"],
        audited_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )


# ==============================================================================
# ROLLOUT-001: PROJECTION IS READ-ONLY
# ==============================================================================


class TestROLLOUT001ProjectionReadOnly:
    """ROLLOUT-001: Projection is read-only."""

    def test_founder_view_is_frozen(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """FounderRolloutView is a frozen dataclass."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_pass,
        )

        with pytest.raises(FrozenInstanceError):
            view.lineage_complete = False  # type: ignore

    def test_customer_view_is_frozen(
        self,
        projection_service: RolloutProjectionService,
    ):
        """CustomerRolloutView is a frozen dataclass."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.GENERAL,
        )

        with pytest.raises(FrozenInstanceError):
            view.is_available = False  # type: ignore

    def test_completion_report_is_frozen(
        self,
        projection_service: RolloutProjectionService,
    ):
        """GovernanceCompletionReport is a frozen dataclass."""
        report = projection_service.generate_completion_report(
            report_id=uuid4(),
            contract_id=uuid4(),
            audit_verdict="PASS",
            execution_summary={"status": "COMPLETED"},
            health_before={"cap": "HEALTHY"},
            health_after={"cap": "HEALTHY"},
            evidence_refs=["ref1"],
        )

        assert report is not None
        with pytest.raises(FrozenInstanceError):
            report.audit_verdict = "FAIL"  # type: ignore

    def test_blast_radius_is_frozen(self):
        """BlastRadius is a frozen dataclass."""
        br = BlastRadius(
            tenant_count=10,
            customer_segment="beta",
            region="us-east",
            estimated_users=100,
        )

        with pytest.raises(FrozenInstanceError):
            br.tenant_count = 20  # type: ignore

    def test_stabilization_window_is_frozen(self):
        """StabilizationWindow is a frozen dataclass."""
        sw = StabilizationWindow(
            started_at=datetime.now(timezone.utc),
            duration_hours=24,
            elapsed_hours=12.0,
            is_satisfied=False,
            remaining_hours=12.0,
        )

        with pytest.raises(FrozenInstanceError):
            sw.is_satisfied = True  # type: ignore


# ==============================================================================
# ROLLOUT-002: STAGE ADVANCEMENT REQUIRES AUDIT PASS
# ==============================================================================


class TestROLLOUT002AuditPassRequired:
    """ROLLOUT-002: Stage advancement requires audit PASS."""

    def test_pass_audit_allows_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """PASS verdict allows stage advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.PLANNED,
            target_stage=RolloutStage.INTERNAL,
            audit_verdict="PASS",
            stabilization=StabilizationWindow(
                started_at=datetime.now(timezone.utc) - timedelta(hours=25),
                duration_hours=24,
                elapsed_hours=25.0,
                is_satisfied=True,
                remaining_hours=0.0,
            ),
            health_degraded=False,
        )

        assert can_advance is True

    def test_fail_audit_blocks_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """FAIL verdict blocks stage advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.PLANNED,
            target_stage=RolloutStage.INTERNAL,
            audit_verdict="FAIL",
            stabilization=None,
            health_degraded=False,
        )

        assert can_advance is False
        assert "FAIL" in reason

    def test_inconclusive_audit_blocks_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """INCONCLUSIVE verdict blocks stage advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.PLANNED,
            target_stage=RolloutStage.INTERNAL,
            audit_verdict="INCONCLUSIVE",
            stabilization=None,
            health_degraded=False,
        )

        assert can_advance is False
        assert "INCONCLUSIVE" in reason

    def test_completion_report_only_on_pass(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Completion report only generated for PASS verdict."""
        report_pass = projection_service.generate_completion_report(
            report_id=uuid4(),
            contract_id=uuid4(),
            audit_verdict="PASS",
            execution_summary={},
            health_before=None,
            health_after=None,
            evidence_refs=[],
        )

        report_fail = projection_service.generate_completion_report(
            report_id=uuid4(),
            contract_id=uuid4(),
            audit_verdict="FAIL",
            execution_summary={},
            health_before=None,
            health_after=None,
            evidence_refs=[],
        )

        assert report_pass is not None
        assert report_fail is None


# ==============================================================================
# ROLLOUT-003: STAGE ADVANCEMENT REQUIRES STABILIZATION
# ==============================================================================


class TestROLLOUT003StabilizationRequired:
    """ROLLOUT-003: Stage advancement requires stabilization."""

    def test_stabilization_satisfied_allows_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Satisfied stabilization allows advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.LIMITED,
            audit_verdict="PASS",
            stabilization=StabilizationWindow(
                started_at=datetime.now(timezone.utc) - timedelta(hours=30),
                duration_hours=24,
                elapsed_hours=30.0,
                is_satisfied=True,
                remaining_hours=0.0,
            ),
            health_degraded=False,
        )

        assert can_advance is True

    def test_stabilization_not_satisfied_blocks_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Unsatisfied stabilization blocks advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.LIMITED,
            audit_verdict="PASS",
            stabilization=StabilizationWindow(
                started_at=datetime.now(timezone.utc) - timedelta(hours=10),
                duration_hours=24,
                elapsed_hours=10.0,
                is_satisfied=False,
                remaining_hours=14.0,
            ),
            health_degraded=False,
        )

        assert can_advance is False
        assert "Stabilization" in reason
        assert "14.0" in reason

    def test_stabilization_calculation(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """Stabilization is correctly calculated."""
        started_at = datetime.now(timezone.utc) - timedelta(hours=12)

        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_pass,
            current_stage=RolloutStage.INTERNAL,
            stabilization_started_at=started_at,
        )

        assert view.rollout.stabilization is not None
        assert view.rollout.stabilization.elapsed_hours >= 11.9  # ~12 hours
        assert view.rollout.stabilization.is_satisfied is False
        assert view.rollout.stabilization.remaining_hours >= 11.0


# ==============================================================================
# ROLLOUT-004: NO HEALTH DEGRADATION DURING ROLLOUT
# ==============================================================================


class TestROLLOUT004NoHealthDegradation:
    """ROLLOUT-004: No health degradation during rollout."""

    def test_health_degradation_blocks_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Health degradation blocks stage advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.LIMITED,
            audit_verdict="PASS",
            stabilization=StabilizationWindow(
                started_at=datetime.now(timezone.utc) - timedelta(hours=30),
                duration_hours=24,
                elapsed_hours=30.0,
                is_satisfied=True,
                remaining_hours=0.0,
            ),
            health_degraded=True,  # Health degraded!
        )

        assert can_advance is False
        assert "Health degradation" in reason

    def test_no_health_degradation_allows_advancement(
        self,
        projection_service: RolloutProjectionService,
    ):
        """No health degradation allows advancement."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.LIMITED,
            audit_verdict="PASS",
            stabilization=StabilizationWindow(
                started_at=datetime.now(timezone.utc) - timedelta(hours=30),
                duration_hours=24,
                elapsed_hours=30.0,
                is_satisfied=True,
                remaining_hours=0.0,
            ),
            health_degraded=False,
        )

        assert can_advance is True


# ==============================================================================
# ROLLOUT-005: STAGES ARE MONOTONIC
# ==============================================================================


class TestROLLOUT005StagesMonotonic:
    """ROLLOUT-005: Stages are monotonic (no regression without new contract)."""

    def test_stage_regression_blocked(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Stage regression is blocked."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.LIMITED,
            target_stage=RolloutStage.INTERNAL,  # Regression!
            audit_verdict="PASS",
            stabilization=None,
            health_degraded=False,
        )

        assert can_advance is False
        assert "regression" in reason.lower()

    def test_stage_same_blocked(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Same stage transition is blocked."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.INTERNAL,  # Same!
            audit_verdict="PASS",
            stabilization=None,
            health_degraded=False,
        )

        assert can_advance is False
        assert "regression" in reason.lower()

    def test_stage_skip_blocked(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Stage skipping is blocked."""
        can_advance, reason = projection_service.can_advance_stage(
            current_stage=RolloutStage.PLANNED,
            target_stage=RolloutStage.LIMITED,  # Skipping INTERNAL!
            audit_verdict="PASS",
            stabilization=None,
            health_degraded=False,
        )

        assert can_advance is False
        assert "skip" in reason.lower()

    def test_stage_order_defined(self):
        """Stage order is properly defined."""
        assert STAGE_ORDER[RolloutStage.NOT_VISIBLE] < STAGE_ORDER[RolloutStage.PLANNED]
        assert STAGE_ORDER[RolloutStage.PLANNED] < STAGE_ORDER[RolloutStage.INTERNAL]
        assert STAGE_ORDER[RolloutStage.INTERNAL] < STAGE_ORDER[RolloutStage.LIMITED]
        assert STAGE_ORDER[RolloutStage.LIMITED] < STAGE_ORDER[RolloutStage.GENERAL]

    def test_planned_stages_progression(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """Planned stages show correct progression."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_pass,
            current_stage=RolloutStage.INTERNAL,
        )

        # After INTERNAL, should be LIMITED, GENERAL
        assert RolloutStage.LIMITED in view.rollout.planned_stages
        assert RolloutStage.GENERAL in view.rollout.planned_stages
        assert RolloutStage.INTERNAL not in view.rollout.planned_stages


# ==============================================================================
# ROLLOUT-006: CUSTOMER SEES ONLY CURRENT STAGE FACTS
# ==============================================================================


class TestROLLOUT006CustomerSeesFactsOnly:
    """ROLLOUT-006: Customer sees only current stage facts."""

    def test_general_stage_shows_available(
        self,
        projection_service: RolloutProjectionService,
    ):
        """GENERAL stage shows capability as available."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.GENERAL,
        )

        assert view.is_available is True
        assert view.availability_reason == "Available"

    def test_limited_stage_shows_select_customers(
        self,
        projection_service: RolloutProjectionService,
    ):
        """LIMITED stage shows select customers message."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.LIMITED,
        )

        assert view.is_available is False
        assert "select customers" in view.availability_reason.lower()

    def test_internal_stage_shows_testing(
        self,
        projection_service: RolloutProjectionService,
    ):
        """INTERNAL stage shows testing message."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.INTERNAL,
        )

        assert view.is_available is False
        assert "testing" in view.availability_reason.lower()

    def test_not_visible_shows_not_available(
        self,
        projection_service: RolloutProjectionService,
    ):
        """NOT_VISIBLE stage shows not available."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.NOT_VISIBLE,
        )

        assert view.is_available is False
        assert "not available" in view.availability_reason.lower()

    def test_customer_view_has_no_audit_details(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Customer view has no audit details."""
        view = projection_service.project_customer_view(
            capability_name="cap_x",
            current_stage=RolloutStage.LIMITED,
        )

        # CustomerRolloutView should not have audit, execution, or contract details
        assert not hasattr(view, "audit")
        assert not hasattr(view, "execution")
        assert not hasattr(view, "contract")


# ==============================================================================
# LINEAGE VERIFICATION
# ==============================================================================


class TestLineageVerification:
    """Test lineage completeness checking."""

    def test_complete_lineage(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """Complete lineage produces no gaps."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_pass,
        )

        assert view.lineage_complete is True
        assert len(view.lineage_gaps) == 0

    def test_missing_approval_gap(
        self,
        projection_service: RolloutProjectionService,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """Missing approval creates lineage gap."""
        contract = ContractSummary(
            contract_id=uuid4(),
            issue_id=uuid4(),
            title="Test",
            eligibility_verdict="MAY",
            approved_by=None,  # Not approved!
            approved_at=None,
            affected_capabilities=["cap"],
        )

        view = projection_service.project_founder_view(
            contract=contract,
            execution=execution_summary,
            audit=audit_summary_pass,
        )

        assert view.lineage_complete is False
        assert "not approved" in view.lineage_gaps[0].lower()

    def test_missing_execution_gap(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        audit_summary_pass: AuditSummary,
    ):
        """Missing execution creates lineage gap."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=None,  # No execution!
            audit=audit_summary_pass,
        )

        assert view.lineage_complete is False
        assert any("execution" in gap.lower() for gap in view.lineage_gaps)

    def test_missing_audit_gap(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
    ):
        """Missing audit creates lineage gap."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=None,  # No audit!
        )

        assert view.lineage_complete is False
        assert any("audit" in gap.lower() for gap in view.lineage_gaps)

    def test_failed_audit_gap(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_fail: AuditSummary,
    ):
        """Failed audit creates lineage gap."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_fail,
        )

        assert view.lineage_complete is False
        assert any("FAIL" in gap for gap in view.lineage_gaps)


# ==============================================================================
# PROJECTION SERVICE METADATA
# ==============================================================================


class TestProjectionServiceMetadata:
    """Projection service metadata tests."""

    def test_service_has_version(self, projection_service: RolloutProjectionService):
        """Service has version property."""
        assert projection_service.version == PROJECTION_VERSION

    def test_custom_version(self):
        """Service can be created with custom version."""
        custom_service = RolloutProjectionService(projection_version="2.0.0")
        assert custom_service.version == "2.0.0"

    def test_custom_stabilization_hours(self):
        """Service can have custom stabilization hours."""
        service = RolloutProjectionService(default_stabilization_hours=48)

        started_at = datetime.now(timezone.utc) - timedelta(hours=30)
        contract = ContractSummary(
            contract_id=uuid4(),
            issue_id=uuid4(),
            title="Test",
            eligibility_verdict="MAY",
            approved_by="founder",
            approved_at=datetime.now(timezone.utc),
            affected_capabilities=["cap"],
        )

        view = service.project_founder_view(
            contract=contract,
            execution=None,
            audit=None,
            current_stage=RolloutStage.INTERNAL,
            stabilization_started_at=started_at,
        )

        # With 48h window and 30h elapsed, should not be satisfied
        assert view.rollout.stabilization is not None
        assert view.rollout.stabilization.is_satisfied is False
        assert view.rollout.stabilization.duration_hours == 48


# ==============================================================================
# SERIALIZATION TESTS
# ==============================================================================


class TestSerialization:
    """Test serialization helpers."""

    def test_founder_view_to_dict(
        self,
        projection_service: RolloutProjectionService,
        contract_summary: ContractSummary,
        execution_summary: ExecutionSummary,
        audit_summary_pass: AuditSummary,
    ):
        """FounderRolloutView can be serialized to dict."""
        view = projection_service.project_founder_view(
            contract=contract_summary,
            execution=execution_summary,
            audit=audit_summary_pass,
        )

        result = founder_view_to_dict(view)

        assert "contract" in result
        assert "execution" in result
        assert "audit" in result
        assert "rollout" in result
        assert "lineage_complete" in result
        assert result["contract"]["contract_id"] == str(contract_summary.contract_id)

    def test_completion_report_to_dict(
        self,
        projection_service: RolloutProjectionService,
    ):
        """GovernanceCompletionReport can be serialized to dict."""
        report = projection_service.generate_completion_report(
            report_id=uuid4(),
            contract_id=uuid4(),
            audit_verdict="PASS",
            execution_summary={"status": "COMPLETED"},
            health_before={"cap": "HEALTHY"},
            health_after={"cap": "HEALTHY"},
            evidence_refs=["ref1", "ref2"],
        )

        assert report is not None
        result = completion_report_to_dict(report)

        assert "report_id" in result
        assert "contract_id" in result
        assert "audit_verdict" in result
        assert result["audit_verdict"] == "PASS"


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


class TestRolloutProjectionIntegration:
    """Integration tests for rollout projection."""

    def test_full_founder_projection_flow(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Full founder projection flow with complete lineage."""
        now = datetime.now(timezone.utc)

        contract = ContractSummary(
            contract_id=uuid4(),
            issue_id=uuid4(),
            title="Enable feature X",
            eligibility_verdict="MAY",
            approved_by="founder_alice",
            approved_at=now - timedelta(days=1),
            affected_capabilities=["feature_x"],
        )

        execution = ExecutionSummary(
            job_id=uuid4(),
            status="COMPLETED",
            started_at=now - timedelta(hours=20),
            completed_at=now - timedelta(hours=19),
            steps_executed=5,
            steps_succeeded=5,
        )

        audit = AuditSummary(
            audit_id=uuid4(),
            verdict="PASS",
            checks_passed=["A-001", "A-002", "A-003", "A-004", "A-005", "A-006", "A-007"],
            checks_failed=[],
            audited_at=now - timedelta(hours=18),
        )

        view = projection_service.project_founder_view(
            contract=contract,
            execution=execution,
            audit=audit,
            current_stage=RolloutStage.INTERNAL,
            stabilization_started_at=now - timedelta(hours=18),
        )

        assert view.lineage_complete is True
        assert view.rollout.current_stage == RolloutStage.INTERNAL
        assert RolloutStage.LIMITED in view.rollout.planned_stages

    def test_stage_advancement_lifecycle(
        self,
        projection_service: RolloutProjectionService,
    ):
        """Test full stage advancement lifecycle."""
        # Stage 1: NOT_VISIBLE -> PLANNED (requires audit PASS)
        can_advance, _ = projection_service.can_advance_stage(
            current_stage=RolloutStage.NOT_VISIBLE,
            target_stage=RolloutStage.PLANNED,
            audit_verdict="PASS",
            stabilization=None,
            health_degraded=False,
        )
        assert can_advance is True

        # Stage 2: PLANNED -> INTERNAL (requires stabilization)
        stabilization = StabilizationWindow(
            started_at=datetime.now(timezone.utc) - timedelta(hours=30),
            duration_hours=24,
            elapsed_hours=30.0,
            is_satisfied=True,
            remaining_hours=0.0,
        )

        can_advance, _ = projection_service.can_advance_stage(
            current_stage=RolloutStage.PLANNED,
            target_stage=RolloutStage.INTERNAL,
            audit_verdict="PASS",
            stabilization=stabilization,
            health_degraded=False,
        )
        assert can_advance is True

        # Stage 3: INTERNAL -> LIMITED
        can_advance, _ = projection_service.can_advance_stage(
            current_stage=RolloutStage.INTERNAL,
            target_stage=RolloutStage.LIMITED,
            audit_verdict="PASS",
            stabilization=stabilization,
            health_degraded=False,
        )
        assert can_advance is True

        # Stage 4: LIMITED -> GENERAL
        can_advance, _ = projection_service.can_advance_stage(
            current_stage=RolloutStage.LIMITED,
            target_stage=RolloutStage.GENERAL,
            audit_verdict="PASS",
            stabilization=stabilization,
            health_degraded=False,
        )
        assert can_advance is True
