# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: Onboarding status and progression endpoints
# Callers: Console UI, SDK clients
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-399 (Onboarding State Machine v1)

"""
Onboarding Status API

PIN-399: Provides deterministic onboarding status for UI consumption.

This API surfaces:
1. Current onboarding state
2. Next required action (action_id only - console-agnostic)
3. Blocked capabilities at current state (not routes)

DESIGN INVARIANTS:
- State is the sole authority (ONBOARD-001)
- Instructions are deterministic, not guessed
- No bypass, retry, or skip options exposed
- Backend emits capabilities, consoles map to routes (CONSOLE-001)
- No progress percentages (consoles interpret step_index)

CONSOLE SEPARATION:
- This API is console-agnostic
- Each console maps action_id → route locally
- Each console maps capability → UI affordance locally
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.onboarding")

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# =============================================================================
# CAPABILITY VOCABULARY (Console-Agnostic)
# =============================================================================
# These are product capabilities, not backend routes.
# Consoles map these to their own UI affordances.

CAPABILITY_API_KEY_MANAGEMENT = "api_key_management"
CAPABILITY_POLICY_MANAGEMENT = "policy_management"
CAPABILITY_AGENT_EXECUTION = "agent_execution"
CAPABILITY_RUN_MANAGEMENT = "run_management"
CAPABILITY_SDK_CONNECTION = "sdk_connection"
CAPABILITY_GUARD_ACCESS = "guard_access"
CAPABILITY_BILLING = "billing"
CAPABILITY_LIMITS = "limits"


# =============================================================================
# ACTION TYPE VOCABULARY (Console-Agnostic)
# =============================================================================
# Action types categorize the kind of step, not the specific route.

ACTION_TYPE_TENANT_BOOTSTRAP = "tenant_bootstrap"
ACTION_TYPE_CREDENTIAL_SETUP = "credential_setup"
ACTION_TYPE_INTEGRATION = "integration"
ACTION_TYPE_FINALIZATION = "finalization"


# =============================================================================
# STATE → ACTION MAPPING (Deterministic, Console-Agnostic)
# =============================================================================
# Each state maps to exactly one next action.
# Backend emits action_id and action_type only.
# Each console maps action_id → route locally.

STATE_ACTIONS: dict[OnboardingState, dict] = {
    OnboardingState.CREATED: {
        "action_id": "enter_console",
        "action_type": ACTION_TYPE_TENANT_BOOTSTRAP,
    },
    OnboardingState.IDENTITY_VERIFIED: {
        "action_id": "create_api_key",
        "action_type": ACTION_TYPE_CREDENTIAL_SETUP,
    },
    OnboardingState.API_KEY_CREATED: {
        "action_id": "connect_sdk",
        "action_type": ACTION_TYPE_INTEGRATION,
    },
    OnboardingState.SDK_CONNECTED: {
        "action_id": "complete_setup",
        "action_type": ACTION_TYPE_FINALIZATION,
    },
    OnboardingState.COMPLETE: {
        "action_id": None,
        "action_type": None,
    },
}


# =============================================================================
# STATE → CAPABILITIES (Console-Agnostic)
# =============================================================================
# Which capabilities are allowed/blocked at each state.
# Consoles map capabilities → UI sections locally.

STATE_ALLOWED_CAPABILITIES: dict[OnboardingState, list[str]] = {
    OnboardingState.CREATED: [],
    OnboardingState.IDENTITY_VERIFIED: [
        CAPABILITY_API_KEY_MANAGEMENT,
    ],
    OnboardingState.API_KEY_CREATED: [
        CAPABILITY_API_KEY_MANAGEMENT,
        CAPABILITY_SDK_CONNECTION,
    ],
    OnboardingState.SDK_CONNECTED: [
        CAPABILITY_API_KEY_MANAGEMENT,
        CAPABILITY_SDK_CONNECTION,
        CAPABILITY_POLICY_MANAGEMENT,
        CAPABILITY_AGENT_EXECUTION,
        CAPABILITY_RUN_MANAGEMENT,
        CAPABILITY_GUARD_ACCESS,
    ],
    OnboardingState.COMPLETE: [
        CAPABILITY_API_KEY_MANAGEMENT,
        CAPABILITY_SDK_CONNECTION,
        CAPABILITY_POLICY_MANAGEMENT,
        CAPABILITY_AGENT_EXECUTION,
        CAPABILITY_RUN_MANAGEMENT,
        CAPABILITY_GUARD_ACCESS,
        CAPABILITY_BILLING,
        CAPABILITY_LIMITS,
    ],
}

STATE_BLOCKED_CAPABILITIES: dict[OnboardingState, list[str]] = {
    OnboardingState.CREATED: [
        CAPABILITY_API_KEY_MANAGEMENT,
        CAPABILITY_POLICY_MANAGEMENT,
        CAPABILITY_AGENT_EXECUTION,
        CAPABILITY_RUN_MANAGEMENT,
        CAPABILITY_SDK_CONNECTION,
        CAPABILITY_GUARD_ACCESS,
        CAPABILITY_BILLING,
        CAPABILITY_LIMITS,
    ],
    OnboardingState.IDENTITY_VERIFIED: [
        CAPABILITY_POLICY_MANAGEMENT,
        CAPABILITY_AGENT_EXECUTION,
        CAPABILITY_RUN_MANAGEMENT,
        CAPABILITY_SDK_CONNECTION,
        CAPABILITY_GUARD_ACCESS,
        CAPABILITY_BILLING,
        CAPABILITY_LIMITS,
    ],
    OnboardingState.API_KEY_CREATED: [
        CAPABILITY_POLICY_MANAGEMENT,
        CAPABILITY_AGENT_EXECUTION,
        CAPABILITY_RUN_MANAGEMENT,
        CAPABILITY_GUARD_ACCESS,
        CAPABILITY_BILLING,
        CAPABILITY_LIMITS,
    ],
    OnboardingState.SDK_CONNECTED: [
        CAPABILITY_BILLING,
        CAPABILITY_LIMITS,
    ],
    OnboardingState.COMPLETE: [],
}

# Total number of onboarding steps (for step_index/total_steps)
TOTAL_ONBOARDING_STEPS = 5  # CREATED(0) through COMPLETE(4)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS (Console-Agnostic)
# =============================================================================


class NextAction(BaseModel):
    """Next required action for onboarding progression (console-agnostic)."""

    action_id: str = Field(..., description="Action identifier (console maps to route)")
    action_type: str = Field(..., description="Action category (tenant_bootstrap, credential_setup, etc.)")


class OnboardingStatusResponse(BaseModel):
    """Complete onboarding status for a tenant (console-agnostic)."""

    tenant_id: str = Field(..., description="Tenant identifier")
    current_state: str = Field(..., description="Current onboarding state name")
    state_value: int = Field(..., description="Numeric state value (0-4)")
    is_complete: bool = Field(..., description="Whether onboarding is complete")
    step_index: int = Field(..., description="Current step (0-based index)")
    total_steps: int = Field(..., description="Total onboarding steps")
    next_action: Optional[NextAction] = Field(None, description="Next required action")
    allowed_capabilities: list[str] = Field(
        default_factory=list, description="Capabilities allowed at current state"
    )
    blocked_capabilities: list[str] = Field(
        default_factory=list, description="Capabilities blocked at current state"
    )
    timestamp: str = Field(..., description="Response timestamp")


class OnboardingVerifyResponse(BaseModel):
    """Response for identity verification check."""

    verified: bool
    tenant_id: str
    current_state: str
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(request: Request):
    """
    Get current onboarding status for the authenticated tenant.

    Returns console-agnostic data:
    - Current state and step index
    - Next required action (action_id only - console maps to route)
    - Allowed/blocked capabilities (console maps to UI sections)

    This endpoint is the single source of truth for onboarding UI.
    Each console interprets this data according to its own routing.
    """
    # Get auth context
    auth_context = get_auth_context(request)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    tenant_id = getattr(auth_context, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    # Get current state from database (Phase A2: Onboarding SSOT)
    from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
        async_get_onboarding_state,
    )

    state_val = await async_get_onboarding_state(tenant_id)
    if state_val is None:
        current_state = OnboardingState.CREATED
    else:
        current_state = OnboardingState(state_val)

    # Get next action (action_id and action_type only)
    action_data = STATE_ACTIONS.get(current_state, STATE_ACTIONS[OnboardingState.CREATED])
    next_action = None
    if action_data["action_id"] is not None:
        next_action = NextAction(
            action_id=action_data["action_id"],
            action_type=action_data["action_type"],
        )

    # Get capabilities (console-agnostic)
    allowed_capabilities = STATE_ALLOWED_CAPABILITIES.get(current_state, [])
    blocked_capabilities = STATE_BLOCKED_CAPABILITIES.get(current_state, [])

    return OnboardingStatusResponse(
        tenant_id=tenant_id,
        current_state=current_state.name,
        state_value=current_state.value,
        is_complete=current_state == OnboardingState.COMPLETE,
        step_index=current_state.value,
        total_steps=TOTAL_ONBOARDING_STEPS,
        next_action=next_action,
        allowed_capabilities=allowed_capabilities,
        blocked_capabilities=blocked_capabilities,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/verify", response_model=OnboardingVerifyResponse)
async def verify_identity(request: Request):
    """
    Verify identity and advance to IDENTITY_VERIFIED state.

    Called after successful identity verification (e.g., email confirmation,
    SSO completion). This is an explicit verification endpoint, not automatic.

    Note: In production, this would be called by the auth callback handler
    after Clerk confirms identity. For now, it's a manual trigger.
    """
    # Get auth context
    auth_context = get_auth_context(request)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    tenant_id = getattr(auth_context, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    # Trigger transition (Phase A2: Onboarding SSOT)
    from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
        async_advance_onboarding,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

    result = await async_advance_onboarding(
        tenant_id,
        OnboardingStatus.IDENTITY_VERIFIED.value,
        "first_human_auth",
    )

    if result["success"]:
        return OnboardingVerifyResponse(
            verified=True,
            tenant_id=tenant_id,
            current_state=result.get("to_state", "UNKNOWN"),
            message="Identity verified successfully",
        )
    else:
        return OnboardingVerifyResponse(
            verified=False,
            tenant_id=tenant_id,
            current_state=result.get("from_state", "UNKNOWN"),
            message=result.get("message", "Transition failed"),
        )


@router.post("/advance/api-key")
async def advance_api_key_created(request: Request):
    """
    Advance to API_KEY_CREATED state.

    Called after first API key is created. This is typically triggered
    automatically by the API key creation endpoint.

    Returns the new onboarding status.
    """
    auth_context = get_auth_context(request)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    tenant_id = getattr(auth_context, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    # Phase A2: Onboarding SSOT
    from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
        async_advance_onboarding,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

    result = await async_advance_onboarding(
        tenant_id,
        OnboardingStatus.API_KEY_CREATED.value,
        "first_api_key_created",
    )

    return wrap_dict({
        "success": result["success"],
        "from_state": result.get("from_state", "UNKNOWN"),
        "to_state": result.get("to_state", "UNKNOWN"),
        "was_no_op": result.get("was_no_op", False),
    })
