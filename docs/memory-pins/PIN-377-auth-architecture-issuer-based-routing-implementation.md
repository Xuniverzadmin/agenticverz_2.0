# PIN-377: Auth Architecture: Issuer-Based Routing Implementation

**Status:** ✅ COMPLETE
**Created:** 2026-01-09
**Category:** Auth / Architecture
**Milestone:** Auth Gateway Refactor

---

## Summary

Implemented production-grade issuer-based JWT routing, added AuthSource.CONSOLE, fixed RBAC path mappings, created governance artifacts

---

## Details

## Overview

Complete implementation of issuer-based JWT routing for the authentication gateway, replacing the insecure algorithm-based routing approach. This work establishes the canonical auth architecture for AgenticVerz.

## Problem Statement

The original auth gateway routed tokens based on the `alg` header, which is attacker-controlled. A malicious actor could craft a token with `alg: HS256` and potentially bypass Clerk RS256 verification.

## Solution: Issuer-Based Routing

### Core Principle
```
ROUTING IS BASED ON `iss` CLAIM — NEVER ON `alg` HEADER
```

The `alg` header is attacker-controlled metadata. The `iss` claim declares token origin and determines which authenticator handles verification.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TokenClassifier                          │
│  • Parse JWT without verification                           │
│  • Extract `iss` claim                                      │
│  • Return TokenInfo(issuer, raw_token)                      │
│  • NEVER inspect `alg` header                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Console Auth  │  │  Clerk Auth   │  │    Reject     │
│ (HS256)       │  │  (RS256)      │  │               │
│               │  │               │  │               │
│ iss =         │  │ iss in        │  │ Unknown       │
│ agenticverz-  │  │ CLERK_ISSUERS │  │ issuer        │
│ console       │  │               │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

## Changes Made

### 1. Token Issuance (`backend/app/api/onboarding.py`)
- Added `iss: "agenticverz-console"` claim to all issued tokens
- Renamed `JWT_SECRET` to `CONSOLE_JWT_SECRET` (no fallback chains)
- Hard fail if secret not configured

### 2. Auth Gateway (`backend/app/auth/gateway.py`)
- Implemented `TokenClassifier` for issuer extraction
- Issuer-based routing via `_route_by_issuer()`
- Console authenticator for `iss = "agenticverz-console"`
- Clerk authenticator for `iss in CLERK_ISSUERS`
- Grace period for legacy tokens without `iss`

### 3. Gateway Metrics (`backend/app/auth/gateway_metrics.py`) - NEW
- `auth_tokens_verified_total{source}` - successful verifications
- `auth_tokens_rejected_total{source,reason}` - rejections
- `auth_console_missing_iss_total` - grace period usage

### 4. Auth Contexts (`backend/app/auth/contexts.py`)
- Added `AuthSource.CONSOLE` enum value

### 5. Actor Model (`backend/app/auth/actor.py`)
- Added `IdentitySource.CONSOLE` enum value

### 6. Authority Mapping (`backend/app/auth/authority.py`)
- Fixed `AuthSource → IdentitySource` mapping
- `console → CONSOLE`, `clerk → CLERK`, `stub → DEV`

### 7. RBAC Middleware (`backend/app/auth/rbac_middleware.py`)
- Removed `/api/v1/incidents/` and `/ops/` from PUBLIC_PATHS
- These routes now return PolicyObjects for shadow audit
- Fixed 10 failing tests

### 8. Governance Artifacts
- Created `docs/architecture/auth/AUTH_ARCHITECTURE_BASELINE.md`
- Added `BL-AUTH-002` Auth Architecture Lock to `CLAUDE.md`

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `CONSOLE_JWT_SECRET` | Yes | Secret for HS256 console tokens |
| `CLERK_ISSUERS` | No | Comma-separated trusted Clerk issuers |
| `AUTH_CONSOLE_ENABLED` | No | Kill switch (default: true) |
| `AUTH_CONSOLE_ALLOW_MISSING_ISS` | No | Grace period (default: true) |

## Token Contracts

### Console Token
```json
{
  "iss": "agenticverz-console",
  "sub": "<user_id>",
  "exp": <unix_timestamp>,
  "iat": <unix_timestamp>,
  "tenant_id": "<optional>"
}
```

### Clerk Token
```json
{
  "iss": "<clerk_issuer_url>",
  "sub": "<user_id>",
  "exp": <unix_timestamp>
}
```

## Deprecation Plan

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | ACTIVE | Grace period, legacy tokens accepted |
| Phase 1 | PENDING | Reject tokens without `iss` |
| Phase 2 | PENDING | Disable console auth in staging |
| Phase 3 | PENDING | Disable console auth in production |
| Phase 4 | PENDING | Remove HS256 code |

## Test Results

| Test Suite | Result |
|------------|--------|
| `tests/auth/` | 359 passed |
| `tests/test_category2_auth_boundary.py` | 12 passed |
| `tests/authz/test_authority_exhaustion.py` | 905 passed |

## Manual Verification

| Test | Result |
|------|--------|
| Console token with iss | ✅ HTTP 200 |
| Legacy token (no iss) | ✅ HTTP 200 (grace period) |
| Unknown issuer | ✅ HTTP 401 (rejected) |

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/auth/gateway.py` | Issuer-based routing |
| `backend/app/auth/gateway_metrics.py` | Prometheus metrics |
| `backend/app/auth/contexts.py` | AuthSource enum |
| `backend/app/auth/actor.py` | IdentitySource enum |
| `backend/app/auth/authority.py` | Source mapping |
| `docs/architecture/auth/AUTH_ARCHITECTURE_BASELINE.md` | Canonical spec |

## Security Invariants

1. **Routing must be issuer-based** - Never route by `alg` header
2. **Each trust domain has one verifier** - Console and Clerk are separate
3. **No secret fallback chains** - Single source for each secret
4. **Feature-flagged deprecation** - Controlled migration path
5. **Metrics for observability** - Track usage and grace period

## References

- PIN-271: RBAC Authority Separation
- PIN-307: CAP-006 Auth Gateway
- PIN-376: Auth Pattern Enforcement

---

## Commits

- `0fc374c5`

---

## Related PINs

- [PIN-376](PIN-376-.md)
- [PIN-271](PIN-271-.md)
- [PIN-307](PIN-307-.md)
