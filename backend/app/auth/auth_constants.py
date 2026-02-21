# Layer: L4 — Domain Engine
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Canonical JWT claim constants and auth deny reason codes
# Callers: auth_provider, gateway, identity API
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
# capability_id: CAP-006

"""
Auth Constants — Canonical JWT Claims and Deny Reason Codes

Provides:
1. JWT claim field names (locked per V1 design).
2. AuthDenyReason enum for deterministic troubleshooting.

INVARIANTS:
- Claim constants are string literals — no runtime derivation.
- Deny reasons map 1:1 to structured log/metric dimensions.
- External HTTP responses may veil these via veil_policy; internal
  logs/metrics/audit MUST preserve the true deny reason.
"""

from __future__ import annotations

from enum import Enum


# =============================================================================
# Canonical JWT Claim Constants (V1 — Locked)
# =============================================================================

class JWTClaim:
    """
    Canonical JWT claim field names for HOC Identity tokens.

    These match the V1 design lock — all 9 are mandatory in self-issued tokens.
    Clerk tokens use a different claim layout; the ClerkHumanAuthProvider
    maps Clerk claims to the canonical HumanPrincipal contract.
    """

    ISS = "iss"      # Issuer (e.g. "https://auth.agenticverz.com")
    AUD = "aud"      # Audience (e.g. "hoc_identity")
    SUB = "sub"      # Subject — user ID
    TID = "tid"      # Active tenant ID
    SID = "sid"      # Session ID (revocation key)
    TIER = "tier"    # Access tier (RBAC gate hint)
    IAT = "iat"      # Issued at (unix timestamp)
    EXP = "exp"      # Expires at (unix timestamp)
    JTI = "jti"      # JWT ID (uniqueness / replay prevention)

    # Optional claims
    EMAIL = "email"
    ROLES = "roles"          # Role hints (not authoritative; RBAC backend decides)
    CAPS = "caps"            # Capability snapshot (informational only)
    TENANT_SLUG = "tenant_slug"  # Display name only

    # All mandatory claim names as a frozenset for validation
    MANDATORY: frozenset[str] = frozenset({ISS, AUD, SUB, TID, SID, TIER, IAT, EXP, JTI})


# =============================================================================
# Auth Deny Reason Codes
# =============================================================================

class AuthDenyReason(str, Enum):
    """
    Internal reason codes for authentication/authorization denial.

    Used in structured logs, metrics, and audit events.
    External HTTP responses may be veiled (e.g. 404 via veil_policy);
    internal systems MUST preserve the true deny reason.
    """

    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID_SIGNATURE = "TOKEN_INVALID_SIGNATURE"
    TOKEN_MALFORMED = "TOKEN_MALFORMED"
    TOKEN_MISSING_CLAIMS = "TOKEN_MISSING_CLAIMS"
    ISSUER_UNTRUSTED = "ISSUER_UNTRUSTED"
    SESSION_REVOKED = "SESSION_REVOKED"
    TENANT_MISSING = "TENANT_MISSING"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    TIER_INSUFFICIENT = "TIER_INSUFFICIENT"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    ONBOARDING_INCOMPLETE = "ONBOARDING_INCOMPLETE"
    MIXED_AUTH = "MIXED_AUTH"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# =============================================================================
# Auth Provider Identifiers
# =============================================================================

class AuthProviderType(str, Enum):
    """Identifies which auth provider issued/verified the credential."""

    CLERK = "clerk"
    HOC_IDENTITY = "hoc_identity"


# =============================================================================
# HOC Identity Issuer (V1 — Locked)
# =============================================================================

HOC_IDENTITY_ISSUER = "https://auth.agenticverz.com"
HOC_IDENTITY_AUDIENCE = "hoc_identity"
