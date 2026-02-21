# Layer: L2 — Product APIs (Schemas)
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Request/response schemas for HOC Identity API endpoints
# Callers: routes.py
# Allowed Imports: stdlib, pydantic
# Forbidden Imports: L4, L5, L6, ORM
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
HOC Identity API Schemas

Request/response models for /hoc/api/auth/* endpoints.
All fields follow the V1 design lock. Schemas are scaffold-level
with TODO markers where validation logic is deferred.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Register
# =============================================================================

class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: Optional[str] = None  # Optional: join existing tenant


class RegisterResponse(BaseModel):
    user_id: str
    session_id: str
    access_token: str
    refresh_token: str


# =============================================================================
# Login
# =============================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    user_id: str
    session_id: str
    access_token: str
    refresh_token: str


# =============================================================================
# Refresh
# =============================================================================

class RefreshResponse(BaseModel):
    access_token: str
    session_id: str


# =============================================================================
# Switch Tenant
# =============================================================================

class SwitchTenantRequest(BaseModel):
    tenant_id: str
    csrf_token: str  # Double-submit cookie CSRF


class SwitchTenantResponse(BaseModel):
    session_id: str
    access_token: str
    refresh_token: str


# =============================================================================
# Logout
# =============================================================================

class LogoutResponse(BaseModel):
    status: str = "ok"


# =============================================================================
# Me (Current Principal)
# =============================================================================

class MeResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    tenant_id: Optional[str] = None
    tier: Optional[str] = None
    roles: list[str] = []


# =============================================================================
# Password Reset
# =============================================================================

class PasswordResetRequestPayload(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PasswordResetRequestResponse(BaseModel):
    status: str = "sent"


class PasswordResetConfirmPayload(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetConfirmResponse(BaseModel):
    status: str = "ok"


# =============================================================================
# Error
# =============================================================================

class AuthErrorResponse(BaseModel):
    error: str
    message: str
