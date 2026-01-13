# PIN-409: Auth Console Contract — Clerk Identity, Backend Authority

**Status:** LOCKED (PERMANENT)
**Created:** 2026-01-13
**Category:** Architecture / Auth / Frontend
**Related:** AUTH_CONSOLE_CONTRACT.md, FRONTEND_AUTH_CONTRACT.md
**Revision:** This design closes the topic permanently. No forks, no revisits.

---

## Summary

This PIN documents the implementation of the canonical auth model for the four-console architecture. The core principle: **Clerk owns identity, Backend owns authority, Consoles own UX only.**

---

## Problem Statement

The frontend was deriving authorization facts (`isFounder`, `audience`) locally instead of reading them from the backend. This violated the trust model:

| Before (Incorrect) | After (Correct) |
|-------------------|-----------------|
| Frontend derives `isFounder` from Clerk metadata | Backend returns `actor_type` |
| Frontend stores `audience` in authStore | Backend determines from auth context |
| Trust inverted (frontend decides authority) | Trust correct (backend decides authority) |

---

## Implementation

### 1. Backend Session Context Endpoint

**File:** `backend/app/api/session_context.py`

```
GET /api/v1/session/context
```

Returns:
```json
{
  "actor_type": "customer | founder | machine",
  "tenant_id": "...",
  "capabilities": [...],
  "lifecycle_state": "ACTIVE | SUSPENDED | ...",
  "onboarding_state": "COMPLETE | ..."
}
```

**Key design:**
- Uses type-based authority: `FounderAuthContext` → founder, `HumanAuthContext` → customer
- Gets lifecycle state from `TenantLifecycleProvider`
- Frontend reads these facts, never derives them

### 2. Frontend Session Context Hook

**File:** `src/hooks/useSessionContext.ts`

```typescript
const { isFounder, isCustomer, tenantId, isLoading } = useSessionContext();
```

Provides:
- `isFounder`, `isCustomer`, `isMachine` - derived from backend `actor_type`
- `tenantId`, `lifecycleState`, `isActive`
- `isLoading`, `isError` for async handling

### 3. Route Guards Updated

**File:** `src/routes/FounderRoute.tsx`

Both `FounderRoute` and `CustomerRoute` now:
- Use `useSessionContext()` for authorization facts
- No longer derive `isFounder`/`audience` from authStore
- Wait for session context to load before making access decisions

### 4. Deprecated Fields Documented

**Files:** `authStore.ts`, `AIConsoleApp.tsx`

- Marked `audience`, `isFounder` fields as deprecated
- Documented API key fallback as transitional with deprecation plan
- Referenced `useSessionContext()` as the recommended pattern

---

## The Four Consoles

| Console | Audience | Auth Model |
|---------|----------|------------|
| console.agenticverz.com | Customers | Clerk JWT |
| preflight-console.agenticverz.com | Internal devs | Clerk JWT |
| fops.com | Founders only | FOPS JWT (separate) |
| preflight-fops.com | Internal founders | FOPS JWT (separate) |

**Critical:** Customer consoles and Founder consoles NEVER share identity paths.

---

## Preflight Is NOT a Different Auth Mode (INVARIANT)

> **Preflight ≠ relaxed auth. Preflight is a UX/environment distinction only.**

This must be stated explicitly to prevent future confusion:

| Attribute | Production Console | Preflight Console |
|-----------|-------------------|-------------------|
| Human auth | Clerk JWT | Clerk JWT |
| Machine auth | DB-backed API key | DB-backed API key |
| Founder auth | FOPS JWT | FOPS JWT |
| Auth enforcement | Full | Full |
| Session context | `/api/v1/session/context` | `/api/v1/session/context` |

**What preflight changes:**
- Environment variables (different Clerk app, different backend URL)
- UX flags (debug panels, test features)
- Data isolation (separate tenant data)

**What preflight does NOT change:**
- Authentication rules
- Authorization logic
- Identity sources
- Trust boundaries

Preflight users do NOT get:
- Weaker auth
- Bypasses
- Special API keys
- Alternate identity paths

The auth contract is **identical** across all environments.

---

## Two Identity Systems

### 1. Clerk — Human Users
- Used by: console, preflight-console
- Handles: Login, MFA, Sessions, OAuth
- Frontend: Render UI, call hooks, forward JWT
- Frontend must NOT: Decide roles, decode JWT meaningfully

### 2. FOPS Auth — Founder / Control Plane
- Used by: fops, preflight-fops
- Separate auth system (not Clerk)
- `FounderAuthContext` with separate issuer
- Must survive org changes, Clerk outages

---

## Frontend Design Rules

### RULE-AUTH-UI-001
> Frontend only answers: "Is the user signed in?"

**Allowed:**
```typescript
const { isSignedIn } = useAuth();
```

**Forbidden (in new code):**
```typescript
// DO NOT derive these in frontend
isFounder // from metadata
audience  // from authStore
roles     // from Clerk
```

### RULE-AUTH-UI-002
> Frontend never decides what the user can do.

Use `useSessionContext()` to get backend-verified facts.

---

## Files Created/Modified

| File | Action |
|------|--------|
| `backend/app/api/session_context.py` | Created |
| `backend/app/main.py` | Added router registration |
| `src/api/session.ts` | Created |
| `src/hooks/useSessionContext.ts` | Created |
| `src/routes/FounderRoute.tsx` | Modified (uses session context) |
| `src/stores/authStore.ts` | Documented deprecations |
| `src/products/ai-console/app/AIConsoleApp.tsx` | Documented transitional path |
| `docs/architecture/auth/AUTH_CONSOLE_CONTRACT.md` | Created (locked) |

---

## Transitional: API Key Fallback

The API key login path in AIConsoleApp is **TRANSITIONAL**:

**Why it exists:**
1. Demo mode: Quick access without account creation
2. Legacy support: Existing API-key-only customers
3. Developer testing: Local development without Clerk setup

**Deprecation plan:**
1. All new customers use Clerk OAuth exclusively
2. Existing API-key customers are migrated to Clerk
3. Demo mode moves to a separate unauthenticated sandbox
4. API key fallback is removed from AIConsoleApp

---

## Explicitly Forbidden Patterns

| Pattern | Why Forbidden |
|---------|---------------|
| "Founder user" inside Clerk | Founder is control-plane, not role |
| Clerk roles for infra | Violates separation |
| Shared login between console & fops | Identity path mixing |
| UI-derived authority | Frontend reads, never decides |
| `publicMetadata.isFounder` checks | Use backend `actor_type` |

---

## Verification

Build passes with no TypeScript errors:
```
npm run build
✓ built in 14.51s
```

---

## Related Documents

| Document | Location |
|----------|----------|
| Auth Console Contract | `docs/architecture/auth/AUTH_CONSOLE_CONTRACT.md` |
| Frontend Auth Contract | `docs/architecture/FRONTEND_AUTH_CONTRACT.md` |
| Auth Architecture Baseline | `docs/architecture/auth/AUTH_ARCHITECTURE_BASELINE.md` |
| Gateway Middleware | `backend/app/auth/gateway_middleware.py` |
| Auth Contexts | `backend/app/auth/contexts.py` |

---

---

## Final Design (LOCKED)

### Core Invariants
1. **Clerk = Identity Only** - Answers only "Is this a real signed-in human?"
2. **Backend = Authority** - Single source of truth for actor type, capabilities, lifecycle
3. **Consoles = UX Only** - Presentation layer, never decides access

### Capabilities Are The Only Authorization Primitive
- NO roles in frontend
- NO permission flags
- NO boolean checks like `isFounder`
- Everything reduces to `capabilities: string[]`

### Explicitly Forbidden (Forever)
- Backend login endpoints
- Frontend authStore authority
- Role logic in UI
- `isFounder` boolean checks
- Clerk metadata for security decisions
- Console-based authorization

### Why This Is Final
- Boring (low cognitive load)
- Composable (new consoles don't matter)
- Auditable (backend emits facts)
- Immutable (no revisits needed)
- Scalable (orgs, teams, billing fit cleanly)
- Replaceable (Clerk can be swapped later)

---

## Backend RBAC Implementation (2026-01-13)

### Problem
After implementing the session context endpoint, the preflight console was still getting 403 errors on `/api/v1/traces`. Investigation revealed a three-layer bug:

1. **AuthGatewayMiddleware was skipping `/api/v1/traces`** - PIN-407 SDSR validation had added it to public paths
2. **RBAC was extracting roles from JWT claims** - Violates "backend owns authority" principle
3. **No auth_context** - Gateway skipped auth, so RBAC had nothing to consume

### Root Cause Chain
```
/api/v1/traces in PUBLIC_PATHS (gateway_config.py:141)
  → AuthGatewayMiddleware skipped authentication
  → request.state.auth_context = None
  → RBAC saw Bearer header but no auth_context
  → Guardrail triggered AUTH_CONTEXT_MISSING → 403
```

### Fixes Applied

**1. RBAC Capability-Based Authorization** (`rbac_middleware.py`)
- `enforce()` now uses `derive_capabilities_from_context()` as primary path
- Capabilities derived from auth context type, NOT JWT claims
- Centralized capability definitions: `FOUNDER_CAPABILITIES`, `HUMAN_BASE_CAPABILITIES`

**2. Silent Fallback Guardrail** (`rbac_middleware.py`)
```python
if auth_header.startswith("Bearer ") and not machine_token:
    logger.error("AUTH_CONTEXT_MISSING: Human JWT present but auth_context is None")
    return Decision(allowed=False, reason="auth-context-missing")
```
- Legacy RBAC_MATRIX fallback ONLY for X-Machine-Token
- Human requests MUST have auth_context - no silent downgrade

**3. Removed /api/v1/traces from Public Paths** (`gateway_config.py`)
- Lines 141-144 commented out
- Traces endpoint now requires authentication
- Auth context is properly set for RBAC

### Correct Flow (After Fix)
```
Request with Bearer JWT
  → AuthGatewayMiddleware verifies JWT with Clerk
  → Creates HumanAuthContext(actor_id=sub, session_id=sid, ...)
  → Sets request.state.auth_context
  → RBACMiddleware runs
  → derive_capabilities_from_context() → HUMAN_BASE_CAPABILITIES
  → has_capability("trace:read") → True
  → Decision(allowed=True, reason="capability-granted")
```

### Files Modified

| File | Change |
|------|--------|
| `backend/app/auth/rbac_middleware.py` | Capability-based enforce(), guardrails, centralized caps |
| `backend/app/auth/gateway_config.py` | Removed /api/v1/traces from public paths |

### Key Invariants (Permanent)

1. **JWT = Identity Only** - Contains only `sub`, backend derives authority
2. **Capabilities from Context Type** - `HumanAuthContext` → `HUMAN_BASE_CAPABILITIES`
3. **No Silent Fallback** - Human JWT without auth_context = hard error
4. **Centralized Definitions** - All capability grants in one place, auditable

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-13 | Initial implementation - session context endpoint, hook, route guard migration |
| 2026-01-13 | FINAL LOCK - capabilities-only model, forbidden patterns documented |
| 2026-01-13 | Added "Preflight Is NOT a Different Auth Mode" invariant - auth is identical across all environments |
| 2026-01-13 | Backend RBAC fix - capability-based authorization, removed traces from public paths, silent fallback guardrail |
