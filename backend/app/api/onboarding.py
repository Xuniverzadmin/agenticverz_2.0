"""
Customer Onboarding API - M24

Provides OAuth (Google, Azure) and email-based signup with OTP verification.

Endpoints:
    POST /api/v1/auth/login/google     - Initiate Google OAuth
    GET  /api/v1/auth/callback/google  - Google OAuth callback
    POST /api/v1/auth/login/azure      - Initiate Azure OAuth
    GET  /api/v1/auth/callback/azure   - Azure OAuth callback
    POST /api/v1/auth/signup/email     - Email signup (sends OTP)
    POST /api/v1/auth/verify/email     - Verify email OTP
    POST /api/v1/auth/refresh          - Refresh session token
    POST /api/v1/auth/logout           - Logout (invalidate session)
"""

import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator
from redis import Redis
from sqlmodel import Session, select

from ..auth.oauth_providers import (
    OAuthError,
    OAuthUserInfo,
    get_azure_provider,
    get_google_provider,
)
from ..db import engine
from ..models.tenant import User
from ..services.email_verification import (
    EmailVerificationError,
    get_email_verification_service,
)

# Phase 2B: Write services for DB operations
from ..services.tenant_service import TenantService
from ..services.user_write_service import UserWriteService

logger = logging.getLogger("nova.api.onboarding")

router = APIRouter(prefix="/api/v1/auth", tags=["onboarding"])

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
REFRESH_TTL_DAYS = int(os.getenv("REFRESH_TTL_DAYS", "7"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://agenticverz.com")

# Redis for state storage
_redis: Optional[Redis] = None


def get_redis() -> Redis:
    """Get Redis client singleton."""
    global _redis
    if _redis is None:
        import redis

        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============== Request/Response Schemas ==============


class OAuthLoginRequest(BaseModel):
    """OAuth login request (optional redirect_url)."""

    redirect_url: Optional[str] = None


class OAuthLoginResponse(BaseModel):
    """OAuth login response with authorization URL."""

    authorization_url: str
    state: str


class EmailSignupRequest(BaseModel):
    """Email signup request."""

    email: str = Field(..., min_length=5, max_length=255)
    name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class EmailSignupResponse(BaseModel):
    """Email signup response."""

    success: bool
    message: str
    expires_in: int


class EmailVerifyRequest(BaseModel):
    """Email verification request."""

    email: str = Field(..., min_length=5, max_length=255)
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class AuthResponse(BaseModel):
    """Authentication response with tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""

    refresh_token: Optional[str] = None


# ============== Token Management ==============


def create_tokens(user_id: str, tenant_id: Optional[str] = None) -> tuple[str, str]:
    """Create access and refresh tokens."""
    now = utc_now()

    # Access token
    access_payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=SESSION_TTL_HOURS),
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Refresh token
    refresh_jti = secrets.token_urlsafe(16)
    refresh_payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "jti": refresh_jti,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TTL_DAYS),
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Store refresh token jti in Redis for revocation
    redis = get_redis()
    redis.setex(f"refresh_token:{refresh_jti}", REFRESH_TTL_DAYS * 86400, user_id)

    return access_token, refresh_token


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type")

        # For refresh tokens, verify it hasn't been revoked
        if token_type == "refresh":
            jti = payload.get("jti")
            redis = get_redis()
            if not redis.exists(f"refresh_token:{jti}"):
                raise HTTPException(status_code=401, detail="Token has been revoked")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def revoke_refresh_token(token: str):
    """Revoke a refresh token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        jti = payload.get("jti")
        if jti:
            redis = get_redis()
            redis.delete(f"refresh_token:{jti}")
    except jwt.InvalidTokenError:
        pass  # Token already invalid


# ============== User/Tenant Management ==============


def get_or_create_user_from_oauth(user_info: OAuthUserInfo) -> tuple[dict, bool]:
    """Get or create user from OAuth provider info.

    Returns a dict with user data (not the ORM object) to avoid detached session issues.
    """
    with Session(engine) as session:
        # Try to find existing user by email
        statement = select(User).where(User.email == user_info.email)
        result = session.exec(statement).first()
        # Handle both Row tuple and direct model return (SQLModel version differences)
        user = result if isinstance(result, User) else (result[0] if result else None)

        # Phase 2B: Use write service for DB operations
        user_service = UserWriteService(session)

        is_new = False
        if not user:
            # Create new user via write service
            user = user_service.create_user(
                email=user_info.email,
                clerk_user_id=f"{user_info.provider}_{user_info.provider_user_id}",
                name=user_info.name or user_info.given_name,
                avatar_url=user_info.picture,
                status="active",
            )
            is_new = True

            logger.info(f"Created new user via OAuth: {user.id[:8]}... ({user_info.provider})")
        else:
            # Update last login via write service
            user = user_service.update_user_login(user)

        # Extract values before session closes to avoid DetachedInstanceError
        user_data = user_service.user_to_dict(user)
        return user_data, is_new


def get_or_create_user_from_email(email: str, name: Optional[str] = None) -> tuple[dict, bool]:
    """Get or create user from email verification.

    Returns a dict with user data (not the ORM object) to avoid detached session issues.
    """
    with Session(engine) as session:
        # Try to find existing user
        statement = select(User).where(User.email == email)
        result = session.exec(statement).first()
        # Handle both Row tuple and direct model return (SQLModel version differences)
        user = result if isinstance(result, User) else (result[0] if result else None)

        # Phase 2B: Use write service for DB operations
        user_service = UserWriteService(session)

        is_new = False
        if not user:
            # Create new user via write service
            user = user_service.create_user(
                email=email,
                clerk_user_id=f"email_{hashlib.sha256(email.encode()).hexdigest()[:16]}",
                name=name,
                status="active",
            )
            is_new = True

            logger.info(f"Created new user via email: {user.id[:8]}...")
        else:
            # Update last login via write service
            user = user_service.update_user_login(user)

        # Extract values before session closes to avoid DetachedInstanceError
        user_data = user_service.user_to_dict(user)
        return user_data, is_new


def create_default_tenant_for_user(user_data: dict) -> dict:
    """Create a default personal tenant for a new user.

    Args:
        user_data: Dict with user info (id, email, name)

    Returns:
        Dict with tenant_id
    """
    with Session(engine) as session:
        user_id = user_data["id"]
        user_name = user_data.get("name")
        user_email = user_data.get("email")

        # Phase 2B: Use write services for DB operations
        tenant_service = TenantService(session)

        # Create personal tenant via service
        slug = f"personal-{user_id[:8]}"
        tenant = tenant_service.create_tenant(
            name=f"{user_name or user_email}'s Workspace",
            slug=slug,
            plan="free",
            status="active",
        )

        # Create membership (owner) and set as default tenant via service
        tenant_service.create_membership_with_default(
            tenant=tenant,
            user_id=user_id,
            role="owner",
            set_as_default=True,
        )

        logger.info(f"Created default tenant for user: {tenant.id[:8]}...")

        return {"tenant_id": tenant.id}


def user_to_dict(user: User) -> dict:
    """Convert user to dict for response."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "default_tenant_id": user.default_tenant_id,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ============== OAuth Endpoints ==============


@router.post("/login/google", response_model=OAuthLoginResponse)
async def login_google(request: OAuthLoginRequest = None):
    """
    Initiate Google OAuth login flow.

    Returns authorization URL to redirect user to.
    """
    provider = get_google_provider()

    if not provider.is_configured:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    try:
        auth_url, state = provider.get_authorization_url()

        # Store state in Redis for verification
        redis = get_redis()
        state_data = {
            "provider": "google",
            "redirect_url": request.redirect_url if request else None,
        }
        redis.setex(f"oauth_state:{state}", 600, str(state_data))  # 10 min TTL

        return OAuthLoginResponse(authorization_url=auth_url, state=state)

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/callback/google")
async def callback_google(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
):
    """
    Google OAuth callback handler.

    Called by Google after user authorization.
    """
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error={error}")

    # Verify state
    redis = get_redis()
    stored_state = redis.get(f"oauth_state:{state}")
    if not stored_state:
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error=invalid_state")

    redis.delete(f"oauth_state:{state}")

    provider = get_google_provider()

    try:
        # Exchange code for tokens
        tokens = await provider.exchange_code(code)
        access_token = tokens.get("access_token")

        # Get user info
        user_info = await provider.get_user_info(access_token)

        if not user_info.email_verified:
            return RedirectResponse(f"{FRONTEND_URL}/auth/error?error=email_not_verified")

        # Create or get user (returns dict to avoid DetachedInstanceError)
        user_data, is_new = get_or_create_user_from_oauth(user_info)

        # Create default tenant for new users
        if is_new:
            tenant_result = create_default_tenant_for_user(user_data)
            user_data["default_tenant_id"] = tenant_result["tenant_id"]

        # Create session tokens
        access_token, refresh_token = create_tokens(user_data["id"], user_data["default_tenant_id"])

        # Redirect to frontend with tokens
        redirect_url = (
            f"{FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}&is_new={is_new}"
        )
        return RedirectResponse(redirect_url)

    except OAuthError as e:
        logger.error(f"Google OAuth error: {e.message}")
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error={e.error_code}")


@router.post("/login/azure", response_model=OAuthLoginResponse)
async def login_azure(request: OAuthLoginRequest = None):
    """
    Initiate Azure AD OAuth login flow.

    Returns authorization URL to redirect user to.
    """
    provider = get_azure_provider()

    if not provider.is_configured:
        raise HTTPException(status_code=503, detail="Azure OAuth not configured")

    try:
        auth_url, state = provider.get_authorization_url()

        # Store state in Redis for verification
        redis = get_redis()
        state_data = {
            "provider": "azure",
            "redirect_url": request.redirect_url if request else None,
        }
        redis.setex(f"oauth_state:{state}", 600, str(state_data))  # 10 min TTL

        return OAuthLoginResponse(authorization_url=auth_url, state=state)

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/callback/azure")
async def callback_azure(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """
    Azure AD OAuth callback handler.

    Called by Azure AD after user authorization.
    """
    if error:
        logger.warning(f"Azure OAuth error: {error} - {error_description}")
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error={error}")

    # Verify state
    redis = get_redis()
    stored_state = redis.get(f"oauth_state:{state}")
    if not stored_state:
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error=invalid_state")

    redis.delete(f"oauth_state:{state}")

    provider = get_azure_provider()

    try:
        # Exchange code for tokens
        tokens = await provider.exchange_code(code)
        access_token = tokens.get("access_token")

        # Get user info
        user_info = await provider.get_user_info(access_token)

        # Create or get user (returns dict to avoid DetachedInstanceError)
        user_data, is_new = get_or_create_user_from_oauth(user_info)

        # Create default tenant for new users
        if is_new:
            tenant_result = create_default_tenant_for_user(user_data)
            user_data["default_tenant_id"] = tenant_result["tenant_id"]

        # Create session tokens
        access_token, refresh_token = create_tokens(user_data["id"], user_data["default_tenant_id"])

        # Redirect to frontend with tokens
        redirect_url = (
            f"{FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}&is_new={is_new}"
        )
        return RedirectResponse(redirect_url)

    except OAuthError as e:
        logger.error(f"Azure OAuth error: {e.message}")
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?error={e.error_code}")


# ============== Email Verification Endpoints ==============


@router.post("/signup/email", response_model=EmailSignupResponse)
async def signup_email(request: EmailSignupRequest):
    """
    Initiate email-based signup.

    Sends OTP to provided email address.
    """
    service = get_email_verification_service()

    try:
        result = await service.send_otp(request.email, request.name)
        return EmailSignupResponse(
            success=result["success"],
            message=result["message"],
            expires_in=result["expires_in"],
        )
    except EmailVerificationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/verify/email", response_model=AuthResponse)
async def verify_email(request: EmailVerifyRequest):
    """
    Verify email OTP and complete signup.

    Returns access and refresh tokens on success.
    """
    service = get_email_verification_service()

    result = service.verify_otp(request.email, request.otp)

    if not result.success:
        error_detail = {
            "message": result.message,
            "attempts_remaining": result.attempts_remaining,
        }
        raise HTTPException(status_code=400, detail=error_detail)

    # Create or get user (returns dict to avoid DetachedInstanceError)
    user_data, is_new = get_or_create_user_from_email(result.email)

    # Create default tenant for new users
    if is_new:
        tenant_result = create_default_tenant_for_user(user_data)
        user_data["default_tenant_id"] = tenant_result["tenant_id"]

    # Create session tokens
    access_token, refresh_token = create_tokens(user_data["id"], user_data["default_tenant_id"])

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=SESSION_TTL_HOURS * 3600,
        user=user_data,
    )


# ============== Session Management ==============


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    # Get user and extract data before session closes
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="User not found or inactive")
        # Extract user data before session closes
        user_data = user_to_dict(user)

    # Revoke old refresh token
    revoke_refresh_token(request.refresh_token)

    # Create new tokens
    access_token, new_refresh_token = create_tokens(user_id, tenant_id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=SESSION_TTL_HOURS * 3600,
        user=user_data,
    )


@router.post("/logout")
async def logout(request: LogoutRequest = None):
    """
    Logout and invalidate refresh token.
    """
    if request and request.refresh_token:
        revoke_refresh_token(request.refresh_token)

    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user from Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")

    user_id = payload.get("sub")

    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"user": user_to_dict(user)}


@router.get("/providers")
async def get_auth_providers():
    """
    Get available authentication providers.
    """
    google = get_google_provider()
    azure = get_azure_provider()

    return {
        "providers": [
            {
                "id": "google",
                "name": "Google",
                "enabled": google.is_configured,
            },
            {
                "id": "azure",
                "name": "Microsoft",
                "enabled": azure.is_configured,
            },
            {
                "id": "email",
                "name": "Email",
                "enabled": True,  # Always enabled
            },
        ]
    }
