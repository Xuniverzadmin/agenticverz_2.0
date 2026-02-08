# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Session context endpoint for frontend auth state
# Callers: Frontend console (ClerkAuthSync, route guards)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1
# Reference: PIN-409 (Clerk Auth Integration), RULE-AUTH-UI-001

"""
Session Context API

PIN-409: Provides verified session context to frontend.

This endpoint replaces frontend-derived authorization facts (isFounder, audience)
with backend-verified context. The frontend reads, never infers.

Endpoint:
    GET /session/context - Get current session context

Response:
    {
        "actor_type": "customer" | "founder" | "machine",
        "tenant_id": "...",
        "capabilities": [...],  // for machine clients only
        "lifecycle_state": "ACTIVE" | "SUSPENDED" | "TERMINATED" | "ARCHIVED",
        "onboarding_state": "CREATED" | "IDENTITY_VERIFIED" | ... | "COMPLETE"
    }

RULE-AUTH-UI-001: Frontend never decides 'who I am' beyond signed-in vs not.
This endpoint is the single source of truth for authorization facts.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException

from app.auth.contexts import (
    FounderAuthContext,
    HumanAuthContext,
    MachineCapabilityContext,
)
from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_async_session_context,
    sql_text,
)
from app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums import normalize_status
from app.schemas.response import wrap_dict

router = APIRouter(prefix="/session", tags=["Session"])


@router.get("/context")
async def get_session_context(request: Request) -> Dict[str, Any]:
    """
    Get verified session context for the current authenticated user.

    This endpoint returns authorization facts derived from the verified
    backend context. The frontend should use these values instead of
    deriving them locally.

    Returns:
        actor_type: "customer" | "founder" | "machine"
        tenant_id: Tenant ID if applicable (null for founders)
        capabilities: List of scopes for machine clients (empty for humans)
        lifecycle_state: Current tenant lifecycle state (for tenant-scoped actors)
        onboarding_state: Current onboarding state (for tenant-scoped actors)

    Raises:
        401: Not authenticated
    """
    context = get_auth_context(request)

    if context is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    # Determine actor_type from context type (TYPE-BASED AUTHORITY)
    actor_type: str
    tenant_id: Optional[str] = None
    capabilities: List[str] = []
    lifecycle_state: Optional[str] = None
    onboarding_state: Optional[str] = None

    if isinstance(context, FounderAuthContext):
        # Founder: control-plane access, no tenant context
        actor_type = "founder"
        # Founders don't have tenant_id, lifecycle_state, or onboarding_state
        # They operate at the platform level

    elif isinstance(context, HumanAuthContext):
        # Human: customer console user with tenant context
        actor_type = "customer"
        tenant_id = context.tenant_id

        # Get lifecycle and onboarding state if tenant_id is present
        if tenant_id:
            lifecycle_state = await _fetch_lifecycle_state_name(tenant_id)
            onboarding_state = await _get_onboarding_state(tenant_id)

    elif isinstance(context, MachineCapabilityContext):
        # Machine: API key client with scopes
        actor_type = "machine"
        tenant_id = context.tenant_id
        capabilities = list(context.scopes)

        # Get lifecycle state for machine clients too
        if tenant_id:
            lifecycle_state = await _fetch_lifecycle_state_name(tenant_id)

    else:
        # Unknown context type - should not happen
        raise HTTPException(
            status_code=500,
            detail="Unknown authentication context type",
        )

    return wrap_dict({
        "actor_type": actor_type,
        "tenant_id": tenant_id,
        "capabilities": capabilities,
        "lifecycle_state": lifecycle_state,
        "onboarding_state": onboarding_state,
    })


async def _fetch_lifecycle_state_name(tenant_id: str) -> str:
    """Fetch lifecycle state name from DB (Tenant.status)."""
    async with get_async_session_context() as session:
        row = (await session.execute(
            sql_text("SELECT status FROM tenants WHERE id = :tid"),
            {"tid": tenant_id},
        )).mappings().first()
        if row is None:
            return "ACTIVE"
        status = normalize_status(row["status"])
        return status.value.upper()


async def _get_onboarding_state(tenant_id: str) -> str:
    """Fetch onboarding state name from DB (Tenant.onboarding_state)."""
    from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
        async_get_onboarding_state,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

    state = await async_get_onboarding_state(tenant_id)
    if state is None:
        return "CREATED"
    return OnboardingStatus(state).name
