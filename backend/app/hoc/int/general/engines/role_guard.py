# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Phase-5 Role Guard Dependency for endpoint authorization
# Callers: API endpoints (via Depends)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-399 Phase-5 (Post-Onboarding Permissions & Roles)

"""
Phase-5 Role Guard — Dependency-Based Authorization

PIN-399 Phase-5: Authorization is explicit at the endpoint boundary.

DESIGN INVARIANTS (LOCKED):
- ROLE-001: Roles do not exist before onboarding COMPLETE
- ROLE-002: Permissions are derived, not stored
- ROLE-003: Human roles never affect machine scopes
- ROLE-004: Console origin never grants authority
- ROLE-005: Role enforcement never mutates state

USAGE:
    @router.post("/policies")
    async def create_policy(
        request: Request,
        role: TenantRole = Depends(require_role(TenantRole.MEMBER)),
    ):
        ...

ROLE GUARD SEMANTICS:
1. Tenant must be COMPLETE (enforced by onboarding gate)
2. Actor must be human (machine contexts bypass entirely)
3. Actor must have one of the allowed roles
4. Failure returns structured 403 (never generic)
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from .gateway_middleware import get_auth_context
from app.auth.onboarding_state import OnboardingState
from .tenant_roles import TenantRole, get_permissions_for_role, role_has_permission

logger = logging.getLogger("nova.auth.role_guard")


# =============================================================================
# ROLE LOOKUP SERVICE
# =============================================================================


def get_user_role_in_tenant(
    session: Session,
    user_id: str,
    tenant_id: str,
) -> Optional[TenantRole]:
    """
    Look up user's role in a tenant.

    Returns None if user is not a member of the tenant.

    INVARIANT: This is a read-only operation. Never mutates.
    """
    from ..models.tenant import TenantMembership

    statement = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == user_id,
    )
    membership = session.exec(statement).first()

    if membership is None:
        return None

    try:
        return TenantRole.from_string(membership.role)
    except ValueError:
        logger.warning(
            "invalid_role_in_membership",
            extra={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role": membership.role,
            },
        )
        return None


def get_tenant_onboarding_state(
    session: Session,
    tenant_id: str,
) -> Optional[OnboardingState]:
    """
    Get tenant's onboarding state.

    Returns None if tenant not found.
    """
    from ..models.tenant import Tenant

    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        return None

    return OnboardingState(tenant.onboarding_state)


def count_owners_in_tenant(session: Session, tenant_id: str) -> int:
    """
    Count how many OWNERs exist in a tenant.

    Used for OWNER invariant enforcement.
    """
    from sqlmodel import func

    from ..models.tenant import TenantMembership

    statement = select(func.count()).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.role == TenantRole.OWNER.name.lower(),
    )
    result = session.exec(statement).one()
    return result or 0


class OwnerInvariantViolation(Exception):
    """Raised when attempting to remove the last OWNER from a tenant."""

    pass


def validate_owner_invariant(
    session: Session,
    tenant_id: str,
    user_id_to_remove: Optional[str] = None,
) -> None:
    """
    Validate that tenant will still have at least one OWNER.

    INVARIANT: Every tenant has at least one OWNER.
    INVARIANT: OWNER cannot be removed if it's the last one.

    Raises:
        OwnerInvariantViolation: If operation would leave tenant with no OWNER
    """
    from ..models.tenant import TenantMembership

    # Count current OWNERs
    owner_count = count_owners_in_tenant(session, tenant_id)

    # If removing a user, check if they're an OWNER
    if user_id_to_remove:
        statement = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id_to_remove,
            TenantMembership.role == TenantRole.OWNER.name.lower(),
        )
        is_owner = session.exec(statement).first() is not None

        if is_owner and owner_count <= 1:
            raise OwnerInvariantViolation(
                f"Cannot remove last OWNER from tenant {tenant_id}"
            )


# =============================================================================
# ROLE GUARD DEPENDENCY
# =============================================================================


class RoleViolationError(HTTPException):
    """
    Structured 403 for role violations.

    Never generic. Always includes:
    - required_roles
    - actor_role (if known)
    - tenant_id
    """

    def __init__(
        self,
        required_roles: list[str],
        actor_role: Optional[str] = None,
        tenant_id: Optional[str] = None,
        detail: Optional[str] = None,
    ):
        error_detail = {
            "error": "role_violation",
            "required_roles": required_roles,
            "actor_role": actor_role,
            "tenant_id": tenant_id,
            "message": detail or "Insufficient role for this operation",
        }
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_detail,
        )


def require_role(*allowed_roles: TenantRole) -> Callable:
    """
    FastAPI dependency for role-based authorization.

    USAGE:
        @router.post("/policies")
        async def create_policy(
            role: TenantRole = Depends(require_role(TenantRole.MEMBER)),
        ):
            ...

    SEMANTICS:
    1. Machine contexts (API keys) BYPASS this guard entirely
    2. Tenant must be COMPLETE (if not, endpoint should be unreachable)
    3. Actor must have one of the allowed roles
    4. Returns the actor's role for use in endpoint logic

    PROPERTIES (NON-NEGOTIABLE):
    - Pure function (no state mutation)
    - No onboarding logic (handled by onboarding gate)
    - No console awareness
    - Evaluates derived permissions only
    """
    if not allowed_roles:
        raise ValueError("require_role() must specify at least one allowed role")

    async def role_guard_dependency(request: Request) -> TenantRole:
        """
        The actual dependency that runs at request time.

        Returns the actor's TenantRole if authorized.
        Raises RoleViolationError if not.
        """
        from ..db import get_session

        # Get auth context from gateway middleware
        auth_context = get_auth_context(request)

        if auth_context is None:
            logger.warning("role_guard: no auth context")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # INVARIANT ROLE-003: Machine contexts bypass role system
        # API keys use scope-based authorization, not roles
        is_machine = getattr(auth_context, "is_machine", False)
        principal_type = getattr(auth_context, "principal_type", None)

        if is_machine or str(principal_type) == "machine":
            logger.debug(
                "role_guard: machine context bypasses role system",
                extra={"principal_type": principal_type},
            )
            # Return highest allowed role for machine contexts
            # (machines are authorized by scopes, not roles)
            return max(allowed_roles)

        # Get tenant_id from auth context
        tenant_id = getattr(auth_context, "tenant_id", None)
        if tenant_id is None:
            logger.warning("role_guard: no tenant_id in auth context")
            raise RoleViolationError(
                required_roles=[r.name for r in allowed_roles],
                detail="Tenant context required for this operation",
            )

        # Get user_id from auth context
        user_id = getattr(auth_context, "user_id", None)
        if user_id is None:
            logger.warning("role_guard: no user_id in auth context")
            raise RoleViolationError(
                required_roles=[r.name for r in allowed_roles],
                tenant_id=tenant_id,
                detail="User context required for this operation",
            )

        # Look up user's role in tenant
        session = next(get_session())
        try:
            # Check onboarding state (INVARIANT ROLE-001)
            onboarding_state = get_tenant_onboarding_state(session, tenant_id)
            if onboarding_state is None:
                raise RoleViolationError(
                    required_roles=[r.name for r in allowed_roles],
                    tenant_id=tenant_id,
                    detail="Tenant not found",
                )

            if onboarding_state != OnboardingState.COMPLETE:
                # This should not happen - onboarding gate should block first
                # But we enforce anyway for defense in depth
                logger.warning(
                    "role_guard: tenant not COMPLETE",
                    extra={
                        "tenant_id": tenant_id,
                        "onboarding_state": onboarding_state.name,
                    },
                )
                raise RoleViolationError(
                    required_roles=[r.name for r in allowed_roles],
                    tenant_id=tenant_id,
                    detail="Onboarding not complete",
                )

            # Get user's role
            actor_role = get_user_role_in_tenant(session, user_id, tenant_id)

            if actor_role is None:
                logger.warning(
                    "role_guard: user not member of tenant",
                    extra={"user_id": user_id, "tenant_id": tenant_id},
                )
                raise RoleViolationError(
                    required_roles=[r.name for r in allowed_roles],
                    tenant_id=tenant_id,
                    detail="User is not a member of this tenant",
                )

            # Check if actor's role is in allowed roles
            if actor_role not in allowed_roles:
                logger.info(
                    "role_guard: role violation",
                    extra={
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "actor_role": actor_role.name,
                        "required_roles": [r.name for r in allowed_roles],
                    },
                )
                raise RoleViolationError(
                    required_roles=[r.name for r in allowed_roles],
                    actor_role=actor_role.name,
                    tenant_id=tenant_id,
                )

            # Authorization successful
            logger.debug(
                "role_guard: authorized",
                extra={
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "actor_role": actor_role.name,
                },
            )

            return actor_role

        finally:
            session.close()

    return role_guard_dependency


def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency for permission-based authorization.

    USAGE:
        @router.post("/runs")
        async def create_run(
            role: TenantRole = Depends(require_permission("runs:write")),
        ):
            ...

    This is an alternative to require_role() when you want to check
    specific permissions rather than roles.
    """

    async def permission_guard_dependency(request: Request) -> TenantRole:
        """
        Check if actor has a specific permission.
        """
        from ..db import get_session

        auth_context = get_auth_context(request)

        if auth_context is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Machine contexts bypass
        is_machine = getattr(auth_context, "is_machine", False)
        if is_machine:
            return TenantRole.OWNER  # Machines have full access via scopes

        tenant_id = getattr(auth_context, "tenant_id", None)
        user_id = getattr(auth_context, "user_id", None)

        if not tenant_id or not user_id:
            raise RoleViolationError(
                required_roles=[],
                detail=f"Permission '{permission}' requires user and tenant context",
            )

        session = next(get_session())
        try:
            actor_role = get_user_role_in_tenant(session, user_id, tenant_id)

            if actor_role is None:
                raise RoleViolationError(
                    required_roles=[],
                    tenant_id=tenant_id,
                    detail="User is not a member of this tenant",
                )

            if not role_has_permission(actor_role, permission):
                raise RoleViolationError(
                    required_roles=[],
                    actor_role=actor_role.name,
                    tenant_id=tenant_id,
                    detail=f"Permission '{permission}' not granted to role '{actor_role.name}'",
                )

            return actor_role

        finally:
            session.close()

    return permission_guard_dependency


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core dependency
    "require_role",
    "require_permission",
    # Lookup functions
    "get_user_role_in_tenant",
    "get_tenant_onboarding_state",
    "count_owners_in_tenant",
    # Invariant enforcement
    "validate_owner_invariant",
    "OwnerInvariantViolation",
    # Error types
    "RoleViolationError",
]
