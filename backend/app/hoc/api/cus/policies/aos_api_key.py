# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified API KEYS facade - Customer Console Connectivity Domain (API Keys)
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution
#
# GOVERNANCE NOTE:
# This is the ONE facade for API KEYS in the Connectivity domain.
# All API key data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.
#
# SPLIT NOTE:
# This file was split from connectivity.py to separate concerns:
# - integrations.py: SDK/worker integrations
# - aos_api_key.py: API key management (this file)

"""
API Keys API (L2) - Connectivity Domain

Customer-facing endpoints for managing API keys.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/api-keys           → O2 list API keys
- GET /api/v1/api-keys/{id}      → O3 API key detail

Architecture:
- ONE facade for API KEYS in Connectivity domain
- Queries APIKey table
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/api-keys",
    tags=["api-keys"],
)


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# Response Models — API Keys (O2, O3)
# =============================================================================


class APIKeySummary(BaseModel):
    """O2 Result Shape for API keys."""

    key_id: str
    name: str
    prefix: str  # First 12 chars for identification (aos_xxxxxxxx)
    status: str  # ACTIVE, REVOKED, EXPIRED
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int


class APIKeysListResponse(BaseModel):
    """GET /api-keys response (O2)."""

    items: List[APIKeySummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class APIKeyDetailResponse(BaseModel):
    """GET /api-keys/{id} response (O3)."""

    key_id: str
    name: str
    prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    # Permissions
    permissions: Optional[List[str]]
    allowed_workers: Optional[List[str]]
    # Rate limits
    rate_limit_rpm: Optional[int]
    max_concurrent_runs: Optional[int]
    # Revocation info (if revoked)
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]


# =============================================================================
# GET /api-keys - O2 API Keys List
# =============================================================================


@router.get(
    "",
    response_model=APIKeysListResponse,
    summary="List API keys (O2)",
    description="""
    Returns list of API keys for the tenant.

    API keys are used for:
    - SDK authentication
    - Programmatic access to AOS APIs
    - RBAC-controlled permissions
    """,
)
async def list_api_keys(
    request: Request,
    # Filters
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: active, revoked, expired",
            pattern="^(active|revoked|expired)$",
        ),
    ] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> APIKeysListResponse:
    """List API keys. READ-ONLY. Delegates to L4 operation registry."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "api_keys.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_api_keys",
                    "status": status,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Map L4 result to L2 response
        items = [
            APIKeySummary(
                key_id=k.key_id,
                name=k.name,
                prefix=k.prefix,
                status=k.status,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                expires_at=k.expires_at,
                total_requests=k.total_requests,
            )
            for k in result.items
        ]

        return APIKeysListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /api-keys/{key_id} - O3 API Key Detail
# =============================================================================


@router.get(
    "/{key_id}",
    response_model=APIKeyDetailResponse,
    summary="Get API key detail (O3)",
    description="Returns detailed API key info including permissions and rate limits.",
)
async def get_api_key_detail(
    request: Request,
    key_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> APIKeyDetailResponse:
    """Get API key detail (O3). Delegates to L4 operation registry."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "api_keys.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_api_key_detail",
                    "key_id": key_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        if result is None:
            raise HTTPException(status_code=404, detail="API key not found")

        # Map L4 result to L2 response
        return APIKeyDetailResponse(
            key_id=result.key_id,
            name=result.name,
            prefix=result.prefix,
            status=result.status,
            created_at=result.created_at,
            last_used_at=result.last_used_at,
            expires_at=result.expires_at,
            total_requests=result.total_requests,
            permissions=result.permissions,
            allowed_workers=result.allowed_workers,
            rate_limit_rpm=result.rate_limit_rpm,
            max_concurrent_runs=result.max_concurrent_runs,
            revoked_at=result.revoked_at,
            revoked_reason=result.revoked_reason,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )
