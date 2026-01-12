# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Console authentication compatibility shim
# Callers: guard.py, cost_guard.py, and other routes
# Reference: PIN-398 (Auth Design Sanitization)

"""
Console Authentication Compatibility Shim

PIN-398: This module was deleted as part of auth sanitization.
Legacy console token authentication is FORBIDDEN per AUTH_DESIGN.md.

This shim exists ONLY to maintain backwards compatibility with routes
that still import from console_auth. These routes should be migrated
to use Clerk authentication via the gateway middleware.

MIGRATION PATH:
1. Routes should get auth context from request.state.auth_context
2. Use get_auth_context(request) from gateway_middleware
3. Do NOT add new uses of verify_console_token

TODO: Remove this shim once all routes are migrated.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from .contexts import FounderAuthContext
from .gateway_middleware import get_auth_context

logger = logging.getLogger("nova.auth.console_auth")


class CustomerToken(BaseModel):
    """
    Compatibility model for console token data.

    Maps gateway auth context to the old CustomerToken interface.
    """

    tenant_id: str
    org_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = []


class FounderToken(BaseModel):
    """
    Compatibility model for founder (FOPS) token data.

    Maps gateway auth context to the old FounderToken interface.
    """

    user_id: str
    email: str
    mfa_verified: bool = False
    roles: list[str] = []


def verify_fops_token(request: Request) -> FounderToken:
    """
    Founder-only route dependency.

    PIN-398: TYPE-BASED AUTHORITY.
    - If auth_context is FounderAuthContext → ALLOW
    - All other types → REJECT (403)

    No attributes. No roles. No permissions.
    Type is authority.
    """
    auth_context = get_auth_context(request)

    if auth_context is None:
        logger.warning("verify_fops_token called without auth context")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="FOPS authentication required",
        )

    # TYPE-BASED AUTHORITY: FounderAuthContext only
    if not isinstance(auth_context, FounderAuthContext):
        logger.warning("verify_fops_token: not a FounderAuthContext")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Founder access required",
        )

    # Map FounderAuthContext to FounderToken for backward compatibility
    return FounderToken(
        user_id=auth_context.actor_id,
        email="",  # FounderAuthContext has no email
        mfa_verified=True,  # FOPS tokens are trusted
        roles=["founder"],  # Type implies role
    )


def verify_console_token(request: Request) -> CustomerToken:
    """
    Compatibility dependency for routes that expect console tokens.

    PIN-398: Console JWT auth is deleted. This shim maps gateway auth
    context to the CustomerToken interface for backwards compatibility.

    Routes using this should be migrated to use get_auth_context directly.
    """
    auth_context = get_auth_context(request)

    if auth_context is None:
        logger.warning("verify_console_token called without auth context")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Map gateway context to CustomerToken
    tenant_id = getattr(auth_context, "tenant_id", None)
    if tenant_id is None:
        logger.warning("verify_console_token: no tenant_id in auth context")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )

    return CustomerToken(
        tenant_id=tenant_id,
        org_id=tenant_id,  # Use tenant_id as org_id for compatibility
        user_id=getattr(auth_context, "user_id", None),
        email=getattr(auth_context, "email", None),
        roles=getattr(auth_context, "roles", []),
    )
