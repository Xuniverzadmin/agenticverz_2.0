# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB reads/writes)
# Role: Accounts domain facade - unified entry point for account management
# Callers: L2 accounts API (accounts.py)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Customer Console v1 Constitution
#
"""
Accounts Domain Facade (L4)

Unified facade for all accounts domain operations:
- Projects: list, detail
- Users: list, detail, invite, remove, update role
- Profile: get, update
- Billing: summary, invoices
- Support: contact, tickets

GOVERNANCE NOTE:
Account is NOT a domain - it manages who, what, and billing (not what happened).
Account pages MUST NOT display executions, incidents, policies, or logs.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
# Result Types — Projects
# =============================================================================


@dataclass
class ProjectSummaryResult:
    """Project summary for list view."""

    project_id: str
    name: str
    description: Optional[str]
    status: str  # ACTIVE, ARCHIVED
    plan: str  # FREE, PRO, ENTERPRISE
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class ProjectsListResult:
    """Projects list response."""

    items: list[ProjectSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class ProjectDetailResult:
    """Project detail response."""

    project_id: str
    name: str
    slug: str
    description: Optional[str]
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
    updated_at: Optional[datetime]


# =============================================================================
# Result Types — Users
# =============================================================================


@dataclass
class UserSummaryResult:
    """User summary for list view."""

    user_id: str
    email: str
    name: Optional[str]
    role: str  # OWNER, ADMIN, MEMBER, VIEWER
    status: str  # ACTIVE, INVITED, SUSPENDED
    created_at: datetime
    last_login_at: Optional[datetime]


@dataclass
class UsersListResult:
    """Users list response."""

    items: list[UserSummaryResult]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@dataclass
class UserDetailResult:
    """User detail response."""

    user_id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    email_verified: bool
    oauth_provider: Optional[str]
    # Membership
    membership_created_at: datetime
    invited_by: Optional[str]
    # Permissions
    can_manage_keys: bool
    can_run_workers: bool
    can_view_runs: bool
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]


@dataclass
class TenantUserResult:
    """User in tenant."""

    user_id: str
    email: str
    name: Optional[str]
    role: str
    joined_at: datetime


@dataclass
class TenantUsersListResult:
    """List of tenant users."""

    users: list[TenantUserResult]
    total: int


# =============================================================================
# Result Types — Profile
# =============================================================================


@dataclass
class ProfileResult:
    """User profile response."""

    user_id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    tenant_id: str
    tenant_name: Optional[str]
    role: str
    created_at: datetime
    preferences: Optional[dict[str, Any]]


@dataclass
class ProfileUpdateResult:
    """Profile update response."""

    user_id: str
    email: str
    display_name: Optional[str]
    timezone: Optional[str]
    preferences: dict[str, Any]
    updated_at: datetime


# =============================================================================
# Result Types — Billing
# =============================================================================


@dataclass
class BillingSummaryResult:
    """Billing summary response."""

    plan: str  # FREE, PRO, ENTERPRISE
    status: str  # ACTIVE, PAST_DUE, CANCELLED
    billing_period: str  # MONTHLY, ANNUAL
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    usage_this_period: dict[str, Any]
    next_invoice_date: Optional[datetime]
    # Tenant quotas for context
    max_runs_per_day: int
    max_tokens_per_month: int
    runs_this_month: int
    tokens_this_month: int


@dataclass
class InvoiceSummaryResult:
    """Invoice summary."""

    invoice_id: str
    period_start: datetime
    period_end: datetime
    amount_cents: int
    status: str  # paid, pending, void
    description: str


@dataclass
class InvoiceListResult:
    """Invoice list response."""

    invoices: list[InvoiceSummaryResult]
    total: int
    message: Optional[str] = None


# =============================================================================
# Result Types — Support
# =============================================================================


@dataclass
class SupportContactResult:
    """Support contact info."""

    email: str
    hours: str
    response_time: str


@dataclass
class SupportTicketResult:
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


@dataclass
class SupportTicketListResult:
    """Support ticket list response."""

    tickets: list[SupportTicketResult]
    total: int


# =============================================================================
# Result Types — Invitations
# =============================================================================


@dataclass
class InvitationResult:
    """Invitation response."""

    id: str
    email: str
    role: str
    status: str
    created_at: datetime
    expires_at: datetime
    invited_by: str


@dataclass
class InvitationListResult:
    """Invitation list response."""

    invitations: list[InvitationResult]
    total: int


@dataclass
class AcceptInvitationResult:
    """Invitation acceptance result."""

    success: bool
    message: str
    tenant_id: Optional[str] = None
    role: Optional[str] = None


# =============================================================================
# Error Results
# =============================================================================


@dataclass
class AccountsErrorResult:
    """Error result for accounts operations."""

    error: str
    message: str
    status_code: int = 400


# =============================================================================
# Accounts Facade
# =============================================================================


class AccountsFacade:
    """
    Unified facade for all Accounts domain operations.

    Provides:
    - Projects: list, detail
    - Users: list, detail, invite, remove, update role
    - Profile: get, update
    - Billing: summary, invoices
    - Support: contact, tickets

    GOVERNANCE NOTE:
    Account is NOT a domain - it manages who, what, and billing (not what happened).
    """

    # -------------------------------------------------------------------------
    # Projects Operations
    # -------------------------------------------------------------------------

    async def list_projects(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ProjectsListResult:
        """List projects (tenants). In current architecture, Tenant = Project."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

        # Query tenant (current user's tenant is their project)
        stmt = select(Tenant).where(Tenant.id == tenant_id)

        if status is not None:
            stmt = stmt.where(Tenant.status == status)
            filters_applied["status"] = status

        # Count
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
            ProjectSummaryResult(
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

        return ProjectsListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_project_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
    ) -> Optional[ProjectDetailResult]:
        """Get project detail. User can only see their own tenant/project."""
        # Security: User can only see their own tenant/project
        if project_id != tenant_id:
            return None

        stmt = select(Tenant).where(Tenant.id == project_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return None

        return ProjectDetailResult(
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

    # -------------------------------------------------------------------------
    # Users Operations
    # -------------------------------------------------------------------------

    async def list_users(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> UsersListResult:
        """List users in the tenant."""
        filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

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
            UserSummaryResult(
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

        return UsersListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            filters_applied=filters_applied,
        )

    async def get_user_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
    ) -> Optional[UserDetailResult]:
        """Get user detail. Tenant isolation enforced."""
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
            return None

        user: User = row[0]
        membership: TenantMembership = row[1]

        return UserDetailResult(
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

    async def list_tenant_users(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> TenantUsersListResult:
        """List users in the current tenant."""
        stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == tenant_id)
            .order_by(TenantMembership.created_at)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return TenantUsersListResult(
            users=[
                TenantUserResult(
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

    async def update_user_role(
        self,
        session: AsyncSession,
        tenant_id: str,
        caller_user_id: str,
        target_user_id: str,
        new_role: str,
    ) -> TenantUserResult | AccountsErrorResult:
        """Update a user's role in the tenant. Requires owner role."""
        # Check caller is owner
        caller_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == caller_user_id,
        )
        caller_result = await session.execute(caller_stmt)
        caller_membership = caller_result.scalar_one_or_none()

        if caller_membership is None or not caller_membership.can_change_roles():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners can change user roles",
                status_code=403,
            )

        # Cannot change own role
        if target_user_id == caller_user_id:
            return AccountsErrorResult(
                error="invalid_operation",
                message="Cannot change your own role",
                status_code=400,
            )

        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if new_role not in valid_roles:
            return AccountsErrorResult(
                error="invalid_role",
                message=f"Invalid role. Must be one of: {valid_roles}",
                status_code=400,
            )

        # Get target membership
        target_stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == target_user_id,
            )
        )
        target_result = await session.execute(target_stmt)
        row = target_result.one_or_none()

        if row is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found in tenant",
                status_code=404,
            )

        membership, user = row

        membership.role = new_role
        await session.commit()

        return TenantUserResult(
            user_id=membership.user_id,
            email=user.email,
            name=user.name,
            role=membership.role,
            joined_at=membership.created_at,
        )

    async def remove_user(
        self,
        session: AsyncSession,
        tenant_id: str,
        caller_user_id: str,
        target_user_id: str,
    ) -> dict[str, str] | AccountsErrorResult:
        """Remove a user from the tenant. Requires owner or admin role."""
        # Check caller has permission
        caller_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == caller_user_id,
        )
        caller_result = await session.execute(caller_stmt)
        caller_membership = caller_result.scalar_one_or_none()

        if caller_membership is None or not caller_membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can remove users",
                status_code=403,
            )

        # Cannot remove self
        if target_user_id == caller_user_id:
            return AccountsErrorResult(
                error="invalid_operation",
                message="Cannot remove yourself from tenant",
                status_code=400,
            )

        # Get target membership
        target_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == target_user_id,
        )
        target_result = await session.execute(target_stmt)
        target_membership = target_result.scalar_one_or_none()

        if target_membership is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found in tenant",
                status_code=404,
            )

        # Cannot remove owner unless caller is also owner
        if target_membership.role == "owner" and caller_membership.role != "owner":
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners can remove other owners",
                status_code=403,
            )

        await session.delete(target_membership)
        await session.commit()

        return {"message": "User removed from tenant", "user_id": target_user_id}

    # -------------------------------------------------------------------------
    # Profile Operations
    # -------------------------------------------------------------------------

    async def get_profile(
        self,
        session: AsyncSession,
        tenant_id: str,
        clerk_user_id: Optional[str],
    ) -> ProfileResult:
        """Get current user profile."""
        # Query user by Clerk ID
        user = None
        if clerk_user_id:
            user_stmt = select(User).where(User.clerk_user_id == clerk_user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

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
            return ProfileResult(
                user_id=user.id,
                email=user.email,
                name=user.name,
                avatar_url=user.avatar_url,
                tenant_id=tenant_id,
                tenant_name=tenant.name if tenant else None,
                role=role,
                created_at=user.created_at,
                preferences=None,
            )
        else:
            # Return minimal profile from auth context
            return ProfileResult(
                user_id=clerk_user_id or "unknown",
                email="unknown@tenant.local",
                name=None,
                avatar_url=None,
                tenant_id=tenant_id,
                tenant_name=tenant.name if tenant else None,
                role=role,
                created_at=tenant.created_at if tenant else datetime.now(timezone.utc),
                preferences=None,
            )

    async def update_profile(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        display_name: Optional[str] = None,
        timezone_str: Optional[str] = None,
        preferences: Optional[dict[str, Any]] = None,
    ) -> ProfileUpdateResult | AccountsErrorResult:
        """Update current user's profile and preferences."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found",
                status_code=404,
            )

        # Update fields if provided
        if display_name is not None:
            user.name = display_name
        if timezone_str is not None:
            prefs = user.get_preferences()
            prefs["timezone"] = timezone_str
            user.set_preferences(prefs)
        if preferences is not None:
            prefs = user.get_preferences()
            prefs.update(preferences)
            user.set_preferences(prefs)

        user.updated_at = utc_now()
        await session.commit()
        await session.refresh(user)

        return ProfileUpdateResult(
            user_id=user.id,
            email=user.email,
            display_name=user.name,
            timezone=user.get_preferences().get("timezone"),
            preferences=user.get_preferences(),
            updated_at=user.updated_at,
        )

    # -------------------------------------------------------------------------
    # Billing Operations
    # -------------------------------------------------------------------------

    async def get_billing_summary(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> BillingSummaryResult | AccountsErrorResult:
        """Get billing summary for the tenant."""
        # Query tenant
        tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
        tenant_result = await session.execute(tenant_stmt)
        tenant = tenant_result.scalar_one_or_none()

        if tenant is None:
            return AccountsErrorResult(
                error="not_found",
                message="Tenant not found",
                status_code=404,
            )

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
            return BillingSummaryResult(
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
            return BillingSummaryResult(
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

    async def get_billing_invoices(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> InvoiceListResult | AccountsErrorResult:
        """Get billing invoice history."""
        # Get tenant to check plan
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return AccountsErrorResult(
                error="not_found",
                message="Tenant not found",
                status_code=404,
            )

        # Free tier = no invoices, unlimited usage
        if tenant.plan.lower() == "free":
            return InvoiceListResult(
                invoices=[],
                total=0,
                message="Free tier - unlimited usage, no invoices",
            )

        # For paid tiers, would query invoices from billing system
        # Currently all tenants are free tier during platform build
        return InvoiceListResult(
            invoices=[],
            total=0,
            message="Free tier - unlimited usage, no invoices",
        )

    # -------------------------------------------------------------------------
    # Support Operations
    # -------------------------------------------------------------------------

    def get_support_contact(self) -> SupportContactResult:
        """Get support contact information."""
        return SupportContactResult(
            email="support@agenticverz.com",
            hours="24/7",
            response_time="Within 24 hours",
        )

    async def create_support_ticket(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        *,
        subject: str,
        description: str,
        category: str = "general",
        priority: str = "medium",
    ) -> SupportTicketResult:
        """Create a support ticket."""
        now = utc_now()
        new_ticket = SupportTicket(
            id=generate_uuid(),
            tenant_id=tenant_id,
            user_id=user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status="open",
            created_at=now,
            updated_at=now,
        )

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)

        return SupportTicketResult(
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

    async def list_support_tickets(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> SupportTicketListResult:
        """List support tickets for the tenant."""
        stmt = select(SupportTicket).where(SupportTicket.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(SupportTicket.status == status)

        stmt = stmt.order_by(SupportTicket.created_at.desc())

        result = await session.execute(stmt)
        tickets = result.scalars().all()

        return SupportTicketListResult(
            tickets=[
                SupportTicketResult(
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

    # -------------------------------------------------------------------------
    # Invitation Operations
    # -------------------------------------------------------------------------

    async def invite_user(
        self,
        session: AsyncSession,
        tenant_id: str,
        caller_user_id: str,
        *,
        email: str,
        role: str = "member",
    ) -> InvitationResult | AccountsErrorResult:
        """Invite a user to join the tenant. Requires owner or admin role."""
        # Check caller has permission to invite
        stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == caller_user_id,
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()

        if membership is None or not membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can invite users",
                status_code=403,
            )

        # Check if email already invited (pending)
        existing_stmt = select(Invitation).where(
            Invitation.tenant_id == tenant_id,
            Invitation.email == email,
            Invitation.status == "pending",
        )
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            return AccountsErrorResult(
                error="conflict",
                message="Invitation already pending for this email",
                status_code=409,
            )

        # Generate token and hash
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        now = utc_now()
        expires_at = now + timedelta(days=7)  # 7 day expiry

        new_invitation = Invitation(
            id=generate_uuid(),
            tenant_id=tenant_id,
            email=email,
            role=role,
            status="pending",
            token_hash=token_hash,
            invited_by=caller_user_id,
            created_at=now,
            expires_at=expires_at,
        )

        session.add(new_invitation)
        await session.commit()
        await session.refresh(new_invitation)

        return InvitationResult(
            id=new_invitation.id,
            email=new_invitation.email,
            role=new_invitation.role,
            status=new_invitation.status,
            created_at=new_invitation.created_at,
            expires_at=new_invitation.expires_at,
            invited_by=new_invitation.invited_by,
        )

    async def list_invitations(
        self,
        session: AsyncSession,
        tenant_id: str,
        caller_user_id: str,
        *,
        status: Optional[str] = None,
    ) -> InvitationListResult | AccountsErrorResult:
        """List invitations for the tenant. Requires owner or admin role."""
        # Check caller has permission
        stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == caller_user_id,
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()

        if membership is None or not membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can view invitations",
                status_code=403,
            )

        inv_stmt = select(Invitation).where(Invitation.tenant_id == tenant_id)

        if status:
            inv_stmt = inv_stmt.where(Invitation.status == status)

        inv_stmt = inv_stmt.order_by(Invitation.created_at.desc())

        inv_result = await session.execute(inv_stmt)
        invitations = inv_result.scalars().all()

        return InvitationListResult(
            invitations=[
                InvitationResult(
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

    async def accept_invitation(
        self,
        session: AsyncSession,
        invitation_id: str,
        token: str,
    ) -> AcceptInvitationResult:
        """Accept an invitation to join a tenant. Public endpoint."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        stmt = select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
        )
        result = await session.execute(stmt)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            return AcceptInvitationResult(
                success=False,
                message="Invalid or expired invitation",
            )

        now = utc_now()

        if invitation.expires_at < now:
            invitation.status = "expired"
            await session.commit()
            return AcceptInvitationResult(
                success=False,
                message="Invitation has expired",
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
            return AcceptInvitationResult(
                success=True,
                message="Already a member of this tenant",
                tenant_id=invitation.tenant_id,
                role=invitation.role,
            )

        # Create membership
        new_membership = TenantMembership(
            id=generate_uuid(),
            tenant_id=invitation.tenant_id,
            user_id=user.id,
            role=invitation.role,
            created_at=now,
        )
        session.add(new_membership)

        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_at = now

        await session.commit()

        return AcceptInvitationResult(
            success=True,
            message="Invitation accepted",
            tenant_id=invitation.tenant_id,
            role=invitation.role,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_facade_instance: AccountsFacade | None = None


def get_accounts_facade() -> AccountsFacade:
    """Get the singleton AccountsFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AccountsFacade()
    return _facade_instance


__all__ = [
    # Facade
    "AccountsFacade",
    "get_accounts_facade",
    # Projects result types
    "ProjectSummaryResult",
    "ProjectsListResult",
    "ProjectDetailResult",
    # Users result types
    "UserSummaryResult",
    "UsersListResult",
    "UserDetailResult",
    "TenantUserResult",
    "TenantUsersListResult",
    # Profile result types
    "ProfileResult",
    "ProfileUpdateResult",
    # Billing result types
    "BillingSummaryResult",
    "InvoiceSummaryResult",
    "InvoiceListResult",
    # Support result types
    "SupportContactResult",
    "SupportTicketResult",
    "SupportTicketListResult",
    # Invitation result types
    "InvitationResult",
    "InvitationListResult",
    "AcceptInvitationResult",
    # Error result
    "AccountsErrorResult",
]
