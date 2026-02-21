# capability_id: CAP-009
# Layer: L2a — Product API (Console-scoped)
# Product: AI Console (Customer Console)
# Auth: verify_console_token (aud=console)
# Reference: PIN-280, PIN-281 (L2 Promotion Governance)
# NOTE: Workers NEVER call this. SDK NEVER imports this.

"""Guard Policies API - Customer Console Policy Constraints Endpoint

This router provides endpoints for the Customer Console (guard.agenticverz.com).
Focused on POLICY VISIBILITY - customers can see their constraints and limits.

Endpoints:
- GET  /guard/policies          - Policy constraints summary
- GET  /guard/policies/guardrails/{id}  - Guardrail detail

PIN-281 Promotion:
- L4→L3: customer_policies_adapter.py (boundary adapter)
- L3→L2: This file (API route)

Rule: One adapter per route. No business logic here.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

# L3 Adapter (only import from L3)
from app.adapters.customer_policies_adapter import (
    CustomerGuardrail,
    CustomerPolicyConstraints,
    get_customer_policies_adapter,
)

# Category 2 Auth: Domain-separated authentication for Customer Console
from app.auth.console_auth import verify_console_token
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.guard_policies")

# =============================================================================
# Router - Customer Console Policies (tenant-scoped)
# =============================================================================

router = APIRouter(
    prefix="/guard/policies",
    tags=["Guard Console - Policies"],
    dependencies=[Depends(verify_console_token)],  # Category 2: Strict console auth
)


# =============================================================================
# Policy Constraints Endpoint
# =============================================================================


@router.get("", response_model=CustomerPolicyConstraints)
async def get_policy_constraints(
    tenant_id: str = Query(..., description="Tenant ID (required)"),
):
    """
    Get policy constraints for customer.

    Returns summary of:
    - Budget constraints (limit, usage, remaining)
    - Rate limits
    - Active guardrails

    Customer can only see their own tenant's constraints (enforced by adapter).

    This endpoint answers:
    - What are my limits?
    - How much have I used?
    - What protection is active?

    Reference: PIN-281 Phase 5 (L3→L2 promotion)
    """
    adapter = get_customer_policies_adapter()

    try:
        constraints = adapter.get_policy_constraints(tenant_id=tenant_id)
        return constraints
    except Exception as e:
        logger.error(f"Error getting policy constraints for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policy constraints")


# =============================================================================
# Guardrail Detail Endpoint
# =============================================================================


@router.get("/guardrails/{guardrail_id}", response_model=CustomerGuardrail)
async def get_guardrail_detail(
    guardrail_id: str,
    tenant_id: str = Query(..., description="Tenant ID (required)"),
):
    """
    Get guardrail detail.

    Returns information about a specific guardrail:
    - Name and description
    - Whether it's enabled
    - Action on trigger (block, warn, log)

    No threshold values exposed (internal implementation detail).

    Reference: PIN-281 Phase 5 (L3→L2 promotion)
    """
    adapter = get_customer_policies_adapter()

    try:
        guardrail = adapter.get_guardrail_detail(
            tenant_id=tenant_id,
            guardrail_id=guardrail_id,
        )

        if guardrail is None:
            raise HTTPException(
                status_code=404,
                detail=f"Guardrail {guardrail_id} not found",
            )

        return wrap_dict(guardrail.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guardrail {guardrail_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve guardrail")
