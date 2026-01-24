# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: Founder-only onboarding recovery actions
# Callers: fops.com (Founder Console)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-399 Phase-4 (Onboarding Failure & Recovery Semantics)

"""
Founder Onboarding Actions API

PIN-399 Phase-4: Provides founder-only recovery actions for onboarding.

This API surfaces ONE mutation endpoint:
- POST /founder/onboarding/force-complete

DESIGN INVARIANTS (Phase-4 Locked):
- ONBOARD-003: Transitions are monotonic (no backward, ever)
- Recovery is forward-only (force-complete is the only mutation)
- Every action is audited (no audit → action fails)
- Founder-only (customer consoles cannot access)
- Explicit justification required

WHAT THIS DOES NOT DO (Explicitly Forbidden):
- No reset to previous state
- No undo onboarding
- No auto-reset after time
- No silent recovery
- No customer-visible override
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..auth.console_auth import FounderToken, verify_fops_token
from ..auth.onboarding_state import OnboardingState
from ..auth.onboarding_transitions import get_onboarding_service
from ..schemas.response import wrap_dict

logger = logging.getLogger("nova.api.founder_onboarding")

router = APIRouter(prefix="/founder/onboarding", tags=["Founder Onboarding"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================


class ForceCompleteRequest(BaseModel):
    """Request to force-complete onboarding for a tenant."""

    tenant_id: str = Field(..., description="Tenant ID to force-complete")
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Explicit justification (required, min 10 chars)",
    )


class ForceCompleteResponse(BaseModel):
    """Response from force-complete action."""

    success: bool
    tenant_id: str
    from_state: str
    to_state: str
    reason: str
    actor_email: str
    timestamp: str
    audit_id: str


class OnboardingRecoveryAuditRecord(BaseModel):
    """Audit record for onboarding recovery actions."""

    event: str = "onboarding_force_complete"
    tenant_id: str
    from_state: str
    to_state: str
    action: str = "force_complete"
    actor_type: str = "founder"
    actor_id: str
    actor_email: str
    reason: str
    timestamp: str


# =============================================================================
# AUDIT LOGGING
# =============================================================================


def emit_recovery_audit(
    tenant_id: str,
    from_state: OnboardingState,
    to_state: OnboardingState,
    actor_id: str,
    actor_email: str,
    reason: str,
) -> str:
    """
    Emit mandatory audit log for recovery action.

    Returns audit_id for response.

    If this function fails to log, the action MUST fail.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_id = f"audit_onb_{tenant_id}_{int(datetime.now(timezone.utc).timestamp())}"

    audit_record = OnboardingRecoveryAuditRecord(
        event="onboarding_force_complete",
        tenant_id=tenant_id,
        from_state=from_state.name,
        to_state=to_state.name,
        action="force_complete",
        actor_type="founder",
        actor_id=actor_id,
        actor_email=actor_email,
        reason=reason,
        timestamp=timestamp,
    )

    # Log as structured JSON for audit trail
    logger.warning(
        "onboarding_recovery_action",
        extra={
            "audit_id": audit_id,
            **audit_record.model_dump(),
        },
    )

    return audit_id


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/force-complete", response_model=ForceCompleteResponse)
async def force_complete_onboarding(
    request: Request,
    body: ForceCompleteRequest,
    token: FounderToken = Depends(verify_fops_token),
):
    """
    Force-complete onboarding for a tenant.

    PIN-399 Phase-4: This is the ONLY recovery mutation allowed.

    Constraints (Non-Negotiable):
    - Founder-only (enforced by verify_fops_token)
    - Explicit justification required (min 10 chars)
    - Fully audited (action fails if audit fails)
    - Forward-only (advances to COMPLETE, never backward)

    Use cases:
    - White-glove onboarding
    - Enterprise customer unblock
    - Contractual exceptions

    This is the escape hatch. Use it wisely.
    """
    tenant_id = body.tenant_id
    reason = body.reason

    # Get current state
    service = get_onboarding_service()
    current_state = await service.get_current_state(tenant_id)

    if current_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )

    # Already complete - no-op
    if current_state == OnboardingState.COMPLETE:
        return ForceCompleteResponse(
            success=True,
            tenant_id=tenant_id,
            from_state=current_state.name,
            to_state=current_state.name,
            reason=reason,
            actor_email=token.email,
            timestamp=datetime.now(timezone.utc).isoformat(),
            audit_id="no_op",
        )

    # Emit audit FIRST (if this fails, action fails)
    try:
        audit_id = emit_recovery_audit(
            tenant_id=tenant_id,
            from_state=current_state,
            to_state=OnboardingState.COMPLETE,
            actor_id=token.user_id,
            actor_email=token.email,
            reason=reason,
        )
    except Exception as e:
        logger.error(f"Failed to emit audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to emit audit log - action aborted",
        )

    # Execute force-complete transition
    result = await service.advance_to_complete(
        tenant_id=tenant_id,
        trigger=f"founder_force_complete:{token.email}",
    )

    if not result.success:
        logger.error(
            "force_complete_failed",
            extra={
                "tenant_id": tenant_id,
                "from_state": current_state.name,
                "error": result.message,
                "audit_id": audit_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Force-complete failed: {result.message}",
        )

    logger.info(
        "force_complete_succeeded",
        extra={
            "tenant_id": tenant_id,
            "from_state": result.from_state.name,
            "to_state": result.to_state.name,
            "actor_email": token.email,
            "audit_id": audit_id,
        },
    )

    return ForceCompleteResponse(
        success=True,
        tenant_id=tenant_id,
        from_state=result.from_state.name,
        to_state=result.to_state.name,
        reason=reason,
        actor_email=token.email,
        timestamp=datetime.now(timezone.utc).isoformat(),
        audit_id=audit_id,
    )


@router.get("/stalled")
async def get_stalled_tenants(
    request: Request,
    threshold_hours: int = 24,
    token: FounderToken = Depends(verify_fops_token),
):
    """
    Get list of stalled onboarding tenants.

    This is a READ-ONLY endpoint for founder visibility.
    No mutations. Founders can see which tenants are stuck.

    Use the force-complete endpoint to resolve if needed.
    """
    from ..auth.onboarding_transitions import detect_stalled_onboarding

    stalled = await detect_stalled_onboarding(threshold_hours=threshold_hours)

    return wrap_dict({
        "stalled_count": len(stalled),
        "threshold_hours": threshold_hours,
        "tenants": [
            {
                "tenant_id": t.tenant_id,
                "current_state": t.current_state.name,
                "hours_stalled": round(t.hours_in_state, 1),
                "created_at": t.created_at.isoformat(),
            }
            for t in stalled
        ],
    })
