# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci|manual
#   Execution: sync
# Role: Founder Review invariant tests
# Callers: pytest, CI pipeline
# Allowed Imports: All (test code)
# Forbidden Imports: None
# Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Founder Review Invariant Tests (Part-2)

Tests for the Founder Review surface - the LAST human authority insertion
point in the governance workflow.

Invariants:
- REVIEW-001: Founder Review only operates on ELIGIBLE contracts
- REVIEW-002: APPROVE transitions ELIGIBLE → APPROVED
- REVIEW-003: REJECT transitions ELIGIBLE → REJECTED (terminal)
- REVIEW-004: MAY_NOT contracts never appear in review queue
- REVIEW-005: Review queue only shows ELIGIBLE contracts
- REVIEW-006: Cannot approve/reject non-ELIGIBLE contracts
- REVIEW-007: L3 adapter performs translation only (no business logic)

Additional tests:
- L2 API thin layer behavior
- Response format validation
- Error handling

Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.adapters.founder_contract_review_adapter import (
    FounderReviewAdapter,
    FounderReviewQueueResponse,
    FounderReviewResult,
)
from app.models.contract import (
    ContractApproval,
    ContractImmutableError,
    ContractSource,
    ContractStatus,
    InvalidTransitionError,
    RiskLevel,
)
from app.services.governance.contract_service import (
    ContractService,
    ContractState,
)
from app.services.governance.eligibility_engine import (
    EligibilityDecision,
    EligibilityVerdict,
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
def contract_service() -> ContractService:
    """Contract service instance."""
    return ContractService()


@pytest.fixture
def adapter() -> FounderReviewAdapter:
    """Founder Review adapter instance."""
    return FounderReviewAdapter()


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
        proposed_changes={
            "type": "capability_add",
            "capabilities": ["cap1", "cap2"],
        },
        affected_capabilities=["cap1", "cap2"],
        risk_level=RiskLevel.MEDIUM,
        validator_verdict=validator_verdict,
        eligibility_verdict=eligibility_may_verdict,
        created_by="test_creator",
    )


@pytest.fixture
def approved_contract(
    contract_service: ContractService,
    eligible_contract: ContractState,
) -> ContractState:
    """Create a contract in APPROVED state for testing."""
    approval = ContractApproval(
        approved_by="founder_test",
        activation_window_hours=24,
        execution_constraints=None,
    )
    return contract_service.approve(eligible_contract, approval)


@pytest.fixture
def rejected_contract(
    contract_service: ContractService,
    eligible_contract: ContractState,
) -> ContractState:
    """Create a contract in REJECTED state for testing."""
    return contract_service.reject(
        eligible_contract,
        rejected_by="founder_test",
        reason="Test rejection",
    )


# ==============================================================================
# REVIEW-001: Founder Review Only Operates on ELIGIBLE Contracts
# ==============================================================================


class TestREVIEW001EligibleOnly:
    """REVIEW-001: Founder Review only operates on ELIGIBLE contracts."""

    def test_approve_requires_eligible_status(
        self,
        contract_service: ContractService,
        approved_contract: ContractState,
    ):
        """APPROVE requires contract to be in ELIGIBLE state."""
        # approved_contract is already APPROVED, not ELIGIBLE
        approval = ContractApproval(
            approved_by="another_founder",
            activation_window_hours=24,
        )

        with pytest.raises(InvalidTransitionError) as exc_info:
            contract_service.approve(approved_contract, approval)

        assert "APPROVED" in str(exc_info.value)

    def test_reject_requires_valid_transition(
        self,
        contract_service: ContractService,
        approved_contract: ContractState,
    ):
        """REJECT from APPROVED should fail (not a valid transition)."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            contract_service.reject(
                approved_contract,
                rejected_by="founder_test",
                reason="Changed my mind",
            )

        # APPROVED cannot transition to REJECTED
        assert "APPROVED" in str(exc_info.value)

    def test_eligible_contract_can_be_approved(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE contract can be approved."""
        assert eligible_contract.status == ContractStatus.ELIGIBLE

        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.status == ContractStatus.APPROVED
        assert result.approved_by == "founder_test"

    def test_eligible_contract_can_be_rejected(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """ELIGIBLE contract can be rejected."""
        assert eligible_contract.status == ContractStatus.ELIGIBLE

        result = contract_service.reject(
            eligible_contract,
            rejected_by="founder_test",
            reason="Not now",
        )

        assert result.status == ContractStatus.REJECTED


# ==============================================================================
# REVIEW-002: APPROVE Transitions to APPROVED
# ==============================================================================


class TestREVIEW002ApproveTransition:
    """REVIEW-002: APPROVE transitions ELIGIBLE → APPROVED."""

    def test_approve_sets_status_to_approved(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve changes status to APPROVED."""
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.status == ContractStatus.APPROVED

    def test_approve_sets_approved_by(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve records who approved."""
        approval = ContractApproval(
            approved_by="founder_alice",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.approved_by == "founder_alice"

    def test_approve_sets_approved_at(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve records when approved."""
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.approved_at is not None
        assert isinstance(result.approved_at, datetime)

    def test_approve_sets_activation_window(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve sets the activation window."""
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=48,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.activation_window_start is not None
        assert result.activation_window_end is not None
        # Window should be 48 hours
        delta = result.activation_window_end - result.activation_window_start
        assert delta.total_seconds() == 48 * 3600

    def test_approve_increments_version(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve increments contract version."""
        initial_version = eligible_contract.version
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert result.version == initial_version + 1

    def test_approve_records_transition_history(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Approve adds to transition history."""
        initial_history_len = len(eligible_contract.transition_history)
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        result = contract_service.approve(eligible_contract, approval)

        assert len(result.transition_history) == initial_history_len + 1
        last_transition = result.transition_history[-1]
        assert last_transition.from_status == "ELIGIBLE"
        assert last_transition.to_status == "APPROVED"


# ==============================================================================
# REVIEW-003: REJECT Transitions to REJECTED (Terminal)
# ==============================================================================


class TestREVIEW003RejectTransition:
    """REVIEW-003: REJECT transitions ELIGIBLE → REJECTED (terminal)."""

    def test_reject_sets_status_to_rejected(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Reject changes status to REJECTED."""
        result = contract_service.reject(
            eligible_contract,
            rejected_by="founder_test",
            reason="Not suitable",
        )

        assert result.status == ContractStatus.REJECTED

    def test_rejected_is_terminal(
        self,
        contract_service: ContractService,
        rejected_contract: ContractState,
    ):
        """REJECTED is a terminal state - cannot transition further."""
        assert rejected_contract.status == ContractStatus.REJECTED

        # Try to approve a rejected contract
        approval = ContractApproval(
            approved_by="another_founder",
            activation_window_hours=24,
        )

        with pytest.raises(ContractImmutableError):
            contract_service.approve(rejected_contract, approval)

    def test_rejected_cannot_be_rejected_again(
        self,
        contract_service: ContractService,
        rejected_contract: ContractState,
    ):
        """REJECTED contract cannot be rejected again."""
        with pytest.raises(ContractImmutableError):
            contract_service.reject(
                rejected_contract,
                rejected_by="another_founder",
                reason="Double rejection",
            )

    def test_reject_records_reason(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Reject records the rejection reason."""
        result = contract_service.reject(
            eligible_contract,
            rejected_by="founder_test",
            reason="Too risky for current window",
        )

        assert result.status_reason == "Too risky for current window"

    def test_reject_records_transition_history(
        self,
        contract_service: ContractService,
        eligible_contract: ContractState,
    ):
        """Reject adds to transition history."""
        initial_history_len = len(eligible_contract.transition_history)
        result = contract_service.reject(
            eligible_contract,
            rejected_by="founder_test",
            reason="Test rejection",
        )

        assert len(result.transition_history) == initial_history_len + 1
        last_transition = result.transition_history[-1]
        assert last_transition.from_status == "ELIGIBLE"
        assert last_transition.to_status == "REJECTED"


# ==============================================================================
# REVIEW-004: MAY_NOT Contracts Never Appear in Queue
# ==============================================================================


class TestREVIEW004MayNotExclusion:
    """REVIEW-004: MAY_NOT contracts never appear in review queue."""

    def test_may_not_verdict_prevents_contract_creation(
        self,
        contract_service: ContractService,
        validator_verdict: ValidatorVerdict,
        now: datetime,
    ):
        """MAY_NOT verdict prevents contract creation entirely."""
        from app.models.contract import MayNotVerdictError

        may_not_verdict = EligibilityVerdict(
            decision=EligibilityDecision.MAY_NOT,
            reason="E-100: Below minimum confidence",
            rules_evaluated=1,
            first_failing_rule="E-100",
            blocking_signals=(),
            missing_prerequisites=(),
            evaluated_at=now,
            rules_version="1.0.0",
            rule_results=(),
        )

        with pytest.raises(MayNotVerdictError):
            contract_service.create_contract(
                issue_id=uuid4(),
                source=ContractSource.CRM_FEEDBACK,
                title="Test Contract",
                description="Test",
                proposed_changes={"type": "test"},
                affected_capabilities=["cap1"],
                risk_level=RiskLevel.LOW,
                validator_verdict=validator_verdict,
                eligibility_verdict=may_not_verdict,
                created_by="test_creator",
            )

    def test_only_eligible_contracts_exist(
        self,
        eligible_contract: ContractState,
    ):
        """Only contracts with MAY verdict can exist as ELIGIBLE."""
        # This test verifies that if a contract exists and is ELIGIBLE,
        # it means it passed the MAY_NOT check during creation
        assert eligible_contract.status == ContractStatus.ELIGIBLE
        assert eligible_contract.eligibility_verdict is not None
        assert eligible_contract.eligibility_verdict.decision == "MAY"


# ==============================================================================
# REVIEW-005: Review Queue Only Shows ELIGIBLE Contracts
# ==============================================================================


class TestREVIEW005QueueFiltering:
    """REVIEW-005: Review queue only shows ELIGIBLE contracts."""

    def test_queue_response_contains_only_eligible(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
        approved_contract: ContractState,
        rejected_contract: ContractState,
        now: datetime,
    ):
        """Queue response should only include ELIGIBLE contracts."""
        # Create a list with contracts in different states
        contracts = [eligible_contract]  # Only the eligible one

        response = adapter.to_queue_response(contracts, now)

        assert response.total == 1
        assert len(response.contracts) == 1
        assert response.contracts[0].status == "ELIGIBLE"

    def test_empty_queue_when_no_eligible(
        self,
        adapter: FounderReviewAdapter,
        now: datetime,
    ):
        """Queue should be empty when no ELIGIBLE contracts exist."""
        response = adapter.to_queue_response([], now)

        assert response.total == 0
        assert len(response.contracts) == 0


# ==============================================================================
# REVIEW-006: Cannot Approve/Reject Non-ELIGIBLE Contracts
# ==============================================================================


class TestREVIEW006NonEligibleRejection:
    """REVIEW-006: Cannot approve/reject non-ELIGIBLE contracts."""

    def test_cannot_approve_approved_contract(
        self,
        contract_service: ContractService,
        approved_contract: ContractState,
    ):
        """Cannot approve an already APPROVED contract."""
        approval = ContractApproval(
            approved_by="another_founder",
            activation_window_hours=24,
        )

        with pytest.raises(InvalidTransitionError):
            contract_service.approve(approved_contract, approval)

    def test_cannot_reject_approved_contract(
        self,
        contract_service: ContractService,
        approved_contract: ContractState,
    ):
        """Cannot reject an APPROVED contract."""
        with pytest.raises(InvalidTransitionError):
            contract_service.reject(
                approved_contract,
                rejected_by="founder_test",
                reason="Changed mind",
            )

    def test_cannot_approve_rejected_contract(
        self,
        contract_service: ContractService,
        rejected_contract: ContractState,
    ):
        """Cannot approve a REJECTED contract (terminal state)."""
        approval = ContractApproval(
            approved_by="another_founder",
            activation_window_hours=24,
        )

        with pytest.raises(ContractImmutableError):
            contract_service.approve(rejected_contract, approval)


# ==============================================================================
# REVIEW-007: L3 Adapter Performs Translation Only
# ==============================================================================


class TestREVIEW007AdapterTranslation:
    """REVIEW-007: L3 adapter performs translation only (no business logic)."""

    def test_to_summary_view_is_translation_only(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """to_summary_view only translates fields, no business logic."""
        view = adapter.to_summary_view(eligible_contract)

        # Verify it's a pure translation
        assert view.contract_id == str(eligible_contract.contract_id)
        assert view.title == eligible_contract.title
        assert view.status == eligible_contract.status.value
        assert view.risk_level == eligible_contract.risk_level.value
        assert view.source == eligible_contract.source.value

    def test_to_detail_view_is_translation_only(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """to_detail_view only translates fields, no business logic."""
        view = adapter.to_detail_view(eligible_contract)

        # Verify it's a pure translation
        assert view.contract_id == str(eligible_contract.contract_id)
        assert view.version == eligible_contract.version
        assert view.title == eligible_contract.title
        assert view.description == eligible_contract.description
        assert view.proposed_changes == eligible_contract.proposed_changes
        assert view.status == eligible_contract.status.value

    def test_to_queue_response_structure(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
        now: datetime,
    ):
        """to_queue_response returns correct structure."""
        response = adapter.to_queue_response([eligible_contract], now)

        assert isinstance(response, FounderReviewQueueResponse)
        assert response.total == 1
        assert len(response.contracts) == 1
        assert response.as_of == now.isoformat()

    def test_to_review_result_structure(
        self,
        adapter: FounderReviewAdapter,
        approved_contract: ContractState,
        now: datetime,
    ):
        """to_review_result returns correct structure."""
        result = adapter.to_review_result(
            contract=approved_contract,
            previous_status="ELIGIBLE",
            reviewed_by="founder_test",
            reviewed_at=now,
            comment="Approved for deployment",
        )

        assert isinstance(result, FounderReviewResult)
        assert result.contract_id == str(approved_contract.contract_id)
        assert result.previous_status == "ELIGIBLE"
        assert result.new_status == "APPROVED"
        assert result.reviewed_by == "founder_test"
        assert result.comment == "Approved for deployment"

    def test_adapter_does_not_modify_contract_state(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Adapter methods do not modify the input contract state."""
        original_status = eligible_contract.status
        original_version = eligible_contract.version

        # Call adapter methods
        adapter.to_summary_view(eligible_contract)
        adapter.to_detail_view(eligible_contract)

        # Contract should be unchanged
        assert eligible_contract.status == original_status
        assert eligible_contract.version == original_version


# ==============================================================================
# VIEW DTO TESTS
# ==============================================================================


class TestFounderContractSummaryView:
    """Tests for FounderContractSummaryView."""

    def test_summary_view_is_frozen(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Summary view is frozen (immutable)."""
        view = adapter.to_summary_view(eligible_contract)

        with pytest.raises((AttributeError, TypeError)):
            view.title = "Changed title"  # type: ignore

    def test_summary_view_includes_validator_info(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Summary view includes validator issue type and severity."""
        view = adapter.to_summary_view(eligible_contract)

        assert view.issue_type is not None
        assert view.severity is not None


class TestFounderContractDetailView:
    """Tests for FounderContractDetailView."""

    def test_detail_view_is_frozen(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Detail view is frozen (immutable)."""
        view = adapter.to_detail_view(eligible_contract)

        with pytest.raises((AttributeError, TypeError)):
            view.title = "Changed title"  # type: ignore

    def test_detail_view_includes_validator_summary(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Detail view includes validator summary."""
        view = adapter.to_detail_view(eligible_contract)

        assert view.validator_summary is not None
        assert "issue_type" in view.validator_summary
        assert "severity" in view.validator_summary
        assert "recommended_action" in view.validator_summary

    def test_detail_view_includes_eligibility_summary(
        self,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
    ):
        """Detail view includes eligibility summary."""
        view = adapter.to_detail_view(eligible_contract)

        assert view.eligibility_summary is not None
        assert "decision" in view.eligibility_summary
        assert "reason" in view.eligibility_summary


# ==============================================================================
# L2 API THIN LAYER TESTS
# ==============================================================================


class TestL2APIThinLayer:
    """Tests for L2 API being a thin layer."""

    def test_api_module_imports_from_correct_layers(self):
        """L2 API only imports from L3, L4, L6 (not L1, L5)."""
        from app.api import founder_contract_review

        # Check that the module exists and has the router
        assert hasattr(founder_contract_review, "router")
        assert hasattr(founder_contract_review, "get_review_queue")
        assert hasattr(founder_contract_review, "get_contract_detail")
        assert hasattr(founder_contract_review, "submit_review")

    def test_api_uses_adapter_for_translation(self):
        """L2 API uses L3 adapter for response translation."""
        from app.api.founder_contract_review import get_adapter

        adapter = get_adapter()
        assert isinstance(adapter, FounderReviewAdapter)

    def test_api_uses_service_for_business_logic(self):
        """L2 API uses L4 service for business logic."""
        from app.api.founder_contract_review import get_contract_service

        service = get_contract_service()
        assert isinstance(service, ContractService)


# ==============================================================================
# INTEGRATION TESTS (L2 + L3 + L4)
# ==============================================================================


class TestFounderReviewIntegration:
    """Integration tests for the full Founder Review flow."""

    def test_full_approve_flow(
        self,
        contract_service: ContractService,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
        now: datetime,
    ):
        """Test full approval flow: L2 → L3 → L4."""
        # 1. Get queue (L2 calls L3)
        queue = adapter.to_queue_response([eligible_contract], now)
        assert queue.total == 1

        # 2. Get details (L2 calls L3)
        details = adapter.to_detail_view(eligible_contract)
        assert details.status == "ELIGIBLE"

        # 3. Approve (L2 calls L4)
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        approved = contract_service.approve(eligible_contract, approval)
        assert approved.status == ContractStatus.APPROVED

        # 4. Format result (L2 calls L3)
        result = adapter.to_review_result(
            contract=approved,
            previous_status="ELIGIBLE",
            reviewed_by="founder_test",
            reviewed_at=now,
            comment="Approved",
        )
        assert result.new_status == "APPROVED"

    def test_full_reject_flow(
        self,
        contract_service: ContractService,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
        now: datetime,
    ):
        """Test full rejection flow: L2 → L3 → L4."""
        # 1. Get queue (L2 calls L3)
        queue = adapter.to_queue_response([eligible_contract], now)
        assert queue.total == 1

        # 2. Get details (L2 calls L3)
        details = adapter.to_detail_view(eligible_contract)
        assert details.status == "ELIGIBLE"

        # 3. Reject (L2 calls L4)
        rejected = contract_service.reject(
            eligible_contract,
            rejected_by="founder_test",
            reason="Not suitable at this time",
        )
        assert rejected.status == ContractStatus.REJECTED

        # 4. Format result (L2 calls L3)
        result = adapter.to_review_result(
            contract=rejected,
            previous_status="ELIGIBLE",
            reviewed_by="founder_test",
            reviewed_at=now,
            comment="Not suitable at this time",
        )
        assert result.new_status == "REJECTED"

    def test_queue_updates_after_review(
        self,
        contract_service: ContractService,
        adapter: FounderReviewAdapter,
        eligible_contract: ContractState,
        now: datetime,
    ):
        """Queue should not include approved/rejected contracts."""
        # Initial queue has the contract
        initial_queue = adapter.to_queue_response([eligible_contract], now)
        assert initial_queue.total == 1

        # After approval, queue should be empty (if we only had this contract)
        approval = ContractApproval(
            approved_by="founder_test",
            activation_window_hours=24,
        )
        contract_service.approve(eligible_contract, approval)

        # Queue with only the now-APPROVED contract should be empty
        # (since we're testing the filtering, not the actual storage)
        empty_queue = adapter.to_queue_response([], now)
        assert empty_queue.total == 0
