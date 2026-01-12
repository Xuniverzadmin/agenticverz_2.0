# AUTH_DESIGN.md — Authentication & Authorization Invariants

**Status:** LOCKED
**Effective:** 2026-01-12
**Authority:** This document is the single source of truth for authentication design.
**Enforcement:** `scripts/ops/auth_invariant_scanner.py`

---

## Invariants

If code contradicts this document, the code is wrong.

---

### HUMAN IDENTITY

```
AUTH-HUMAN-001: All human users authenticate via Clerk (RS256 JWKS).
AUTH-HUMAN-002: No other human authentication mechanism exists.
AUTH-HUMAN-003: Console JWT (HS256) is not a valid human identity.
AUTH-HUMAN-004: Stub tokens are not valid in any environment.
```

---

### MACHINE IDENTITY

```
AUTH-MACHINE-001: Machine clients authenticate via API Key (X-AOS-Key header).
AUTH-MACHINE-002: API keys are database-validated, not environment-variable matched.
AUTH-MACHINE-003: Machine identity is scoped to a specific tenant.
```

---

### TENANT RESOLUTION

```
AUTH-TENANT-001: Tenant identity derives from Clerk org_id claim or membership lookup.
AUTH-TENANT-002: Tenant identity never comes from URL path parameters.
AUTH-TENANT-003: Tenant identity never comes from request body.
AUTH-TENANT-004: Tenant identity never comes from query parameters.
AUTH-TENANT-005: No fallback tenant exists. Missing tenant is a hard failure.
AUTH-TENANT-006: "default" is not a valid tenant identifier.
```

---

### GATEWAY

```
AUTH-GATEWAY-001: Gateway determines identity only. It does not assign permissions.
AUTH-GATEWAY-002: Gateway produces one context type per plane (Human or Machine).
AUTH-GATEWAY-003: Gateway rejects requests with both JWT and API key (mutual exclusivity).
AUTH-GATEWAY-004: Gateway does not route based on JWT algorithm header.
AUTH-GATEWAY-005: Gateway routes based on JWT issuer claim only.
```

---

### RBAC

```
AUTH-RBAC-001: RBAC is a routing gate. It determines endpoint reachability.
AUTH-RBAC-002: RBAC does not assign permissions.
AUTH-RBAC-003: RBAC does not differentiate between human users.
AUTH-RBAC-004: PUBLIC tier means no authentication required.
AUTH-RBAC-005: SESSION tier means authentication required.
AUTH-RBAC-006: RBAC tiers beyond SESSION are routing decisions, not permission grants.
```

---

### PERMISSIONS

```
AUTH-PERM-001: Permissions are not assigned during authentication.
AUTH-PERM-002: Permissions are derived from roles after onboarding.
AUTH-PERM-003: No wildcard permissions (["*"]) are assigned to human contexts.
AUTH-PERM-004: Onboarding endpoints do not require permissions.
```

---

### ONBOARDING

```
AUTH-ONBOARD-001: Onboarding is permission-free within tenant scope.
AUTH-ONBOARD-002: Authenticated humans may manage API keys for their own tenant.
AUTH-ONBOARD-003: Founders follow the exact same onboarding path as customers.
AUTH-ONBOARD-004: No authentication shortcuts exist for any user class.
AUTH-ONBOARD-005: Onboarding completion is a prerequisite for role-based privileges.
```

---

### FORBIDDEN PATTERNS

```
FORBIDDEN-001: CONSOLE_JWT_SECRET environment variable.
FORBIDDEN-002: AuthSource.CONSOLE enum value.
FORBIDDEN-003: HS256 JWT issuance or verification for humans.
FORBIDDEN-004: permissions=["*"] assignment to HumanAuthContext.
FORBIDDEN-005: Tenant fallback to "default" or None.
FORBIDDEN-006: Issuer routing for "agenticverz-console".
FORBIDDEN-007: stub_ token prefix handling.
FORBIDDEN-008: AUTH_STUB_ENABLED environment variable.
FORBIDDEN-009: AUTH_CONSOLE_ENABLED environment variable.
FORBIDDEN-010: Grace period for missing issuer claims.
```

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-12 | Initial lock | Claude + Founder |

