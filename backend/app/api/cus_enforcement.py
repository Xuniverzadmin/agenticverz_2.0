# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api (SDK, console)
#   Execution: sync
# Role: Enforcement policy API for customer LLM integrations
# Callers: SDK (cus_enforcer.py), customer console
# Allowed Imports: L4 (cus_enforcement_service), L6 (schemas)
# Forbidden Imports: L1, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md Section 15

"""Customer LLM Enforcement API

PURPOSE:
    API endpoints for enforcement policy evaluation.
    SDK calls these endpoints before making LLM calls.

ENDPOINTS:
    POST   /enforcement/check    - Pre-flight enforcement check
    GET    /enforcement/status   - Get current limits and usage
    POST   /enforcement/batch    - Batch pre-flight checks

SEMANTIC:
    - Tenant-isolated: All operations scoped to authenticated tenant
    - Read-only: These endpoints evaluate policies, they don't change them
    - Idempotent: Same request always produces same decision (given same state)

AUTHENTICATION:
    Uses standard tenant authentication via gateway middleware.
    SDK uses X-AOS-Key header.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.schemas.response import wrap_dict, wrap_list
from app.hoc.cus.policies.L5_engines.cus_enforcement_engine import CusEnforcementEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enforcement", tags=["Customer Enforcement"])


# =============================================================================
# SCHEMAS
# =============================================================================


class EnforcementCheckRequest(BaseModel):
    """Request for enforcement check."""

    integration_id: str = Field(..., description="Integration ID to check")
    estimated_cost_cents: int = Field(
        default=0, ge=0, description="Estimated cost of the call in cents"
    )
    estimated_tokens: int = Field(
        default=0, ge=0, description="Estimated tokens for the call"
    )


class EnforcementBatchRequest(BaseModel):
    """Request for batch enforcement check."""

    requests: List[EnforcementCheckRequest] = Field(
        ..., max_length=100, description="List of enforcement check requests"
    )


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_enforcement_service() -> CusEnforcementEngine:
    """Dependency to get enforcement service instance."""
    return CusEnforcementEngine()


def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from authenticated request."""
    # Try to get from auth context
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context and hasattr(auth_context, "tenant_id"):
        return str(auth_context.tenant_id)

    # Fallback: header for development/SDK
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Final fallback: demo tenant
    return "demo-tenant"


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/check", summary="Pre-flight enforcement check")
async def check_enforcement(
    payload: EnforcementCheckRequest,
    request: Request,
    service: CusEnforcementEngine = Depends(get_enforcement_service),
):
    """Check enforcement policy before making an LLM call.

    This is the primary endpoint for SDK pre-flight checks. Returns a decision
    that tells the SDK whether to proceed, warn, throttle, or block.

    The decision includes:
    - result: allowed, warned, throttled, blocked, hard_blocked
    - reasons: Explainability data for why the decision was made
    - degraded: True if decision made with incomplete telemetry

    IMPORTANT: This endpoint is read-only and idempotent. Calling it multiple
    times with the same state will produce the same result.
    """
    tenant_id = get_tenant_id(request)

    try:
        decision = await service.evaluate(
            tenant_id=tenant_id,
            integration_id=payload.integration_id,
            estimated_cost_cents=payload.estimated_cost_cents,
            estimated_tokens=payload.estimated_tokens,
        )

        return wrap_dict(decision.to_dict())

    except Exception as e:
        logger.exception(f"Enforcement check failed: {e}")
        # On failure, return allowed with degraded flag
        return wrap_dict(
            {
                "result": "allowed",
                "integration_id": payload.integration_id,
                "tenant_id": tenant_id,
                "reasons": [
                    {
                        "code": "check_failed",
                        "message": f"Enforcement check failed: {str(e)}",
                    }
                ],
                "degraded": True,
            }
        )


@router.get("/status", summary="Get enforcement status")
async def get_enforcement_status(
    request: Request,
    integration_id: str = Query(..., description="Integration ID"),
    service: CusEnforcementEngine = Depends(get_enforcement_service),
):
    """Get current enforcement status for an integration.

    Returns current limits, usage, and remaining allowances. Useful for
    displaying in dashboards or for SDK to show users their current state.

    Does NOT make an enforcement decision - use /check for that.
    """
    tenant_id = get_tenant_id(request)

    try:
        status = await service.get_enforcement_status(
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return wrap_dict(status)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", summary="Batch enforcement check")
async def batch_enforcement_check(
    payload: EnforcementBatchRequest,
    request: Request,
    service: CusEnforcementEngine = Depends(get_enforcement_service),
):
    """Check enforcement for multiple requests at once.

    Useful for batch operations or when making multiple calls in sequence.
    Returns decisions in the same order as the requests.
    """
    tenant_id = get_tenant_id(request)

    try:
        requests = [
            {
                "integration_id": r.integration_id,
                "estimated_cost_cents": r.estimated_cost_cents,
                "estimated_tokens": r.estimated_tokens,
            }
            for r in payload.requests
        ]

        decisions = await service.evaluate_batch(
            tenant_id=tenant_id,
            requests=requests,
        )

        return wrap_list(
            [d.to_dict() for d in decisions],
            total=len(decisions),
        )

    except Exception as e:
        logger.exception(f"Batch enforcement check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
