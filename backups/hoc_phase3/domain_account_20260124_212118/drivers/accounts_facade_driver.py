# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB reads/writes)
# Role: Accounts domain facade driver - pure data access for accounts operations
# Callers: accounts_facade.py (L4)
# Allowed Imports: L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This driver was extracted from accounts_facade.py to enforce L4/L6 separation.
# All DB operations are now in this L6 driver.
# The facade (L4) delegates to this driver for data access.

"""
Accounts Facade Driver (L6)

Pure data access layer for accounts domain operations.

Provides:
- Tenant/Project queries
- User queries
- Membership queries
- Profile queries
- Billing queries
- Support ticket queries
- Invitation queries

All methods return snapshot dataclasses, not ORM models.
Business logic belongs in the facade (L4), not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

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
# Snapshot Dataclasses
# =============================================================================


@dataclass
class TenantSnapshot:
    """Tenant data from DB for list view."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class TenantDetailSnapshot:
    """Detailed tenant data from DB."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    onboarding_state: int
    onboarding_complete: bool
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class UserSnapshot:
    """User data from DB for list view."""
    id: str
    email: str
    name: Optional[str]
    status: str
    role: str
    created_at: datetime
    last_login_at: Optional[datetime]


@dataclass
class UserDetailSnapshot:
    """Detailed user data from DB."""
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    status: str
    role: str
    email_verified: bool
    oauth_provider: Optional[str]
    membership_created_at: datetime
    invited_by: Optional[str]
    can_manage_keys: bool
    can_run_workers: bool
    can_view_runs: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]


@dataclass
class MembershipSnapshot:
    """Tenant membership data from DB."""
    user_id: str
    email: str
    name: Optional[str]
    role: str
    created_at: datetime


@dataclass
class ProfileSnapshot:
    """User profile data from DB."""
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
class SubscriptionSnapshot:
    """Subscription data from DB."""
    plan: str
    status: str
    billing_period: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]


@dataclass
class InvitationSnapshot:
    """Invitation data from DB."""
    id: str
    email: str
    role: str
    status: str
    token_hash: str
    invited_by: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]


@dataclass
class TicketSnapshot:
    """Support ticket data from DB."""
    id: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


# =============================================================================
# Accounts Facade Driver
# =============================================================================


class AccountsFacadeDriver:
    """
    L6 Driver for accounts domain data access.

    All methods are pure data access - no business logic.
    Returns snapshot dataclasses, not ORM models.
    """

    # -------------------------------------------------------------------------
    # Project/Tenant Operations
    # -------------------------------------------------------------------------

    async def fetch_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> Optional[TenantSnapshot]:
        """Fetch a tenant by ID."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return None

        return TenantSnapshot(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            plan=tenant.plan,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

    async def fetch_tenants(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TenantSnapshot]:
        """Fetch tenants (filtered by tenant_id for isolation)."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)

        if status is not None:
            stmt = stmt.where(Tenant.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        tenants = result.scalars().all()

        return [
            TenantSnapshot(
                id=t.id,
                name=t.name,
                slug=t.slug,
                status=t.status,
                plan=t.plan,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ]

    async def count_tenants(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> int:
        """Count tenants."""
        stmt = select(func.count(Tenant.id)).where(Tenant.id == tenant_id)
        if status is not None:
            stmt = stmt.where(Tenant.status == status)

        result = await session.execute(stmt)
        return result.scalar() or 0

    async def fetch_tenant_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> Optional[TenantDetailSnapshot]:
        """Fetch detailed tenant data."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return None

        return TenantDetailSnapshot(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            plan=tenant.plan,
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
    # User Operations
    # -------------------------------------------------------------------------

    async def fetch_users(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserSnapshot]:
        """Fetch users in a tenant."""
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
        if status is not None:
            stmt = stmt.where(User.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = result.all()

        return [
            UserSnapshot(
                id=row.id,
                email=row.email,
                name=row.name,
                status=row.status,
                role=row.role,
                created_at=row.created_at,
                last_login_at=row.last_login_at,
            )
            for row in rows
        ]

    async def count_users(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count users in a tenant."""
        stmt = (
            select(func.count(User.id))
            .join(TenantMembership, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == tenant_id)
        )
        if role is not None:
            stmt = stmt.where(TenantMembership.role == role)
        if status is not None:
            stmt = stmt.where(User.status == status)

        result = await session.execute(stmt)
        return result.scalar() or 0

    async def fetch_user_detail(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
    ) -> Optional[UserDetailSnapshot]:
        """Fetch detailed user data with membership."""
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

        return UserDetailSnapshot(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            status=user.status,
            role=membership.role,
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

    async def fetch_tenant_memberships(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> list[MembershipSnapshot]:
        """Fetch all memberships for a tenant."""
        stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(TenantMembership.tenant_id == tenant_id)
            .order_by(TenantMembership.created_at)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            MembershipSnapshot(
                user_id=membership.user_id,
                email=user.email,
                name=user.name,
                role=membership.role,
                created_at=membership.created_at,
            )
            for membership, user in rows
        ]

    async def fetch_membership(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
    ) -> Optional[TenantMembership]:
        """Fetch a specific membership (returns ORM model for mutations)."""
        stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def fetch_membership_with_user(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
    ) -> Optional[tuple[TenantMembership, User]]:
        """Fetch membership with user data."""
        stmt = (
            select(TenantMembership, User)
            .join(User, TenantMembership.user_id == User.id)
            .where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        result = await session.execute(stmt)
        row = result.one_or_none()
        return row if row else None

    async def update_membership_role(
        self,
        session: AsyncSession,
        membership: TenantMembership,
        new_role: str,
    ) -> MembershipSnapshot:
        """Update membership role."""
        membership.role = new_role
        await session.commit()

        # Get user for snapshot
        user_stmt = select(User).where(User.id == membership.user_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one()

        return MembershipSnapshot(
            user_id=membership.user_id,
            email=user.email,
            name=user.name,
            role=membership.role,
            created_at=membership.created_at,
        )

    async def delete_membership(
        self,
        session: AsyncSession,
        membership: TenantMembership,
    ) -> bool:
        """Delete a membership."""
        await session.delete(membership)
        await session.commit()
        return True

    # -------------------------------------------------------------------------
    # Profile Operations
    # -------------------------------------------------------------------------

    async def fetch_profile(
        self,
        session: AsyncSession,
        tenant_id: str,
        clerk_user_id: Optional[str],
    ) -> ProfileSnapshot:
        """Fetch user profile."""
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
        role = "member"
        if user:
            membership_stmt = (
                select(TenantMembership)
                .where(TenantMembership.user_id == user.id)
                .where(TenantMembership.tenant_id == tenant_id)
            )
            membership_result = await session.execute(membership_stmt)
            membership = membership_result.scalar_one_or_none()
            if membership:
                role = membership.role

        if user:
            return ProfileSnapshot(
                user_id=user.id,
                email=user.email,
                name=user.name,
                avatar_url=user.avatar_url,
                tenant_id=tenant_id,
                tenant_name=tenant.name if tenant else None,
                role=role,
                created_at=user.created_at,
                preferences=None,  # Parsed from JSON in facade
            )
        else:
            from datetime import timezone
            return ProfileSnapshot(
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

    async def fetch_user_by_id(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> Optional[User]:
        """Fetch user by ID (returns ORM model for mutations)."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_profile(
        self,
        session: AsyncSession,
        user: User,
        *,
        display_name: Optional[str] = None,
        timezone_str: Optional[str] = None,
        preferences: Optional[dict[str, Any]] = None,
    ) -> User:
        """Update user profile fields."""
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
        return user

    # -------------------------------------------------------------------------
    # Billing Operations
    # -------------------------------------------------------------------------

    async def fetch_subscription(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> Optional[SubscriptionSnapshot]:
        """Fetch latest subscription for tenant."""
        stmt = (
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription is None:
            return None

        return SubscriptionSnapshot(
            plan=subscription.plan,
            status=subscription.status,
            billing_period=subscription.billing_period,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
        )

    # -------------------------------------------------------------------------
    # Support Ticket Operations
    # -------------------------------------------------------------------------

    async def insert_support_ticket(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        *,
        subject: str,
        description: str,
        category: str,
        priority: str,
    ) -> TicketSnapshot:
        """Insert a new support ticket."""
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

        return TicketSnapshot(
            id=new_ticket.id,
            subject=new_ticket.subject,
            description=new_ticket.description,
            category=new_ticket.category,
            priority=new_ticket.priority,
            status=new_ticket.status,
            resolution=new_ticket.resolution,
            created_at=new_ticket.created_at,
            updated_at=new_ticket.updated_at,
            resolved_at=new_ticket.resolved_at,
        )

    async def fetch_support_tickets(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> list[TicketSnapshot]:
        """Fetch support tickets for tenant."""
        stmt = select(SupportTicket).where(SupportTicket.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(SupportTicket.status == status)

        stmt = stmt.order_by(SupportTicket.created_at.desc())
        result = await session.execute(stmt)
        tickets = result.scalars().all()

        return [
            TicketSnapshot(
                id=t.id,
                subject=t.subject,
                description=t.description,
                category=t.category,
                priority=t.priority,
                status=t.status,
                resolution=t.resolution,
                created_at=t.created_at,
                updated_at=t.updated_at,
                resolved_at=t.resolved_at,
            )
            for t in tickets
        ]

    # -------------------------------------------------------------------------
    # Invitation Operations
    # -------------------------------------------------------------------------

    async def fetch_invitation_by_email(
        self,
        session: AsyncSession,
        tenant_id: str,
        email: str,
        status: str = "pending",
    ) -> Optional[Invitation]:
        """Fetch pending invitation by email."""
        stmt = select(Invitation).where(
            Invitation.tenant_id == tenant_id,
            Invitation.email == email,
            Invitation.status == status,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def insert_invitation(
        self,
        session: AsyncSession,
        tenant_id: str,
        email: str,
        role: str,
        token_hash: str,
        invited_by: str,
        expires_at: datetime,
    ) -> InvitationSnapshot:
        """Insert a new invitation."""
        now = utc_now()
        new_invitation = Invitation(
            id=generate_uuid(),
            tenant_id=tenant_id,
            email=email,
            role=role,
            status="pending",
            token_hash=token_hash,
            invited_by=invited_by,
            created_at=now,
            expires_at=expires_at,
        )

        session.add(new_invitation)
        await session.commit()
        await session.refresh(new_invitation)

        return InvitationSnapshot(
            id=new_invitation.id,
            email=new_invitation.email,
            role=new_invitation.role,
            status=new_invitation.status,
            token_hash=new_invitation.token_hash,
            invited_by=new_invitation.invited_by,
            created_at=new_invitation.created_at,
            expires_at=new_invitation.expires_at,
            accepted_at=new_invitation.accepted_at,
        )

    async def fetch_invitations(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        status: Optional[str] = None,
    ) -> list[InvitationSnapshot]:
        """Fetch invitations for tenant."""
        stmt = select(Invitation).where(Invitation.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(Invitation.status == status)

        stmt = stmt.order_by(Invitation.created_at.desc())
        result = await session.execute(stmt)
        invitations = result.scalars().all()

        return [
            InvitationSnapshot(
                id=inv.id,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                token_hash=inv.token_hash,
                invited_by=inv.invited_by,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                accepted_at=inv.accepted_at,
            )
            for inv in invitations
        ]

    async def fetch_invitation_by_id_and_token(
        self,
        session: AsyncSession,
        invitation_id: str,
        token_hash: str,
    ) -> Optional[Invitation]:
        """Fetch invitation by ID and token hash."""
        stmt = select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def fetch_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Fetch user by email."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def insert_user(
        self,
        session: AsyncSession,
        email: str,
        name: str,
    ) -> User:
        """Insert a new user."""
        now = utc_now()
        user = User(
            id=generate_uuid(),
            email=email,
            name=name,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        await session.flush()
        return user

    async def insert_membership(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        role: str,
    ) -> TenantMembership:
        """Insert a new membership."""
        now = utc_now()
        membership = TenantMembership(
            id=generate_uuid(),
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            created_at=now,
        )
        session.add(membership)
        return membership

    async def update_invitation_accepted(
        self,
        session: AsyncSession,
        invitation: Invitation,
    ) -> InvitationSnapshot:
        """Mark invitation as accepted."""
        now = utc_now()
        invitation.status = "accepted"
        invitation.accepted_at = now
        await session.commit()

        return InvitationSnapshot(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            token_hash=invitation.token_hash,
            invited_by=invitation.invited_by,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
        )

    async def update_invitation_expired(
        self,
        session: AsyncSession,
        invitation: Invitation,
    ) -> None:
        """Mark invitation as expired."""
        invitation.status = "expired"
        await session.commit()


# =============================================================================
# Singleton Factory
# =============================================================================

_driver_instance: AccountsFacadeDriver | None = None


def get_accounts_facade_driver() -> AccountsFacadeDriver:
    """Get the singleton AccountsFacadeDriver instance."""
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = AccountsFacadeDriver()
    return _driver_instance


__all__ = [
    # Driver
    "AccountsFacadeDriver",
    "get_accounts_facade_driver",
    # Snapshots
    "TenantSnapshot",
    "TenantDetailSnapshot",
    "UserSnapshot",
    "UserDetailSnapshot",
    "MembershipSnapshot",
    "ProfileSnapshot",
    "SubscriptionSnapshot",
    "InvitationSnapshot",
    "TicketSnapshot",
]
