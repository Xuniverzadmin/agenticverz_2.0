# Authentication Invariants

**Version:** 1.0
**Status:** LOCKED
**Effective:** 2026-01-11
**Authority:** Founder-ratified, immutable without explicit approval

---

## Contract Statement

> *What authentication patterns are unconditionally forbidden, regardless of convenience?*

These invariants are **constitutional**. Violation is a design failure, not a bug.

---

## AUTH-001: Tenant IDs Never Appear in Authenticated URLs

**Invariant:**

> Any authenticated customer data route containing `{tenant_id}` in the path is **invalid by design**.

**Scope:**

| Console | Scope | AUTH-001 Applies? |
|---------|-------|-------------------|
| Customer Console | `/api/v1/...` data endpoints | **YES** |
| Operator Console | `/operator/...` | No (operators need cross-tenant access) |
| Admin endpoints | `/api/v1/tenants`, `/api/v1/tenants/switch` | No (administrative, not data access) |

**Rationale:**

| Property | Why It Matters |
|----------|----------------|
| Cross-tenant forgery prevention | URL parameters can be manipulated; auth context cannot |
| RBAC tractability | One authorization model, not N per-tenant variants |
| Uniform access surface | Works for UI, agents, CLI, SDSR, Aurora identically |
| Scalability | Tenant-in-URL patterns break under organizational complexity |

**Correct Pattern:**

```
GET /api/v1/api-keys
Authorization: Bearer <JWT with tenant claims>
```

Tenant resolved from: `TenantContext` via `Depends(get_tenant_context)`

**Forbidden Pattern:**

```
GET /api/v1/tenants/{tenant_id}/api-keys
Authorization: Bearer <JWT>
```

**Expected Behavior on Violation:**

- RBAC returns 403 (default deny on unknown route)
- Frontend API client throws `AUTH-001 VIOLATION` error
- This is **correct and desirable**
- The 403/error is a design alarm, not a bug

**Frontend Enforcement:**

```typescript
// website/app-shell/src/api/client.ts
// Throws error if customer API path contains tenant ID
assertAuth001Compliance(config.url);
```

---

## AUTH-002: JWT XOR API Key (Mutual Exclusivity)

**Invariant:**

> A request must authenticate with exactly one credential type: JWT OR API Key, never both.

**Rationale:**

- Prevents credential confusion attacks
- Simplifies auth gateway routing
- Clear precedence eliminates ambiguity

**Expected Behavior on Violation:**

- Auth gateway returns 401 with error: "Ambiguous credentials"
- Both credentials are rejected
- Request must be retried with single credential type

---

## AUTH-003: Issuer-Based Routing, Never Algorithm-Based

**Invariant:**

> JWT routing decisions are made by `iss` claim, NEVER by `alg` header.

**Rationale:**

- `alg` header is attacker-controlled
- `iss` claim is signed and verified
- Algorithm confusion attacks are eliminated

**Implementation:**

```python
# CORRECT: Route by issuer
if payload.get("iss") == "console":
    return _authenticate_console(token)
elif payload.get("iss").startswith("https://clerk."):
    return _authenticate_clerk(token)

# FORBIDDEN: Route by algorithm
if header.get("alg") == "HS256":  # NEVER DO THIS
    ...
```

---

## AUTH-004: Tenant Identity From Auth Context Only

**Invariant:**

> Tenant identity is derived exclusively from authentication context (JWT claims), never from:
> - URL path parameters
> - Query parameters
> - Request body fields
> - HTTP headers (other than Authorization)

**Rationale:**

- Single source of truth
- Cannot be spoofed by request manipulation
- Enables consistent multi-tenant isolation

**Implementation:**

```python
# TenantContext is injected once from JWT claims
ctx: TenantContext = Depends(get_tenant_context)

# Downstream code uses ctx.tenant_id
# Never extracts tenant from request parameters
```

---

## Enforcement

### Backend

- Auth gateway enforces AUTH-002, AUTH-003, AUTH-004 at L4
- RBAC enforces AUTH-001 via default deny on unknown routes
- No backend endpoint accepts `{tenant_id}` in authenticated paths

### Frontend

- API client must reject paths containing `/tenants/` for authenticated calls
- ESLint rule flags tenant-in-URL patterns
- Compile-time validation in SDK

### SDSR/Aurora

- Scenario validation rejects observations with tenant-in-URL evidence
- Pipeline contracts inherit these invariants

---

## Violation Response

| Invariant | Response | Severity |
|-----------|----------|----------|
| AUTH-001 | 403 Forbidden | Design Alarm |
| AUTH-002 | 401 Unauthorized | Hard Reject |
| AUTH-003 | Code Review Block | Critical |
| AUTH-004 | 403 Forbidden | Design Alarm |

---

## Related Documents

- `design/auth/RBAC_RULES.yaml` — Canonical RBAC schema
- `backend/app/auth/gateway.py` — Auth gateway implementation
- `backend/app/auth/gateway_middleware.py` — L3 boundary adapter
- PIN-391 — RBAC Query Authority

---

*This contract is machine-enforced. Non-compliant patterns will be rejected.*
