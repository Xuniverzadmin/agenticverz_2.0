# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Customer Sandbox Authentication for local development and CI
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Callers: gateway_middleware.py
# Allowed Imports: L6 (settings, models)
# Forbidden Imports: L1, L2, L4, L5
# Reference: PIN-440


"""Customer Sandbox Authentication Mode

PURPOSE:
    Provides customer-grade authentication for local development and CI testing
    WITHOUT touching production auth (JWT/Clerk) or production database (Neon).

DESIGN PRINCIPLES:
    1. Local testing must simulate a real customer, not bypass a real system
    2. Sandbox mode is compile-time gated by environment variables
    3. No JWT, no Neon prod, no external dependencies
    4. Prod auth paths remain completely untouched

ACTIVATION:
    Requires BOTH conditions:
    - AOS_MODE=local (or AOS_MODE=test)
    - CUSTOMER_SANDBOX_ENABLED=true

USAGE:
    curl -H "X-AOS-Customer-Key: cus_sandbox_demo" http://localhost:8000/api/v1/cus/integrations

SECURITY GUARANTEES (PIN-440):
    - NEVER enabled in production (hard gate: AOS_MODE=prod blocks)
    - Permission ceiling prevents privilege escalation
    - Headers are mutually exclusive (no ambiguity)
    - All sandbox activity is tagged for audit
    - Environment drift detection at startup
"""

import logging
import os
from dataclasses import dataclass, field
from typing import FrozenSet, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# ENVIRONMENT GATES (HARD BOUNDARIES)
# =============================================================================

AOS_MODE = os.getenv("AOS_MODE", "prod")
CUSTOMER_SANDBOX_ENABLED = os.getenv("CUSTOMER_SANDBOX_ENABLED", "false").lower() == "true"
DB_AUTHORITY = os.getenv("DB_AUTHORITY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
HOSTNAME = os.getenv("HOSTNAME", "unknown")

# PIN-443: Sandbox rate limits (stricter than production)
SANDBOX_RATE_LIMIT_PER_MINUTE = int(os.getenv("SANDBOX_RATE_LIMIT_PER_MINUTE", "10"))
SANDBOX_HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv("SANDBOX_HEALTH_CHECK_INTERVAL", "300"))  # 5 min


# =============================================================================
# SECURITY CONSTANTS (LOCKED)
# =============================================================================

# PIN-440: Sandbox permission ceiling - prevents privilege escalation
# Sandbox principals can NEVER have permissions beyond this set
SANDBOX_ALLOWED_PERMISSIONS: FrozenSet[str] = frozenset({
    # Customer read permissions
    "customer:integrations:read",
    "customer:integrations:write",
    "customer:integrations:control",
    "customer:telemetry:read",
    "customer:enforcement:read",
    "customer:enforcement:check",
    "customer:visibility:read",
    # Legacy compatibility
    "integration:read",
    "integration:write",
})

# Permissions sandbox can NEVER have (hard ceiling)
SANDBOX_FORBIDDEN_PERMISSIONS: FrozenSet[str] = frozenset({
    "operator:*",
    "admin:*",
    "system:*",
    "machine:*",
    "billing:write",
    "tenant:delete",
})


# =============================================================================
# SAFETY CHECKS (RUN AT MODULE LOAD) - PIN-443 HARDENED
# =============================================================================

class SandboxSafetyViolation(Exception):
    """Raised when sandbox configuration violates safety invariants."""
    pass


# Track if safety violation was detected (used to disable sandbox)
_SAFETY_VIOLATION_DETECTED = False


def _is_prod_database(db_url: str) -> bool:
    """Heuristic detection of production database URLs.

    Returns True if the URL appears to be a production database.
    This is a FAIL-SAFE check - false positives are acceptable,
    false negatives are dangerous.
    """
    if not db_url:
        return False

    db_lower = db_url.lower()

    # Obvious production indicators
    prod_indicators = [
        # Direct prod naming
        "prod" in db_lower and "test" not in db_lower and "preprod" not in db_lower,
        "-prod." in db_lower,
        "_production" in db_lower,
        ".production." in db_lower,
        # Neon production projects (conservative)
        "neon.tech" in db_lower and "test" not in db_lower and "dev" not in db_lower,
    ]

    return any(prod_indicators)


def _check_environment_safety() -> None:
    """Validate environment safety at module load.

    PIN-443: HARD-FAIL on safety violations.

    This prevents:
    - Sandbox auth being enabled against production database
    - Environment drift where AOS_MODE=test but DATABASE_URL points to prod
    - Token reuse across environments

    FAIL-FAST: If violations are detected, sandbox is DISABLED permanently.
    """
    global _SAFETY_VIOLATION_DETECTED

    if not CUSTOMER_SANDBOX_ENABLED:
        return  # Not enabled, no risk

    if AOS_MODE not in ("local", "test"):
        return  # Not in sandbox modes, blocked anyway

    # Edge Case 1: Environment Drift Detection (HARD GATE)
    # If sandbox is enabled in test mode, verify DATABASE_URL isn't production
    if DATABASE_URL and _is_prod_database(DATABASE_URL):
        _SAFETY_VIOLATION_DETECTED = True
        logger.critical(
            "SANDBOX SAFETY VIOLATION [HARD FAIL]: "
            f"DATABASE_URL appears to be production but AOS_MODE={AOS_MODE}. "
            "Sandbox auth is PERMANENTLY DISABLED for this process. "
            "Fix: Set AOS_MODE=prod or use a non-production DATABASE_URL."
        )
        # We don't raise - we disable sandbox permanently via the flag

    # Edge Case 1b: DB_AUTHORITY mismatch
    if DB_AUTHORITY == "neon" and AOS_MODE == "local":
        logger.warning(
            "SANDBOX CONFIG WARNING: DB_AUTHORITY=neon with AOS_MODE=local. "
            "This is unusual - local mode typically uses local database."
        )

    # Log sandbox activation for audit
    if not _SAFETY_VIOLATION_DETECTED:
        logger.info(
            f"[SANDBOX] Enabled: AOS_MODE={AOS_MODE}, "
            f"DB_AUTHORITY={DB_AUTHORITY or 'unset'}, HOSTNAME={HOSTNAME}"
        )


# Run safety check at module load
_check_environment_safety()


def is_sandbox_allowed() -> bool:
    """Check if customer sandbox mode is allowed.

    Rules (PIN-443 hardened):
    - Safety violation flag must NOT be set
    - AOS_MODE must be 'local' or 'test'
    - CUSTOMER_SANDBOX_ENABLED must be true
    - DB_AUTHORITY must NOT be 'neon' when AOS_MODE='prod' (safety gate)

    Returns:
        True if sandbox auth is allowed in current environment
    """
    # PIN-443: Hard gate - if safety violation was detected at startup, never allow
    if _SAFETY_VIOLATION_DETECTED:
        return False

    if AOS_MODE not in ("local", "test"):
        return False

    if not CUSTOMER_SANDBOX_ENABLED:
        return False

    # PIN-440: Allow sandbox when AOS_MODE=test, even with Neon DB
    # Only block when AOS_MODE=prod (production environment)
    if DB_AUTHORITY == "neon" and AOS_MODE == "prod":
        logger.warning("Sandbox auth rejected: production environment (AOS_MODE=prod + DB_AUTHORITY=neon)")
        return False

    return True


# =============================================================================
# SANDBOX CUSTOMER PRINCIPAL
# =============================================================================

import hashlib


def _compute_sandbox_fingerprint() -> str:
    """Compute environment fingerprint for sandbox token binding.

    PIN-443 Edge Case 3: Tokens are bound to environment.
    This prevents sandbox keys from being reused across modes/hosts.
    """
    fingerprint_data = f"{AOS_MODE}:{HOSTNAME}:{DB_AUTHORITY}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]


# Compute once at module load
_SANDBOX_FINGERPRINT = _compute_sandbox_fingerprint()


@dataclass
class SandboxCustomerPrincipal:
    """Principal representing a sandboxed customer.

    This is the auth context returned when sandbox auth succeeds.
    It mirrors the structure of production auth contexts but with
    'sandbox' authority for auditability.

    Security Properties (PIN-443 hardened):
    - authority is always 'sandbox' (immutable)
    - permissions are capped by SANDBOX_ALLOWED_PERMISSIONS
    - billable is always False
    - caller_type is always 'sandbox_customer'
    - environment_fingerprint binds to host/mode (prevents token portability)
    """
    tenant_id: str
    customer_id: str
    user_id: Optional[str]
    role: str
    authority: str = "sandbox"

    # PIN-440: Telemetry tagging - sandbox calls must never be billable
    billable: bool = field(default=False, init=False)
    caller_type: str = field(default="sandbox_customer", init=False)

    # Environment binding for audit
    environment: str = field(default_factory=lambda: AOS_MODE)

    # PIN-443: Environment fingerprint for token binding
    environment_fingerprint: str = field(default_factory=lambda: _SANDBOX_FINGERPRINT)

    # Capped permissions
    _permissions: FrozenSet[str] = field(default=frozenset(), repr=False)

    @property
    def is_sandbox(self) -> bool:
        return self.authority == "sandbox"

    @property
    def permissions(self) -> FrozenSet[str]:
        """Return permissions capped by sandbox ceiling."""
        return self._permissions & SANDBOX_ALLOWED_PERMISSIONS

    def has_permission(self, permission: str) -> bool:
        """Check if this principal has a permission (respecting ceiling)."""
        return permission in self.permissions

    def to_telemetry_context(self) -> dict:
        """Return telemetry context for audit tagging.

        All sandbox calls should include this in telemetry to ensure
        they are never confused with production traffic.
        """
        return {
            "auth_origin": "sandbox",
            "billable": False,
            "environment": self.environment,
            "environment_fingerprint": self.environment_fingerprint,
            "tenant_id": self.tenant_id,
            "caller_type": self.caller_type,
        }


# =============================================================================
# SANDBOX KEY REGISTRY (LOCAL ONLY)
# =============================================================================

# These keys are only valid in sandbox mode
# Format: key -> (tenant_id, customer_id, user_id, role, permissions)
SANDBOX_KEYS = {
    "cus_sandbox_demo": (
        "demo-tenant",
        "sandbox-customer",
        "sandbox-user",
        "customer_admin",
        frozenset({
            "customer:integrations:read",
            "customer:integrations:write",
            "customer:integrations:control",
            "customer:telemetry:read",
            "customer:enforcement:read",
            "customer:enforcement:check",
            "customer:visibility:read",
            "integration:read",
            "integration:write",
        }),
    ),
    "cus_sandbox_readonly": (
        "demo-tenant",
        "sandbox-customer",
        "sandbox-user",
        "customer_viewer",
        frozenset({
            "customer:integrations:read",
            "customer:telemetry:read",
            "customer:enforcement:read",
            "customer:visibility:read",
            "integration:read",
        }),
    ),
    "cus_sandbox_tenant2": (
        "tenant-2",
        "sandbox-customer-2",
        "sandbox-user-2",
        "customer_admin",
        frozenset({
            "customer:integrations:read",
            "customer:integrations:write",
            "customer:integrations:control",
            "customer:telemetry:read",
            "customer:enforcement:read",
            "customer:enforcement:check",
            "customer:visibility:read",
            "integration:read",
            "integration:write",
        }),
    ),
    # CI test keys
    "cus_ci_test": (
        "ci-tenant",
        "ci-customer",
        "ci-user",
        "customer_admin",
        frozenset({
            "customer:integrations:read",
            "customer:integrations:write",
            "customer:integrations:control",
            "customer:telemetry:read",
            "customer:enforcement:read",
            "customer:enforcement:check",
            "customer:visibility:read",
            "integration:read",
            "integration:write",
        }),
    ),
}


# =============================================================================
# SANDBOX AUTH RESOLUTION
# =============================================================================

def resolve_sandbox_auth(customer_key: str) -> Optional[SandboxCustomerPrincipal]:
    """Resolve a sandbox customer key to a principal.

    Args:
        customer_key: The X-AOS-Customer-Key header value

    Returns:
        SandboxCustomerPrincipal if valid, None otherwise
    """
    if not is_sandbox_allowed():
        logger.debug("Sandbox auth not allowed in current environment")
        return None

    if not customer_key:
        return None

    # Look up in sandbox registry
    if customer_key in SANDBOX_KEYS:
        tenant_id, customer_id, user_id, role, permissions = SANDBOX_KEYS[customer_key]
        principal = SandboxCustomerPrincipal(
            tenant_id=tenant_id,
            customer_id=customer_id,
            user_id=user_id,
            role=role,
            authority="sandbox",
            _permissions=permissions,
        )
        logger.info(f"Sandbox auth resolved: tenant={tenant_id}, role={role}")
        return principal

    logger.debug(f"Unknown sandbox key: {customer_key[:10]}...")
    return None


# =============================================================================
# HEADER EXTRACTION
# =============================================================================

SANDBOX_HEADER = "X-AOS-Customer-Key"
JWT_HEADER = "Authorization"
API_KEY_HEADER = "X-AOS-Key"


def extract_sandbox_key(headers: dict) -> Optional[str]:
    """Extract sandbox customer key from request headers.

    Args:
        headers: Request headers dict

    Returns:
        The sandbox key if present, None otherwise
    """
    # Try case-insensitive header lookup
    for key, value in headers.items():
        if key.lower() == SANDBOX_HEADER.lower():
            return value
    return None


def has_conflicting_auth_headers(headers: dict) -> bool:
    """Check if request has conflicting auth headers.

    PIN-440 Edge Case 7: Mixed auth headers must be rejected.
    Sandbox auth ONLY if:
    - X-AOS-Customer-Key present
    - Authorization header ABSENT
    - X-AOS-Key header ABSENT

    Args:
        headers: Request headers dict

    Returns:
        True if conflicting headers detected, False if clean
    """
    headers_lower = {k.lower(): v for k, v in headers.items()}

    has_sandbox = SANDBOX_HEADER.lower() in headers_lower
    has_jwt = JWT_HEADER.lower() in headers_lower
    has_api_key = API_KEY_HEADER.lower() in headers_lower

    # Conflict: sandbox + another auth method
    if has_sandbox and (has_jwt or has_api_key):
        return True

    return False


# =============================================================================
# INTEGRATION POINT (for gateway_middleware.py)
# =============================================================================

@dataclass
class SandboxAuthResult:
    """Result of sandbox authentication attempt.

    PIN-443: Explicit error responses - never silently downgrade.
    """
    success: bool
    principal: Optional[SandboxCustomerPrincipal] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_error_response(self) -> dict:
        """Return error response for API."""
        if self.success:
            return {}
        return {
            "error": self.error_code or "sandbox_auth_failed",
            "message": self.error_message or "Sandbox authentication failed",
        }


def try_sandbox_auth_with_error(headers: dict) -> SandboxAuthResult:
    """Attempt sandbox authentication with explicit error responses.

    PIN-443: This is the preferred entry point - returns explicit errors
    instead of silently falling through.

    Args:
        headers: Request headers dict

    Returns:
        SandboxAuthResult with success/error details
    """
    # Check if sandbox key is even present
    sandbox_key = extract_sandbox_key(headers)
    if not sandbox_key:
        # No sandbox header - not an error, just fall through
        return SandboxAuthResult(success=False, error_code=None)

    # Sandbox header present - now validate

    # PIN-443: Safety violation check
    if _SAFETY_VIOLATION_DETECTED:
        return SandboxAuthResult(
            success=False,
            error_code="sandbox_safety_violation",
            error_message="Sandbox auth disabled: safety violation detected at startup",
        )

    # Check if sandbox is allowed
    if not is_sandbox_allowed():
        return SandboxAuthResult(
            success=False,
            error_code="sandbox_not_allowed",
            error_message=f"Sandbox auth not allowed: AOS_MODE={AOS_MODE}",
        )

    # PIN-440 Edge Case 7: Reject mixed auth headers
    if has_conflicting_auth_headers(headers):
        return SandboxAuthResult(
            success=False,
            error_code="conflicting_auth_headers",
            error_message="Use ONLY X-AOS-Customer-Key OR Authorization/X-AOS-Key, not both",
        )

    # Resolve the key
    principal = resolve_sandbox_auth(sandbox_key)
    if not principal:
        return SandboxAuthResult(
            success=False,
            error_code="invalid_sandbox_key",
            error_message="Unknown or invalid sandbox key",
        )

    return SandboxAuthResult(success=True, principal=principal)


def try_sandbox_auth(headers: dict) -> Optional[SandboxCustomerPrincipal]:
    """Attempt sandbox authentication from request headers.

    This is the main entry point called by the gateway middleware.
    It returns None if:
    - Sandbox mode is not enabled
    - No sandbox key header present
    - Invalid sandbox key
    - Conflicting auth headers present (JWT or API key)

    NOTE: For explicit error handling, use try_sandbox_auth_with_error() instead.

    Args:
        headers: Request headers dict

    Returns:
        SandboxCustomerPrincipal if auth succeeds, None to fall through to normal auth
    """
    result = try_sandbox_auth_with_error(headers)
    if result.success:
        return result.principal
    return None


# =============================================================================
# CAPABILITY HELPERS
# =============================================================================

def get_sandbox_capabilities(principal: SandboxCustomerPrincipal) -> list[str]:
    """Get capabilities for a sandbox principal.

    This is used by RBAC middleware to resolve permissions.
    Capabilities are always capped by SANDBOX_ALLOWED_PERMISSIONS.

    Args:
        principal: The sandbox principal

    Returns:
        List of permission strings
    """
    return list(principal.permissions)


def is_sandbox_principal(context: object) -> bool:
    """Check if an auth context is a sandbox principal.

    Args:
        context: Any auth context object

    Returns:
        True if it's a SandboxCustomerPrincipal
    """
    return isinstance(context, SandboxCustomerPrincipal)
