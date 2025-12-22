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
