# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: API key write operations (create, list-with-revoked, revoke)
# Callers: Console UI, SDK
# Allowed Imports: L4
# Forbidden Imports: L1, L5, L6
#
# GOVERNANCE NOTE:
# Extracted from logs/tenants.py (Phase 1.4 domain repair plan).
# Write operations for API keys now live under the api_keys/ domain directory.
# URL prefix stays /tenant/api-keys for backward compatibility.

"""
API Key Write Operations (L2)

Extracted from logs/tenants.py to establish domain authority under api_keys/.

Endpoints:
- GET    /tenant/api-keys            → List API keys (with revoked filter)
- POST   /tenant/api-keys            → Create new API key
- DELETE  /tenant/api-keys/{key_id}  → Revoke API key
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_sync_session_dep,
)
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.api_key_writes")

# API KEY SURFACE POLICY INVARIANT (UC-002, closed — not deferred):
# This router serves WRITE endpoints at /tenant/api-keys.
# Only POST (create) triggers onboarding advancement via _maybe_advance_to_api_key_created.
# Read-only flows (aos_api_key.py at /api-keys) do NOT trigger onboarding advancement.
# The split is intentional and canonical: domain authority by directory,
# URL prefix by backward compatibility.
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 3
router = APIRouter(prefix="/tenant/api-keys", tags=["API Keys (Write)"])


# =============================================================================
# L4 Registry Dispatch Helper
# =============================================================================


async def _api_keys_op(session, tenant_id: str, method: str, **kwargs):
    """Execute an API keys operation via L4 registry (api_keys.write)."""
    registry = get_operation_registry()
    return await registry.execute(
        "api_keys.write",
        OperationContext(
            session=None,
            tenant_id=tenant_id,
            params={"method": method, "sync_session": session, "tenant_id": tenant_id, **kwargs},
        ),
    )


# =============================================================================
# Onboarding Transition Helper
# =============================================================================


async def _maybe_advance_to_api_key_created(tenant_id: str) -> None:
    """
    PIN-399: Trigger onboarding state transition on first API key creation.

    Called after successful API key creation to potentially advance
    a tenant from IDENTITY_VERIFIED to API_KEY_CREATED.

    This is idempotent - if tenant is already at or past API_KEY_CREATED,
    this is a no-op.
    """
    try:
        # Phase A2: Onboarding SSOT
        from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
            async_advance_onboarding,
        )
        from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingStatus

        result = await async_advance_onboarding(
            tenant_id,
            OnboardingStatus.API_KEY_CREATED.value,
            "first_api_key_created",
        )

        if result["success"] and not result.get("was_no_op"):
            logger.info(
                "onboarding_advanced_on_api_key_creation",
                extra={
                    "tenant_id": tenant_id,
                    "from_state": result.get("from_state"),
                    "to_state": result.get("to_state"),
                },
            )

    except Exception as e:
        # Onboarding transition failure should not block API key creation
        logger.warning(f"Failed to advance onboarding state on API key creation: {e}")


# =============================================================================
# Request/Response Schemas
# =============================================================================


class APIKeyCreateRequest(BaseModel):
    """Request to create an API key."""

    name: str = Field(..., min_length=1, max_length=100)
    permissions: Optional[List[str]] = Field(default=None)
    allowed_workers: Optional[List[str]] = Field(default=None)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)
    rate_limit_rpm: Optional[int] = Field(default=None, ge=1, le=1000)
    max_concurrent_runs: Optional[int] = Field(default=None, ge=1, le=100)


class APIKeyResponse(BaseModel):
    """API key information (without the actual key)."""

    id: str
    name: str
    key_prefix: str
    status: str
    last_used_at: Optional[str]
    total_requests: int
    expires_at: Optional[str]
    created_at: str


class APIKeyCreatedResponse(APIKeyResponse):
    """Response when creating an API key (includes the key once)."""

    key: str = Field(..., description="The full API key. Store this securely - it won't be shown again!")


# =============================================================================
# GET /tenant/api-keys — List API keys
# =============================================================================


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    include_revoked: bool = False,
    ctx: TenantContext = Depends(get_tenant_context),
    session=Depends(get_sync_session_dep),
):
    """
    List all API keys for the current tenant.

    Requires admin permission.
    """
    if not ctx.has_permission("admin:*") and not ctx.has_permission("keys:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: requires admin or keys:read permission"
        )

    result = await _api_keys_op(
        session, ctx.tenant_id, "list_api_keys",
        include_revoked=include_revoked,
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    keys = result.data

    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            status=k.status,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            total_requests=k.total_requests,
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            created_at=k.created_at.isoformat() if k.created_at else "",
        )
        for k in keys
    ]


# =============================================================================
# POST /tenant/api-keys — Create API key
# =============================================================================


@router.post("", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: APIKeyCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session=Depends(get_sync_session_dep),
):
    """
    Create a new API key for the current tenant.

    **Important:** The full API key is only shown once in this response.
    Store it securely!

    Requires admin permission.
    """
    if not ctx.has_permission("admin:*") and not ctx.has_permission("keys:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: requires admin or keys:create permission"
        )

    result = await _api_keys_op(
        session, ctx.tenant_id, "create_api_key",
        name=request.name, user_id=ctx.user_id,
        permissions=request.permissions, allowed_workers=request.allowed_workers,
        expires_in_days=request.expires_in_days, rate_limit_rpm=request.rate_limit_rpm,
        max_concurrent_runs=request.max_concurrent_runs,
    )
    if not result.success:
        if result.error_code == "QUOTA_EXCEEDED":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"API key limit exceeded: {result.error}"
            )
        raise HTTPException(status_code=500, detail=result.error)

    full_key = result.data["full_key"]
    api_key = result.data["api_key"]

    # PIN-399: Trigger onboarding state transition on first API key creation
    await _maybe_advance_to_api_key_created(ctx.tenant_id)

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=full_key,
        status=api_key.status,
        last_used_at=None,
        total_requests=0,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat() if api_key.created_at else "",
    )


# =============================================================================
# DELETE /tenant/api-keys/{key_id} — Revoke API key
# =============================================================================


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    reason: str = Query(default="Manual revocation"),
    ctx: TenantContext = Depends(get_tenant_context),
    session=Depends(get_sync_session_dep),
):
    """
    Revoke an API key.

    The key cannot be un-revoked. Create a new key instead.

    Requires admin permission.
    """
    if not ctx.has_permission("admin:*") and not ctx.has_permission("keys:revoke"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: requires admin or keys:revoke permission"
        )

    result = await _api_keys_op(
        session, ctx.tenant_id, "revoke_api_key",
        key_id=key_id, reason=reason, user_id=ctx.user_id,
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    return wrap_dict({"success": True, "message": f"API key {key_id} revoked"})
