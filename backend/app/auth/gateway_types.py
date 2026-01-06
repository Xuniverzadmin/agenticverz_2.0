# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Gateway authentication result types and error definitions
# Callers: AuthGateway, gateway_middleware
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Gateway Authentication Types

This module defines result types and error classes for the Auth Gateway.

GatewayResult is a union type representing the outcome of gateway authentication:
- Success → HumanAuthContext or MachineCapabilityContext
- Failure → GatewayAuthError

INVARIANTS:
- Every gateway call returns exactly one GatewayResult
- Errors have specific codes for programmatic handling
- Error messages are safe to return to clients
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from .contexts import GatewayContext, HumanAuthContext, MachineCapabilityContext


class GatewayErrorCode(str, Enum):
    """
    Error codes for gateway authentication failures.

    These codes enable programmatic error handling and
    consistent audit logging.
    """

    # Header errors
    MISSING_AUTH = "missing_auth"  # No auth headers present
    MIXED_AUTH = "mixed_auth"  # Both JWT and API Key present (HARD FAIL)
    MALFORMED_HEADER = "malformed_header"  # Header format invalid

    # JWT errors
    JWT_EXPIRED = "jwt_expired"  # Token expired
    JWT_INVALID = "jwt_invalid"  # Token signature/format invalid
    JWT_CLAIMS_INVALID = "jwt_claims_invalid"  # Required claims missing

    # Session errors
    SESSION_REVOKED = "session_revoked"  # Session has been revoked

    # API Key errors
    API_KEY_INVALID = "api_key_invalid"  # Key not found or invalid
    API_KEY_EXPIRED = "api_key_expired"  # Key has expired
    API_KEY_REVOKED = "api_key_revoked"  # Key has been revoked
    API_KEY_SCOPE_DENIED = "api_key_scope_denied"  # Key lacks required scope

    # Rate limiting
    RATE_LIMITED = "rate_limited"  # Too many requests

    # Plane errors
    PLANE_MISMATCH = "plane_mismatch"  # Human on machine-only route or vice versa
    WORKER_JWT_FORBIDDEN = "worker_jwt_forbidden"  # Worker path using JWT

    # Server errors
    PROVIDER_UNAVAILABLE = "provider_unavailable"  # Auth provider down
    INTERNAL_ERROR = "internal_error"  # Unexpected error


@dataclass(frozen=True)
class GatewayAuthError:
    """
    Authentication error from the gateway.

    Contains all information needed for:
    - HTTP response (code, message)
    - Audit logging (error_code, details)
    - Programmatic handling (error_code)
    """

    error_code: GatewayErrorCode
    message: str  # Safe to return to client
    http_status: int  # HTTP status code to return
    details: Optional[str] = None  # Internal details (for logging only)

    def __repr__(self) -> str:
        return f"GatewayAuthError({self.error_code.value}: {self.message})"


# Common error factory functions
def error_missing_auth() -> GatewayAuthError:
    """No authentication headers present."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.MISSING_AUTH,
        message="Authentication required",
        http_status=401,
    )


def error_mixed_auth() -> GatewayAuthError:
    """Both JWT and API Key headers present - HARD FAIL."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.MIXED_AUTH,
        message="Cannot use both JWT and API Key authentication",
        http_status=400,
        details="Mutual exclusivity violated: Authorization header and X-AOS-Key both present",
    )


def error_jwt_expired() -> GatewayAuthError:
    """JWT token has expired."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.JWT_EXPIRED,
        message="Token has expired",
        http_status=401,
    )


def error_jwt_invalid(detail: str = "") -> GatewayAuthError:
    """JWT token is invalid."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.JWT_INVALID,
        message="Invalid token",
        http_status=401,
        details=detail,
    )


def error_session_revoked() -> GatewayAuthError:
    """Session has been revoked."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.SESSION_REVOKED,
        message="Session has been revoked",
        http_status=401,
    )


def error_api_key_invalid() -> GatewayAuthError:
    """API key is invalid."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.API_KEY_INVALID,
        message="Invalid API key",
        http_status=401,
    )


def error_api_key_revoked() -> GatewayAuthError:
    """API key has been revoked."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.API_KEY_REVOKED,
        message="API key has been revoked",
        http_status=401,
    )


def error_rate_limited(retry_after: int = 60) -> GatewayAuthError:
    """Rate limit exceeded."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.RATE_LIMITED,
        message=f"Rate limit exceeded. Retry after {retry_after} seconds",
        http_status=429,
        details=f"retry_after={retry_after}",
    )


def error_plane_mismatch(expected: str, actual: str) -> GatewayAuthError:
    """Authentication plane doesn't match route requirements."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.PLANE_MISMATCH,
        message=f"This endpoint requires {expected} authentication",
        http_status=403,
        details=f"expected={expected}, actual={actual}",
    )


def error_worker_jwt_forbidden() -> GatewayAuthError:
    """Worker endpoint cannot use JWT authentication."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.WORKER_JWT_FORBIDDEN,
        message="Worker endpoints require API key authentication",
        http_status=403,
        details="JWT auth forbidden on worker paths",
    )


def error_provider_unavailable(provider: str) -> GatewayAuthError:
    """Auth provider is unavailable."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.PROVIDER_UNAVAILABLE,
        message="Authentication service temporarily unavailable",
        http_status=503,
        details=f"provider={provider}",
    )


def error_internal(detail: str = "") -> GatewayAuthError:
    """Internal error during authentication."""
    return GatewayAuthError(
        error_code=GatewayErrorCode.INTERNAL_ERROR,
        message="Internal authentication error",
        http_status=500,
        details=detail,
    )


# Result type: either a context or an error
GatewayResult = Union[GatewayContext, GatewayAuthError]


def is_success(result: GatewayResult) -> bool:
    """Check if gateway result is successful (context, not error)."""
    return isinstance(result, (HumanAuthContext, MachineCapabilityContext))


def is_error(result: GatewayResult) -> bool:
    """Check if gateway result is an error."""
    return isinstance(result, GatewayAuthError)


def unwrap_context(result: GatewayResult) -> GatewayContext:
    """
    Extract context from result, raising if error.

    Use only after checking is_success().
    """
    if isinstance(result, GatewayAuthError):
        raise ValueError(f"Cannot unwrap error: {result}")
    return result


def unwrap_error(result: GatewayResult) -> GatewayAuthError:
    """
    Extract error from result, raising if success.

    Use only after checking is_error().
    """
    if not isinstance(result, GatewayAuthError):
        raise ValueError(f"Cannot unwrap success: {result}")
    return result
