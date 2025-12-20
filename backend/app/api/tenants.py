"""
Tenant & API Key Management API (M21)

Provides:
- Tenant management endpoints
- API key CRUD operations
- Usage and quota queries
- Worker registry endpoints
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..auth.tenant_auth import TenantContext, get_tenant_context
from ..services.tenant_service import (
    QuotaExceededError,
    TenantService,
    TenantServiceError,
)
from ..services.worker_registry_service import (
    WorkerNotFoundError,
    WorkerRegistryService,
)

logger = logging.getLogger("nova.api.tenants")

router = APIRouter(prefix="/api/v1", tags=["Tenants & API Keys"])


# ============== Dependency Injection ==============


def get_db():
    """Get database session."""
    from ..db import get_session

    return next(get_session())


def get_services(
    session: Session = Depends(get_db),
):
    """Get tenant and worker registry services."""
    return {
        "tenant": TenantService(session),
        "registry": WorkerRegistryService(session),
        "session": session,
    }


# ============== Request/Response Schemas ==============


class TenantResponse(BaseModel):
    """Tenant information response."""

    id: str
    name: str
    slug: str
    plan: str
    status: str
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    created_at: str


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


class UsageSummaryResponse(BaseModel):
    """Usage summary for a tenant."""

    tenant_id: str
    period: dict
    meters: dict
    total_records: int


class WorkerSummaryResponse(BaseModel):
    """Worker summary information."""

    id: str
    name: str
    description: Optional[str]
    version: str
    status: str
    moats: List[str]
    tokens_per_run_estimate: Optional[int]
    cost_per_run_cents: Optional[int]


class WorkerDetailResponse(WorkerSummaryResponse):
    """Detailed worker information."""

    is_public: bool
    default_config: dict
    input_schema: dict
    output_schema: dict
    created_at: Optional[str]
    updated_at: Optional[str]


class WorkerConfigRequest(BaseModel):
    """Request to configure a worker for a tenant."""

    enabled: bool = True
    config: Optional[dict] = None
    brand: Optional[dict] = None
    max_runs_per_day: Optional[int] = Field(default=None, ge=1)
    max_tokens_per_run: Optional[int] = Field(default=None, ge=1000)


class WorkerConfigResponse(BaseModel):
    """Worker configuration response."""

    worker_id: str
    enabled: bool
    config: dict
    brand: dict
    max_runs_per_day: Optional[int]
    max_tokens_per_run: Optional[int]


class RunHistoryItem(BaseModel):
    """Run history item."""

    id: str
    worker_id: str
    task: str
    status: str
    success: Optional[bool]
    total_tokens: Optional[int]
    total_latency_ms: Optional[int]
    cost_cents: Optional[int]
    created_at: str
    completed_at: Optional[str]


class QuotaCheckResponse(BaseModel):
    """Quota check response."""

    allowed: bool
    reason: str
    quota_name: str
    current: int
    limit: int


# ============== Tenant Endpoints ==============


@router.get("/tenant", response_model=TenantResponse)
async def get_current_tenant(
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Get information about the current tenant (from API key).
    """
    tenant = services["tenant"].get_tenant(ctx.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        status=tenant.status,
        max_workers=tenant.max_workers,
        max_runs_per_day=tenant.max_runs_per_day,
        max_concurrent_runs=tenant.max_concurrent_runs,
        max_tokens_per_month=tenant.max_tokens_per_month,
        max_api_keys=tenant.max_api_keys,
        runs_today=tenant.runs_today,
        runs_this_month=tenant.runs_this_month,
        tokens_this_month=tenant.tokens_this_month,
        created_at=tenant.created_at.isoformat() if tenant.created_at else "",
    )


@router.get("/tenant/usage", response_model=UsageSummaryResponse)
async def get_tenant_usage(
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Get usage summary for the current tenant.
    """
    summary = services["tenant"].get_usage_summary(ctx.tenant_id)
    return UsageSummaryResponse(**summary)


@router.get("/tenant/quota/runs", response_model=QuotaCheckResponse)
async def check_run_quota(
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Check if the tenant can create a new run.
    """
    tenant = services["tenant"].get_tenant(ctx.tenant_id)
    allowed, reason = services["tenant"].check_run_quota(ctx.tenant_id)

    return QuotaCheckResponse(
        allowed=allowed,
        reason=reason,
        quota_name="runs_per_day",
        current=tenant.runs_today if tenant else 0,
        limit=tenant.max_runs_per_day if tenant else 0,
    )


@router.get("/tenant/quota/tokens", response_model=QuotaCheckResponse)
async def check_token_quota(
    tokens_needed: int = Query(default=10000, ge=1),
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Check if the tenant has token budget for an operation.
    """
    tenant = services["tenant"].get_tenant(ctx.tenant_id)
    allowed, reason = services["tenant"].check_token_quota(ctx.tenant_id, tokens_needed)

    return QuotaCheckResponse(
        allowed=allowed,
        reason=reason,
        quota_name="tokens_per_month",
        current=tenant.tokens_this_month if tenant else 0,
        limit=tenant.max_tokens_per_month if tenant else 0,
    )


# ============== API Key Endpoints ==============


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    include_revoked: bool = False,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    List all API keys for the current tenant.

    Requires admin permission.
    """
    if not ctx.has_permission("admin:*") and not ctx.has_permission("keys:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: requires admin or keys:read permission"
        )

    keys = services["tenant"].list_api_keys(ctx.tenant_id, include_revoked)

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


@router.post("/api-keys", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: APIKeyCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
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

    try:
        full_key, api_key = services["tenant"].create_api_key(
            tenant_id=ctx.tenant_id,
            name=request.name,
            user_id=ctx.user_id,
            permissions=request.permissions,
            allowed_workers=request.allowed_workers,
            expires_in_days=request.expires_in_days,
            rate_limit_rpm=request.rate_limit_rpm,
            max_concurrent_runs=request.max_concurrent_runs,
        )

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

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"API key limit exceeded: {e.limit} keys maximum"
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    reason: str = Query(default="Manual revocation"),
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
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

    try:
        services["tenant"].revoke_api_key(
            key_id=key_id,
            reason=reason,
            user_id=ctx.user_id,
        )
        return {"success": True, "message": f"API key {key_id} revoked"}

    except TenantServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Worker Registry Endpoints ==============


@router.get("/workers", response_model=List[WorkerSummaryResponse])
async def list_workers(
    status: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    List all available workers.
    """
    summaries = services["registry"].list_worker_summaries(status=status)
    return [WorkerSummaryResponse(**s) for s in summaries]


@router.get("/workers/available", response_model=List[dict])
async def list_available_workers_for_tenant(
    include_disabled: bool = False,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    List workers available to the current tenant with their configurations.
    """
    workers = services["registry"].get_workers_for_tenant(
        ctx.tenant_id,
        include_disabled=include_disabled,
    )
    return workers


@router.get("/workers/{worker_id}", response_model=WorkerDetailResponse)
async def get_worker_details(
    worker_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Get detailed information about a specific worker.
    """
    try:
        details = services["registry"].get_worker_details(worker_id)
        return WorkerDetailResponse(**details)
    except WorkerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")


@router.get("/workers/{worker_id}/config", response_model=WorkerConfigResponse)
async def get_worker_config(
    worker_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Get the effective configuration for a worker (tenant overrides merged with defaults).
    """
    try:
        config = services["registry"].get_effective_worker_config(ctx.tenant_id, worker_id)
        return WorkerConfigResponse(**config)
    except WorkerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")


@router.put("/workers/{worker_id}/config", response_model=WorkerConfigResponse)
async def set_worker_config(
    worker_id: str,
    request: WorkerConfigRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    Set tenant-specific configuration for a worker.

    Requires admin permission.
    """
    if not ctx.has_permission("admin:*") and not ctx.has_permission("workers:configure"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: requires admin or workers:configure permission",
        )

    try:
        services["registry"].set_tenant_worker_config(
            tenant_id=ctx.tenant_id,
            worker_id=worker_id,
            enabled=request.enabled,
            config=request.config,
            brand=request.brand,
            max_runs_per_day=request.max_runs_per_day,
            max_tokens_per_run=request.max_tokens_per_run,
        )

        # Return effective config
        config = services["registry"].get_effective_worker_config(ctx.tenant_id, worker_id)
        return WorkerConfigResponse(**config)

    except WorkerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")


# ============== Run History Endpoints ==============


@router.get("/runs", response_model=List[RunHistoryItem])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    worker_id: Optional[str] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    services: dict = Depends(get_services),
):
    """
    List runs for the current tenant.
    """
    runs = services["tenant"].list_runs(
        tenant_id=ctx.tenant_id,
        limit=limit,
        offset=offset,
        status=status,
        worker_id=worker_id,
    )

    return [
        RunHistoryItem(
            id=r.id,
            worker_id=r.worker_id,
            task=r.task[:200],  # Truncate
            status=r.status,
            success=r.success,
            total_tokens=r.total_tokens,
            total_latency_ms=r.total_latency_ms,
            cost_cents=r.cost_cents,
            created_at=r.created_at.isoformat() if r.created_at else "",
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in runs
    ]


# ============== Health Check ==============


@router.get("/tenant/health")
async def tenant_health():
    """
    Health check for tenant system.
    """
    return {
        "status": "healthy",
        "version": "M21",
        "features": [
            "tenant_isolation",
            "api_key_management",
            "quota_enforcement",
            "usage_metering",
            "worker_registry",
        ],
    }
