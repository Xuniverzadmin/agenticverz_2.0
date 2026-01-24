# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Founder (FOPS) authentication dependency
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Callers: Founder-only route handlers
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-398 (Founder Auth Architecture)


"""
Founder Authentication Dependency

This module provides the FastAPI dependency for founder-only routes.
Type-based authority: if auth_context is FounderAuthContext, access is granted.

INVARIANTS:
- No attribute checks (is_founder, roles, etc.)
- No permission checks
- Type is authority
- All other context types are REJECTED

Usage:
    @router.get("/admin/action")
    async def admin_action(
        founder: FounderAuthContext = Depends(verify_fops_token)
    ):
        # Only founders reach here
        ...
"""

from fastapi import Depends, HTTPException, Request, status

from app.auth.contexts import FounderAuthContext
from app.auth.gateway_middleware import get_auth_context


def verify_fops_token(request: Request) -> FounderAuthContext:
    """
    Verify request has founder (FOPS) authentication.

    TYPE-BASED AUTHORITY:
    - If auth_context is FounderAuthContext → ALLOW
    - All other types → REJECT (403)

    No attributes. No roles. No permissions.
    Type is authority.
    """
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if not isinstance(auth_context, FounderAuthContext):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Founder access required",
        )

    return auth_context


# Alias for cleaner route definitions
require_founder = Depends(verify_fops_token)
