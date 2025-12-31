# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api (every authenticated request)
#   Execution: sync
# Role: API key verification dependency for FastAPI routes
# Callers: All protected API routes via Depends()
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Security

import os

from fastapi import Header, HTTPException, status

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
