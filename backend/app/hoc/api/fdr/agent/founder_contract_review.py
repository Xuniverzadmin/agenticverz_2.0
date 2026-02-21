# capability_id: CAP-005
# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: founder-console (fops.agenticverz.com)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Founder Review API - contract approval/rejection gate
# Callers: Founder Console (frontend)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Founder Review API (L2)

Provides Founder-only endpoints for contract review.
This is the LAST human authority insertion point in the governance workflow.

Endpoints:
  GET  /fdr/contracts/review-queue       - List ELIGIBLE contracts
  GET  /fdr/contracts/{contract_id}      - Get contract details
  POST /fdr/contracts/{contract_id}/review - Submit APPROVE or REJECT

Audience: FOUNDER ONLY
Security: Requires Founder authentication

HARD RULES (from PART2_CRM_WORKFLOW_CHARTER.md):
- L2 is a THIN layer: HTTP handling only
- NO business logic (that's L4's job)
- NO state machine implementation (that's L4's job)
- Founder Review may ONLY transition ELIGIBLE → APPROVED or → REJECTED
- MAY_NOT contracts NEVER appear in the queue (enforced by L4)

This API is a "narrow valve":
- Read: Queue of ELIGIBLE contracts, contract details
- Write: APPROVE or REJECT (binary decision)

That's it. No 'update'. No 'edit'. No 'retry'. No 'override'.

Reference: PIN-293, PART2_CRM_WORKFLOW_CHARTER.md
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# L3 imports (allowed)
from app.adapters.founder_contract_review_adapter import (
    FounderReviewAdapter,
)

# Auth imports (FOPS token required for founder-only endpoints)
from app.auth.console_auth import FounderToken, verify_fops_token

# L4 imports (allowed)
from app.models.contract import (
    ContractApproval,
    ContractImmutableError,
    ContractStatus,
    InvalidTransitionError,
)
# V2.0.0 - hoc_spine authority
from app.hoc.cus.hoc_spine.authority.contracts import (
    ContractService,
    ContractState,
)

# L6 imports (allowed)


router = APIRouter(prefix="/fdr/contracts", tags=["founder-review"])


# =============================================================================
# REQUEST/RESPONSE MODELS (Pydantic for OpenAPI docs)
# =============================================================================


class ReviewDecisionRequest(BaseModel):
    """Request body for contract review decision."""

    decision: str = Field(
        ...,
        description="Review decision: 'APPROVE' or 'REJECT'",
        pattern="^(APPROVE|REJECT)$",
    )
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional comment explaining the decision",
    )
    activation_window_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours until activation window expires (for APPROVE only)",
    )


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_contract_service() -> ContractService:
    """Get ContractService instance."""
    return ContractService()


def get_adapter() -> FounderReviewAdapter:
    """Get FounderReviewAdapter instance."""
    return FounderReviewAdapter()


# =============================================================================
# IN-MEMORY STORAGE (TEMPORARY - TO BE REPLACED WITH REPOSITORY)
# =============================================================================
# This is a temporary in-memory store for contracts.
# In production, this will be replaced with a proper repository
# that persists to the database.

_contract_store: Dict[UUID, ContractState] = {}


def get_contract_by_id(contract_id: UUID) -> Optional[ContractState]:
    """Get contract from store by ID."""
    return _contract_store.get(contract_id)


def save_contract(contract: ContractState) -> None:
    """Save contract to store."""
    _contract_store[contract.contract_id] = contract


def get_eligible_contracts() -> List[ContractState]:
    """Get all contracts in ELIGIBLE status."""
    return [c for c in _contract_store.values() if c.status == ContractStatus.ELIGIBLE]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/review-queue", response_model=None)
async def get_review_queue(
    token: FounderToken = Depends(verify_fops_token),
    adapter: FounderReviewAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get the Founder Review Queue.

    Returns all contracts in ELIGIBLE status awaiting founder review.
    MAY_NOT contracts never appear here (enforced by L4).

    Returns:
        FounderReviewQueueResponse with:
        - total: Count of contracts awaiting review
        - contracts: List of contract summaries
        - as_of: Timestamp when queue was fetched

    Audience: Founder only
    """
    eligible_contracts = get_eligible_contracts()
    now = datetime.now(timezone.utc)

    response = adapter.to_queue_response(eligible_contracts, now)

    return _dataclass_to_dict(response)


@router.get("/{contract_id}", response_model=None)
async def get_contract_detail(
    contract_id: UUID,
    token: FounderToken = Depends(verify_fops_token),
    adapter: FounderReviewAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get contract details for review.

    Returns full contract context for making APPROVE/REJECT decision.

    Args:
        contract_id: UUID of the contract

    Returns:
        FounderContractDetailView with full contract context

    Raises:
        404: Contract not found

    Audience: Founder only
    """
    contract = get_contract_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {contract_id} not found",
        )

    view = adapter.to_detail_view(contract)

    return _dataclass_to_dict(view)


@router.post("/{contract_id}/review", response_model=None)
async def submit_review(
    contract_id: UUID,
    request: ReviewDecisionRequest,
    token: FounderToken = Depends(verify_fops_token),
    service: ContractService = Depends(get_contract_service),
    adapter: FounderReviewAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Submit a review decision for a contract.

    This is the Founder Review Gate - the last human authority point
    in the governance workflow.

    Allowed transitions:
    - ELIGIBLE → APPROVED (decision = "APPROVE")
    - ELIGIBLE → REJECTED (decision = "REJECT")

    Args:
        contract_id: UUID of the contract to review
        request: Review decision (APPROVE or REJECT)

    Returns:
        FounderReviewResult with:
        - contract_id: The reviewed contract
        - previous_status: Status before review
        - new_status: Status after review
        - reviewed_by: Founder ID (from auth context)
        - reviewed_at: Timestamp
        - comment: Optional comment

    Raises:
        404: Contract not found
        400: Invalid transition (contract not ELIGIBLE)
        409: Contract in terminal state

    Audience: Founder only
    """
    contract = get_contract_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {contract_id} not found",
        )

    # Capture previous status for response
    previous_status = contract.status.value
    now = datetime.now(timezone.utc)

    # Get founder ID from authenticated token
    founder_id = token.sub

    try:
        if request.decision == "APPROVE":
            # Create approval object for L4
            approval = ContractApproval(
                approved_by=founder_id,
                activation_window_hours=request.activation_window_hours,
                execution_constraints=None,
            )

            # L4 enforces state machine rules
            updated_contract = service.approve(contract, approval)

        elif request.decision == "REJECT":
            # L4 enforces state machine rules
            updated_contract = service.reject(
                contract,
                rejected_by=founder_id,
                reason=request.comment or "Rejected by founder",
            )

        else:
            # This should never happen due to Pydantic validation
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision: {request.decision}. Must be APPROVE or REJECT.",
            )

        # Persist the updated contract
        save_contract(updated_contract)

        # Build response using L3 adapter
        result = adapter.to_review_result(
            contract=updated_contract,
            previous_status=previous_status,
            reviewed_by=founder_id,
            reviewed_at=now,
            comment=request.comment,
        )

        return _dataclass_to_dict(result)

    except ContractImmutableError as e:
        # Contract is in terminal state
        raise HTTPException(
            status_code=409,
            detail=f"Contract {contract_id} is in terminal state and cannot be modified: {e}",
        )

    except InvalidTransitionError as e:
        # Invalid state transition (e.g., not ELIGIBLE)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition: {e}",
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a dataclass to a dictionary, handling nested dataclasses.

    This is a simple recursive conversion for JSON serialization.
    """
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = _dataclass_to_dict(value)
        return result
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _dataclass_to_dict(value) for key, value in obj.items()}
    else:
        return obj


# =============================================================================
# TESTING UTILITIES (L8 - Not for production use)
# =============================================================================


def _inject_test_contract(contract: ContractState) -> None:
    """
    Inject a contract for testing purposes.

    This is an L8 (testing) utility that should NOT be used in production.
    It allows tests to set up contract state without going through
    the full workflow.

    Args:
        contract: ContractState to inject
    """
    _contract_store[contract.contract_id] = contract


def _clear_test_contracts() -> None:
    """
    Clear all contracts from the store.

    This is an L8 (testing) utility for test cleanup.
    """
    _contract_store.clear()


def _get_all_test_contracts() -> Dict[UUID, ContractState]:
    """
    Get all contracts from the store.

    This is an L8 (testing) utility for test verification.
    """
    return _contract_store.copy()
