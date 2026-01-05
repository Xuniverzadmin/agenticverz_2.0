# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci|manual
#   Execution: sync
# Role: Contract Model invariant tests
# Callers: pytest, CI pipeline
# Allowed Imports: All (test code)
# Forbidden Imports: None
# Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1

"""
Contract Model Invariant Tests (Part-2)

Tests for the 7 CONTRACT invariants defined in SYSTEM_CONTRACT_OBJECT.md:

- CONTRACT-001: Status transitions must follow state machine
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job exists
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable
- CONTRACT-006: proposed_changes must validate schema
- CONTRACT-007: confidence_score range [0,1]

Additional governance tests:
- MAY_NOT enforcement (mechanically un-overridable)
- State machine completeness
- Transition history recording

Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.contract import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    AuditVerdict,
    ContractApproval,
    ContractImmutableError,
    ContractSource,
    ContractStatus,
    InvalidTransitionError,
    MayNotVerdictError,
    RiskLevel,
)
from app.services.governance.contract_service import (
    CONTRACT_SERVICE_VERSION,
    ContractService,
    ContractState,
    ContractStateMachine,
)
from app.services.governance.eligibility_engine import (
    EligibilityDecision,
    EligibilityVerdict,
    RuleResult,
)
from app.services.governance.validator_service import (
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorVerdict,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def now() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def validator_verdict(now: datetime) -> ValidatorVerdict:
    """Valid validator verdict for testing."""
    return ValidatorVerdict(
        issue_type=IssueType.CAPABILITY_REQUEST,
        severity=Severity.MEDIUM,
        affected_capabilities=("cap1", "cap2"),
        recommended_action=RecommendedAction.CREATE_CONTRACT,
        confidence_score=Decimal("0.85"),
        reason="Test capability request",
        evidence={"source": "test"},
        analyzed_at=now,
        validator_version="1.0.0",
    )


@pytest.fixture
def eligibility_may_verdict(now: datetime) -> EligibilityVerdict:
    """Eligibility verdict with MAY decision."""
    return EligibilityVerdict(
        decision=EligibilityDecision.MAY,
        reason="All rules passed",
        rules_evaluated=6,
        first_failing_rule=None,
        blocking_signals=(),
        missing_prerequisites=(),
        evaluated_at=now,
        rules_version="1.0.0",
        rule_results=(),
    )


@pytest.fixture
def eligibility_may_not_verdict(now: datetime) -> EligibilityVerdict:
    """Eligibility verdict with MAY_NOT decision."""
    return EligibilityVerdict(
        decision=EligibilityDecision.MAY_NOT,
        reason="E-100: Below minimum confidence",
        rules_evaluated=1,
        first_failing_rule="E-100",
        blocking_signals=(),
        missing_prerequisites=(),
        evaluated_at=now,
        rules_version="1.0.0",
        rule_results=(
            RuleResult(
                rule_id="E-100",
                rule_name="Below Minimum Confidence",
                passed=False,
                reason="Confidence 0.25 < 0.30",
                evidence={},
            ),
        ),
    )


@pytest.fixture
def contract_service() -> ContractService:
    """Contract service instance."""
    return ContractService()


@pytest.fixture
def eligible_contract(
    contract_service: ContractService,
    validator_verdict: ValidatorVerdict,
    eligibility_may_verdict: EligibilityVerdict,
) -> ContractState:
    """Create a contract in ELIGIBLE state for testing."""
    return contract_service.create_contract(
        issue_id=uuid4(),
        source=ContractSource.CRM_FEEDBACK,
        title="Test Contract",
        description="Test description",
        proposed_changes={"type": "capability_enable", "capability_name": "test"},
        affected_capabilities=["test"],
        risk_level=RiskLevel.LOW,
        validator_verdict=validator_verdict,
        eligibility_verdict=eligibility_may_verdict,
        created_by="test_user",
    )


# ==============================================================================
# CONTRACT-001: Status transitions must follow state machine
# ==============================================================================


class TestCONTRACT001ValidTransitions:
    """CONTRACT-001: Status transitions must follow state machine."""

    def test_eligible_to_approved_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE → APPROVED is a valid transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        assert approved.status == ContractStatus.APPROVED
        assert approved.approved_by == "founder"

    def test_approved_to_active_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """APPROVED → ACTIVE is a valid transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        job_id = uuid4()
        active = contract_service.activate(approved, job_id)

        assert active.status == ContractStatus.ACTIVE
        assert active.job_id == job_id

    def test_active_to_completed_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ACTIVE → COMPLETED is a valid transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        completed = contract_service.complete(active, "All checks passed")

        assert completed.status == ContractStatus.COMPLETED
        assert completed.audit_verdict == AuditVerdict.PASS

    def test_active_to_failed_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ACTIVE → FAILED is a valid transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        failed = contract_service.fail(active, "Job failed")

        assert failed.status == ContractStatus.FAILED
        assert failed.audit_verdict == AuditVerdict.FAIL

    def test_eligible_to_rejected_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE → REJECTED is a valid transition."""
        rejected = contract_service.reject(eligible_contract, "founder", "Does not meet requirements")

        assert rejected.status == ContractStatus.REJECTED

    def test_eligible_to_expired_is_valid(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE → EXPIRED is a valid transition."""
        expired = contract_service.expire(eligible_contract)

        assert expired.status == ContractStatus.EXPIRED

    def test_invalid_transition_raises_error(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Invalid transitions raise InvalidTransitionError."""
        # ELIGIBLE → ACTIVE is not valid (must go through APPROVED)
        with pytest.raises(InvalidTransitionError) as exc_info:
            contract_service.activate(eligible_contract, uuid4())

        assert exc_info.value.from_status == ContractStatus.ELIGIBLE
        assert exc_info.value.to_status == ContractStatus.ACTIVE

    def test_invalid_transition_completed_is_rejected(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE → COMPLETED is not valid."""
        with pytest.raises(InvalidTransitionError):
            contract_service.complete(eligible_contract, "Invalid")


# ==============================================================================
# CONTRACT-002: APPROVED requires approved_by
# ==============================================================================


class TestCONTRACT002ApprovedRequiresApprover:
    """CONTRACT-002: APPROVED requires approved_by."""

    def test_approved_has_approved_by(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """APPROVED state has approved_by set."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        assert approved.approved_by == "founder"
        assert approved.approved_at is not None

    def test_approved_requires_approved_by_in_context(self):
        """State machine validation requires approved_by for APPROVED transition."""
        # Create a mock state in ELIGIBLE
        state = ContractState(
            contract_id=uuid4(),
            version=1,
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            status=ContractStatus.ELIGIBLE,
            status_reason=None,
            title="Test",
            description=None,
            proposed_changes={},
            affected_capabilities=[],
            risk_level=RiskLevel.LOW,
            validator_verdict=None,
            eligibility_verdict=None,
            confidence_score=None,
            created_by="test",
            approved_by=None,
            approved_at=None,
            activation_window_start=None,
            activation_window_end=None,
            execution_constraints=None,
            job_id=None,
            audit_verdict=AuditVerdict.PENDING,
            audit_reason=None,
            audit_completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=None,
            transition_history=[],
        )

        # Attempt transition without approved_by
        with pytest.raises(InvalidTransitionError) as exc_info:
            ContractStateMachine.validate_transition(state, ContractStatus.APPROVED, {})

        assert "approved_by" in str(exc_info.value)


# ==============================================================================
# CONTRACT-003: ACTIVE requires job exists
# ==============================================================================


class TestCONTRACT003ActiveRequiresJob:
    """CONTRACT-003: ACTIVE requires job exists."""

    def test_active_has_job_id(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ACTIVE state has job_id set."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        job_id = uuid4()
        active = contract_service.activate(approved, job_id)

        assert active.job_id == job_id

    def test_active_requires_job_id_in_context(self):
        """State machine validation requires job_id for ACTIVE transition."""
        state = ContractState(
            contract_id=uuid4(),
            version=1,
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            status=ContractStatus.APPROVED,
            status_reason=None,
            title="Test",
            description=None,
            proposed_changes={},
            affected_capabilities=[],
            risk_level=RiskLevel.LOW,
            validator_verdict=None,
            eligibility_verdict=None,
            confidence_score=None,
            created_by="test",
            approved_by="founder",
            approved_at=datetime.now(timezone.utc),
            activation_window_start=None,
            activation_window_end=None,
            execution_constraints=None,
            job_id=None,
            audit_verdict=AuditVerdict.PENDING,
            audit_reason=None,
            audit_completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=None,
            transition_history=[],
        )

        # Attempt transition without job_id
        with pytest.raises(InvalidTransitionError) as exc_info:
            ContractStateMachine.validate_transition(state, ContractStatus.ACTIVE, {})

        assert "job_id" in str(exc_info.value)


# ==============================================================================
# CONTRACT-004: COMPLETED requires audit_verdict = PASS
# ==============================================================================


class TestCONTRACT004CompletedRequiresPass:
    """CONTRACT-004: COMPLETED requires audit_verdict = PASS."""

    def test_completed_has_pass_verdict(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """COMPLETED state has audit_verdict = PASS."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        completed = contract_service.complete(active, "All checks passed")

        assert completed.audit_verdict == AuditVerdict.PASS
        assert completed.audit_reason == "All checks passed"

    def test_completed_requires_pass_in_context(self):
        """State machine validation requires audit_verdict = PASS for COMPLETED."""
        state = ContractState(
            contract_id=uuid4(),
            version=1,
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            status=ContractStatus.ACTIVE,
            status_reason=None,
            title="Test",
            description=None,
            proposed_changes={},
            affected_capabilities=[],
            risk_level=RiskLevel.LOW,
            validator_verdict=None,
            eligibility_verdict=None,
            confidence_score=None,
            created_by="test",
            approved_by="founder",
            approved_at=datetime.now(timezone.utc),
            activation_window_start=None,
            activation_window_end=None,
            execution_constraints=None,
            job_id=uuid4(),
            audit_verdict=AuditVerdict.PENDING,
            audit_reason=None,
            audit_completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=None,
            transition_history=[],
        )

        # Attempt transition with FAIL verdict
        with pytest.raises(InvalidTransitionError) as exc_info:
            ContractStateMachine.validate_transition(
                state, ContractStatus.COMPLETED, {"audit_verdict": AuditVerdict.FAIL}
            )

        assert "audit_verdict" in str(exc_info.value) and "PASS" in str(exc_info.value)

    def test_completed_requires_pass_even_with_pending(self):
        """COMPLETED transition with PENDING audit should fail."""
        state = ContractState(
            contract_id=uuid4(),
            version=1,
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            status=ContractStatus.ACTIVE,
            status_reason=None,
            title="Test",
            description=None,
            proposed_changes={},
            affected_capabilities=[],
            risk_level=RiskLevel.LOW,
            validator_verdict=None,
            eligibility_verdict=None,
            confidence_score=None,
            created_by="test",
            approved_by="founder",
            approved_at=datetime.now(timezone.utc),
            activation_window_start=None,
            activation_window_end=None,
            execution_constraints=None,
            job_id=uuid4(),
            audit_verdict=AuditVerdict.PENDING,
            audit_reason=None,
            audit_completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=None,
            transition_history=[],
        )

        # No audit_verdict in context means PENDING, which is not PASS
        with pytest.raises(InvalidTransitionError):
            ContractStateMachine.validate_transition(state, ContractStatus.COMPLETED, {})


# ==============================================================================
# CONTRACT-005: Terminal states are immutable
# ==============================================================================


class TestCONTRACT005TerminalImmutable:
    """CONTRACT-005: Terminal states are immutable."""

    def test_terminal_states_defined(self):
        """Terminal states are correctly defined."""
        assert ContractStatus.COMPLETED in TERMINAL_STATES
        assert ContractStatus.FAILED in TERMINAL_STATES
        assert ContractStatus.REJECTED in TERMINAL_STATES
        assert ContractStatus.EXPIRED in TERMINAL_STATES
        assert len(TERMINAL_STATES) == 4

    def test_completed_cannot_transition(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """COMPLETED contracts cannot transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        completed = contract_service.complete(active, "All checks passed")

        with pytest.raises(ContractImmutableError) as exc_info:
            contract_service.fail(completed, "Attempt to fail completed")

        assert exc_info.value.status == ContractStatus.COMPLETED

    def test_failed_cannot_transition(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """FAILED contracts cannot transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        failed = contract_service.fail(active, "Job failed")

        with pytest.raises(ContractImmutableError):
            contract_service.complete(failed, "Attempt to complete failed")

    def test_rejected_cannot_transition(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """REJECTED contracts cannot transition."""
        rejected = contract_service.reject(eligible_contract, "founder", "Rejected")

        with pytest.raises(ContractImmutableError):
            contract_service.approve(rejected, ContractApproval(approved_by="founder"))

    def test_expired_cannot_transition(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """EXPIRED contracts cannot transition."""
        expired = contract_service.expire(eligible_contract)

        with pytest.raises(ContractImmutableError):
            contract_service.approve(expired, ContractApproval(approved_by="founder"))


# ==============================================================================
# CONTRACT-006: proposed_changes must validate schema
# ==============================================================================


class TestCONTRACT006ProposedChangesSchema:
    """CONTRACT-006: proposed_changes must validate schema."""

    def test_proposed_changes_accepted(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_verdict: EligibilityVerdict,
    ):
        """Valid proposed_changes are accepted."""
        contract = contract_service.create_contract(
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            title="Test Contract",
            description=None,
            proposed_changes={
                "type": "capability_enable",
                "capability_name": "test_capability",
                "target_lifecycle": "PREVIEW",
            },
            affected_capabilities=["test_capability"],
            risk_level=RiskLevel.LOW,
            validator_verdict=validator_verdict,
            eligibility_verdict=eligibility_may_verdict,
            created_by="test_user",
        )

        assert contract.proposed_changes["type"] == "capability_enable"
        assert contract.proposed_changes["capability_name"] == "test_capability"

    def test_proposed_changes_stored(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Proposed changes are stored in contract state."""
        assert eligible_contract.proposed_changes is not None
        assert isinstance(eligible_contract.proposed_changes, dict)


# ==============================================================================
# CONTRACT-007: confidence_score range [0,1]
# ==============================================================================


class TestCONTRACT007ConfidenceRange:
    """CONTRACT-007: confidence_score range [0,1]."""

    def test_confidence_from_validator(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_verdict: EligibilityVerdict,
    ):
        """Confidence score is taken from validator verdict."""
        contract = contract_service.create_contract(
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            title="Test Contract",
            description=None,
            proposed_changes={"type": "test"},
            affected_capabilities=["test"],
            risk_level=RiskLevel.LOW,
            validator_verdict=validator_verdict,
            eligibility_verdict=eligibility_may_verdict,
            created_by="test_user",
        )

        assert contract.confidence_score == Decimal("0.85")

    def test_confidence_below_zero_rejected(
        self,
        contract_service: ContractService,
        eligibility_may_verdict: EligibilityVerdict,
        now: datetime,
    ):
        """Confidence score below 0 is rejected."""
        bad_verdict = ValidatorVerdict(
            issue_type=IssueType.CAPABILITY_REQUEST,
            severity=Severity.MEDIUM,
            affected_capabilities=("cap1",),
            recommended_action=RecommendedAction.CREATE_CONTRACT,
            confidence_score=Decimal("-0.10"),
            reason="Test",
            evidence={},
            analyzed_at=now,
            validator_version="1.0.0",
        )

        with pytest.raises(ValueError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test Contract",
                description=None,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=bad_verdict,
                eligibility_verdict=eligibility_may_verdict,
                created_by="test_user",
            )

        assert "Confidence" in str(exc_info.value)

    def test_confidence_above_one_rejected(
        self,
        contract_service: ContractService,
        eligibility_may_verdict: EligibilityVerdict,
        now: datetime,
    ):
        """Confidence score above 1 is rejected."""
        bad_verdict = ValidatorVerdict(
            issue_type=IssueType.CAPABILITY_REQUEST,
            severity=Severity.MEDIUM,
            affected_capabilities=("cap1",),
            recommended_action=RecommendedAction.CREATE_CONTRACT,
            confidence_score=Decimal("1.50"),
            reason="Test",
            evidence={},
            analyzed_at=now,
            validator_version="1.0.0",
        )

        with pytest.raises(ValueError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test Contract",
                description=None,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=bad_verdict,
                eligibility_verdict=eligibility_may_verdict,
                created_by="test_user",
            )

        assert "Confidence" in str(exc_info.value)


# ==============================================================================
# MAY_NOT ENFORCEMENT (Mechanically Un-overridable)
# ==============================================================================


class TestMayNotEnforcement:
    """MAY_NOT verdicts are mechanically un-overridable."""

    def test_may_not_prevents_contract_creation(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_not_verdict: EligibilityVerdict,
    ):
        """MAY_NOT verdict prevents contract creation."""
        with pytest.raises(MayNotVerdictError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test Contract",
                description=None,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=validator_verdict,
                eligibility_verdict=eligibility_may_not_verdict,
                created_by="test_user",
            )

        assert "MAY_NOT" in str(exc_info.value)

    def test_may_not_error_contains_reason(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_not_verdict: EligibilityVerdict,
    ):
        """MayNotVerdictError contains the eligibility reason."""
        with pytest.raises(MayNotVerdictError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test Contract",
                description=None,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=validator_verdict,
                eligibility_verdict=eligibility_may_not_verdict,
                created_by="test_user",
            )

        assert exc_info.value.reason == eligibility_may_not_verdict.reason

    def test_may_is_required_for_creation(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_verdict: EligibilityVerdict,
    ):
        """MAY verdict is required for contract creation."""
        # This should succeed
        contract = contract_service.create_contract(
            issue_id=uuid4(),
            source=ContractSource.CRM_FEEDBACK,
            title="Test Contract",
            description=None,
            proposed_changes={"type": "test"},
            affected_capabilities=["test"],
            risk_level=RiskLevel.LOW,
            validator_verdict=validator_verdict,
            eligibility_verdict=eligibility_may_verdict,
            created_by="test_user",
        )

        assert contract.status == ContractStatus.ELIGIBLE


# ==============================================================================
# STATE MACHINE COMPLETENESS
# ==============================================================================


class TestStateMachineCompleteness:
    """Test state machine is complete and well-formed."""

    def test_all_statuses_have_transitions_defined(self):
        """All statuses have transition rules defined."""
        for status in ContractStatus:
            assert status in VALID_TRANSITIONS, f"{status} missing from VALID_TRANSITIONS"

    def test_terminal_states_have_no_transitions(self):
        """Terminal states have empty transition sets."""
        for status in TERMINAL_STATES:
            assert VALID_TRANSITIONS[status] == frozenset(), f"Terminal state {status} should have no valid transitions"

    def test_non_terminal_states_have_transitions(self):
        """Non-terminal states have at least one valid transition."""
        non_terminal = set(ContractStatus) - TERMINAL_STATES
        for status in non_terminal:
            assert len(VALID_TRANSITIONS[status]) > 0, f"Non-terminal state {status} should have valid transitions"


# ==============================================================================
# TRANSITION HISTORY RECORDING
# ==============================================================================


class TestTransitionHistory:
    """Test transition history is recorded correctly."""

    def test_creation_records_initial_transitions(
        self,
        eligible_contract: ContractState,
    ):
        """Contract creation records DRAFT → VALIDATED → ELIGIBLE transitions."""
        history = eligible_contract.transition_history

        assert len(history) == 3
        assert history[0].from_status == "NONE"
        assert history[0].to_status == ContractStatus.DRAFT.value
        assert history[1].from_status == ContractStatus.DRAFT.value
        assert history[1].to_status == ContractStatus.VALIDATED.value
        assert history[2].from_status == ContractStatus.VALIDATED.value
        assert history[2].to_status == ContractStatus.ELIGIBLE.value

    def test_approval_records_transition(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approval records the transition."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        history = approved.transition_history
        last_transition = history[-1]

        assert last_transition.from_status == ContractStatus.ELIGIBLE.value
        assert last_transition.to_status == ContractStatus.APPROVED.value
        assert last_transition.transitioned_by == "founder"

    def test_full_lifecycle_records_all_transitions(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Full lifecycle records all transitions."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        completed = contract_service.complete(active, "All checks passed")

        history = completed.transition_history

        # Initial 3 (creation) + approve + activate + complete = 6
        assert len(history) == 6

        statuses = [t.to_status for t in history]
        expected = [
            ContractStatus.DRAFT.value,
            ContractStatus.VALIDATED.value,
            ContractStatus.ELIGIBLE.value,
            ContractStatus.APPROVED.value,
            ContractStatus.ACTIVE.value,
            ContractStatus.COMPLETED.value,
        ]
        assert statuses == expected


# ==============================================================================
# VERSION AND CONFIGURATION
# ==============================================================================


class TestVersionAndConfig:
    """Test version and configuration handling."""

    def test_service_version_returned(self, contract_service: ContractService):
        """Service version is accessible."""
        assert contract_service.version == CONTRACT_SERVICE_VERSION

    def test_service_version_semantic(self):
        """Service version follows semantic versioning."""
        parts = CONTRACT_SERVICE_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ==============================================================================
# INPUT VALIDATION
# ==============================================================================


class TestInputValidation:
    """Test input validation."""

    def test_title_max_length_enforced(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_verdict: EligibilityVerdict,
    ):
        """Title exceeding 200 characters is rejected."""
        long_title = "x" * 201

        with pytest.raises(ValueError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title=long_title,
                description=None,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=validator_verdict,
                eligibility_verdict=eligibility_may_verdict,
                created_by="test_user",
            )

        assert "200" in str(exc_info.value)

    def test_description_max_length_enforced(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        eligibility_may_verdict: EligibilityVerdict,
    ):
        """Description exceeding 4000 characters is rejected."""
        long_desc = "x" * 4001

        with pytest.raises(ValueError) as exc_info:
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test",
                description=long_desc,
                proposed_changes={"type": "test"},
                affected_capabilities=["test"],
                risk_level=RiskLevel.LOW,
                validator_verdict=validator_verdict,
                eligibility_verdict=eligibility_may_verdict,
                created_by="test_user",
            )

        assert "4000" in str(exc_info.value)


# ==============================================================================
# QUERY HELPERS
# ==============================================================================


class TestQueryHelpers:
    """Test query helper methods."""

    def test_is_terminal_for_completed(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """is_terminal returns True for COMPLETED."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)
        active = contract_service.activate(approved, uuid4())
        completed = contract_service.complete(active, "Pass")

        assert contract_service.is_terminal(completed) is True

    def test_is_terminal_for_eligible(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """is_terminal returns False for ELIGIBLE."""
        assert contract_service.is_terminal(eligible_contract) is False

    def test_can_approve_for_eligible(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """can_approve returns True for ELIGIBLE with MAY verdict."""
        assert contract_service.can_approve(eligible_contract) is True

    def test_can_approve_for_approved(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """can_approve returns False for already APPROVED."""
        approval = ContractApproval(approved_by="founder")
        approved = contract_service.approve(eligible_contract, approval)

        assert contract_service.can_approve(approved) is False

    def test_get_valid_transitions(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """get_valid_transitions returns correct transitions for ELIGIBLE."""
        valid = contract_service.get_valid_transitions(eligible_contract)

        assert ContractStatus.APPROVED in valid
        assert ContractStatus.REJECTED in valid
        assert ContractStatus.EXPIRED in valid
        assert ContractStatus.ACTIVE not in valid
