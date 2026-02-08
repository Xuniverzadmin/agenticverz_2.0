# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified RETRIEVAL facade - L2 API for mediated data access
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-094 (Mediated Data Retrieval API)
# GOVERNANCE NOTE:
# This is the ONE facade for RETRIEVAL domain.
# All data access flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Retrieval API (L2)

Provides mediated data retrieval operations:
- POST /retrieval/access (mediated data access)

This is the ONLY facade for mediated data retrieval.
All data access from LLM-controlled code MUST flow through this router.

INVARIANT: Deny-by-default. All access blocked unless explicitly allowed by policy.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.services.retrieval_facade import (
    RetrievalFacade,
    get_retrieval_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


# =============================================================================
# Request/Response Models
# =============================================================================


class AccessDataRequest(BaseModel):
    """Request for mediated data access."""
    run_id: str = Field(..., description="Run context for this access")
    plane_id: str = Field(..., description="Knowledge plane to access")
    action: str = Field(..., description="Action: query, retrieve, search, list")
    payload: Dict[str, Any] = Field(..., description="Action-specific payload")


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> RetrievalFacade:
    """Get the retrieval facade."""
    return get_retrieval_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/access", response_model=Dict[str, Any])
async def access_data(
    request: AccessDataRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: RetrievalFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("retrieval.access")),
):
    """
    Mediated data access (GAP-094).

    **Tier: REACT ($9)** - Mediated data access.

    All data access from LLM-controlled code MUST go through this endpoint.
    Implements deny-by-default policy enforcement.

    INVARIANT: Access is BLOCKED unless explicitly allowed by policy.
    """
    result = await facade.access_data(
        tenant_id=ctx.tenant_id,
        run_id=request.run_id,
        plane_id=request.plane_id,
        action=request.action,
        payload=request.payload,
    )

    if not result.success:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {result.error}",
        )

    return wrap_dict(result.to_dict())
