# PIN-440: Customer Sandbox Authentication Mode

**Status:** PARTIAL (Auth module implemented, integration blocked)
**Created:** 2026-01-17
**Author:** Claude Opus 4.5
**Domain:** Authentication / Customer Integrations
**Related:** PIN-439 (Customer LLM Integrations Complete)

---

## Problem Statement

Testing customer integration APIs (`/api/v1/cus/*`) fails with `missing_auth` because:

1. **DB Authority = Neon (production)** - System correctly treats all requests as production
2. **Auth Authority = Production Gateway** - JWT/API key enforced
3. **Local backend = Treated like prod** - No bypass for testing

When calling:
```bash
curl http://localhost:8000/api/v1/cus/integrations
```

The system correctly responds:
```json
{"error": "missing_auth", "message": "Authentication required"}
```

This is **by design** - the system is behaving correctly. The mistake is trying to test customer APIs using operator-grade auth or no auth.

---

## Root Cause Analysis

| Layer | Current State | Issue |
|-------|---------------|-------|
| DB Authority | `DB_AUTHORITY=neon` | Production database, no local sandbox |
| Auth Gateway | Production mode | JWT/Clerk validation enforced |
| RBAC Rules | Missing `/api/v1/cus/*` | Paths not in RBAC_RULES.yaml |
| Machine Auth | `X-AOS-Key` available | Doesn't map to customer tenant context |

**Key Insight:** Local testing must simulate a real customer, not bypass a real system.

---

## Designed Solution: Customer Sandbox Auth Mode

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REQUEST ARRIVES                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         SANDBOX AUTH CHECK (new, first in chain)           │
│  IF AOS_MODE=local AND CUSTOMER_SANDBOX_ENABLED=true:      │
│    IF header "X-AOS-Customer-Key" present:                 │
│      → Resolve to SandboxCustomerPrincipal                 │
│      → Skip normal auth, continue to handler               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (if no sandbox key)
┌─────────────────────────────────────────────────────────────┐
│              Normal Auth Gateway (unchanged)                │
│  • JWT validation (Clerk)                                   │
│  • API key validation (X-AOS-Key)                          │
│  • RBAC enforcement                                         │
└─────────────────────────────────────────────────────────────┘
```

### Environment Gates (Hard Boundaries)

```env
# Required for sandbox mode
AOS_MODE=local           # or "test"
CUSTOMER_SANDBOX_ENABLED=true

# Safety gate: sandbox is BLOCKED if DB_AUTHORITY=neon
DB_AUTHORITY=local       # Must NOT be "neon"
```

### Sandbox Keys

| Key | Tenant | Role |
|-----|--------|------|
| `cus_sandbox_demo` | demo-tenant | customer_admin |
| `cus_sandbox_readonly` | demo-tenant | customer_viewer |
| `cus_sandbox_tenant2` | tenant-2 | customer_admin |
| `cus_ci_test` | ci-tenant | customer_admin |

### Usage

```bash
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
     http://localhost:8000/api/v1/cus/integrations
```

---

## What Was Implemented

### 1. Customer Sandbox Auth Module
**File:** `backend/app/auth/customer_sandbox.py`

- `SandboxCustomerPrincipal` dataclass
- `is_sandbox_allowed()` - environment gate check
- `try_sandbox_auth()` - main entry point for gateway
- `SANDBOX_KEYS` registry
- Safety gate: refuses to run if `DB_AUTHORITY=neon`

### 2. Gateway Middleware Integration
**File:** `backend/app/auth/gateway_middleware.py`

- Added sandbox auth check BEFORE normal auth
- Injects `request.state.auth_context = SandboxCustomerPrincipal`
- Sets `request.state.is_sandbox = True` for audit trail

### 3. Seed Data Script
**File:** `backend/scripts/seed_sandbox_data.py`

- Seeds demo-tenant, tenant-2, ci-tenant
- Creates sample integrations (OpenAI, Anthropic)
- Creates 7 days of usage data
- Safety gate: refuses to run on Neon

---

## What's Blocking

### Issue 1: DB Authority Conflict

Current production setup:
```env
DB_AUTHORITY=neon
```

Sandbox mode requires:
```env
DB_AUTHORITY=local
```

**Impact:** Sandbox auth is correctly blocked by safety gate.

### Issue 2: Local DB Missing Tables

Local postgres (`nova_db`) doesn't have `cus_*` tables because:
- Alembic blocks migrations on `DB_AUTHORITY=local`
- This is a governance safeguard (PIN-related)

### Issue 3: RBAC Rules Not Configured

The `/api/v1/cus/*` paths are not in `RBAC_RULES.yaml`, so even machine auth (`X-AOS-Key`) fails.

---

## Options to Proceed

### Option A: Add RBAC Rules for Machine Auth (Recommended for Prod)

Add to `RBAC_RULES.yaml`:
```yaml
- path_prefix: /api/v1/cus/
  tier: MACHINE
  required_capabilities:
    - customer:integrations:read
    - customer:integrations:write
```

**Pros:** Works with Neon, proper production path
**Cons:** Requires capability mapping

### Option B: Enable Sandbox Mode for CI/Local

Create separate local test environment:
1. Allow alembic on `DB_AUTHORITY=test` (new authority level)
2. Run migrations on local DB
3. Enable sandbox mode
4. Test with `X-AOS-Customer-Key`

**Pros:** Isolated testing, no Neon cost
**Cons:** Requires governance exception for migrations

### Option C: Temporary Public Path (NOT Recommended)

Add `/api/v1/cus/*` to public paths.

**Pros:** Quick
**Cons:** Breaks security model, no audit trail

---

## Recommended Resolution Path

1. **Short-term (Testing):** Add RBAC rule for `/api/v1/cus/*` with machine auth
2. **Medium-term (CI):** Create `DB_AUTHORITY=test` level for CI database
3. **Long-term (Local Dev):** Full sandbox mode with local seeding

---

## Architecture Principle (Locked)

> **Local testing must simulate a real customer, not bypass a real system.**

What we MUST NOT do:
- ❌ Add customer paths to `PUBLIC_PATHS`
- ❌ Disable auth middleware
- ❌ Hardcode tenant IDs in routes
- ❌ Skip enforcement in "test mode"

What we MUST do:
- ✅ Use customer-grade auth (sandbox or real)
- ✅ Gate sandbox strictly by environment
- ✅ Keep prod auth path untouched
- ✅ Maintain audit trail

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `backend/app/auth/customer_sandbox.py` | NEW | Sandbox auth module |
| `backend/app/auth/gateway_middleware.py` | MODIFIED | Sandbox integration |
| `backend/scripts/seed_sandbox_data.py` | NEW | Local data seeder |

---

## Next Steps

1. [ ] Decide on resolution path (A, B, or hybrid)
2. [ ] Implement RBAC rules for machine auth (Option A)
3. [ ] Or create `DB_AUTHORITY=test` governance exception (Option B)
4. [ ] Test customer integration API end-to-end
5. [ ] Update PIN-439 with test results

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-17 | Created - documented sandbox auth architecture and blockers |
