# Layer: L2 — API
# AUDIENCE: SHARED
# Role: Single authority for tenant resolution - ends ambiguity
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Callers: API routers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L4, L5
# Reference: Tenant Resolution Contract


"""Tenant Resolver - Single Authority for Tenant Identity

INVARIANT (NON-NEGOTIABLE):
    Tenant identity must be fully resolved before entering the service layer.
    Services never infer, parse, or default tenant_id.

This module is the ONLY place where tenant_id is resolved from requests.
All downstream code receives UUID, never strings.

RESOLUTION ORDER:
    1. Auth context (human JWT or DB-backed machine key with tenant)
    2. X-Tenant-ID header (machine-plane fallback, must be valid UUID)
    3. Fail closed (400 error, never guess)

NEVER:
    - Return str(None)
    - Return "demo-tenant"
    - Construct UUID from untrusted strings in service layer
"""

from uuid import UUID

from fastapi import HTTPException, Request


def resolve_tenant_id(request: Request) -> UUID:
    """Resolve tenant_id from request. Returns UUID or raises HTTPException.

    This is the SINGLE AUTHORITY for tenant resolution.
    Use this in all API endpoints that require tenant context.

    Args:
        request: FastAPI Request object

    Returns:
        UUID: Validated tenant_id

    Raises:
        HTTPException 400: If tenant_id is missing or invalid
    """
    # 1. Auth context wins (human JWT or DB-backed machine key)
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context:
        tenant_id = getattr(auth_context, "tenant_id", None)
        if tenant_id is not None:
            # Already UUID from auth context
            if isinstance(tenant_id, UUID):
                return tenant_id
            # String from auth context (shouldn't happen, but handle it)
            try:
                return UUID(str(tenant_id))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid tenant_id in auth context: {tenant_id}"
                )

    # 2. Machine-plane header fallback (explicit)
    header_tid = request.headers.get("X-Tenant-ID")
    if header_tid:
        try:
            return UUID(header_tid)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid X-Tenant-ID header (must be valid UUID)"
            )

    # 3. Fail closed - never guess
    raise HTTPException(
        status_code=400,
        detail="tenant_id required (provide via auth or X-Tenant-ID header)"
    )


def resolve_tenant_id_optional(request: Request) -> UUID | None:
    """Resolve tenant_id from request, returning None if not present.

    Use this for endpoints where tenant context is optional.

    Args:
        request: FastAPI Request object

    Returns:
        UUID | None: Validated tenant_id or None

    Raises:
        HTTPException 400: If tenant_id is present but invalid
    """
    # 1. Auth context
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context:
        tenant_id = getattr(auth_context, "tenant_id", None)
        if tenant_id is not None:
            if isinstance(tenant_id, UUID):
                return tenant_id
            try:
                return UUID(str(tenant_id))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid tenant_id in auth context: {tenant_id}"
                )

    # 2. Machine-plane header fallback
    header_tid = request.headers.get("X-Tenant-ID")
    if header_tid:
        try:
            return UUID(header_tid)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid X-Tenant-ID header (must be valid UUID)"
            )

    # 3. No tenant context - return None (caller decides what to do)
    return None
