# Auth Architecture Baseline

**Status:** LOCKED
**Version:** 1.0.0
**Effective:** 2026-01-09
**Owner:** Founder
**Last Modified By:** Claude (PIN-XXX)

---

## Document Purpose

This document is the **single source of truth** for the AgenticVerz authentication architecture. All authentication-related code changes must conform to this baseline.

**Modifications require explicit owner approval.**

---

## 1. Core Invariants (Non-Negotiable)

### 1.1 Routing Must Be Issuer-Based

```
ROUTING IS BASED ON `iss` CLAIM — NEVER ON `alg` HEADER
```

The `alg` header is attacker-controlled metadata. It must **never** influence routing decisions.

### 1.2 Each Trust Domain Has Exactly One Verifier

| Trust Domain | Issuer | Algorithm | Secret/Key | Authenticator |
|--------------|--------|-----------|------------|---------------|
| Console (Internal) | `agenticverz-console` | HS256 | `CONSOLE_JWT_SECRET` | `_authenticate_console()` |
| Clerk (External) | Values in `CLERK_ISSUERS` | RS256 | JWKS (public key) | `_authenticate_clerk()` |

No shared secrets. No shared semantics. No cross-domain verification.

### 1.3 Every JWT Must Declare Its Issuer

- Missing `iss` in production = invalid token
- Grace period allows missing `iss` (controlled by `AUTH_CONSOLE_ALLOW_MISSING_ISS`)
- Grace period is **temporary** — will be removed

### 1.4 Deprecation Is Enforced By Code

- Feature flags control behavior
- Metrics track usage
- Comments are not enforcement

---

## 2. Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                        AuthGateway                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   TokenClassifier                        │ │
│  │  ─────────────────────────────────────────────────────  │ │
│  │  • Parse JWT without verification                        │ │
│  │  • Extract `iss` claim                                   │ │
│  │  • Return TokenInfo(issuer, raw_token)                   │ │
│  │  • NEVER inspect `alg` header                            │ │
│  └──────────────────────────┬──────────────────────────────┘ │
│                             │                                 │
│              ┌──────────────┼──────────────┐                 │
│              │              │              │                 │
│              ▼              ▼              ▼                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │ Console Auth  │  │  Clerk Auth   │  │    Reject     │    │
│  │ (HS256)       │  │  (RS256)      │  │               │    │
│  │               │  │               │  │               │    │
│  │ iss =         │  │ iss in        │  │ Unknown       │    │
│  │ agenticverz-  │  │ CLERK_ISSUERS │  │ issuer        │    │
│  │ console       │  │               │  │               │    │
│  └───────┬───────┘  └───────┬───────┘  └───────────────┘    │
│          │                  │                                 │
│          ▼                  ▼                                 │
│  ┌───────────────┐  ┌───────────────┐                        │
│  │ HumanAuth     │  │ HumanAuth     │                        │
│  │ Context       │  │ Context       │                        │
│  │               │  │               │                        │
│  │ auth_source=  │  │ auth_source=  │                        │
│  │ CONSOLE       │  │ CLERK         │                        │
│  └───────────────┘  └───────────────┘                        │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. Token Contracts

### 3.1 Console Token Contract

**Issuer:** `agenticverz-console`
**Algorithm:** HS256 (symmetric)
**Secret:** `CONSOLE_JWT_SECRET` (environment variable)

**Required Claims:**
```json
{
  "iss": "agenticverz-console",
  "sub": "<user_id>",
  "exp": <unix_timestamp>,
  "iat": <unix_timestamp>
}
```

**Optional Claims:**
```json
{
  "tenant_id": "<org_id>",
  "email": "<user_email>",
  "name": "<display_name>",
  "sid": "<session_id>",
  "jti": "<token_id>"
}
```

**Verification Rules:**
- Algorithm must be HS256
- Signature verified with `CONSOLE_JWT_SECRET`
- `exp` must be in the future
- `sub` must be present
- `iss` must be `agenticverz-console` (or missing during grace period)

### 3.2 Clerk Token Contract

**Issuer:** Values configured in `CLERK_ISSUERS`
**Algorithm:** RS256 (asymmetric)
**Verification:** JWKS (public key from Clerk)

**Required Claims:**
```json
{
  "iss": "<clerk_issuer_url>",
  "sub": "<user_id>",
  "exp": <unix_timestamp>
}
```

**Verification Rules:**
- Algorithm must be RS256
- Signature verified via JWKS
- `iss` must exactly match a value in `CLERK_ISSUERS`
- `exp` must be in the future
- `sub` must be present

---

## 4. Configuration

### 4.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONSOLE_JWT_SECRET` | Yes | (none) | Secret for HS256 console token verification |
| `CLERK_ISSUERS` | No | (empty) | Comma-separated list of trusted Clerk issuer URLs |
| `AUTH_CONSOLE_ENABLED` | No | `true` | Kill switch for console authentication |
| `AUTH_CONSOLE_ALLOW_MISSING_ISS` | No | `true` | Grace period for legacy tokens without `iss` |
| `AUTH_STUB_ENABLED` | No | `true` | Enable stub tokens for development/CI |

### 4.2 Configuration Rules

1. **No fallback chains:** Each variable has one source. No `JWT_SECRET` → `CONSOLE_JWT_SECRET` → `AOS_JWT_SECRET` chains.

2. **Fail on missing secret:** If `CONSOLE_JWT_SECRET` is not set and console auth is enabled, startup must fail.

3. **Warn on empty CLERK_ISSUERS:** If `CLERK_ISSUERS` is empty, log a warning. Clerk auth will be effectively disabled.

---

## 5. Auth Sources and Identity Mapping

### 5.1 AuthSource Enum

```python
class AuthSource(str, Enum):
    CONSOLE = "console"  # Internal console HS256 JWT (transitional)
    CLERK = "clerk"      # Production Clerk RS256 JWT
    STUB = "stub"        # Development stub token
    API_KEY = "api_key"  # Machine API key
```

### 5.2 IdentitySource Enum

```python
class IdentitySource(str, Enum):
    CONSOLE = "console"  # Internal console HS256 JWT
    CLERK = "clerk"      # Production Clerk RS256 JWT
    OIDC = "oidc"        # Keycloak/generic OIDC
    INTERNAL = "internal"# Internal service-to-service
    SYSTEM = "system"    # CI, workers, automation
    DEV = "dev"          # Local development
```

### 5.3 Mapping Rules

| AuthSource | IdentitySource |
|------------|----------------|
| `console` | `CONSOLE` |
| `clerk` | `CLERK` |
| `stub` | `DEV` |
| (unknown) | `DEV` |

---

## 6. Metrics

### 6.1 Required Metrics

```
auth_tokens_verified_total{source="console|clerk|stub"}
auth_tokens_rejected_total{source="...", reason="..."}
auth_console_missing_iss_total
```

### 6.2 Metric Recording Rules

- Record `auth_tokens_verified_total` **only after successful verification**
- Record `auth_tokens_rejected_total` with specific reason codes
- Record `auth_console_missing_iss_total` for every grace-period acceptance

### 6.3 Rejection Reason Codes

| Reason | Description |
|--------|-------------|
| `malformed` | JWT could not be parsed |
| `expired` | Token has expired |
| `invalid_signature` | Signature verification failed |
| `missing_sub` | Missing subject claim |
| `untrusted_issuer` | Issuer not in trusted list |
| `issuer_mismatch` | Issuer doesn't match expected value |
| `disabled` | Auth method is disabled via feature flag |
| `not_configured` | Provider not configured |
| `revoked` | Session has been revoked |
| `library_missing` | Required library not installed |
| `secret_missing` | Required secret not configured |
| `internal_error` | Unexpected error |

---

## 7. Deprecation Plan

### Phase 0 — Current (Grace Period Active)

- `AUTH_CONSOLE_ENABLED=true`
- `AUTH_CONSOLE_ALLOW_MISSING_ISS=true`
- Old tokens (missing `iss`) accepted with warning
- Metrics track usage

### Phase 1 — Soft Deprecation

- `AUTH_CONSOLE_ALLOW_MISSING_ISS=false`
- Tokens without `iss` are rejected
- All console tokens must have `iss: agenticverz-console`

### Phase 2 — Staging Kill

- `AUTH_CONSOLE_ENABLED=false` in staging
- Validate Clerk-only paths work
- Monitor for breakage

### Phase 3 — Production Kill

- `AUTH_CONSOLE_ENABLED=false` in production
- Console authentication fully disabled
- HS256 code can be removed

### Phase 4 — Code Removal

- Remove console authenticator
- Remove `CONSOLE_JWT_SECRET` handling
- Remove `AuthSource.CONSOLE`
- Remove grace period logic

---

## 8. File Locations

| Component | File |
|-----------|------|
| Token Issuance | `backend/app/api/onboarding.py` |
| Gateway | `backend/app/auth/gateway.py` |
| Metrics | `backend/app/auth/gateway_metrics.py` |
| AuthSource Enum | `backend/app/auth/contexts.py` |
| IdentitySource Enum | `backend/app/auth/actor.py` |
| Authority Mapping | `backend/app/auth/authority.py` |
| Gateway Middleware | `backend/app/auth/gateway_middleware.py` |
| Gateway Config | `backend/app/auth/gateway_config.py` |
| Clerk Provider | `backend/app/auth/clerk_provider.py` |

---

## 9. Prohibited Changes

The following changes are **explicitly prohibited** without owner approval:

1. **Reintroducing algorithm-based routing** — Routing must remain issuer-based
2. **Adding secret fallback chains** — Each secret has one source
3. **Merging Console and Clerk authenticators** — They are separate trust domains
4. **Renaming standard claims** — `iss`, `sub`, `exp` are JWT standards
5. **Removing feature flags** — Deprecation must remain controllable
6. **Removing metrics** — Usage must remain observable
7. **Removing grace period prematurely** — Wait for Phase 1 approval
8. **Adding new auth paths without contract** — All auth paths must be documented here

---

## 10. Allowed Changes (Safe Zone)

The following changes may proceed **without approval**:

1. Bug fixes inside an authenticator (no semantic change)
2. Logging improvements (no semantic change)
3. Additional metrics (non-breaking, additive only)
4. Test coverage improvements
5. Documentation updates
6. Feature flag value changes via environment (not code defaults)
7. Removal of deprecated code **after Phase 4 approval**

---

## 11. Change Protocol

If a change is required that violates this baseline:

1. **Stop implementation**
2. **Produce a Design Change Proposal (DCP)** including:
   - Current baseline section affected
   - Reason change is required
   - Blast radius analysis
   - Migration plan
3. **Wait for explicit owner approval**
4. **Update this baseline document**
5. **Proceed with implementation**

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-09 | Claude | Initial baseline established |

---

## 13. Attestation

This architecture has been reviewed and approved for production use.

- Issuer-based routing: **Implemented**
- Trust domain separation: **Implemented**
- Feature-flagged deprecation: **Implemented**
- Metrics: **Implemented**
- Grace period: **Active**

**Status: LOCKED**
