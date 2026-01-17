# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Tenant state derivation (authoritative)
# Callers: Auth middleware, API endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: docs/architecture/contracts/AUTHORITY_CONTRACT.md

"""
Tenant State Resolver

Derives tenant state from account and user readiness.
State is COMPUTED, not manually set.

Design Rules:
- State is derived from: account → users → bindings → billing
- onboarding_state column is CACHED, system-owned
- No direct updates except via resolver
- Auth must fail loudly with explicit state info

State Derivation:
    CREATED (0)      → tenant exists
    CONFIGURING (1)  → account created
    VALIDATING (2)   → at least one user exists
    PROVISIONING (3) → user verified, bindings created
    COMPLETE (4)     → ≥1 ACTIVE user bound, billing ok
    SUSPENDED (5)    → billing hold or policy violation
    ARCHIVED (6)     → soft deleted
"""

from enum import IntEnum
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class TenantState(IntEnum):
    """
    Tenant lifecycle states.

    States are ordered by progression through onboarding.
    Only COMPLETE (4) allows full operations.
    """
    CREATED = 0       # Tenant record exists, nothing else
    CONFIGURING = 1   # Account created, setup in progress
    VALIDATING = 2    # User exists, pending verification
    PROVISIONING = 3  # User verified, creating bindings
    COMPLETE = 4      # Fully operational
    SUSPENDED = 5     # Billing/policy hold
    ARCHIVED = 6      # Soft deleted

    @classmethod
    def from_int(cls, value: int) -> "TenantState":
        """Convert integer to TenantState, defaulting to CREATED."""
        try:
            return cls(value)
        except ValueError:
            return cls.CREATED

    @property
    def is_operational(self) -> bool:
        """Can this tenant perform normal operations?"""
        return self == TenantState.COMPLETE

    @property
    def is_active(self) -> bool:
        """Is this tenant active (not suspended/archived)?"""
        return self not in (TenantState.SUSPENDED, TenantState.ARCHIVED)

    @property
    def allows_read(self) -> bool:
        """Can this tenant read data?"""
        return self not in (TenantState.ARCHIVED,)

    @property
    def allows_write(self) -> bool:
        """Can this tenant write data?"""
        return self == TenantState.COMPLETE


class TenantStateResolver:
    """
    Derives tenant state from account/user readiness.

    This is the AUTHORITATIVE source of tenant state.
    The onboarding_state column in the database is a CACHE
    that should be updated by this resolver.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve(self, tenant_id: str) -> TenantState:
        """
        Derive the current state for a tenant.

        Checks (in order):
        1. Does tenant exist?
        2. Is tenant archived/suspended?
        3. Does account exist?
        4. Does at least one user exist?
        5. Is at least one user verified?
        6. Are RBAC bindings in place?
        7. Is billing ok?

        Returns:
            TenantState derived from current data
        """
        from sqlalchemy import text

        # Check 1: Tenant exists and get cached state
        tenant_query = text("""
            SELECT id, onboarding_state, billing_state
            FROM tenants
            WHERE id = :tenant_id
        """)
        result = await self.session.execute(tenant_query, {"tenant_id": tenant_id})
        tenant_row = result.first()

        if not tenant_row:
            # Tenant doesn't exist - this is an error condition
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        tenant_id, cached_state, billing_state = tenant_row

        # Check 2: Explicit suspension or archive
        if cached_state == TenantState.ARCHIVED:
            return TenantState.ARCHIVED
        if cached_state == TenantState.SUSPENDED or billing_state == "SUSPENDED":
            return TenantState.SUSPENDED

        # Check 3: Account exists
        account_query = text("""
            SELECT COUNT(*) FROM accounts WHERE tenant_id = :tenant_id
        """)
        result = await self.session.execute(account_query, {"tenant_id": tenant_id})
        account_count = result.scalar() or 0

        if account_count == 0:
            return TenantState.CREATED

        # Check 4: At least one user exists
        user_query = text("""
            SELECT COUNT(*) FROM account_users au
            JOIN accounts a ON au.account_id = a.id
            WHERE a.tenant_id = :tenant_id
        """)
        result = await self.session.execute(user_query, {"tenant_id": tenant_id})
        user_count = result.scalar() or 0

        if user_count == 0:
            return TenantState.CONFIGURING

        # Check 5: At least one verified user
        verified_query = text("""
            SELECT COUNT(*) FROM account_users au
            JOIN accounts a ON au.account_id = a.id
            WHERE a.tenant_id = :tenant_id
            AND au.email_verified = true
        """)
        result = await self.session.execute(verified_query, {"tenant_id": tenant_id})
        verified_count = result.scalar() or 0

        if verified_count == 0:
            return TenantState.VALIDATING

        # Check 6: RBAC bindings exist
        binding_query = text("""
            SELECT COUNT(*) FROM tenant_users
            WHERE tenant_id = :tenant_id
            AND status = 'ACTIVE'
        """)
        result = await self.session.execute(binding_query, {"tenant_id": tenant_id})
        binding_count = result.scalar() or 0

        if binding_count == 0:
            return TenantState.PROVISIONING

        # All checks passed
        return TenantState.COMPLETE

    async def resolve_and_cache(self, tenant_id: str) -> TenantState:
        """
        Resolve state and update the cached value in the database.

        Use this when you need to ensure the cache is fresh.
        """
        from sqlalchemy import text

        state = await self.resolve(tenant_id)

        # Update the cached state
        update_query = text("""
            UPDATE tenants
            SET onboarding_state = :state
            WHERE id = :tenant_id
        """)
        await self.session.execute(update_query, {
            "tenant_id": tenant_id,
            "state": state.value
        })

        return state


class TenantNotFoundError(Exception):
    """Raised when tenant doesn't exist."""
    pass


class TenantNotReadyError(Exception):
    """Raised when tenant is not in COMPLETE state."""
    def __init__(self, tenant_id: str, current_state: TenantState):
        self.tenant_id = tenant_id
        self.current_state = current_state
        super().__init__(
            f"Tenant {tenant_id} is in state {current_state.name} ({current_state.value}), "
            f"requires COMPLETE (4)"
        )


async def require_tenant_ready(
    session: AsyncSession,
    tenant_id: str,
    use_cache: bool = True
) -> TenantState:
    """
    Gate function: Ensure tenant is in COMPLETE state.

    Use in endpoints that require full tenant operations.

    Args:
        session: Database session
        tenant_id: Tenant to check
        use_cache: If True, use cached state. If False, resolve fresh.

    Returns:
        TenantState.COMPLETE

    Raises:
        HTTPException(403) if tenant is not ready
        HTTPException(404) if tenant doesn't exist
    """
    resolver = TenantStateResolver(session)

    try:
        if use_cache:
            # Fast path: check cached state first
            from sqlalchemy import text
            query = text("SELECT onboarding_state FROM tenants WHERE id = :tenant_id")
            result = await session.execute(query, {"tenant_id": tenant_id})
            row = result.first()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "tenant_not_found",
                        "tenant_id": tenant_id,
                        "message": f"Tenant {tenant_id} does not exist"
                    }
                )

            cached_state = TenantState.from_int(row[0])

            # If cached state is COMPLETE, trust it
            if cached_state == TenantState.COMPLETE:
                return cached_state

            # Otherwise, resolve to get accurate state
            state = await resolver.resolve(tenant_id)
        else:
            state = await resolver.resolve(tenant_id)

    except TenantNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "tenant_not_found",
                "tenant_id": tenant_id,
                "message": f"Tenant {tenant_id} does not exist"
            }
        )

    if state != TenantState.COMPLETE:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_not_ready",
                "tenant_id": tenant_id,
                "state": state.value,
                "state_name": state.name,
                "required_state": TenantState.COMPLETE.value,
                "required_state_name": TenantState.COMPLETE.name,
                "message": f"Tenant is in state {state.name} ({state.value}), "
                          f"requires COMPLETE ({TenantState.COMPLETE.value})"
            }
        )

    return state


async def require_tenant_active(
    session: AsyncSession,
    tenant_id: str
) -> TenantState:
    """
    Gate function: Ensure tenant is not suspended or archived.

    Use for read-only operations that should work during onboarding.

    Args:
        session: Database session
        tenant_id: Tenant to check

    Returns:
        Current TenantState (any active state)

    Raises:
        HTTPException(403) if tenant is suspended/archived
        HTTPException(404) if tenant doesn't exist
    """
    resolver = TenantStateResolver(session)

    try:
        state = await resolver.resolve(tenant_id)
    except TenantNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "tenant_not_found",
                "tenant_id": tenant_id,
                "message": f"Tenant {tenant_id} does not exist"
            }
        )

    if not state.is_active:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_inactive",
                "tenant_id": tenant_id,
                "state": state.value,
                "state_name": state.name,
                "message": f"Tenant is {state.name} and cannot perform operations"
            }
        )

    return state
