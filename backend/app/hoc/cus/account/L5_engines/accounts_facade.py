# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/account/L5_engines/accounts_facade.py
# Temporal:
#   Trigger: api
#   Execution: async (DB reads/writes)
# Role: Accounts domain facade - unified entry point for account management
# Callers: L2 accounts API (accounts.py)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, L7 (at runtime)
# Reference: Customer Console v1 Constitution, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# PHASE 2.5B REMEDIATION (2026-01-24):
# This facade has been refactored to comply with HOC Layer Topology V1.
# All DB operations are now delegated to AccountsFacadeDriver (L6).
# SQLAlchemy and L7 model imports moved to TYPE_CHECKING block.
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
"""
Accounts Domain Facade (L5)

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

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

# L6 driver import (allowed at runtime)
from app.hoc.cus.account.L6_drivers.accounts_facade_driver import (
    AccountsFacadeDriver,
    get_accounts_facade_driver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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

    LAYER COMPLIANCE (Phase 2.5B):
    This L4 facade delegates all DB operations to AccountsFacadeDriver (L6).
    Business logic (validation, permissions) remains here.
    """

    def __init__(self, driver: AccountsFacadeDriver | None = None) -> None:
        """Initialize facade with optional driver injection."""
        self._driver = driver or get_accounts_facade_driver()

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
        if status is not None:
            filters_applied["status"] = status

        # Delegate to driver
        tenants = await self._driver.fetch_tenants(
            session, tenant_id, status=status, limit=limit, offset=offset
        )
        total = await self._driver.count_tenants(session, tenant_id, status=status)

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

        # Delegate to driver
        tenant = await self._driver.fetch_tenant_detail(session, project_id)
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
            onboarding_complete=tenant.onboarding_complete,
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
        if role is not None:
            filters_applied["role"] = role
        if status is not None:
            filters_applied["status"] = status

        # Delegate to driver
        users = await self._driver.fetch_users(
            session, tenant_id, role=role, status=status, limit=limit, offset=offset
        )
        total = await self._driver.count_users(
            session, tenant_id, role=role, status=status
        )

        items = [
            UserSummaryResult(
                user_id=u.id,
                email=u.email,
                name=u.name,
                role=u.role.upper(),
                status=u.status.upper(),
                created_at=u.created_at,
                last_login_at=u.last_login_at,
            )
            for u in users
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
        # Delegate to driver
        user = await self._driver.fetch_user_detail(session, tenant_id, user_id)
        if user is None:
            return None

        return UserDetailResult(
            user_id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            role=user.role.upper(),
            status=user.status.upper(),
            email_verified=user.email_verified,
            oauth_provider=user.oauth_provider,
            membership_created_at=user.membership_created_at,
            invited_by=user.invited_by,
            can_manage_keys=user.can_manage_keys,
            can_run_workers=user.can_run_workers,
            can_view_runs=user.can_view_runs,
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
        # Delegate to driver
        memberships = await self._driver.fetch_tenant_memberships(session, tenant_id)

        return TenantUsersListResult(
            users=[
                TenantUserResult(
                    user_id=m.user_id,
                    email=m.email,
                    name=m.name,
                    role=m.role,
                    joined_at=m.created_at,
                )
                for m in memberships
            ],
            total=len(memberships),
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
        # Business logic: Check caller has permission
        caller_membership = await self._driver.fetch_membership(
            session, tenant_id, caller_user_id
        )

        if caller_membership is None or not caller_membership.can_change_roles():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners can change user roles",
                status_code=403,
            )

        # Business logic: Cannot change own role
        if target_user_id == caller_user_id:
            return AccountsErrorResult(
                error="invalid_operation",
                message="Cannot change your own role",
                status_code=400,
            )

        # Business logic: Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if new_role not in valid_roles:
            return AccountsErrorResult(
                error="invalid_role",
                message=f"Invalid role. Must be one of: {valid_roles}",
                status_code=400,
            )

        # Get target membership with user data
        target_data = await self._driver.fetch_membership_with_user(
            session, tenant_id, target_user_id
        )

        if target_data is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found in tenant",
                status_code=404,
            )

        membership, _user = target_data

        # Delegate to driver for update
        updated = await self._driver.update_membership_role(
            session, membership, new_role
        )

        return TenantUserResult(
            user_id=updated.user_id,
            email=updated.email,
            name=updated.name,
            role=updated.role,
            joined_at=updated.created_at,
        )

    async def remove_user(
        self,
        session: AsyncSession,
        tenant_id: str,
        caller_user_id: str,
        target_user_id: str,
    ) -> dict[str, str] | AccountsErrorResult:
        """Remove a user from the tenant. Requires owner or admin role."""
        # Business logic: Check caller has permission
        caller_membership = await self._driver.fetch_membership(
            session, tenant_id, caller_user_id
        )

        if caller_membership is None or not caller_membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can remove users",
                status_code=403,
            )

        # Business logic: Cannot remove self
        if target_user_id == caller_user_id:
            return AccountsErrorResult(
                error="invalid_operation",
                message="Cannot remove yourself from tenant",
                status_code=400,
            )

        # Get target membership
        target_membership = await self._driver.fetch_membership(
            session, tenant_id, target_user_id
        )

        if target_membership is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found in tenant",
                status_code=404,
            )

        # Business logic: Cannot remove owner unless caller is also owner
        if target_membership.role == "owner" and caller_membership.role != "owner":
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners can remove other owners",
                status_code=403,
            )

        # Delegate to driver for deletion
        await self._driver.delete_membership(session, target_membership)

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
        # Delegate to driver
        profile = await self._driver.fetch_profile(session, tenant_id, clerk_user_id)

        return ProfileResult(
            user_id=profile.user_id,
            email=profile.email,
            name=profile.name,
            avatar_url=profile.avatar_url,
            tenant_id=profile.tenant_id,
            tenant_name=profile.tenant_name,
            role=profile.role.upper(),
            created_at=profile.created_at,
            preferences=profile.preferences,
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
        # Delegate to driver for user lookup
        user = await self._driver.fetch_user_by_id(session, user_id)

        if user is None:
            return AccountsErrorResult(
                error="not_found",
                message="User not found",
                status_code=404,
            )

        # Delegate to driver for update
        updated_user = await self._driver.update_user_profile(
            session,
            user,
            display_name=display_name,
            timezone_str=timezone_str,
            preferences=preferences,
        )

        return ProfileUpdateResult(
            user_id=updated_user.id,
            email=updated_user.email,
            display_name=updated_user.name,
            timezone=updated_user.get_preferences().get("timezone"),
            preferences=updated_user.get_preferences(),
            updated_at=updated_user.updated_at,
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
        # Delegate to driver for tenant lookup
        tenant = await self._driver.fetch_tenant_detail(session, tenant_id)

        if tenant is None:
            return AccountsErrorResult(
                error="not_found",
                message="Tenant not found",
                status_code=404,
            )

        # Delegate to driver for subscription lookup
        subscription = await self._driver.fetch_subscription(session, tenant_id)

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
        # Delegate to driver for tenant lookup
        tenant = await self._driver.fetch_tenant_detail(session, tenant_id)

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
        # Delegate to driver
        ticket = await self._driver.insert_support_ticket(
            session,
            tenant_id,
            user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
        )

        return SupportTicketResult(
            id=ticket.id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            status=ticket.status,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolution=ticket.resolution,
            resolved_at=ticket.resolved_at,
        )

    async def list_support_tickets(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> SupportTicketListResult:
        """List support tickets for the tenant."""
        # Delegate to driver
        tickets = await self._driver.fetch_support_tickets(
            session, tenant_id, status=status
        )

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
        # Business logic: Check caller has permission to invite
        membership = await self._driver.fetch_membership(
            session, tenant_id, caller_user_id
        )

        if membership is None or not membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can invite users",
                status_code=403,
            )

        # Business logic: Check if email already invited (pending)
        existing = await self._driver.fetch_invitation_by_email(
            session, tenant_id, email, status="pending"
        )
        if existing:
            return AccountsErrorResult(
                error="conflict",
                message="Invitation already pending for this email",
                status_code=409,
            )

        # Generate token and hash
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)  # 7 day expiry

        # Delegate to driver
        invitation = await self._driver.insert_invitation(
            session,
            tenant_id,
            email,
            role,
            token_hash,
            caller_user_id,
            expires_at,
        )

        return InvitationResult(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            invited_by=invitation.invited_by,
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
        # Business logic: Check caller has permission
        membership = await self._driver.fetch_membership(
            session, tenant_id, caller_user_id
        )

        if membership is None or not membership.can_manage_users():
            return AccountsErrorResult(
                error="forbidden",
                message="Only owners and admins can view invitations",
                status_code=403,
            )

        # Delegate to driver
        invitations = await self._driver.fetch_invitations(
            session, tenant_id, status=status
        )

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

        # Delegate to driver for invitation lookup
        invitation = await self._driver.fetch_invitation_by_id_and_token(
            session, invitation_id, token_hash
        )

        if invitation is None:
            return AcceptInvitationResult(
                success=False,
                message="Invalid or expired invitation",
            )

        now = datetime.now(timezone.utc)

        if invitation.expires_at < now:
            await self._driver.update_invitation_expired(session, invitation)
            return AcceptInvitationResult(
                success=False,
                message="Invitation has expired",
            )

        # Check if user exists with this email
        user = await self._driver.fetch_user_by_email(session, invitation.email)

        if user is None:
            # Create new user
            user = await self._driver.insert_user(
                session,
                invitation.email,
                invitation.email.split("@")[0],  # Default name from email
            )

        # Check if already a member
        existing_membership = await self._driver.fetch_membership(
            session, invitation.tenant_id, user.id
        )
        if existing_membership:
            await self._driver.update_invitation_accepted(session, invitation)
            return AcceptInvitationResult(
                success=True,
                message="Already a member of this tenant",
                tenant_id=invitation.tenant_id,
                role=invitation.role,
            )

        # Create membership
        await self._driver.insert_membership(
            session, invitation.tenant_id, user.id, invitation.role
        )

        # Update invitation
        await self._driver.update_invitation_accepted(session, invitation)

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
