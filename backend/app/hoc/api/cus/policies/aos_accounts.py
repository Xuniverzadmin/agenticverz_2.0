# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified ACCOUNTS facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: ACCOUNTS - One Facade Architecture, Customer Console v1 Constitution
#
# GOVERNANCE NOTE:
# Account is NOT a domain - it manages who, what, and billing (not what happened).
# This is secondary navigation (top-right or footer), not sidebar.
# Account pages MUST NOT display executions, incidents, policies, or logs.
#
# This is the ONE facade for ACCOUNTS.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Accounts API (L2)

Customer-facing endpoints for account management: projects, users, profile, billing.
All requests are tenant-scoped via auth_context.

IMPORTANT: Account is NOT a domain. It manages:
- WHO (users, profile)
- WHAT (projects)
- BILLING (subscription, invoices)

It does NOT manage or display:
- Executions
- Incidents
- Policies
- Logs

Endpoints:
- GET /api/v1/accounts/projects            → O2 list projects
- GET /api/v1/accounts/projects/{id}       → O3 project detail
- GET /api/v1/accounts/users               → O2 list users
- GET /api/v1/accounts/users/{id}          → O3 user detail
- GET /api/v1/accounts/profile             → Current user profile
- PUT /api/v1/accounts/profile             → Update profile
- GET /api/v1/accounts/billing             → Billing summary
- GET /api/v1/accounts/billing/invoices    → Invoice history

Architecture:
- ONE facade for all ACCOUNTS needs
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

from datetime import datetime, timedelta
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)
from app.models.tenant import (
    Invitation,
    Subscription,
    SupportTicket,
    Tenant,
    TenantMembership,
    User,
    generate_uuid,
    utc_now,
)

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/accounts",
    tags=["accounts"],
)


# =============================================================================
# Helper: Get tenant and user from auth context
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


def get_user_id_from_auth(request: Request) -> str | None:
    """Extract user_id from auth_context. Returns None if not available."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        return None

    return getattr(auth_context, "user_id", None)


# =============================================================================
# Response Models — Projects (O2, O3)
# =============================================================================


class ProjectSummary(BaseModel):
    """O2 Result Shape for projects."""

    project_id: str
    name: str
    description: str | None
    status: str  # ACTIVE, ARCHIVED
    plan: str  # FREE, PRO, ENTERPRISE
    created_at: datetime
    updated_at: datetime | None


class ProjectsListResponse(BaseModel):
    """GET /projects response (O2)."""

    items: List[ProjectSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class ProjectDetailResponse(BaseModel):
    """GET /projects/{id} response (O3)."""

    project_id: str
    name: str
    slug: str
    description: str | None
    status: str
    plan: str
    # Quotas
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    # Usage
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    # Onboarding
    onboarding_state: int
    onboarding_complete: bool
    # Timestamps
    created_at: datetime
    updated_at: datetime | None


# =============================================================================
# Response Models — Users (O2, O3)
# =============================================================================


class UserSummary(BaseModel):
    """O2 Result Shape for users."""

    user_id: str
    email: str
    name: str | None
    role: str  # OWNER, ADMIN, MEMBER, VIEWER
    status: str  # ACTIVE, INVITED, SUSPENDED
    created_at: datetime
    last_login_at: datetime | None


class UsersListResponse(BaseModel):
    """GET /users response (O2)."""

    items: List[UserSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class UserDetailResponse(BaseModel):
    """GET /users/{id} response (O3)."""

    user_id: str
    email: str
    name: str | None
    avatar_url: str | None
    role: str
    status: str
    email_verified: bool
    oauth_provider: str | None
    # Membership
    membership_created_at: datetime
    invited_by: str | None
    # Permissions
    can_manage_keys: bool
    can_run_workers: bool
    can_view_runs: bool
    # Timestamps
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None


# =============================================================================
# Response Models — Profile
# =============================================================================


class ProfileResponse(BaseModel):
    """GET /profile response."""

    user_id: str
    email: str
    name: str | None
    avatar_url: str | None
    tenant_id: str
    tenant_name: str | None
    role: str
    created_at: datetime
    preferences: dict[str, Any] | None


# =============================================================================
# Response Models — Billing
# =============================================================================


class BillingSummaryResponse(BaseModel):
    """GET /billing response."""

    plan: str  # FREE, PRO, ENTERPRISE
    status: str  # ACTIVE, PAST_DUE, CANCELLED
    billing_period: str  # MONTHLY, ANNUAL
    current_period_start: datetime | None
    current_period_end: datetime | None
    usage_this_period: dict[str, Any]
    next_invoice_date: datetime | None
    # Tenant quotas for context
    max_runs_per_day: int
    max_tokens_per_month: int
    runs_this_month: int
    tokens_this_month: int


# =============================================================================
# GET /projects - O2 Projects List
# =============================================================================


@router.get(
    "/projects",
    response_model=ProjectsListResponse,
    summary="List projects (O2)",
    description="""
    Returns list of projects (tenants) the user has access to.

    In the current architecture, Tenant serves as the project context.
    Most users belong to a single tenant/project.
    """,
)
async def list_projects(
    request: Request,
    # Filters
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: active, suspended",
            pattern="^(active|suspended)$",
        ),
    ] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> ProjectsListResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_projects",
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
            ProjectSummary(
                project_id=p.project_id,
                name=p.name,
                description=p.description,
                status=p.status,
                plan=p.plan,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in result.items
        ]

        return ProjectsListResponse(
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
# GET /projects/{project_id} - O3 Project Detail
# =============================================================================


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get project detail (O3)",
    description="Returns detailed project info including quotas and usage.",
)
async def get_project_detail(
    request: Request,
    project_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ProjectDetailResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_project_detail",
                    "project_id": project_id,
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
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Cannot access other projects."},
            )

        return ProjectDetailResponse(
            project_id=result.project_id,
            name=result.name,
            slug=result.slug,
            description=result.description,
            status=result.status,
            plan=result.plan,
            max_workers=result.max_workers,
            max_runs_per_day=result.max_runs_per_day,
            max_concurrent_runs=result.max_concurrent_runs,
            max_tokens_per_month=result.max_tokens_per_month,
            max_api_keys=result.max_api_keys,
            runs_today=result.runs_today,
            runs_this_month=result.runs_this_month,
            tokens_this_month=result.tokens_this_month,
            onboarding_state=result.onboarding_state,
            onboarding_complete=result.onboarding_complete,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /users - O2 Users List
# =============================================================================


@router.get(
    "/users",
    response_model=UsersListResponse,
    summary="List users (O2)",
    description="Returns list of users in the tenant.",
)
async def list_users(
    request: Request,
    # Filters
    role: Annotated[
        Optional[str],
        Query(
            description="Filter by role: owner, admin, member, viewer",
            pattern="^(owner|admin|member|viewer)$",
        ),
    ] = None,
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: active, suspended",
            pattern="^(active|suspended)$",
        ),
    ] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> UsersListResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_users",
                    "role": role,
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
            UserSummary(
                user_id=u.user_id,
                email=u.email,
                name=u.name,
                role=u.role,
                status=u.status,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
            )
            for u in result.items
        ]

        return UsersListResponse(
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
# GET /users/{user_id} - O3 User Detail
# =============================================================================


@router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user detail (O3)",
    description="Returns detailed user info including permissions.",
)
async def get_user_detail(
    request: Request,
    user_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> UserDetailResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_user_detail",
                    "user_id": user_id,
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
            raise HTTPException(status_code=404, detail="User not found in this tenant")

        return UserDetailResponse(
            user_id=result.user_id,
            email=result.email,
            name=result.name,
            avatar_url=result.avatar_url,
            role=result.role,
            status=result.status,
            email_verified=result.email_verified,
            oauth_provider=result.oauth_provider,
            membership_created_at=result.membership_created_at,
            invited_by=result.invited_by,
            can_manage_keys=result.can_manage_keys,
            can_run_workers=result.can_run_workers,
            can_view_runs=result.can_view_runs,
            created_at=result.created_at,
            updated_at=result.updated_at,
            last_login_at=result.last_login_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /profile - Current User Profile
# =============================================================================


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get current user profile",
    description="Returns profile of the authenticated user.",
)
async def get_profile(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ProfileResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)
    clerk_user_id = get_user_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_profile",
                    "clerk_user_id": clerk_user_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        return ProfileResponse(
            user_id=result.user_id,
            email=result.email,
            name=result.name,
            avatar_url=result.avatar_url,
            tenant_id=result.tenant_id,
            tenant_name=result.tenant_name,
            role=result.role,
            created_at=result.created_at,
            preferences=result.preferences,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /billing - Billing Summary
# =============================================================================


@router.get(
    "/billing",
    response_model=BillingSummaryResponse,
    summary="Get billing summary",
    description="Returns billing summary for the tenant.",
)
async def get_billing_summary(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> BillingSummaryResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    tenant_id = get_tenant_id_from_auth(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_billing_summary",
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error result
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(status_code=result.status_code, detail=result.message)

        return BillingSummaryResponse(
            plan=result.plan,
            status=result.status,
            billing_period=result.billing_period,
            current_period_start=result.current_period_start,
            current_period_end=result.current_period_end,
            usage_this_period=result.usage_this_period,
            next_invoice_date=result.next_invoice_date,
            max_runs_per_day=result.max_runs_per_day,
            max_tokens_per_month=result.max_tokens_per_month,
            runs_this_month=result.runs_this_month,
            tokens_this_month=result.tokens_this_month,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile preferences."""

    display_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    preferences: Optional[dict] = Field(None, description="User preferences as JSON")


class ProfileUpdateResponse(BaseModel):
    """Profile update response."""

    user_id: str
    email: str
    display_name: Optional[str]
    timezone: Optional[str]
    preferences: dict
    updated_at: datetime


@router.put("/profile", response_model=ProfileUpdateResponse)
async def update_profile(
    request: Request,
    update: ProfileUpdateRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ProfileUpdateResponse:
    """WRITE customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)
    user_id = auth_ctx.user_id

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "update_profile",
                    "user_id": user_id,
                    "display_name": update.display_name,
                    "timezone_str": update.timezone,
                    "preferences": update.preferences,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error result
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(status_code=result.status_code, detail=result.message)

        return ProfileUpdateResponse(
            user_id=result.user_id,
            email=result.email,
            display_name=result.display_name,
            timezone=result.timezone,
            preferences=result.preferences,
            updated_at=result.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "update_failed", "message": str(e)},
        )


# =============================================================================
# BILLING - INVOICES (Free Tier = Unlimited)
# =============================================================================


class InvoiceSummary(BaseModel):
    """Invoice summary for billing history."""

    invoice_id: str
    period_start: datetime
    period_end: datetime
    amount_cents: int
    status: str  # paid, pending, void
    description: str


class InvoiceListResponse(BaseModel):
    """List of invoices response."""

    invoices: List[InvoiceSummary]
    total: int
    message: Optional[str] = None


@router.get("/billing/invoices", response_model=InvoiceListResponse)
async def get_billing_invoices(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> InvoiceListResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)
    tenant_id = auth_ctx.tenant_id

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_billing_invoices",
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error result
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(status_code=result.status_code, detail=result.message)

        # Map L4 result to L2 response
        invoices = [
            InvoiceSummary(
                invoice_id=inv.invoice_id,
                period_start=inv.period_start,
                period_end=inv.period_end,
                amount_cents=inv.amount_cents,
                status=inv.status,
                description=inv.description,
            )
            for inv in result.invoices
        ]

        return InvoiceListResponse(
            invoices=invoices,
            total=result.total,
            message=result.message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# SUPPORT TICKETS (CRM Workflow Integration)
# =============================================================================


class SupportTicketCreate(BaseModel):
    """Create a support ticket."""

    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=4000)
    category: str = Field(default="general", max_length=50)
    priority: str = Field(default="medium", max_length=20)


class SupportTicketResponse(BaseModel):
    """Support ticket response."""

    id: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class SupportTicketListResponse(BaseModel):
    """List of support tickets."""

    tickets: List[SupportTicketResponse]
    total: int


class SupportContactResponse(BaseModel):
    """Support contact information."""

    email: str
    hours: str
    response_time: str


@router.get("/support", response_model=SupportContactResponse)
def get_support_contact() -> SupportContactResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    registry = get_operation_registry()
    op = registry.execute_sync(
        "account.query",
        OperationContext(
            session=None,
            tenant_id=None,
            params={
                "method": "get_support_contact",
            },
        ),
    )
    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={"error": "operation_failed", "message": op.error},
        )
    result = op.data

    return SupportContactResponse(
        email=result.email,
        hours=result.hours,
        response_time=result.response_time,
    )


@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=201)
async def create_support_ticket(
    request: Request,
    ticket: SupportTicketCreate,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SupportTicketResponse:
    """WRITE customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "create_support_ticket",
                    "user_id": auth_ctx.user_id,
                    "subject": ticket.subject,
                    "description": ticket.description,
                    "category": ticket.category,
                    "priority": ticket.priority,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        return SupportTicketResponse(
            id=result.id,
            subject=result.subject,
            description=result.description,
            category=result.category,
            priority=result.priority,
            status=result.status,
            created_at=result.created_at,
            updated_at=result.updated_at,
            resolution=result.resolution,
            resolved_at=result.resolved_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "create_failed", "message": str(e)},
        )


@router.get("/support/tickets", response_model=SupportTicketListResponse)
async def list_support_tickets(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session_dep),
) -> SupportTicketListResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "list_support_tickets",
                    "status": status,
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
        tickets = [
            SupportTicketResponse(
                id=t.id,
                subject=t.subject,
                description=t.description,
                category=t.category,
                priority=t.priority,
                status=t.status,
                created_at=t.created_at,
                updated_at=t.updated_at,
                resolution=t.resolution,
                resolved_at=t.resolved_at,
            )
            for t in result.tickets
        ]

        return SupportTicketListResponse(
            tickets=tickets,
            total=result.total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# USER INVITATION & MANAGEMENT
# =============================================================================


class InviteUserRequest(BaseModel):
    """Request to invite a user to the tenant."""

    email: str = Field(..., max_length=255)
    role: str = Field(default="member", max_length=50)


class InvitationResponse(BaseModel):
    """Invitation response."""

    id: str
    email: str
    role: str
    status: str
    created_at: datetime
    expires_at: datetime
    invited_by: str


class InvitationListResponse(BaseModel):
    """List of invitations."""

    invitations: List[InvitationResponse]
    total: int


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""

    token: str = Field(..., description="Invitation token from email")


class UpdateUserRoleRequest(BaseModel):
    """Request to update a user's role."""

    role: str = Field(..., max_length=50)


class TenantUserResponse(BaseModel):
    """User in tenant response."""

    user_id: str
    email: str
    name: Optional[str]
    role: str
    joined_at: datetime


class TenantUserListResponse(BaseModel):
    """List of users in tenant."""

    users: List[TenantUserResponse]
    total: int


@router.post("/users/invite", response_model=InvitationResponse, status_code=201)
async def invite_user(
    request: Request,
    invite: InviteUserRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> InvitationResponse:
    """WRITE customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "invite_user",
                    "caller_user_id": auth_ctx.user_id,
                    "email": invite.email,
                    "role": invite.role,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error result
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(status_code=result.status_code, detail=result.message)

        return InvitationResponse(
            id=result.id,
            email=result.email,
            role=result.role,
            status=result.status,
            created_at=result.created_at,
            expires_at=result.expires_at,
            invited_by=result.invited_by,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "invite_failed", "message": str(e)},
        )


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session_dep),
) -> InvitationListResponse:
    """READ-ONLY customer facade - delegates to L4 AccountsFacade."""
    auth_ctx = get_auth_context(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "list_invitations",
                    "caller_user_id": auth_ctx.user_id,
                    "status": status,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error result
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(status_code=result.status_code, detail=result.message)

        # Map L4 result to L2 response
        invitations = [
            InvitationResponse(
                id=inv.id,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                invited_by=inv.invited_by,
            )
            for inv in result.invitations
        ]

        return InvitationListResponse(
            invitations=invitations,
            total=result.total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


@router.post("/invitations/{invitation_id}/accept", status_code=200)
async def accept_invitation(
    invitation_id: str,
    accept: AcceptInvitationRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> dict:
    """
    Accept an invitation to join a tenant.

    This is a public endpoint (no auth required) as the user
    may not have an account yet.

    Layer: L2 (Product APIs) — delegates to L4 AccountsFacade
    """
    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=None,
                params={
                    "method": "accept_invitation",
                    "invitation_id": invitation_id,
                    "token": accept.token,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle failure cases
        if not result.success:
            # Determine status code based on message
            if "expired" in result.message.lower():
                status_code = 410
            elif "invalid" in result.message.lower():
                status_code = 404
            else:
                status_code = 400
            raise HTTPException(status_code=status_code, detail=result.message)

        # Build response
        response: dict = {"message": result.message}
        if result.tenant_id:
            response["tenant_id"] = result.tenant_id
        if result.role:
            response["role"] = result.role

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "accept_failed", "message": str(e)},
        )


@router.get("/users", response_model=TenantUserListResponse)
async def list_tenant_users(
    request: Request,
    session: AsyncSession = Depends(get_async_session_dep),
) -> TenantUserListResponse:
    """
    List users in the current tenant.

    Layer: L2 (Product APIs) — delegates to L4 AccountsFacade
    """
    auth_ctx = get_auth_context(request)

    try:
        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "list_tenant_users",
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
        return TenantUserListResponse(
            users=[
                TenantUserResponse(
                    user_id=u.user_id,
                    email=u.email,
                    name=u.name,
                    role=u.role,
                    joined_at=u.joined_at,
                )
                for u in result.users
            ],
            total=result.total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


@router.put("/users/{user_id}/role", response_model=TenantUserResponse)
async def update_user_role(
    request: Request,
    user_id: str,
    update: UpdateUserRoleRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> TenantUserResponse:
    """
    Update a user's role in the tenant.

    Requires: owner role.

    Layer: L2 (Product APIs) — delegates to L4 AccountsFacade
    """
    auth_ctx = get_auth_context(request)

    try:
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult

        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "update_user_role",
                    "caller_user_id": auth_ctx.user_id,
                    "target_user_id": user_id,
                    "new_role": update.role,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error results
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(
                status_code=result.status_code,
                detail=result.message,
            )

        # Map L4 result to L2 response
        return TenantUserResponse(
            user_id=result.user_id,
            email=result.email,
            name=result.name,
            role=result.role,
            joined_at=result.joined_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "update_failed", "message": str(e)},
        )


@router.delete("/users/{user_id}", status_code=200)
async def remove_user(
    request: Request,
    user_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> dict:
    """
    Remove a user from the tenant.

    Requires: owner or admin role.

    Layer: L2 (Product APIs) — delegates to L4 AccountsFacade
    """
    auth_ctx = get_auth_context(request)

    try:
        # L5 engine import (migrated to HOC per SWEEP-29)
        from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult

        registry = get_operation_registry()
        op = await registry.execute(
            "account.query",
            OperationContext(
                session=session,
                tenant_id=auth_ctx.tenant_id,
                params={
                    "method": "remove_user",
                    "caller_user_id": auth_ctx.user_id,
                    "target_user_id": user_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )
        result = op.data

        # Handle error results
        if isinstance(result, AccountsErrorResult):
            raise HTTPException(
                status_code=result.status_code,
                detail=result.message,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "remove_failed", "message": str(e)},
        )
