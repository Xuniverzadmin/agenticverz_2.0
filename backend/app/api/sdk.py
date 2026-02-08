# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: SDK connection and registration endpoints
# Callers: SDK clients (Python, JS, etc.)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-399 (Onboarding State Machine v1)

"""
SDK Endpoints

PIN-399: Provides SDK handshake and registration endpoints for onboarding.

These endpoints are called by SDK clients during initial setup:
1. /sdk/handshake - Validate SDK connection and advance onboarding
2. /sdk/register - Register SDK instance (future use)
3. /sdk/instructions - Get SDK setup instructions (future use)

ONBOARDING TRANSITIONS:
- /sdk/handshake triggers: API_KEY_CREATED → SDK_CONNECTED
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..auth.gateway_middleware import get_auth_context

logger = logging.getLogger("nova.api.sdk")

router = APIRouter(prefix="/sdk", tags=["SDK"])


# ============== Request/Response Schemas ==============


class HandshakeRequest(BaseModel):
    """SDK handshake request."""

    sdk_version: str = Field(..., description="SDK version string")
    sdk_language: str = Field(..., description="SDK language (python, javascript, etc.)")
    client_id: Optional[str] = Field(None, description="Optional client identifier")


class HandshakeResponse(BaseModel):
    """SDK handshake response."""

    success: bool
    message: str
    server_version: str
    tenant_id: str
    onboarding_state: str
    timestamp: str


class InstructionsResponse(BaseModel):
    """SDK setup instructions response."""

    tenant_id: str
    api_base_url: str
    websocket_url: Optional[str]
    docs_url: str
    example_code: str


# ============== Onboarding Transition Helper ==============


async def _maybe_advance_to_sdk_connected(tenant_id: str) -> Optional[str]:
    """
    PIN-399: Trigger onboarding state transition on first SDK handshake.

    Returns the new state name if transition occurred, None otherwise.
    """
    try:
        from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
            async_advance_onboarding,
        )
        from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

        result = await async_advance_onboarding(
            tenant_id,
            OnboardingStatus.SDK_CONNECTED.value,
            "first_sdk_handshake",
        )

        if result.get("success") and not result.get("was_no_op"):
            logger.info(
                "onboarding_advanced_on_sdk_handshake",
                extra={
                    "tenant_id": tenant_id,
                    "from_state": result.get("from_state"),
                    "to_state": result.get("to_state"),
                },
            )
            return result.get("to_state")

        return result.get("to_state") if result.get("success") else None

    except Exception as e:
        logger.warning(f"Failed to advance onboarding state on SDK handshake: {e}")
        return None


# ============== Endpoints ==============


@router.post("/handshake", response_model=HandshakeResponse)
async def sdk_handshake(
    request: Request,
    body: HandshakeRequest,
):
    """
    SDK handshake endpoint.

    Called by SDK clients on first connection to validate setup
    and trigger onboarding state transition.

    PIN-399: This endpoint triggers API_KEY_CREATED → SDK_CONNECTED transition.

    Requires: Valid API key authentication (X-AOS-Key header)
    """
    # Get auth context (set by gateway middleware)
    auth_context = get_auth_context(request)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Get tenant_id from auth context
    tenant_id = getattr(auth_context, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    # Log handshake attempt
    logger.info(
        "sdk_handshake_received",
        extra={
            "tenant_id": tenant_id,
            "sdk_version": body.sdk_version,
            "sdk_language": body.sdk_language,
            "client_id": body.client_id,
        },
    )

    # Trigger onboarding transition
    new_state = await _maybe_advance_to_sdk_connected(tenant_id)

    # Get current state for response
    from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
        async_get_onboarding_state,
    )
    from app.hoc.cus.account.L5_schemas.onboarding_state import ONBOARDING_STATUS_NAMES

    state_val = await async_get_onboarding_state(tenant_id)
    state_name = ONBOARDING_STATUS_NAMES.get(state_val or 0, "UNKNOWN")

    return HandshakeResponse(
        success=True,
        message="SDK handshake successful",
        server_version="1.0.0",
        tenant_id=tenant_id,
        onboarding_state=state_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/instructions", response_model=InstructionsResponse)
async def get_sdk_instructions(
    request: Request,
):
    """
    Get SDK setup instructions.

    Returns configuration and example code for SDK setup.

    Requires: Valid authentication (JWT or API key)
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

    # Return instructions
    import os

    api_base = os.getenv("API_BASE_URL", "https://api.agenticverz.com")

    return InstructionsResponse(
        tenant_id=tenant_id,
        api_base_url=api_base,
        websocket_url=None,  # Future: WebSocket support
        docs_url="https://docs.agenticverz.com/sdk",
        example_code=f'''
# Python SDK Example
from aos_sdk import AOS

aos = AOS(api_key="your-api-key")

# Run an agent
result = aos.run(
    agent_id="your-agent-id",
    goal="Your goal here",
)

print(result.status)
'''.strip(),
    )
