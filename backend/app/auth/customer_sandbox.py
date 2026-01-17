# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Customer Sandbox Authentication for local development and CI
# Callers: gateway_middleware.py
# Allowed Imports: L6 (settings, models)
# Forbidden Imports: L1, L2, L4, L5
# Reference: PIN-439

"""Customer Sandbox Authentication Mode

PURPOSE:
    Provides customer-grade authentication for local development and CI testing
    WITHOUT touching production auth (JWT/Clerk) or production database (Neon).

DESIGN PRINCIPLES:
    1. Local testing must simulate a real customer, not bypass a real system
    2. Sandbox mode is compile-time gated by environment variables
    3. No JWT, no Neon, no external dependencies
    4. Prod auth paths remain completely untouched

ACTIVATION:
    Requires BOTH conditions:
    - AOS_MODE=local (or AOS_MODE=test)
    - CUSTOMER_SANDBOX_ENABLED=true

USAGE:
    curl -H "X-AOS-Customer-Key: cus_sandbox_demo" http://localhost:8000/api/v1/cus/integrations

SECURITY:
    - NEVER enabled in production (hard gate)
    - NEVER uses Neon database
    - Authority is "sandbox" (auditable)
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# =============================================================================
# ENVIRONMENT GATES (HARD BOUNDARIES)
# =============================================================================

AOS_MODE = os.getenv("AOS_MODE", "prod")
CUSTOMER_SANDBOX_ENABLED = os.getenv("CUSTOMER_SANDBOX_ENABLED", "false").lower() == "true"
DB_AUTHORITY = os.getenv("DB_AUTHORITY", "")


def is_sandbox_allowed() -> bool:
    """Check if customer sandbox mode is allowed.

    Rules:
    - AOS_MODE must be 'local' or 'test'
    - CUSTOMER_SANDBOX_ENABLED must be true
    - DB_AUTHORITY must NOT be 'neon' (safety gate)
    """
    if AOS_MODE not in ("local", "test"):
        return False

    if not CUSTOMER_SANDBOX_ENABLED:
        return False

    # Extra safety: never allow sandbox with Neon
    if DB_AUTHORITY == "neon":
        logger.warning("Sandbox auth rejected: DB_AUTHORITY=neon is not allowed in sandbox mode")
        return False

    return True


# =============================================================================
# SANDBOX CUSTOMER PRINCIPAL
# =============================================================================

@dataclass
class SandboxCustomerPrincipal:
    """Principal representing a sandboxed customer.

    This is the auth context returned when sandbox auth succeeds.
    It mirrors the structure of production auth contexts but with
    'sandbox' authority for auditability.
    """
    tenant_id: str
    customer_id: str
    user_id: Optional[str]
    role: str
    authority: str = "sandbox"

    @property
    def is_sandbox(self) -> bool:
        return self.authority == "sandbox"


# =============================================================================
# SANDBOX KEY REGISTRY (LOCAL ONLY)
# =============================================================================

# These keys are only valid in sandbox mode
# Format: key -> (tenant_id, customer_id, user_id, role)
SANDBOX_KEYS = {
    "cus_sandbox_demo": ("demo-tenant", "sandbox-customer", "sandbox-user", "customer_admin"),
    "cus_sandbox_readonly": ("demo-tenant", "sandbox-customer", "sandbox-user", "customer_viewer"),
    "cus_sandbox_tenant2": ("tenant-2", "sandbox-customer-2", "sandbox-user-2", "customer_admin"),
    # CI test keys
    "cus_ci_test": ("ci-tenant", "ci-customer", "ci-user", "customer_admin"),
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
        tenant_id, customer_id, user_id, role = SANDBOX_KEYS[customer_key]
        principal = SandboxCustomerPrincipal(
            tenant_id=tenant_id,
            customer_id=customer_id,
            user_id=user_id,
            role=role,
            authority="sandbox",
        )
        logger.info(f"Sandbox auth resolved: tenant={tenant_id}, role={role}")
        return principal

    logger.debug(f"Unknown sandbox key: {customer_key[:10]}...")
    return None


# =============================================================================
# HEADER EXTRACTION
# =============================================================================

SANDBOX_HEADER = "X-AOS-Customer-Key"


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


# =============================================================================
# INTEGRATION POINT (for gateway_middleware.py)
# =============================================================================

def try_sandbox_auth(headers: dict) -> Optional[SandboxCustomerPrincipal]:
    """Attempt sandbox authentication from request headers.

    This is the main entry point called by the gateway middleware.
    It returns None if:
    - Sandbox mode is not enabled
    - No sandbox key header present
    - Invalid sandbox key

    Args:
        headers: Request headers dict

    Returns:
        SandboxCustomerPrincipal if auth succeeds, None to fall through to normal auth
    """
    if not is_sandbox_allowed():
        return None

    sandbox_key = extract_sandbox_key(headers)
    if not sandbox_key:
        return None

    return resolve_sandbox_auth(sandbox_key)
