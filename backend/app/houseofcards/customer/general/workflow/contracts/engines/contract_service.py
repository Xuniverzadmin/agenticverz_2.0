# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Contract Service - stateful contract state machine (pure business logic)
# Callers: L3 (adapters), L2 (governance APIs)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)
#
# ==============================================================================
# GOVERNANCE RULE: CONTRACT-STATE-MACHINE (Non-Negotiable)
# ==============================================================================
#
# This service manages System Contract state transitions.
#
# Contract properties:
#   - STATEFUL: Contracts persist and transition through lifecycle
#   - IMMUTABLE POST-TERMINAL: Terminal states cannot revert
#   - AUDIT-ANCHORED: Every transition is recorded
#   - MAY_NOT ENFORCED: Eligibility MAY_NOT is mechanically un-overridable
#
# The Contract Service:
#   - MAY: Create contracts from eligible proposals, transition states
#   - MUST NOT: Create contracts from MAY_NOT verdicts, bypass state machine
#
# Enforcement:
#   - MayNotVerdictError for MAY_NOT attempts (un-overridable)
#   - InvalidTransitionError for state violations
#   - ContractImmutableError for terminal state modifications
#
# Reference: SYSTEM_CONTRACT_OBJECT.md (frozen), part2-design-v1
#
# ==============================================================================

"""
Part-2 Contract Service (L4)

Manages the System Contract state machine - the first stateful component
in the Part-2 governance workflow.

Responsibilities:
1. Create contracts from validated + eligible proposals
2. Enforce state machine transitions
3. Record transition history for audit
4. Enforce terminal state immutability

Invariants (from SYSTEM_CONTRACT_OBJECT.md):
- CONTRACT-001: Status transitions must follow state machine
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job exists
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable
- CONTRACT-006: proposed_changes must validate schema
- CONTRACT-007: confidence_score range [0,1]

MAY_NOT ENFORCEMENT (PIN-291):
- MAY_NOT verdicts are mechanically un-overridable
- No constructor, method, or bypass can create contracts from MAY_NOT
- This is not a business rule; it is a system invariant

Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from app.models.contract import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    AuditVerdict,
    ContractApproval,
    ContractImmutableError,
    ContractSource,
    ContractStatus,
    EligibilityVerdictData,
    InvalidTransitionError,
    MayNotVerdictError,
    RiskLevel,
    TransitionRecord,
    ValidatorVerdictData,
)
from app.services.governance.eligibility_engine import (
    EligibilityDecision,
    EligibilityVerdict,
)
from app.services.governance.validator_service import ValidatorVerdict

# Contract Service version
CONTRACT_SERVICE_VERSION = "1.0.0"


# ==============================================================================
# CONTRACT STATE MACHINE
# ==============================================================================


@dataclass
class ContractState:
    """
    In-memory representation of contract state.

    Used for state machine operations before persistence.
    """

    contract_id: UUID
    version: int
    issue_id: UUID
    source: ContractSource
    status: ContractStatus
    status_reason: Optional[str]
    title: str
    description: Optional[str]
    proposed_changes: dict[str, Any]
    affected_capabilities: list[str]
    risk_level: RiskLevel
    validator_verdict: Optional[ValidatorVerdictData]
    eligibility_verdict: Optional[EligibilityVerdictData]
    confidence_score: Optional[Decimal]
    created_by: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    activation_window_start: Optional[datetime]
    activation_window_end: Optional[datetime]
    execution_constraints: Optional[dict[str, Any]]
    job_id: Optional[UUID]
    audit_verdict: AuditVerdict
    audit_reason: Optional[str]
    audit_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    transition_history: list[TransitionRecord]


class ContractStateMachine:
    """
    State machine for System Contract lifecycle.

    Enforces:
    - CONTRACT-001: Valid transitions only
    - CONTRACT-002: APPROVED requires approved_by
    - CONTRACT-003: ACTIVE requires job_id
    - CONTRACT-004: COMPLETED requires audit_verdict = PASS
    - CONTRACT-005: Terminal states are immutable
    """

    @staticmethod
    def can_transition(
        from_status: ContractStatus,
        to_status: ContractStatus,
    ) -> bool:
        """Check if a transition is valid."""
        valid_targets = VALID_TRANSITIONS.get(from_status, frozenset())
        return to_status in valid_targets

    @staticmethod
    def validate_transition(
        state: ContractState,
        to_status: ContractStatus,
        context: dict[str, Any],
    ) -> None:
        """
        Validate a state transition, raising errors if invalid.

        Args:
            state: Current contract state
            to_status: Target status
            context: Transition context (approved_by, job_id, etc.)

        Raises:
            ContractImmutableError: If contract is in terminal state
            InvalidTransitionError: If transition is invalid
        """
        # CONTRACT-005: Terminal states are immutable
        if state.status in TERMINAL_STATES:
            raise ContractImmutableError(state.contract_id, state.status)

        # CONTRACT-001: Valid transitions only
        if not ContractStateMachine.can_transition(state.status, to_status):
            raise InvalidTransitionError(
                state.status,
                to_status,
                f"No valid transition from {state.status.value} to {to_status.value}",
            )

        # CONTRACT-002: APPROVED requires approved_by
        if to_status == ContractStatus.APPROVED:
            if not context.get("approved_by"):
                raise InvalidTransitionError(
                    state.status,
                    to_status,
                    "APPROVED requires approved_by",
                )

        # CONTRACT-003: ACTIVE requires job exists
        if to_status == ContractStatus.ACTIVE:
            if not context.get("job_id"):
                raise InvalidTransitionError(
                    state.status,
                    to_status,
                    "ACTIVE requires job_id",
                )

        # CONTRACT-004: COMPLETED requires audit_verdict = PASS
        if to_status == ContractStatus.COMPLETED:
            if context.get("audit_verdict") != AuditVerdict.PASS:
                raise InvalidTransitionError(
                    state.status,
                    to_status,
                    "COMPLETED requires audit_verdict = PASS",
                )

    @staticmethod
    def transition(
        state: ContractState,
        to_status: ContractStatus,
        reason: str,
        transitioned_by: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ContractState:
        """
        Execute a state transition, returning new state.

        Args:
            state: Current contract state
            to_status: Target status
            reason: Reason for transition
            transitioned_by: Who initiated the transition
            context: Additional transition context

        Returns:
            New ContractState with updated status and history

        Raises:
            ContractImmutableError: If contract is in terminal state
            InvalidTransitionError: If transition is invalid
        """
        context = context or {}

        # Validate transition
        ContractStateMachine.validate_transition(state, to_status, context)

        # Record transition
        now = datetime.now(timezone.utc)
        transition_record = TransitionRecord(
            from_status=state.status.value,
            to_status=to_status.value,
            reason=reason,
            transitioned_by=transitioned_by,
            transitioned_at=now,
        )

        # Create new state with updated values
        new_history = state.transition_history + [transition_record]

        # Build updated state
        updated_state = ContractState(
            contract_id=state.contract_id,
            version=state.version + 1,
            issue_id=state.issue_id,
            source=state.source,
            status=to_status,
            status_reason=reason,
            title=state.title,
            description=state.description,
            proposed_changes=state.proposed_changes,
            affected_capabilities=state.affected_capabilities,
            risk_level=state.risk_level,
            validator_verdict=state.validator_verdict,
            eligibility_verdict=state.eligibility_verdict,
            confidence_score=state.confidence_score,
            created_by=state.created_by,
            approved_by=context.get("approved_by", state.approved_by),
            approved_at=context.get("approved_at", state.approved_at),
            activation_window_start=context.get("activation_window_start", state.activation_window_start),
            activation_window_end=context.get("activation_window_end", state.activation_window_end),
            execution_constraints=context.get("execution_constraints", state.execution_constraints),
            job_id=context.get("job_id", state.job_id),
            audit_verdict=context.get("audit_verdict", state.audit_verdict),
            audit_reason=context.get("audit_reason", state.audit_reason),
            audit_completed_at=context.get("audit_completed_at", state.audit_completed_at),
            created_at=state.created_at,
            updated_at=now,
            expires_at=state.expires_at,
            transition_history=new_history,
        )

        return updated_state


# ==============================================================================
# CONTRACT SERVICE
# ==============================================================================


class ContractService:
    """
    Part-2 Contract Service (L4)

    Manages System Contract lifecycle - the first stateful component
    of the Part-2 governance workflow.

    Key Properties:
    - Consumes validator + eligibility outputs
    - Enforces MAY_NOT mechanically (un-overridable)
    - Implements state machine with invariants
    - No execution logic (that's for Job Executor)

    Reference: SYSTEM_CONTRACT_OBJECT.md, PIN-291
    """

    def __init__(self, service_version: str = CONTRACT_SERVICE_VERSION):
        self._version = service_version
        self._state_machine = ContractStateMachine

    @property
    def version(self) -> str:
        """Return service version."""
        return self._version

    # ==========================================================================
    # CONTRACT CREATION
    # ==========================================================================

    def create_contract(
        self,
        issue_id: UUID,
        source: ContractSource,
        title: str,
        description: Optional[str],
        proposed_changes: dict[str, Any],
        affected_capabilities: list[str],
        risk_level: RiskLevel,
        validator_verdict: ValidatorVerdict,
        eligibility_verdict: EligibilityVerdict,
        created_by: str,
        expires_in_hours: int = 72,
    ) -> ContractState:
        """
        Create a new System Contract from validated + eligible proposal.

        This method REQUIRES:
        1. A ValidatorVerdict (proof of validation)
        2. An EligibilityVerdict with decision = MAY (proof of eligibility)

        MAY_NOT ENFORCEMENT (ABSOLUTE):
        If eligibility_verdict.decision is MAY_NOT, this method raises
        MayNotVerdictError. This is mechanically un-overridable.

        Args:
            issue_id: UUID of the source issue
            source: Issue source classification
            title: Contract title (max 200 chars)
            description: Contract description (optional, max 4000 chars)
            proposed_changes: Schema-validated change proposal
            affected_capabilities: List of affected capabilities
            risk_level: Risk classification
            validator_verdict: Proof of validation (from ValidatorService)
            eligibility_verdict: Proof of eligibility (from EligibilityEngine)
            created_by: Creator identifier
            expires_in_hours: TTL for DRAFT state (default 72)

        Returns:
            ContractState in ELIGIBLE status (bypasses DRAFT and VALIDATED
            since we already have those verdicts)

        Raises:
            MayNotVerdictError: If eligibility_verdict.decision is MAY_NOT
            ValueError: If inputs are invalid
        """
        # ==================================================================
        # MAY_NOT ENFORCEMENT (ABSOLUTE - UN-OVERRIDABLE)
        # ==================================================================
        # This check is the constitutional gate. It cannot be bypassed,
        # overridden, or worked around. If eligibility says MAY_NOT,
        # no contract can be created. Period.
        # ==================================================================
        if eligibility_verdict.decision == EligibilityDecision.MAY_NOT:
            raise MayNotVerdictError(eligibility_verdict.reason)

        # Validate inputs
        if len(title) > 200:
            raise ValueError("Title must be 200 characters or less")
        if description and len(description) > 4000:
            raise ValueError("Description must be 4000 characters or less")
        if validator_verdict.confidence_score < 0 or validator_verdict.confidence_score > 1:
            raise ValueError("Confidence score must be between 0 and 1")

        # Create contract state (starts at ELIGIBLE since we have verdicts)
        now = datetime.now(timezone.utc)
        contract_id = uuid4()

        # Convert verdicts to storable data
        validator_data = ValidatorVerdictData(
            issue_type=validator_verdict.issue_type.value,
            severity=validator_verdict.severity.value,
            affected_capabilities=list(validator_verdict.affected_capabilities),
            recommended_action=validator_verdict.recommended_action.value,
            confidence_score=validator_verdict.confidence_score,
            reason=validator_verdict.reason,
            analyzed_at=validator_verdict.analyzed_at,
            validator_version=validator_verdict.validator_version,
        )

        eligibility_data = EligibilityVerdictData(
            decision=eligibility_verdict.decision.value,
            reason=eligibility_verdict.reason,
            blocking_signals=list(eligibility_verdict.blocking_signals),
            missing_prerequisites=list(eligibility_verdict.missing_prerequisites),
            evaluated_at=eligibility_verdict.evaluated_at,
            rules_version=eligibility_verdict.rules_version,
        )

        # Initial transition record (creation is DRAFT → VALIDATED → ELIGIBLE)
        initial_history = [
            TransitionRecord(
                from_status="NONE",
                to_status=ContractStatus.DRAFT.value,
                reason="Contract created from issue",
                transitioned_by="system",
                transitioned_at=now,
            ),
            TransitionRecord(
                from_status=ContractStatus.DRAFT.value,
                to_status=ContractStatus.VALIDATED.value,
                reason=f"Validated: {validator_verdict.reason}",
                transitioned_by="system",
                transitioned_at=now,
            ),
            TransitionRecord(
                from_status=ContractStatus.VALIDATED.value,
                to_status=ContractStatus.ELIGIBLE.value,
                reason=f"Eligible: {eligibility_verdict.reason}",
                transitioned_by="system",
                transitioned_at=now,
            ),
        ]

        contract_state = ContractState(
            contract_id=contract_id,
            version=1,
            issue_id=issue_id,
            source=source,
            status=ContractStatus.ELIGIBLE,
            status_reason="Ready for founder review",
            title=title,
            description=description,
            proposed_changes=proposed_changes,
            affected_capabilities=affected_capabilities,
            risk_level=risk_level,
            validator_verdict=validator_data,
            eligibility_verdict=eligibility_data,
            confidence_score=validator_verdict.confidence_score,
            created_by=created_by,
            approved_by=None,
            approved_at=None,
            activation_window_start=None,
            activation_window_end=None,
            execution_constraints=None,
            job_id=None,
            audit_verdict=AuditVerdict.PENDING,
            audit_reason=None,
            audit_completed_at=None,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=expires_in_hours),
            transition_history=initial_history,
        )

        return contract_state

    # ==========================================================================
    # STATE TRANSITIONS
    # ==========================================================================

    def approve(
        self,
        state: ContractState,
        approval: ContractApproval,
    ) -> ContractState:
        """
        Approve a contract (Founder Review Gate).

        Args:
            state: Current contract state (must be ELIGIBLE)
            approval: Approval details

        Returns:
            ContractState in APPROVED status

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If not in ELIGIBLE state
        """
        now = datetime.now(timezone.utc)

        context = {
            "approved_by": approval.approved_by,
            "approved_at": now,
            "activation_window_start": now,
            "activation_window_end": now + timedelta(hours=approval.activation_window_hours),
            "execution_constraints": approval.execution_constraints,
        }

        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.APPROVED,
            reason=f"Approved by {approval.approved_by}",
            transitioned_by=approval.approved_by,
            context=context,
        )

    def reject(
        self,
        state: ContractState,
        rejected_by: str,
        reason: str,
    ) -> ContractState:
        """
        Reject a contract.

        Args:
            state: Current contract state
            rejected_by: Who rejected
            reason: Rejection reason

        Returns:
            ContractState in REJECTED status (terminal)

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If transition is invalid
        """
        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.REJECTED,
            reason=reason,
            transitioned_by=rejected_by,
        )

    def activate(
        self,
        state: ContractState,
        job_id: UUID,
        activated_by: str = "system",
    ) -> ContractState:
        """
        Activate a contract (start execution).

        Args:
            state: Current contract state (must be APPROVED)
            job_id: UUID of the governance job
            activated_by: Who activated

        Returns:
            ContractState in ACTIVE status

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If not in APPROVED state
        """
        context = {"job_id": job_id}

        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.ACTIVE,
            reason="Activation window started",
            transitioned_by=activated_by,
            context=context,
        )

    def complete(
        self,
        state: ContractState,
        audit_reason: str,
        completed_by: str = "system",
    ) -> ContractState:
        """
        Complete a contract (job succeeded + audit passed).

        Args:
            state: Current contract state (must be ACTIVE)
            audit_reason: Audit verdict reason
            completed_by: Who completed

        Returns:
            ContractState in COMPLETED status (terminal)

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If not in ACTIVE state or audit not PASS
        """
        now = datetime.now(timezone.utc)

        context = {
            "audit_verdict": AuditVerdict.PASS,
            "audit_reason": audit_reason,
            "audit_completed_at": now,
        }

        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.COMPLETED,
            reason=audit_reason,
            transitioned_by=completed_by,
            context=context,
        )

    def fail(
        self,
        state: ContractState,
        failure_reason: str,
        audit_verdict: AuditVerdict = AuditVerdict.FAIL,
        failed_by: str = "system",
    ) -> ContractState:
        """
        Fail a contract (job failed or audit failed).

        Args:
            state: Current contract state
            failure_reason: Why it failed
            audit_verdict: Audit verdict (FAIL or INCONCLUSIVE)
            failed_by: Who recorded failure

        Returns:
            ContractState in FAILED status (terminal)

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If transition is invalid
        """
        now = datetime.now(timezone.utc)

        context = {
            "audit_verdict": audit_verdict,
            "audit_reason": failure_reason,
            "audit_completed_at": now,
        }

        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.FAILED,
            reason=failure_reason,
            transitioned_by=failed_by,
            context=context,
        )

    def expire(
        self,
        state: ContractState,
        expired_by: str = "system",
    ) -> ContractState:
        """
        Expire a contract (TTL exceeded).

        Args:
            state: Current contract state (must be DRAFT, VALIDATED, or ELIGIBLE)
            expired_by: Who marked as expired

        Returns:
            ContractState in EXPIRED status (terminal)

        Raises:
            ContractImmutableError: If contract is terminal
            InvalidTransitionError: If not in expirable state
        """
        return self._state_machine.transition(
            state=state,
            to_status=ContractStatus.EXPIRED,
            reason="TTL exceeded",
            transitioned_by=expired_by,
        )

    # ==========================================================================
    # QUERY HELPERS
    # ==========================================================================

    def is_terminal(self, state: ContractState) -> bool:
        """Check if contract is in terminal state."""
        return state.status in TERMINAL_STATES

    def is_approved(self, state: ContractState) -> bool:
        """Check if contract is approved (including later states)."""
        return state.status in {
            ContractStatus.APPROVED,
            ContractStatus.ACTIVE,
            ContractStatus.COMPLETED,
        }

    def can_approve(self, state: ContractState) -> bool:
        """Check if contract can be approved."""
        return (
            state.status == ContractStatus.ELIGIBLE
            and state.eligibility_verdict is not None
            and state.eligibility_verdict.decision == EligibilityDecision.MAY.value
        )

    def get_valid_transitions(self, state: ContractState) -> frozenset[ContractStatus]:
        """Get valid transitions from current state."""
        if state.status in TERMINAL_STATES:
            return frozenset()
        return VALID_TRANSITIONS.get(state.status, frozenset())
