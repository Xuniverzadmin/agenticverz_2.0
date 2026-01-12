# PIN-397: Authentication Invariants Locked

**Status:** LOCKED
**Created:** 2026-01-11
**Category:** Auth / Governance / System Contract
**Milestone:** Phase G Steady State

---

## Summary

Locked the authoritative Authentication Invariants document. This contract formalizes four constitutional auth rules that protect the system from credential manipulation, tenant forgery, and auth confusion attacks.

---

## Contract Location

```
docs/governance/AUTH_INVARIANTS.md
```

---

## Invariants (Constitutional)

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| AUTH-001 | Tenant IDs never appear in authenticated customer URLs | Frontend guard + RBAC 403 |
| AUTH-002 | JWT XOR API Key (mutual exclusivity) | Gateway 401 |
| AUTH-003 | Issuer-based routing, never algorithm-based | Gateway implementation |
| AUTH-004 | Tenant identity from auth context only | TenantContext design |

---

## AUTH-001 Incident & Resolution

### Problem Detected

Frontend `ConnectPage` was calling:
```
GET /api/v1/tenants/{tenant_id}/api-keys
```

This violated AUTH-001: "Tenant IDs never appear in authenticated URLs"

### Root Cause

Frontend mental model assumed: "I know the tenant ID, so I should pass it"

Backend truth: "If you're authenticated, I already know your tenant"

### Resolution

1. **Fixed frontend** (`website/onboarding/src/pages/ConnectPage.tsx`)
   - Changed to call `/api/v1/api-keys` (tenant from JWT)

2. **Added frontend guardrail** (`website/app-shell/src/api/client.ts`)
   - `assertAuth001Compliance()` rejects tenant-in-URL for customer endpoints
   - Throws explicit `AUTH-001 VIOLATION` error

3. **Created onboarding API client** (`website/onboarding/src/lib/api.ts`)
   - Standalone guarded client for onboarding flows

### 403 Behavior Confirmation

The 403 error was **correct and desirable**:
- RBAC correctly denied unknown route pattern
- No backend changes needed
- Gateway, auth, TenantContext all working as designed

---

## Scope Clarification

| Console | Scope | AUTH-001 Applies? |
|---------|-------|-------------------|
| Customer Console | `/api/v1/...` data endpoints | **YES** |
| Operator Console | `/operator/...` | No (cross-tenant access required) |
| Admin endpoints | `/api/v1/tenants`, `/api/v1/tenants/switch` | No (administrative) |

---

## Files Modified

| File | Change |
|------|--------|
| `docs/governance/AUTH_INVARIANTS.md` | Created - 4 invariants |
| `website/onboarding/src/pages/ConnectPage.tsx` | Fixed tenant-in-URL violation |
| `website/app-shell/src/api/client.ts` | Added AUTH-001 guard |
| `website/onboarding/src/lib/api.ts` | Created guarded API client |

---

## Prevention

### Frontend (Runtime)

```typescript
// Throws on violation
assertAuth001Compliance(config.url);
```

### Backend (RBAC)

Unknown routes get 403 (default deny).

### Future: ESLint Rule (Optional)

Could add static analysis to catch at build time:
```javascript
// eslint-plugin-agenticverz
// Rule: no-tenant-in-api-path
```

---

## Related PINs

- PIN-391 — RBAC Query Authority
- PIN-392 — Authorization Constitution
- PIN-271 — RBAC Architecture Directive

---

*This PIN locks authentication invariants. Modification requires founder approval.*
