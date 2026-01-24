# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: system-wide (dogfood)
# Temporal:
#   Trigger: none (DEPRECATED)
#   Execution: none (DEPRECATED)
# Role: M17 Internal Worker Registry - WorkerRegistry/WorkerConfig catalog (DEPRECATED)
# Callers: None - NOT registered in main.py
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: M17 milestone
#
# DEPRECATION NOTE:
# This file is DEPRECATED and NOT served via any route.
# It was originally split from connectivity.py but represents internal
# worker registry data (WorkerRegistry, WorkerConfig tables) which is
# dogfood/internal infrastructure, NOT customer-facing integrations.
#
# The actual customer-facing LLM integration API is in aos_cus_integrations.py
# which handles customer BYOK (Bring Your Own Key) LLM provider management.
#
# STATUS: DEPRECATED - Code preserved for reference only.
# ROUTES: NONE - Router not registered in main.py.

"""
M17 Internal Worker Registry (DEPRECATED)

STATUS: DEPRECATED - Not served via any route.

This file contained read-only endpoints for viewing WorkerRegistry
and WorkerConfig tables. This is internal infrastructure for the
AOS worker system, not customer-facing integration management.

Original Endpoints (NO LONGER SERVED):
- GET /api/v1/integrations           → Listed workers from WorkerRegistry
- GET /api/v1/integrations/{id}      → Worker detail with WorkerConfig

Tables:
- WorkerRegistry: Available workers (business-builder, etc.)
- WorkerConfig: Per-tenant worker configuration/limits

For customer LLM integration management, see: aos_cus_integrations.py
"""

from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.tenant import WorkerConfig, WorkerRegistry

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integrations"],
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
# GET /integrations - O2 Integrations List
# =============================================================================


@router.get(
    "",
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
    "/{integration_id}",
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
