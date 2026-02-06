# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Debug endpoint for auth context visibility
# Callers: Developers, debugging tools
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: AUTHORITY_CONTRACT.md (Section: Debug Endpoints)

"""
Debug Auth Context Endpoint

Provides visibility into the current authentication state.
This endpoint is for DEBUGGING only — never expose in production without auth.

Authority Contract (AUTH_AUTHORITY.md):
- This endpoint reveals the interpreted auth context
- Shows which auth plane was selected (HUMAN vs MACHINE)
- Shows tenant state as derived (not cached)
- Helps diagnose auth failures without guessing

SECURITY NOTE:
- This endpoint should be protected behind auth
- Do not return sensitive tokens or secrets
- Return only interpreted state, not raw inputs
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_async_session_context,
)
from app.schemas.response import wrap_dict
from app.auth.contexts import (
    AuthPlane,
    FounderAuthContext,
    HumanAuthContext,
    MachineCapabilityContext,
)

router = APIRouter(prefix="/debug/auth", tags=["debug"])


class AuthContextDebugResponse(BaseModel):
    """Debug response showing current auth context state."""

    # Auth plane selected
    auth_plane: Optional[str]  # "HUMAN" | "MACHINE" | None

    # Identity info (non-sensitive)
    actor_id: Optional[str]
    actor_type: Optional[str]  # "human" | "machine" | "founder" | None

    # Tenant state
    tenant_id: Optional[str]
    tenant_state: Optional[str]  # Derived state name
    tenant_state_value: Optional[int]  # Derived state value

    # Account (for human context)
    account_id: Optional[str]

    # Capabilities (for machine context)
    scopes: Optional[list[str]]
    rate_limit: Optional[int]

    # Session info (for human context)
    session_id: Optional[str]  # Truncated for security

    # Founder info
    reason: Optional[str]  # FOPS reason

    # Metadata
    auth_source: Optional[str]
    authenticated_at: Optional[str]
    debug_timestamp: str

    # Diagnostic info
    headers_received: Dict[str, str]  # What headers were present (masked)
    context_type: Optional[str]  # The exact context class name


def _mask_value(value: str, visible_chars: int = 8) -> str:
    """Mask a sensitive value, showing only first N chars."""
    if not value:
        return ""
    if len(value) <= visible_chars:
        return value
    return f"{value[:visible_chars]}..."


async def _get_tenant_state(tenant_id: Optional[str]) -> tuple[Optional[str], Optional[int]]:
    """
    Get the DERIVED tenant state (not cached).

    Uses TenantStateResolver to compute state from:
    account → users → bindings → billing

    Returns:
        Tuple of (state_name, state_value) or (None, None) if no tenant
    """
    if not tenant_id:
        return None, None

    try:
        from app.domain.tenants.state_resolver import TenantState, TenantStateResolver

        async with get_async_session_context() as session:
            resolver = TenantStateResolver(session)
            state = await resolver.resolve(tenant_id)
            return state.name, state.value
    except Exception as e:
        # Don't fail the debug endpoint on tenant resolution errors
        return f"ERROR: {str(e)}", None


@router.get("/context", response_model=AuthContextDebugResponse)
async def get_auth_context(request: Request):
    """
    Debug endpoint: Show current auth context.

    Returns the interpreted authentication context for the current request.
    This reveals:
    - Which auth plane was selected (HUMAN vs MACHINE)
    - The resolved identity
    - The derived tenant state (computed, not cached)
    - What the gateway understood from the headers

    Use this to debug auth failures and understand system state.
    """
    # Get auth context from request state (set by gateway middleware)
    auth_context = getattr(request.state, "auth_context", None)

    # Build header info (masked for security)
    headers_received = {}
    if request.headers.get("authorization"):
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            headers_received["Authorization"] = f"Bearer {_mask_value(auth_header[7:])}"
        else:
            headers_received["Authorization"] = _mask_value(auth_header)
    if request.headers.get("x-aos-key"):
        headers_received["X-AOS-Key"] = _mask_value(request.headers.get("x-aos-key", ""))
    if request.headers.get("x-tenant-id"):
        headers_received["X-Tenant-ID"] = request.headers.get("x-tenant-id", "")

    # Default response (no context)
    response_data: Dict[str, Any] = {
        "auth_plane": None,
        "actor_id": None,
        "actor_type": None,
        "tenant_id": None,
        "tenant_state": None,
        "tenant_state_value": None,
        "account_id": None,
        "scopes": None,
        "rate_limit": None,
        "session_id": None,
        "reason": None,
        "auth_source": None,
        "authenticated_at": None,
        "debug_timestamp": datetime.now(timezone.utc).isoformat(),
        "headers_received": headers_received,
        "context_type": None,
    }

    if auth_context is None:
        # No context - either no auth headers or auth failed
        return AuthContextDebugResponse(**response_data)

    # Extract common fields
    if hasattr(auth_context, "plane"):
        response_data["auth_plane"] = auth_context.plane.value.upper()

    if hasattr(auth_context, "actor_id"):
        response_data["actor_id"] = auth_context.actor_id

    if hasattr(auth_context, "auth_source"):
        response_data["auth_source"] = auth_context.auth_source.value

    if hasattr(auth_context, "authenticated_at") and auth_context.authenticated_at:
        response_data["authenticated_at"] = auth_context.authenticated_at.isoformat()

    # Type-specific extraction
    if isinstance(auth_context, HumanAuthContext):
        response_data["actor_type"] = "human"
        response_data["context_type"] = "HumanAuthContext"
        response_data["tenant_id"] = auth_context.tenant_id
        response_data["account_id"] = auth_context.account_id
        if auth_context.session_id:
            response_data["session_id"] = _mask_value(auth_context.session_id)

    elif isinstance(auth_context, MachineCapabilityContext):
        response_data["actor_type"] = "machine"
        response_data["context_type"] = "MachineCapabilityContext"
        response_data["tenant_id"] = auth_context.tenant_id
        response_data["scopes"] = list(auth_context.scopes)
        response_data["rate_limit"] = auth_context.rate_limit

    elif isinstance(auth_context, FounderAuthContext):
        response_data["actor_type"] = "founder"
        response_data["context_type"] = "FounderAuthContext"
        response_data["reason"] = auth_context.reason
        response_data["tenant_id"] = None  # Founders are not tenant-scoped

    # Get derived tenant state
    tenant_id = response_data.get("tenant_id")
    state_name, state_value = await _get_tenant_state(tenant_id)
    response_data["tenant_state"] = state_name
    response_data["tenant_state_value"] = state_value

    return AuthContextDebugResponse(**response_data)


@router.get("/planes")
async def get_auth_planes():
    """
    Debug endpoint: Show available auth planes and their characteristics.

    This is a reference endpoint - no auth context required.
    """
    return wrap_dict({
        "planes": {
            "HUMAN": {
                "header": "Authorization: Bearer <jwt>",
                "providers": ["Clerk (RS256)"],
                "context_type": "HumanAuthContext",
                "description": "Console users authenticate via Clerk JWT",
                "mutual_exclusivity": "Cannot use X-AOS-Key header simultaneously",
            },
            "MACHINE": {
                "header": "X-AOS-Key: <api_key>",
                "providers": ["API Key Service", "Legacy AOS_API_KEY"],
                "context_type": "MachineCapabilityContext",
                "description": "SDK/CLI/Workers authenticate via API key",
                "mutual_exclusivity": "Cannot use Authorization header simultaneously",
            },
        },
        "mutual_exclusivity_rule": "JWT XOR API Key - both present is HARD FAIL",
        "reference": "AUTHORITY_CONTRACT.md",
    })


@router.get("/tenant-states")
async def get_tenant_states():
    """
    Debug endpoint: Show tenant state definitions.

    This is a reference endpoint - no auth context required.
    """
    from app.domain.tenants.state_resolver import TenantState

    return wrap_dict({
        "states": {
            state.name: {
                "value": state.value,
                "is_operational": state.is_operational,
                "is_active": state.is_active,
                "allows_read": state.allows_read,
                "allows_write": state.allows_write,
            }
            for state in TenantState
        },
        "derivation_chain": [
            "tenant exists → CREATED (0)",
            "account created → CONFIGURING (1)",
            "at least one user exists → VALIDATING (2)",
            "user verified, bindings created → PROVISIONING (3)",
            "≥1 ACTIVE user bound, billing ok → COMPLETE (4)",
            "billing hold or policy violation → SUSPENDED (5)",
            "soft deleted → ARCHIVED (6)",
        ],
        "authority_rule": "State is COMPUTED from account/user/binding readiness, never manually set",
        "reference": "AUTHORITY_CONTRACT.md",
    })
