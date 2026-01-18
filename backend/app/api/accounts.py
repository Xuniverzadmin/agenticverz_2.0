# Layer: L2 — Product APIs
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
    """List projects (tenants). READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Query tenant (current user's tenant is their project)
        # In a multi-tenant setup, we'd join through TenantMembership
        stmt = select(Tenant).where(Tenant.id == tenant_id)

        if status is not None:
            stmt = stmt.where(Tenant.status == status)
            filters_applied["status"] = status

        # Count (for single tenant, always 1)
        count_stmt = select(func.count(Tenant.id)).where(Tenant.id == tenant_id)
        if status is not None:
            count_stmt = count_stmt.where(Tenant.status == status)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Execute
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        tenants = result.scalars().all()

        items = [
            ProjectSummary(
                project_id=t.id,
                name=t.name,
                description=None,  # Tenant doesn't have description field
                status=t.status.upper(),
                plan=t.plan.upper(),
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ]

        return ProjectsListResponse(
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
    """Get project detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    # Security: User can only see their own tenant/project
    if project_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Cannot access other projects."},
        )

    try:
        stmt = select(Tenant).where(Tenant.id == project_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectDetailResponse(
            project_id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            description=None,
            status=tenant.status.upper(),
            plan=tenant.plan.upper(),
            max_workers=tenant.max_workers,
            max_runs_per_day=tenant.max_runs_per_day,
            max_concurrent_runs=tenant.max_concurrent_runs,
            max_tokens_per_month=tenant.max_tokens_per_month,
            max_api_keys=tenant.max_api_keys,
            runs_today=tenant.runs_today,
            runs_this_month=tenant.runs_this_month,
            tokens_this_month=tenant.tokens_this_month,
            onboarding_state=tenant.onboarding_state,
            onboarding_complete=tenant.has_completed_onboarding(),
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
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
    """List users. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Join User with TenantMembership to get tenant users with roles
        stmt = (
            select(
                User.id,
                User.email,
                User.name,
                User.status,
                User.created_at,
                User.last_login_at,
                TenantMembership.role,
            )
            .join(TenantMembership, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == tenant_id)
            .order_by(User.email)
        )

        if role is not None:
            stmt = stmt.where(TenantMembership.role == role)
            filters_applied["role"] = role

        if status is not None:
            stmt = stmt.where(User.status == status)
            filters_applied["status"] = status

        # Count total
        count_stmt = (
            select(func.count(User.id))
            .join(TenantMembership, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == tenant_id)
        )
        if role is not None:
            count_stmt = count_stmt.where(TenantMembership.role == role)
        if status is not None:
            count_stmt = count_stmt.where(User.status == status)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = result.all()

        items = [
            UserSummary(
                user_id=row.id,
                email=row.email,
                name=row.name,
                role=row.role.upper(),
                status=row.status.upper(),
                created_at=row.created_at,
                last_login_at=row.last_login_at,
            )
            for row in rows
        ]

        return UsersListResponse(
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
    """Get user detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        # Query user with membership in this tenant
        stmt = (
            select(User, TenantMembership)
            .join(TenantMembership, TenantMembership.user_id == User.id)
            .where(User.id == user_id)
            .where(TenantMembership.tenant_id == tenant_id)
        )

        result = await session.execute(stmt)
        row = result.first()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found in this tenant")

        user: User = row[0]
        membership: TenantMembership = row[1]

        return UserDetailResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            role=membership.role.upper(),
            status=user.status.upper(),
            email_verified=user.email_verified,
            oauth_provider=user.oauth_provider,
            membership_created_at=membership.created_at,
            invited_by=membership.invited_by,
            can_manage_keys=membership.can_manage_keys(),
            can_run_workers=membership.can_run_workers(),
            can_view_runs=membership.can_view_runs(),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
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
    """Get current user profile."""

    tenant_id = get_tenant_id_from_auth(request)
    clerk_user_id = get_user_id_from_auth(request)

    try:
        # Query user and tenant
        if clerk_user_id:
            # Find user by Clerk ID
            user_stmt = select(User).where(User.clerk_user_id == clerk_user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
        else:
            user = None

        # Get tenant info
        tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
        tenant_result = await session.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()

        # Get membership role if user exists
        role = "MEMBER"  # Default
        if user:
            membership_stmt = (
                select(TenantMembership)
                .where(TenantMembership.user_id == user.id)
                .where(TenantMembership.tenant_id == tenant_id)
            )
            membership_result = await session.execute(membership_stmt)
            membership = membership_result.scalar_one_or_none()
            if membership:
                role = membership.role.upper()

        if user:
            return ProfileResponse(
                user_id=user.id,
                email=user.email,
                name=user.name,
                avatar_url=user.avatar_url,
                tenant_id=tenant_id,
                tenant_name=tenant.name if tenant else None,
                role=role,
                created_at=user.created_at,
                preferences=None,  # No preferences field in model yet
            )
        else:
            # Return minimal profile from auth context
            return ProfileResponse(
                user_id=clerk_user_id or "unknown",
                email="unknown@tenant.local",
                name=None,
                avatar_url=None,
                tenant_id=tenant_id,
                tenant_name=tenant.name if tenant else None,
                role=role,
                created_at=tenant.created_at if tenant else datetime.utcnow(),
                preferences=None,
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
    """Get billing summary."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        # Query tenant and subscription
        tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
        tenant_result = await session.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()

        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Query subscription if exists
        sub_stmt = (
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        sub_result = await session.execute(sub_stmt)
        subscription = sub_result.scalar_one_or_none()

        # Build response
        if subscription:
            return BillingSummaryResponse(
                plan=subscription.plan.upper(),
                status=subscription.status.upper(),
                billing_period=subscription.billing_period.upper(),
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                usage_this_period={
                    "runs": tenant.runs_this_month,
                    "tokens": tenant.tokens_this_month,
                },
                next_invoice_date=subscription.current_period_end,
                max_runs_per_day=tenant.max_runs_per_day,
                max_tokens_per_month=tenant.max_tokens_per_month,
                runs_this_month=tenant.runs_this_month,
                tokens_this_month=tenant.tokens_this_month,
            )
        else:
            # Free tier / no subscription
            return BillingSummaryResponse(
                plan=tenant.plan.upper(),
                status="ACTIVE",
                billing_period="UNLIMITED",
                current_period_start=tenant.created_at,
                current_period_end=None,
                usage_this_period={
                    "runs": tenant.runs_this_month,
                    "tokens": tenant.tokens_this_month,
                },
                next_invoice_date=None,
                max_runs_per_day=tenant.max_runs_per_day,
                max_tokens_per_month=tenant.max_tokens_per_month,
                runs_this_month=tenant.runs_this_month,
                tokens_this_month=tenant.tokens_this_month,
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


class ProfileResponse(BaseModel):
    """User profile response."""

    user_id: str
    email: str
    display_name: Optional[str]
    timezone: Optional[str]
    preferences: dict
    updated_at: datetime


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: Request,
    update: ProfileUpdateRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> ProfileResponse:
    """
    Update current user's profile and preferences.

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)
    user_id = auth_ctx.user_id

    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if update.display_name is not None:
            user.name = update.display_name
        if update.timezone is not None:
            # Store timezone in preferences
            prefs = user.get_preferences()
            prefs["timezone"] = update.timezone
            user.set_preferences(prefs)
        if update.preferences is not None:
            # Merge with existing preferences
            prefs = user.get_preferences()
            prefs.update(update.preferences)
            user.set_preferences(prefs)

        user.updated_at = utc_now()
        await session.commit()
        await session.refresh(user)

        return ProfileResponse(
            user_id=user.id,
            email=user.email,
            display_name=user.name,
            timezone=user.get_preferences().get("timezone"),
            preferences=user.get_preferences(),
            updated_at=user.updated_at,
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
    """
    Get billing invoice history.

    For free tier (demo-tenant), returns empty list with unlimited usage message.

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)
    tenant_id = auth_ctx.tenant_id

    try:
        # Get tenant to check plan
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Free tier = no invoices, unlimited usage
        if tenant.plan.lower() == "free":
            return InvoiceListResponse(
                invoices=[],
                total=0,
                message="Free tier - unlimited usage, no invoices",
            )

        # For paid tiers, would query invoices from billing system
        # Currently all tenants are free tier during platform build
        return InvoiceListResponse(
            invoices=[],
            total=0,
            message="Free tier - unlimited usage, no invoices",
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
async def get_support_contact() -> SupportContactResponse:
    """
    Get support contact information.

    Layer: L2 (Product APIs)
    """
    return SupportContactResponse(
        email="support@agenticverz.com",
        hours="24/7",
        response_time="Within 24 hours",
    )


@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=201)
async def create_support_ticket(
    request: Request,
    ticket: SupportTicketCreate,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SupportTicketResponse:
    """
    Create a support ticket.

    This feeds into the CRM workflow (Part-2) with human-in-the-loop
    at Step 5 (Founder Review). No automatic agent assignment.

    Layer: L2 (Product APIs)
    Reference: PART2_CRM_WORKFLOW_CHARTER.md
    """
    auth_ctx = get_auth_context(request)

    try:
        now = utc_now()
        new_ticket = SupportTicket(
            id=generate_uuid(),
            tenant_id=auth_ctx.tenant_id,
            user_id=auth_ctx.user_id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            status="open",
            created_at=now,
            updated_at=now,
        )

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)

        # TODO: Trigger CRM workflow via issue_event_id
        # This would create an entry in the CRM system per PART2_CRM_WORKFLOW_CHARTER.md
        # Step 1: CRM Ticket Created → Step 2: Auto-Classification → etc.

        return SupportTicketResponse(
            id=new_ticket.id,
            subject=new_ticket.subject,
            description=new_ticket.description,
            category=new_ticket.category,
            priority=new_ticket.priority,
            status=new_ticket.status,
            created_at=new_ticket.created_at,
            updated_at=new_ticket.updated_at,
            resolution=new_ticket.resolution,
            resolved_at=new_ticket.resolved_at,
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
    """
    List support tickets for the current tenant.

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)

    try:
        stmt = select(SupportTicket).where(
            SupportTicket.tenant_id == auth_ctx.tenant_id
        )

        if status:
            stmt = stmt.where(SupportTicket.status == status)

        stmt = stmt.order_by(SupportTicket.created_at.desc())

        result = await session.execute(stmt)
        tickets = result.scalars().all()

        return SupportTicketListResponse(
            tickets=[
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
                for t in tickets
            ],
            total=len(tickets),
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
    """
    Invite a user to join the tenant.

    Requires: owner or admin role.

    Layer: L2 (Product APIs)
    """
    import hashlib
    import secrets

    auth_ctx = get_auth_context(request)

    try:
        # Check caller has permission to invite
        stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == auth_ctx.tenant_id,
            TenantMembership.user_id == auth_ctx.user_id,
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()

        if membership is None or not membership.can_manage_users():
            raise HTTPException(
                status_code=403,
                detail="Only owners and admins can invite users",
            )

        # Check if email already invited (pending)
        existing_stmt = select(Invitation).where(
            Invitation.tenant_id == auth_ctx.tenant_id,
            Invitation.email == invite.email,
            Invitation.status == "pending",
        )
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Invitation already pending for this email",
            )

        # Generate token and hash
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        now = utc_now()
        expires_at = now + timedelta(days=7)  # 7 day expiry

        new_invitation = Invitation(
            id=generate_uuid(),
            tenant_id=auth_ctx.tenant_id,
            email=invite.email,
            role=invite.role,
            status="pending",
            token_hash=token_hash,
            invited_by=auth_ctx.user_id,
            created_at=now,
            expires_at=expires_at,
        )

        session.add(new_invitation)
        await session.commit()
        await session.refresh(new_invitation)

        # TODO: Send invitation email with token
        # The token would be included in an invitation link

        return InvitationResponse(
            id=new_invitation.id,
            email=new_invitation.email,
            role=new_invitation.role,
            status=new_invitation.status,
            created_at=new_invitation.created_at,
            expires_at=new_invitation.expires_at,
            invited_by=new_invitation.invited_by,
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
    """
    List invitations for the current tenant.

    Requires: owner or admin role.

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)

    try:
        # Check caller has permission
        stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == auth_ctx.tenant_id,
            TenantMembership.user_id == auth_ctx.user_id,
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()

        if membership is None or not membership.can_manage_users():
            raise HTTPException(
                status_code=403,
                detail="Only owners and admins can view invitations",
            )

        inv_stmt = select(Invitation).where(
            Invitation.tenant_id == auth_ctx.tenant_id
        )

        if status:
            inv_stmt = inv_stmt.where(Invitation.status == status)

        inv_stmt = inv_stmt.order_by(Invitation.created_at.desc())

        inv_result = await session.execute(inv_stmt)
        invitations = inv_result.scalars().all()

        return InvitationListResponse(
            invitations=[
                InvitationResponse(
                    id=inv.id,
                    email=inv.email,
                    role=inv.role,
                    status=inv.status,
                    created_at=inv.created_at,
                    expires_at=inv.expires_at,
                    invited_by=inv.invited_by,
                )
                for inv in invitations
            ],
            total=len(invitations),
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

    Layer: L2 (Product APIs)
    """
    import hashlib

    try:
        token_hash = hashlib.sha256(accept.token.encode()).hexdigest()

        stmt = select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
        )
        result = await session.execute(stmt)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            raise HTTPException(
                status_code=404,
                detail="Invalid or expired invitation",
            )

        now = utc_now()

        if invitation.expires_at < now:
            invitation.status = "expired"
            await session.commit()
            raise HTTPException(
                status_code=410,
                detail="Invitation has expired",
            )

        # Check if user exists with this email
        user_stmt = select(User).where(User.email == invitation.email)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user is None:
            # Create new user
            user = User(
                id=generate_uuid(),
                email=invitation.email,
                name=invitation.email.split("@")[0],  # Default name from email
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            await session.flush()

        # Check if already a member
        member_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == invitation.tenant_id,
            TenantMembership.user_id == user.id,
        )
        member_result = await session.execute(member_stmt)
        if member_result.scalar_one_or_none():
            invitation.status = "accepted"
            invitation.accepted_at = now
            await session.commit()
            return {"message": "Already a member of this tenant"}

        # Create membership
        membership = TenantMembership(
            id=generate_uuid(),
            tenant_id=invitation.tenant_id,
            user_id=user.id,
            role=invitation.role,
            created_at=now,
        )
        session.add(membership)

        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_at = now

        await session.commit()

        return {
            "message": "Invitation accepted",
            "tenant_id": invitation.tenant_id,
            "role": invitation.role,
        }

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

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)

    try:
        stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == auth_ctx.tenant_id)
            .order_by(TenantMembership.created_at)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return TenantUserListResponse(
            users=[
                TenantUserResponse(
                    user_id=membership.user_id,
                    email=user.email,
                    name=user.name,
                    role=membership.role,
                    joined_at=membership.created_at,
                )
                for membership, user in rows
            ],
            total=len(rows),
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

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)

    try:
        # Check caller is owner
        caller_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == auth_ctx.tenant_id,
            TenantMembership.user_id == auth_ctx.user_id,
        )
        caller_result = await session.execute(caller_stmt)
        caller_membership = caller_result.scalar_one_or_none()

        if caller_membership is None or not caller_membership.can_change_roles():
            raise HTTPException(
                status_code=403,
                detail="Only owners can change user roles",
            )

        # Cannot change own role
        if user_id == auth_ctx.user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot change your own role",
            )

        # Get target membership
        target_stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(
                TenantMembership.tenant_id == auth_ctx.tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        target_result = await session.execute(target_stmt)
        row = target_result.one_or_none()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found in tenant")

        membership, user = row

        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if update.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {valid_roles}",
            )

        membership.role = update.role
        await session.commit()

        return TenantUserResponse(
            user_id=membership.user_id,
            email=user.email,
            name=user.name,
            role=membership.role,
            joined_at=membership.created_at,
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

    Layer: L2 (Product APIs)
    """
    auth_ctx = get_auth_context(request)

    try:
        # Check caller has permission
        caller_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == auth_ctx.tenant_id,
            TenantMembership.user_id == auth_ctx.user_id,
        )
        caller_result = await session.execute(caller_stmt)
        caller_membership = caller_result.scalar_one_or_none()

        if caller_membership is None or not caller_membership.can_manage_users():
            raise HTTPException(
                status_code=403,
                detail="Only owners and admins can remove users",
            )

        # Cannot remove self
        if user_id == auth_ctx.user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove yourself from tenant",
            )

        # Get target membership
        target_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == auth_ctx.tenant_id,
            TenantMembership.user_id == user_id,
        )
        target_result = await session.execute(target_stmt)
        target_membership = target_result.scalar_one_or_none()

        if target_membership is None:
            raise HTTPException(status_code=404, detail="User not found in tenant")

        # Cannot remove owner (unless caller is also owner)
        if target_membership.role == "owner" and caller_membership.role != "owner":
            raise HTTPException(
                status_code=403,
                detail="Only owners can remove other owners",
            )

        await session.delete(target_membership)
        await session.commit()

        return {"message": "User removed from tenant", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "remove_failed", "message": str(e)},
        )
