# capability_id: CAP-012
"""
Auth module for AOS.

Provides Clerk-based authentication (the ONLY human auth path) and
authorization utilities.

Reference: AUTH_DESIGN.md
- AUTH-HUMAN-001: All human users authenticate via Clerk (RS256 JWKS)
- AUTH-HUMAN-002: No other human authentication mechanism exists
- AUTH-MACHINE-001: Machine clients authenticate via API Key

Stale re-exports removed (2026-02-06):
The following modules were re-exported here but do not exist in this package.
They live at their canonical locations in app/auth/ and are imported directly
from there by consumers. No code imports from app.hoc.int.account.engines.

Removed re-exports and their canonical locations:
  - authorization_choke → app/auth/authorization_choke.py
  - clerk_provider → app/auth/clerk_provider.py
  - jwt_auth → app/auth/jwt_auth.py
  - oidc_provider → app/auth/oidc_provider.py
  - rbac → app/auth/rbac.py
  - role_mapping → app/auth/role_mapping.py
  - shadow_audit → app/auth/shadow_audit.py
"""

import os

from fastapi import Header, HTTPException, status

# API Key configuration
AOS_API_KEY = os.getenv("AOS_API_KEY", "")


async def verify_api_key(x_aos_key: str = Header(..., alias="X-AOS-Key")):
    """
    Verify the API key from X-AOS-Key header.
    Rejects all requests without a valid key.
    """
    if not AOS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server misconfigured: AOS_API_KEY not set"
        )

    if x_aos_key != AOS_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return x_aos_key


__all__ = [
    "verify_api_key",
    "AOS_API_KEY",
]
