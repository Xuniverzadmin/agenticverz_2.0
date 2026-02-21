# capability_id: CAP-005
# Layer: L3 — Boundary Adapter
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Translate Contract domain models to Founder Review views
# Callers: founder_review.py (L2)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Founder Review Adapter (L3)

Translates L4 Contract domain models to Founder-facing review views.

L4 (ContractService) → L3 (this adapter) → L2 (founder_review.py)

The adapter:
1. Receives ContractState domain models from L4
2. Selects/renames fields for Founder audience
3. Returns FounderReviewView for L2

HARD RULES (from PART2_CRM_WORKFLOW_CHARTER.md):
- NO business logic (that's L4's job)
- NO state transitions (that's L4's job)
- NO eligibility decisions (that's L4's job)
- NO permissions logic (that's L2's job)
- ONLY field selection, translation, formatting

Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

# V2.0.0 - hoc_spine authority
from app.hoc.cus.hoc_spine.authority.contracts import ContractState

# =============================================================================
# L3 VIEW DTOs (Founder-facing, not domain models)
# =============================================================================


@dataclass(frozen=True)
class FounderContractSummaryView:
    """
    Founder-facing contract summary for the review queue.

    This is what Founder Console sees in the list view.
    Distinct from ContractState (L4 domain model).
    """

    contract_id: str
    title: str
    status: str
    risk_level: str
    source: str
    affected_capabilities: List[str]
    confidence_score: Optional[float]
    created_at: str  # ISO8601 string for JSON
    expires_at: Optional[str]  # ISO8601 string for JSON
    issue_type: Optional[str]
    severity: Optional[str]


@dataclass(frozen=True)
class FounderContractDetailView:
    """
    Founder-facing contract detail for review.

    This is what Founder sees when they click into a contract.
    Includes full context for making APPROVE/REJECT decision.
    """

    # Identity
    contract_id: str
    version: int

    # Status
    status: str
    status_reason: Optional[str]

    # Content
    title: str
    description: Optional[str]
    proposed_changes: dict[str, Any]
    affected_capabilities: List[str]
    risk_level: str

    # Validator Summary (what machine analysis found)
    validator_summary: Optional[dict[str, Any]]

    # Eligibility Summary (why this is eligible)
    eligibility_summary: Optional[dict[str, Any]]

    # Confidence
    confidence_score: Optional[float]

    # Origin
    source: str
    issue_id: str
    created_by: str

    # Timing
    created_at: str
    expires_at: Optional[str]

    # Review state (empty until reviewed)
    approved_by: Optional[str]
    approved_at: Optional[str]

    # History
    transition_count: int


@dataclass(frozen=True)
class FounderReviewQueueResponse:
    """
    Response for GET /fdr/contracts/review-queue.

    List of ELIGIBLE contracts awaiting founder review.
    """

    total: int
    contracts: List[FounderContractSummaryView]
    as_of: str  # ISO8601


@dataclass(frozen=True)
class FounderReviewDecision:
    """
    Input for founder review decision.

    This is what L2 receives from the Founder Console.
    """

    decision: str  # "APPROVE" or "REJECT"
    comment: Optional[str]


@dataclass(frozen=True)
class FounderReviewResult:
    """
    Result of a founder review action.

    Returned after APPROVE or REJECT.
    """

    contract_id: str
    previous_status: str
    new_status: str
    reviewed_by: str
    reviewed_at: str
    comment: Optional[str]


# =============================================================================
# L3 ADAPTER CLASS
# =============================================================================


class FounderReviewAdapter:
    """
    Boundary adapter for Founder Review contract views.

    This class provides the ONLY interface that L2 (founder_review.py) may use
    to access Contract data for review. It translates domain models to
    Founder-facing views.

    PIN-293 L3 Rule: Translation only, no business logic.
    """

    def to_summary_view(self, contract: ContractState) -> FounderContractSummaryView:
        """
        Convert a ContractState to Founder-facing summary view.

        Field selection and formatting only.
        """
        # Extract validator info if present
        issue_type = None
        severity = None
        if contract.validator_verdict:
            issue_type = contract.validator_verdict.issue_type
            severity = contract.validator_verdict.severity

        return FounderContractSummaryView(
            contract_id=str(contract.contract_id),
            title=contract.title,
            status=contract.status.value,
            risk_level=contract.risk_level.value,
            source=contract.source.value,
            affected_capabilities=list(contract.affected_capabilities),
            confidence_score=float(contract.confidence_score) if contract.confidence_score else None,
            created_at=contract.created_at.isoformat() if contract.created_at else "",
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            issue_type=issue_type,
            severity=severity,
        )

    def to_detail_view(self, contract: ContractState) -> FounderContractDetailView:
        """
        Convert a ContractState to Founder-facing detail view.

        Full context for review decision.
        """
        # Build validator summary (what the machine found)
        validator_summary = None
        if contract.validator_verdict:
            vv = contract.validator_verdict
            validator_summary = {
                "issue_type": vv.issue_type,
                "severity": vv.severity,
                "recommended_action": vv.recommended_action,
                "confidence_score": float(vv.confidence_score),
                "reason": vv.reason,
                "analyzed_at": vv.analyzed_at.isoformat() if vv.analyzed_at else None,
            }

        # Build eligibility summary (why this is eligible)
        eligibility_summary = None
        if contract.eligibility_verdict:
            ev = contract.eligibility_verdict
            eligibility_summary = {
                "decision": ev.decision,
                "reason": ev.reason,
                "blocking_signals": list(ev.blocking_signals) if ev.blocking_signals else [],
                "missing_prerequisites": list(ev.missing_prerequisites) if ev.missing_prerequisites else [],
                "evaluated_at": ev.evaluated_at.isoformat() if ev.evaluated_at else None,
            }

        return FounderContractDetailView(
            contract_id=str(contract.contract_id),
            version=contract.version,
            status=contract.status.value,
            status_reason=contract.status_reason,
            title=contract.title,
            description=contract.description,
            proposed_changes=contract.proposed_changes,
            affected_capabilities=list(contract.affected_capabilities),
            risk_level=contract.risk_level.value,
            validator_summary=validator_summary,
            eligibility_summary=eligibility_summary,
            confidence_score=float(contract.confidence_score) if contract.confidence_score else None,
            source=contract.source.value,
            issue_id=str(contract.issue_id),
            created_by=contract.created_by,
            created_at=contract.created_at.isoformat() if contract.created_at else "",
            expires_at=contract.expires_at.isoformat() if contract.expires_at else None,
            approved_by=contract.approved_by,
            approved_at=contract.approved_at.isoformat() if contract.approved_at else None,
            transition_count=len(contract.transition_history) if contract.transition_history else 0,
        )

    def to_queue_response(
        self,
        contracts: List[ContractState],
        as_of: datetime,
    ) -> FounderReviewQueueResponse:
        """
        Convert list of ELIGIBLE contracts to review queue response.

        Args:
            contracts: List of ContractState in ELIGIBLE status
            as_of: Timestamp when queue was fetched

        Returns:
            FounderReviewQueueResponse for L2 to return
        """
        summaries = [self.to_summary_view(c) for c in contracts]

        return FounderReviewQueueResponse(
            total=len(summaries),
            contracts=summaries,
            as_of=as_of.isoformat(),
        )

    def to_review_result(
        self,
        contract: ContractState,
        previous_status: str,
        reviewed_by: str,
        reviewed_at: datetime,
        comment: Optional[str],
    ) -> FounderReviewResult:
        """
        Create review result after APPROVE or REJECT.

        Args:
            contract: Updated contract state
            previous_status: Status before review
            reviewed_by: Founder ID who reviewed
            reviewed_at: When review was recorded
            comment: Optional comment from founder

        Returns:
            FounderReviewResult for L2 to return
        """
        return FounderReviewResult(
            contract_id=str(contract.contract_id),
            previous_status=previous_status,
            new_status=contract.status.value,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at.isoformat(),
            comment=comment,
        )
