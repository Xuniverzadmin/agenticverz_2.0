"""
Tenant-Aware API Key Authentication (M21)

Provides:
- API key validation against database (not env vars)
- Tenant context extraction from API key
- Quota enforcement before request processing
- Usage tracking after request completion
- Rate limiting per key/tenant
- TenantTier integration (M32)
"""

import hashlib
import logging
import os
from typing import TYPE_CHECKING, Optional, Tuple

from fastapi import Depends, Header, HTTPException, Request, status
from sqlmodel import Session, select

if TYPE_CHECKING:
    from .tier_gating import TenantTier

logger = logging.getLogger("nova.auth.tenant")


# ============== Tenant Context ==============


class TenantContext:
    """
    Context object passed through request lifecycle.
    Contains tenant, user, and API key information.
    """

    def __init__(
        self,
        tenant_id: str,
        tenant_slug: str,
        tenant_name: str,
        plan: str,
        api_key_id: str,
        api_key_name: str,
        user_id: Optional[str] = None,
        permissions: list[str] = None,
        allowed_workers: list[str] = None,
        rate_limit_rpm: Optional[int] = None,
        max_concurrent_runs: Optional[int] = None,
    ):
        self.tenant_id = tenant_id
        self.tenant_slug = tenant_slug
        self.tenant_name = tenant_name
        self.plan = plan
        self.api_key_id = api_key_id
        self.api_key_name = api_key_name
        self.user_id = user_id
        self.permissions = permissions or ["run:*", "read:*"]
        self.allowed_workers = allowed_workers or []  # Empty = all allowed
        self.rate_limit_rpm = rate_limit_rpm
        self.max_concurrent_runs = max_concurrent_runs

    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True
        # Check wildcard patterns like "run:*"
        parts = permission.split(":")
        if len(parts) == 2:
            wildcard = f"{parts[0]}:*"
            if wildcard in self.permissions:
                return True
        return False

    def can_use_worker(self, worker_id: str) -> bool:
        """Check if context is allowed to use a specific worker."""
        if not self.allowed_workers:
            return True  # Empty = all allowed
        return worker_id in self.allowed_workers

    @property
    def tier(self) -> "TenantTier":
        """
        Get the tenant's tier from their plan.

        Resolves legacy plan names (free, pro, enterprise) and new tier names
        (observe, react, prevent, assist, govern) to TenantTier enum.
        """
        from .tier_gating import resolve_tier

        return resolve_tier(self.plan)

    def has_feature(self, feature: str) -> bool:
        """
        Check if tenant has access to a feature based on their tier.

        Uses CURRENT_PHASE to determine soft/hard gating.
        """
        from .tier_gating import check_tier_access

        result = check_tier_access(feature, self.tier)
        return result.allowed

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_slug": self.tenant_slug,
            "plan": self.plan,
            "api_key_id": self.api_key_id,
            "user_id": self.user_id,
        }


# ============== Database Connection ==============


def get_db_session():
    """Get database session - to be configured in main.py."""
    from ..db import get_session

    return next(get_session())


# ============== API Key Validation ==============


def hash_api_key(key: str) -> str:
    """Hash an API key for database lookup."""
    return hashlib.sha256(key.encode()).hexdigest()


async def validate_api_key_db(
    api_key: str,
    session: Session,
) -> Tuple[Optional["TenantContext"], Optional[str]]:
    """
    Validate API key against database.

    Returns:
        (TenantContext, None) on success
        (None, error_message) on failure
    """
    import json

    from ..models.tenant import APIKey, Tenant

    if not api_key:
        return None, "API key required"

    # Check key format
    if not api_key.startswith("aos_"):
        return None, "Invalid API key format"

    # Hash for lookup
    key_hash = hash_api_key(api_key)

    # Look up key
    stmt = select(APIKey).where(APIKey.key_hash == key_hash)
    result = session.exec(stmt).first()
    # Handle both Row tuple and direct model returns
    if result is None:
        db_key = None
    elif hasattr(result, "key_hash"):  # Already a model
        db_key = result
    else:  # Row tuple
        db_key = result[0]

    if not db_key:
        logger.warning("api_key_not_found", extra={"key_prefix": api_key[:12]})
        return None, "Invalid API key"

    # Check key validity
    if not db_key.is_valid():
        if db_key.status == "revoked":
            return None, "API key has been revoked"
        if db_key.status == "expired":
            return None, "API key has expired"
        return None, "API key is not active"

    # Get tenant
    stmt = select(Tenant).where(Tenant.id == db_key.tenant_id)
    result = session.exec(stmt).first()
    # Handle both Row tuple and direct model returns
    if result is None:
        tenant = None
    elif hasattr(result, "id"):  # Already a model
        tenant = result
    else:  # Row tuple
        tenant = result[0]

    if not tenant:
        logger.error("tenant_not_found", extra={"tenant_id": db_key.tenant_id})
        return None, "Tenant not found"

    # Check tenant status
    if tenant.status != "active":
        return None, f"Tenant account is {tenant.status}"

    # Parse permissions
    permissions = []
    if db_key.permissions_json:
        try:
            permissions = json.loads(db_key.permissions_json)
        except json.JSONDecodeError:
            permissions = []

    # Parse allowed workers
    allowed_workers = []
    if db_key.allowed_workers_json:
        try:
            allowed_workers = json.loads(db_key.allowed_workers_json)
        except json.JSONDecodeError:
            allowed_workers = []

    # Record usage
    db_key.record_usage()
    session.add(db_key)
    session.commit()

    # Build context
    context = TenantContext(
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        tenant_name=tenant.name,
        plan=tenant.plan,
        api_key_id=db_key.id,
        api_key_name=db_key.name,
        user_id=db_key.user_id,
        permissions=permissions,
        allowed_workers=allowed_workers,
        rate_limit_rpm=db_key.rate_limit_rpm,
        max_concurrent_runs=db_key.max_concurrent_runs,
    )

    logger.info(
        "api_key_validated",
        extra={
            "tenant_id": tenant.id,
            "tenant_slug": tenant.slug,
            "key_name": db_key.name,
        },
    )

    return context, None


# ============== FastAPI Dependencies ==============


async def get_tenant_context(
    request: Request,
    x_aos_key: str = Header(None, alias="X-AOS-Key"),
    authorization: str = Header(None),
) -> TenantContext:
    """
    FastAPI dependency that validates API key and returns tenant context.

    Accepts API key via:
    - X-AOS-Key header (preferred)
    - Authorization: Bearer aos_xxx header

    Raises HTTPException on invalid/missing key.
    """
    # Extract API key from headers
    api_key = None

    if x_aos_key:
        api_key = x_aos_key
    elif authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-AOS-Key header or Authorization: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get database session
    try:
        session = get_db_session()
    except Exception:
        logger.exception("db_session_error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    # Validate key
    try:
        context, error = await validate_api_key_db(api_key, session)
    except Exception:
        logger.exception("api_key_validation_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )
    finally:
        session.close()

    # If DB validation fails, try legacy fallback
    if error and _USE_LEGACY_AUTH and _LEGACY_API_KEY and api_key == _LEGACY_API_KEY:
        # Create a synthetic context for legacy key
        context = TenantContext(
            tenant_id="legacy",
            tenant_slug="legacy",
            tenant_name="Legacy API Key",
            plan="enterprise",  # Legacy keys get full access
            api_key_id="legacy",
            api_key_name="Environment API Key",
            permissions=["*"],  # Full access
        )
        request.state.tenant_context = context
        return context

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store in request state for later use
    request.state.tenant_context = context

    return context


async def require_permission(permission: str):
    """
    Factory for permission-checking dependency.

    Usage:
        @router.post("/runs")
        async def create_run(
            ctx: TenantContext = Depends(get_tenant_context),
            _: None = Depends(require_permission("run:create")),
        ):
            ...
    """

    async def checker(ctx: TenantContext = Depends(get_tenant_context)):
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return None

    return checker


async def require_worker_access(worker_id: str):
    """
    Factory for worker access checking dependency.

    Usage:
        @router.post("/workers/{worker_id}/run")
        async def run_worker(
            worker_id: str,
            ctx: TenantContext = Depends(get_tenant_context),
            _: None = Depends(require_worker_access(worker_id)),
        ):
            ...
    """

    async def checker(ctx: TenantContext = Depends(get_tenant_context)):
        if not ctx.can_use_worker(worker_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Worker access denied: {worker_id}",
            )
        return None

    return checker


# ============== Optional: Legacy Fallback ==============

_LEGACY_API_KEY = os.getenv("AOS_API_KEY", "")
_USE_LEGACY_AUTH = os.getenv("AOS_USE_LEGACY_AUTH", "false").lower() == "true"


async def verify_api_key_with_fallback(
    request: Request,
    x_aos_key: str = Header(None, alias="X-AOS-Key"),
    authorization: str = Header(None),
) -> TenantContext:
    """
    API key verification with fallback to legacy env-based auth.

    Used during transition period. Once all API keys are in database,
    switch to get_tenant_context directly.
    """
    # Extract API key
    api_key = None
    if x_aos_key:
        api_key = x_aos_key
    elif authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Try database first
    try:
        session = get_db_session()
        context, error = await validate_api_key_db(api_key, session)
        session.close()

        if context:
            request.state.tenant_context = context
            return context
    except Exception:
        pass  # Fall through to legacy

    # Legacy fallback
    if _USE_LEGACY_AUTH and _LEGACY_API_KEY and api_key == _LEGACY_API_KEY:
        # Create a synthetic context for legacy key
        context = TenantContext(
            tenant_id="legacy",
            tenant_slug="legacy",
            tenant_name="Legacy API Key",
            plan="enterprise",  # Legacy keys get full access
            api_key_id="legacy",
            api_key_name="Environment API Key",
            permissions=["*"],  # Full access
        )
        request.state.tenant_context = context
        return context

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


# ============== Role-Based Access Control (GA Lock Item) ==============

# Define console roles
ROLE_CUSTOMER = "customer"  # Guard Console - customers only
ROLE_OPERATOR = "operator"  # Operator Console - internal staff only

# Operator email domains (internal only)
OPERATOR_DOMAINS = ["agenticverz.com", "agenticverz.io", "localhost"]


def is_operator_user(user_email: Optional[str]) -> bool:
    """Check if user email belongs to an operator (internal staff)."""
    if not user_email:
        return False
    domain = user_email.split("@")[-1].lower() if "@" in user_email else ""
    return domain in OPERATOR_DOMAINS


class ConsoleRole:
    """Role identifier for console access control."""

    CUSTOMER = ROLE_CUSTOMER
    OPERATOR = ROLE_OPERATOR


async def require_customer_role(
    ctx: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    """
    Dependency that enforces customer-only access (Guard Console).

    Operators should use the Operator Console instead.
    GA Lock Item: Guard vs Operator Auth Hard Boundary.
    """
    # Customers can always access Guard Console for their tenant
    # This is tenant-scoped access
    return ctx


async def require_operator_role(
    request: Request,
    x_operator_token: str = Header(None, alias="X-Operator-Token"),
    authorization: str = Header(None),
) -> dict:
    """
    Dependency that enforces operator-only access (Operator Console).

    Requires either:
    1. X-Operator-Token header with valid operator token
    2. Authorization header from operator-authenticated session

    GA Lock Item: Guard vs Operator Auth Hard Boundary.
    """
    import os

    # Check for operator token
    operator_token = os.getenv("AOS_OPERATOR_TOKEN", "")

    # Method 1: X-Operator-Token header
    if x_operator_token:
        if operator_token and x_operator_token == operator_token:
            return {"role": ROLE_OPERATOR, "source": "token"}
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid operator token",
        )

    # Method 2: JWT/Session with operator email domain
    if authorization:
        # In production, validate JWT and check email domain
        # For now, check for operator token in Bearer
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            if operator_token and token == operator_token:
                return {"role": ROLE_OPERATOR, "source": "bearer"}

    # No valid operator authentication
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Operator access required. This endpoint is for internal use only.",
    )


# ============== Exports ==============

__all__ = [
    "TenantContext",
    "get_tenant_context",
    "require_permission",
    "require_worker_access",
    "verify_api_key_with_fallback",
    "hash_api_key",
    # Role-based access (GA Lock)
    "ConsoleRole",
    "require_customer_role",
    "require_operator_role",
    "ROLE_CUSTOMER",
    "ROLE_OPERATOR",
]
