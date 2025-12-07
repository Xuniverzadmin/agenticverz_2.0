"""
RBAC (Role-Based Access Control) Integration for Policy API

This module provides authorization checks for approval workflows.
It integrates with Clerk (primary) or legacy auth service for role validation.

Usage:
    from app.auth.rbac import check_approver_permission, RBACError

    try:
        check_approver_permission(
            approver_id="user-123",
            required_level=3,
            tenant_id="tenant-abc"
        )
    except RBACError as e:
        raise HTTPException(status_code=403, detail=str(e))
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import httpx

logger = logging.getLogger("nova.auth.rbac")

# Auth service configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
AUTH_SERVICE_TIMEOUT = float(os.getenv("AUTH_SERVICE_TIMEOUT", "5.0"))
RBAC_ENABLED = os.getenv("RBAC_ENABLED", "false").lower() == "true"
RBAC_ENFORCE = os.getenv("RBAC_ENFORCE", "false").lower() == "true"

# Clerk configuration (M8 - preferred auth provider)
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
USE_CLERK_AUTH = bool(CLERK_SECRET_KEY)

# Production safety: fail-closed when enforcement is enabled
FAIL_CLOSED_ON_AUTH_ERROR = RBAC_ENFORCE


class ApprovalLevel(IntEnum):
    """Approval levels mapped to organizational roles."""
    SELF = 1        # Self-approval for low-risk operations
    TEAM_MEMBER = 2  # Any authenticated team member
    TEAM_LEAD = 3    # Team lead or senior engineer
    MANAGER = 4      # Manager or policy admin
    OWNER = 5        # Owner override (requires audit)


@dataclass
class RBACResult:
    """Result of RBAC permission check."""
    allowed: bool
    approver_id: str
    granted_level: int
    required_level: int
    reason: Optional[str] = None
    roles: list = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []


class RBACError(Exception):
    """Raised when authorization check fails."""

    def __init__(self, message: str, approver_id: str, required_level: int):
        self.message = message
        self.approver_id = approver_id
        self.required_level = required_level
        super().__init__(message)


async def _get_user_roles_async(approver_id: str, tenant_id: Optional[str] = None) -> dict:
    """
    Fetch user roles from Clerk or legacy auth service (async version).

    Args:
        approver_id: User ID to check
        tenant_id: Optional tenant context

    Returns:
        Dict with user info and roles

    Raises:
        RBACError: If auth service is unavailable or user not found
    """
    if not RBAC_ENABLED:
        if RBAC_ENFORCE:
            # Fail-closed: RBAC enforcement requires RBAC to be enabled
            logger.error(f"RBAC_ENFORCE=true but RBAC_ENABLED=false - configuration error")
            raise RBACError(
                "RBAC enforcement enabled but RBAC not configured",
                approver_id,
                0,
            )
        # Return mock response when RBAC is disabled (dev/test only)
        logger.warning(f"RBAC disabled, returning mock roles for {approver_id} - NOT FOR PRODUCTION")
        return {
            "user_id": approver_id,
            "roles": ["team_member"],
            "max_approval_level": 3,  # Default to team lead level
            "tenant_id": tenant_id,
        }

    # Use Clerk if configured (M8+)
    if USE_CLERK_AUTH:
        try:
            from app.auth.clerk_provider import get_user_roles_from_clerk
            return await get_user_roles_from_clerk(approver_id, tenant_id)
        except Exception as e:
            logger.error(f"Clerk auth error: {e}")
            raise RBACError(
                f"Clerk authorization failed: {e}",
                approver_id,
                0,
            )

    # Fall back to legacy auth service
    try:
        async with httpx.AsyncClient(timeout=AUTH_SERVICE_TIMEOUT) as client:
            params = {"tenant_id": tenant_id} if tenant_id else {}
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/v1/users/{approver_id}/roles",
                params=params,
            )

            if response.status_code == 404:
                raise RBACError(
                    f"User {approver_id} not found in auth service",
                    approver_id,
                    0,
                )

            response.raise_for_status()
            return response.json()

    except httpx.RequestError as e:
        logger.error(f"Auth service unavailable: {e}")
        # Fail closed - deny if auth service is down
        raise RBACError(
            "Authorization service unavailable",
            approver_id,
            0,
        )


def _get_user_roles(approver_id: str, tenant_id: Optional[str] = None) -> dict:
    """
    Fetch user roles from auth service (sync wrapper).

    This is a synchronous wrapper around _get_user_roles_async for
    backward compatibility with existing sync code.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _get_user_roles_async(approver_id, tenant_id)
                )
                return future.result(timeout=AUTH_SERVICE_TIMEOUT + 1)
        else:
            return loop.run_until_complete(
                _get_user_roles_async(approver_id, tenant_id)
            )
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(_get_user_roles_async(approver_id, tenant_id))


def _role_to_level(roles: list) -> int:
    """
    Map user roles to maximum approval level.

    Role hierarchy:
    - owner -> level 5
    - manager, policy_admin -> level 4
    - team_lead, senior_engineer -> level 3
    - team_member, engineer -> level 2
    - guest, readonly -> level 1
    """
    role_levels = {
        "owner": 5,
        "admin": 5,
        "manager": 4,
        "policy_admin": 4,
        "director": 4,
        "team_lead": 3,
        "senior_engineer": 3,
        "tech_lead": 3,
        "team_member": 2,
        "engineer": 2,
        "developer": 2,
        "guest": 1,
        "readonly": 1,
    }

    max_level = 1
    for role in roles:
        role_lower = role.lower()
        if role_lower in role_levels:
            max_level = max(max_level, role_levels[role_lower])

    return max_level


def check_approver_permission(
    approver_id: str,
    required_level: int,
    tenant_id: Optional[str] = None,
) -> RBACResult:
    """
    Check if approver has permission to approve at the required level.

    Args:
        approver_id: ID of the user attempting approval
        required_level: Minimum approval level required (1-5)
        tenant_id: Optional tenant context for multi-tenant checks

    Returns:
        RBACResult with authorization decision

    Raises:
        RBACError: If authorization fails
    """
    # Validate level
    if required_level < 1 or required_level > 5:
        raise ValueError(f"Invalid approval level: {required_level}")

    # Fetch user roles
    user_info = _get_user_roles(approver_id, tenant_id)
    roles = user_info.get("roles", [])

    # Check if auth service returned a max level directly
    if "max_approval_level" in user_info:
        granted_level = user_info["max_approval_level"]
    else:
        granted_level = _role_to_level(roles)

    # Log high-level approvals for audit
    if required_level >= ApprovalLevel.OWNER:
        logger.warning(
            "owner_level_approval_attempt",
            extra={
                "approver_id": approver_id,
                "required_level": required_level,
                "granted_level": granted_level,
                "tenant_id": tenant_id,
                "roles": roles,
            }
        )

    # Check permission
    allowed = granted_level >= required_level

    result = RBACResult(
        allowed=allowed,
        approver_id=approver_id,
        granted_level=granted_level,
        required_level=required_level,
        roles=roles,
        reason=None if allowed else f"Insufficient permission: has level {granted_level}, needs {required_level}",
    )

    # Log the decision
    logger.info(
        "rbac_check",
        extra={
            "allowed": allowed,
            "approver_id": approver_id,
            "required_level": required_level,
            "granted_level": granted_level,
            "tenant_id": tenant_id,
        }
    )

    if not allowed:
        raise RBACError(
            result.reason,
            approver_id,
            required_level,
        )

    return result


def require_approval_level(level: int):
    """
    Decorator factory for requiring minimum approval level.

    Usage:
        @require_approval_level(ApprovalLevel.MANAGER)
        async def approve_high_risk_request(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, approver_id: str, tenant_id: Optional[str] = None, **kwargs):
            check_approver_permission(approver_id, level, tenant_id)
            return await func(*args, approver_id=approver_id, tenant_id=tenant_id, **kwargs)
        return wrapper
    return decorator
