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

from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.tenant import Subscription, Tenant, TenantMembership, User

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
