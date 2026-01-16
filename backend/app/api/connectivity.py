# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified CONNECTIVITY domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: CONNECTIVITY Domain - One Facade Architecture, Customer Console v1 Constitution
#
# GOVERNANCE NOTE:
# This is the ONE facade for CONNECTIVITY domain.
# All integrations and API keys data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Connectivity API (L2)

Customer-facing endpoints for managing integrations and API keys.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/connectivity/integrations           → O2 list integrations (SDK/workers)
- GET /api/v1/connectivity/integrations/{id}      → O3 integration detail
- GET /api/v1/connectivity/api-keys               → O2 list API keys
- GET /api/v1/connectivity/api-keys/{id}          → O3 API key detail

Architecture:
- ONE facade for all CONNECTIVITY needs (integrations + api-keys)
- Queries WorkerRegistry, WorkerConfig, APIKey tables
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.tenant import APIKey, WorkerConfig, WorkerRegistry

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/connectivity",
    tags=["connectivity"],
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
# Response Models — Integrations (O2, O3)
# =============================================================================


class IntegrationSummary(BaseModel):
    """O2 Result Shape for integrations (SDK/workers)."""

    integration_id: str
    name: str
    description: Optional[str]
    integration_type: str  # SDK, WORKER, WEBHOOK
    version: str
    status: str  # INSTALLED, AVAILABLE, COMING_SOON, DEPRECATED
    is_enabled: bool  # Tenant-specific enablement
    created_at: datetime
    last_used_at: Optional[datetime]


class IntegrationsListResponse(BaseModel):
    """GET /integrations response (O2)."""

    items: List[IntegrationSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class IntegrationDetailResponse(BaseModel):
    """GET /integrations/{id} response (O3)."""

    integration_id: str
    name: str
    description: Optional[str]
    integration_type: str
    version: str
    status: str
    is_enabled: bool
    is_public: bool
    # Configuration
    default_config: Optional[dict]
    tenant_config: Optional[dict]
    input_schema: Optional[dict]
    output_schema: Optional[dict]
    # Pricing
    tokens_per_run_estimate: Optional[int]
    cost_per_run_cents: Optional[int]
    # Tenant-specific limits
    max_runs_per_day: Optional[int]
    max_tokens_per_run: Optional[int]
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]


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
# GET /integrations - O2 Integrations List
# =============================================================================


@router.get(
    "/integrations",
    response_model=IntegrationsListResponse,
    summary="List integrations (O2)",
    description="""
    Returns list of SDK/worker integrations available and installed for the tenant.

    Integrations include:
    - AOS SDK (manages LLM provider, API keys, infra setup)
    - Workers (business-builder, etc.)
    """,
)
async def list_integrations(
    request: Request,
    # Filters
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: INSTALLED, AVAILABLE, COMING_SOON, DEPRECATED",
            pattern="^(INSTALLED|AVAILABLE|COMING_SOON|DEPRECATED)$",
        ),
    ] = None,
    is_enabled: Annotated[Optional[bool], Query(description="Filter by enabled state")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> IntegrationsListResponse:
    """List integrations. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Query WorkerRegistry with optional WorkerConfig join for tenant-specific state
        stmt = (
            select(
                WorkerRegistry.id.label("integration_id"),
                WorkerRegistry.name,
                WorkerRegistry.description,
                WorkerRegistry.version,
                WorkerRegistry.status.label("registry_status"),
                WorkerRegistry.is_public,
                WorkerRegistry.created_at,
                WorkerConfig.enabled.label("is_enabled"),
                WorkerConfig.updated_at.label("last_used_at"),
            )
            .outerjoin(
                WorkerConfig, (WorkerConfig.worker_id == WorkerRegistry.id) & (WorkerConfig.tenant_id == tenant_id)
            )
            .order_by(WorkerRegistry.name)
        )

        # Status filter - map to registry status or tenant installation status
        if status == "INSTALLED":
            stmt = stmt.where(WorkerConfig.id.isnot(None))
            filters_applied["status"] = "INSTALLED"
        elif status == "AVAILABLE":
            stmt = stmt.where((WorkerConfig.id.is_(None)) & (WorkerRegistry.status == "available"))
            filters_applied["status"] = "AVAILABLE"
        elif status == "COMING_SOON":
            stmt = stmt.where(WorkerRegistry.status == "coming_soon")
            filters_applied["status"] = "COMING_SOON"
        elif status == "DEPRECATED":
            stmt = stmt.where(WorkerRegistry.status == "deprecated")
            filters_applied["status"] = "DEPRECATED"

        if is_enabled is not None:
            if is_enabled:
                stmt = stmt.where(WorkerConfig.enabled == True)  # noqa: E712
            else:
                stmt = stmt.where(
                    (WorkerConfig.enabled == False)  # noqa: E712
                    | (WorkerConfig.id.is_(None))
                )
            filters_applied["is_enabled"] = is_enabled

        # Count total
        count_stmt = select(func.count(WorkerRegistry.id))
        if status == "INSTALLED":
            count_subq = select(WorkerConfig.worker_id).where(WorkerConfig.tenant_id == tenant_id).subquery()
            count_stmt = count_stmt.where(WorkerRegistry.id.in_(select(count_subq.c.worker_id)))

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            # Determine status based on tenant config existence
            if row.is_enabled is not None:
                display_status = "INSTALLED"
            elif row.registry_status == "available":
                display_status = "AVAILABLE"
            elif row.registry_status == "coming_soon":
                display_status = "COMING_SOON"
            elif row.registry_status == "deprecated":
                display_status = "DEPRECATED"
            else:
                display_status = row.registry_status.upper() if row.registry_status else "AVAILABLE"

            items.append(
                IntegrationSummary(
                    integration_id=row.integration_id,
                    name=row.name,
                    description=row.description,
                    integration_type="WORKER",  # All registry items are workers/SDK
                    version=row.version,
                    status=display_status,
                    is_enabled=row.is_enabled if row.is_enabled is not None else False,
                    created_at=row.created_at,
                    last_used_at=row.last_used_at,
                )
            )

        return IntegrationsListResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /integrations/{integration_id} - O3 Integration Detail
# =============================================================================


@router.get(
    "/integrations/{integration_id}",
    response_model=IntegrationDetailResponse,
    summary="Get integration detail (O3)",
    description="Returns detailed integration info including configuration and pricing.",
)
async def get_integration_detail(
    request: Request,
    integration_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> IntegrationDetailResponse:
    """Get integration detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        import json

        # Query registry with optional tenant config
        stmt = (
            select(WorkerRegistry, WorkerConfig)
            .outerjoin(
                WorkerConfig, (WorkerConfig.worker_id == WorkerRegistry.id) & (WorkerConfig.tenant_id == tenant_id)
            )
            .where(WorkerRegistry.id == integration_id)
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Integration not found")

        registry: WorkerRegistry = row[0]
        config: Optional[WorkerConfig] = row[1]

        # Determine status
        if config is not None:
            display_status = "INSTALLED"
            is_enabled = config.enabled
        elif registry.status == "available":
            display_status = "AVAILABLE"
            is_enabled = False
        else:
            display_status = registry.status.upper() if registry.status else "AVAILABLE"
            is_enabled = False

        # Parse JSON fields
        default_config = json.loads(registry.default_config_json) if registry.default_config_json else None
        tenant_config = json.loads(config.config_json) if config and config.config_json else None
        input_schema = json.loads(registry.input_schema_json) if registry.input_schema_json else None
        output_schema = json.loads(registry.output_schema_json) if registry.output_schema_json else None

        return IntegrationDetailResponse(
            integration_id=registry.id,
            name=registry.name,
            description=registry.description,
            integration_type="WORKER",
            version=registry.version,
            status=display_status,
            is_enabled=is_enabled,
            is_public=registry.is_public,
            default_config=default_config,
            tenant_config=tenant_config,
            input_schema=input_schema,
            output_schema=output_schema,
            tokens_per_run_estimate=registry.tokens_per_run_estimate,
            cost_per_run_cents=registry.cost_per_run_cents,
            max_runs_per_day=config.max_runs_per_day if config else None,
            max_tokens_per_run=config.max_tokens_per_run if config else None,
            created_at=registry.created_at,
            updated_at=config.updated_at if config else registry.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /api-keys - O2 API Keys List
# =============================================================================


@router.get(
    "/api-keys",
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
    """List API keys. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Base query - exclude synthetic keys from customer view
        stmt = (
            select(APIKey)
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
            .order_by(APIKey.created_at.desc())
        )

        if status is not None:
            stmt = stmt.where(APIKey.status == status)
            filters_applied["status"] = status

        # Count total
        count_stmt = (
            select(func.count(APIKey.id)).where(APIKey.tenant_id == tenant_id).where(APIKey.is_synthetic == False)  # noqa: E712
        )
        if status is not None:
            count_stmt = count_stmt.where(APIKey.status == status)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        keys = result.scalars().all()

        items = [
            APIKeySummary(
                key_id=key.id,
                name=key.name,
                prefix=key.key_prefix,
                status=key.status.upper(),
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                total_requests=key.total_requests,
            )
            for key in keys
        ]

        return APIKeysListResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
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
    "/api-keys/{key_id}",
    response_model=APIKeyDetailResponse,
    summary="Get API key detail (O3)",
    description="Returns detailed API key info including permissions and rate limits.",
)
async def get_api_key_detail(
    request: Request,
    key_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> APIKeyDetailResponse:
    """Get API key detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        import json

        stmt = (
            select(APIKey)
            .where(APIKey.id == key_id)
            .where(APIKey.tenant_id == tenant_id)
            .where(APIKey.is_synthetic == False)  # noqa: E712
        )

        result = await session.execute(stmt)
        key = result.scalar_one_or_none()

        if key is None:
            raise HTTPException(status_code=404, detail="API key not found")

        # Parse JSON fields
        permissions = json.loads(key.permissions_json) if key.permissions_json else None
        allowed_workers = json.loads(key.allowed_workers_json) if key.allowed_workers_json else None

        return APIKeyDetailResponse(
            key_id=key.id,
            name=key.name,
            prefix=key.key_prefix,
            status=key.status.upper(),
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            total_requests=key.total_requests,
            permissions=permissions,
            allowed_workers=allowed_workers,
            rate_limit_rpm=key.rate_limit_rpm,
            max_concurrent_runs=key.max_concurrent_runs,
            revoked_at=key.revoked_at,
            revoked_reason=key.revoked_reason,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )
