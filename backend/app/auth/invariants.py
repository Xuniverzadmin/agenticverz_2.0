# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Invariant guards for auth gateway enforcement
# Callers: AuthGateway, gateway_middleware
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Auth Gateway Invariant Guards

Hard-fail guards that enforce authentication invariants.
These guards are called within the gateway and middleware
to ensure the auth contract is never violated.

INVARIANTS:
1. No mixed auth (JWT AND API Key) - HARD FAIL
2. Plane must match route requirement - HARD FAIL
3. Workers never use JWT - HARD FAIL
4. Headers are stripped after gateway - ENFORCED
"""

from __future__ import annotations

import logging
from typing import Optional

from .contexts import AuthPlane, GatewayContext, HumanAuthContext, MachineCapabilityContext
from .gateway_types import (
    GatewayAuthError,
    error_mixed_auth,
    error_plane_mismatch,
    error_worker_jwt_forbidden,
)

logger = logging.getLogger("nova.auth.invariants")


class AuthInvariantViolation(Exception):
    """
    Raised when an auth invariant is violated.

    This is a HARD FAIL - the request MUST be rejected.
    """

    def __init__(self, invariant: str, message: str):
        self.invariant = invariant
        self.message = message
        super().__init__(f"AUTH_INVARIANT_VIOLATION [{invariant}]: {message}")


# =============================================================================
# Invariant I1: No Mixed Auth
# =============================================================================


def assert_no_mixed_auth(
    authorization_header: Optional[str],
    api_key_header: Optional[str],
) -> Optional[GatewayAuthError]:
    """
    Assert that both JWT and API Key are not present.

    INVARIANT I1: A request MUST use JWT XOR API Key, never both.
    Mutual exclusivity is enforced at the gateway level.

    Args:
        authorization_header: Authorization header value
        api_key_header: X-AOS-Key header value

    Returns:
        GatewayAuthError if invariant violated, None otherwise.
    """
    has_jwt = authorization_header is not None and authorization_header.strip() != ""
    has_api_key = api_key_header is not None and api_key_header.strip() != ""

    if has_jwt and has_api_key:
        logger.error(
            "AUTH_INVARIANT_I1_VIOLATED",
            extra={
                "invariant": "no_mixed_auth",
                "has_jwt": True,
                "has_api_key": True,
            },
        )
        return error_mixed_auth()

    return None


# =============================================================================
# Invariant I2: Plane Match
# =============================================================================


def assert_plane_match(
    path: str,
    context: GatewayContext,
) -> Optional[GatewayAuthError]:
    """
    Assert that auth plane matches route requirement.

    INVARIANT I2: Auth plane must be compatible with route.
    - HUMAN_ONLY routes reject API key auth
    - MACHINE_ONLY routes reject JWT auth

    Args:
        path: Request path
        context: Auth context from gateway

    Returns:
        GatewayAuthError if invariant violated, None otherwise.
    """
    from .route_planes import PlaneRequirement, get_plane_requirement

    requirement = get_plane_requirement(path)

    if requirement == PlaneRequirement.BOTH:
        return None

    actual_plane = context.plane

    if requirement == PlaneRequirement.HUMAN_ONLY:
        if actual_plane != AuthPlane.HUMAN:
            logger.error(
                "AUTH_INVARIANT_I2_VIOLATED",
                extra={
                    "invariant": "plane_match",
                    "path": path,
                    "required": "human_only",
                    "actual": actual_plane.value,
                },
            )
            return error_plane_mismatch("human", actual_plane.value)

    if requirement == PlaneRequirement.MACHINE_ONLY:
        if actual_plane != AuthPlane.MACHINE:
            logger.error(
                "AUTH_INVARIANT_I2_VIOLATED",
                extra={
                    "invariant": "plane_match",
                    "path": path,
                    "required": "machine_only",
                    "actual": actual_plane.value,
                },
            )
            return error_plane_mismatch("machine", actual_plane.value)

    return None


# =============================================================================
# Invariant I3: No Worker JWT
# =============================================================================


def assert_no_worker_jwt(
    path: str,
    context: GatewayContext,
) -> Optional[GatewayAuthError]:
    """
    Assert that worker paths never use JWT authentication.

    INVARIANT I3: Worker endpoints MUST use API key auth.
    Workers cannot impersonate users via JWT.

    Args:
        path: Request path
        context: Auth context from gateway

    Returns:
        GatewayAuthError if invariant violated, None otherwise.
    """
    from .route_planes import is_worker_path

    if not is_worker_path(path):
        return None

    if isinstance(context, HumanAuthContext):
        logger.error(
            "AUTH_INVARIANT_I3_VIOLATED",
            extra={
                "invariant": "no_worker_jwt",
                "path": path,
                "auth_type": "human",
                "actor_id": context.actor_id,
            },
        )
        return error_worker_jwt_forbidden()

    return None


# =============================================================================
# Invariant I4: Admin No API Key (implicit in I2, but explicit for clarity)
# =============================================================================


def assert_admin_no_api_key(
    path: str,
    context: GatewayContext,
) -> Optional[GatewayAuthError]:
    """
    Assert that admin paths never use API key authentication.

    INVARIANT I4: Admin endpoints MUST use human (JWT) auth.
    Prevents privilege escalation via API keys.

    Args:
        path: Request path
        context: Auth context from gateway

    Returns:
        GatewayAuthError if invariant violated, None otherwise.
    """
    from .route_planes import is_admin_path

    if not is_admin_path(path):
        return None

    if isinstance(context, MachineCapabilityContext):
        logger.error(
            "AUTH_INVARIANT_I4_VIOLATED",
            extra={
                "invariant": "admin_no_api_key",
                "path": path,
                "auth_type": "machine",
                "key_id": context.key_id,
            },
        )
        return error_plane_mismatch("human", "machine")

    return None


# =============================================================================
# Combined Check
# =============================================================================


def check_all_invariants(
    path: str,
    context: GatewayContext,
) -> Optional[GatewayAuthError]:
    """
    Run all post-authentication invariant checks.

    Called by gateway middleware after successful authentication.

    Args:
        path: Request path
        context: Auth context from gateway

    Returns:
        First GatewayAuthError encountered, or None if all pass.
    """
    # I2: Plane match
    error = assert_plane_match(path, context)
    if error:
        return error

    # I3: No worker JWT
    error = assert_no_worker_jwt(path, context)
    if error:
        return error

    # I4: Admin no API key
    error = assert_admin_no_api_key(path, context)
    if error:
        return error

    return None


# =============================================================================
# Header Stripping (I5)
# =============================================================================


def get_headers_to_strip() -> list[str]:
    """
    Get list of headers to strip after gateway processing.

    INVARIANT I5: Auth headers are stripped after gateway.
    Downstream code consumes context, not headers.

    Returns:
        List of header names to remove from request.
    """
    return [
        "Authorization",
        "X-AOS-Key",
    ]


def strip_auth_headers(headers: dict) -> dict:
    """
    Remove auth headers from a headers dict.

    Use this to create a sanitized copy of headers
    for downstream processing.

    Args:
        headers: Original headers dict

    Returns:
        New dict with auth headers removed.
    """
    stripped = dict(headers)
    for header in get_headers_to_strip():
        stripped.pop(header, None)
        stripped.pop(header.lower(), None)
    return stripped


# =============================================================================
# Invariant Summary (for documentation)
# =============================================================================

INVARIANT_DEFINITIONS = {
    "I1": {
        "name": "no_mixed_auth",
        "description": "Request must use JWT XOR API Key, never both",
        "enforcement": "Gateway.authenticate()",
        "failure": "400 Bad Request",
    },
    "I2": {
        "name": "plane_match",
        "description": "Auth plane must match route requirement",
        "enforcement": "check_all_invariants()",
        "failure": "403 Forbidden",
    },
    "I3": {
        "name": "no_worker_jwt",
        "description": "Worker paths cannot use JWT authentication",
        "enforcement": "check_all_invariants()",
        "failure": "403 Forbidden",
    },
    "I4": {
        "name": "admin_no_api_key",
        "description": "Admin paths cannot use API key authentication",
        "enforcement": "check_all_invariants()",
        "failure": "403 Forbidden",
    },
    "I5": {
        "name": "headers_stripped",
        "description": "Auth headers removed after gateway processing",
        "enforcement": "gateway_middleware",
        "failure": "N/A (always applied)",
    },
}
