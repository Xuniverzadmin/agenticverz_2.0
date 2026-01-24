# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Console API authentication helpers (key verification)
# Callers: Guard Console, Ops Console routers
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: PIN-148

"""
API Auth Helpers - Console Authentication

PIN-148: M29 Auth Boundary Verification

Provides API key verification for Guard and Ops console endpoints.
These endpoints previously had frontend-only auth which could be bypassed.

Usage:
    from app.api.auth_helpers import verify_console_api_key

    router = APIRouter(dependencies=[Depends(verify_console_api_key)])

    # Or per-endpoint:
    @router.get("/status")
    async def get_status(_: str = Depends(verify_console_api_key)):
        ...
"""

import os
from typing import Optional

from fastapi import Header, HTTPException, status

# API Key from environment
AOS_API_KEY = os.getenv("AOS_API_KEY", "")


async def verify_console_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """
    Verify API key for console endpoints.

    Accepts X-API-Key header (matching frontend client.ts).
    Returns the validated API key.

    Raises:
        HTTPException 401: If API key is missing or invalid
        HTTPException 500: If AOS_API_KEY not configured
    """
    if not AOS_API_KEY:
        # Server misconfigured - fail open in dev, fail closed in prod
        if os.getenv("ENV", "development") == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server misconfigured: API key not set"
            )
        # In development, allow unauthenticated access for local testing
        return "dev-mode"

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if x_api_key != AOS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key", headers={"WWW-Authenticate": "ApiKey"}
        )

    return x_api_key


__all__ = ["verify_console_api_key"]
