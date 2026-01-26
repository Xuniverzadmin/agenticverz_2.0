# AUTH Console Contract (FINAL - LOCKED)

**Status:** LOCKED (PERMANENT)
**Effective:** 2026-01-13
**Reference:** PIN-409
**Revision:** This design closes the topic permanently. No forks, no revisits.

---

## Core Invariants (Non-Negotiable)

> **Clerk owns identity. Backend owns authority. Consoles own UX only.**

These three statements are the entire auth model. Everything else derives from them.

---

## 1. Clerk's Role — Identity Only (Nothing Else)

Clerk is **not** the auth system. Clerk is **only** the identity provider.

### Clerk IS responsible for:
- Verifying humans (email, password, OAuth, MFA)
- Maintaining sessions
- Issuing signed JWTs
- Handling account recovery, device security

### Clerk is NOT responsible for:
- Roles
- Founder vs customer distinction
- Tenant authority
- Capabilities
- Console routing
- Feature access
- Lifecycle decisions

> **INVARIANT (LOCKED)**
> Clerk answers only: **"Is this a real signed-in human?"**

---

## 2. Backend Authority — Single Source of Truth

The backend is the **only authority** for:
- Who the actor is
- What they can do
- Which tenant they belong to
- What lifecycle state applies

### `/api/v1/session/context`

This endpoint is the **only contract** the frontend trusts.

Returns **facts**, never guesses:
```json
{
  "actor_type": "customer | founder | machine",
  "tenant_id": "uuid",
  "capabilities": ["api_key_management", "ops:view"],
  "onboarding_state": "COMPLETE",
  "lifecycle_state": "ACTIVE"
}
```

> **INVARIANT (LOCKED)**
> Frontend never derives authority.
> Frontend never infers roles.
> Frontend never trusts Clerk metadata.

---

## 3. Actor Model — Closed and Explicit

There are exactly **three** actor types. No extensions.

| Actor Type | Source | Meaning |
|------------|--------|---------|
| `customer` | Clerk → HumanAuthContext | Normal tenant user |
| `founder` | FOPS token → FounderAuthContext | Internal, privileged |
| `machine` | API key → MachineCapabilityContext | SDK / automation |

> Actor type is **determined in gateway**, never in UI.

---

## 4. Console Model — UX Surface Only

Four consoles exist. They are **presentation layers**, not security domains.

| Console | Purpose | Authority |
|---------|---------|-----------|
| console.agenticverz.com | Customer UI | Backend |
| preflight-console.agenticverz.com | Internal testing | Backend |
| fops.com | Founder UI | Backend |
| preflight-fops.com | Founder testing | Backend |

### Console selection rules:
- Console **never** decides access
- Console **only** renders what backend allows
- Console **never** checks roles directly

> **INVARIANT (LOCKED)**
> Console type influences **UX**, not **authority**.

### 4.1 Preflight Is NOT a Different Auth Mode (INVARIANT)

> **Preflight ≠ relaxed auth. Preflight is a UX/environment distinction only.**

| Attribute | Production | Preflight |
|-----------|------------|-----------|
| Human auth | Clerk JWT | Clerk JWT |
| Machine auth | DB-backed API key | DB-backed API key |
| Founder auth | FOPS JWT | FOPS JWT |
| Auth enforcement | Full | Full |

**What preflight changes:** Environment variables, UX flags, data isolation.

**What preflight does NOT change:** Authentication rules, authorization logic, identity sources, trust boundaries.

Preflight users do NOT get weaker auth, bypasses, special API keys, or alternate identity paths. The auth contract is **identical** across all environments.

---

## 5. Capabilities — The Only Authorization Primitive

There are:
- **NO** "roles" in the frontend
- **NO** permission flags
- **NO** boolean checks like `isFounder`

Everything reduces to:
```typescript
capabilities: string[]
```

Examples:
- `api_key_management`
- `tenant:read`
- `tenant:write`
- `ops:view`
- `ops:mutate`

Frontend logic becomes:
```typescript
if (capabilities.includes("ops:view")) {
  renderFounderPanel();
}
```

> **INVARIANT (LOCKED)**
> Capabilities come **only** from backend.
> Frontend never invents them.

---

## 6. Clerk Metadata — Non-Authoritative, Transitional Only

Clerk `publicMetadata`:
- MAY exist
- MUST NOT be trusted
- MUST NOT be read for security decisions

Allowed **only** for:
- UX hints
- Display labels
- Transitional compatibility

### End state:
- Clerk metadata is ignored
- Backend emits all authority facts
- Metadata eventually removed without impact

> This guarantees **no second migration**.

---

## 7. Session Context Caching — Per Request Only

Backend must:
- Compute session context once per request
- Store it on `request.state`
- Reuse it across guards and handlers

This ensures:
- Cheap execution
- No inconsistency
- No cross-request bleed

---

## 8. Lifecycle & Offboarding — Already Correct

- Onboarding state is historical
- Lifecycle state is authoritative
- Termination revokes keys
- Suspension blocks SDK
- Archive is terminal

No coupling to Clerk. No coupling to UI.

---

## 9. Explicitly Forbidden (Forever)

These will **never** be reintroduced:

| Forbidden Pattern | Why |
|-------------------|-----|
| Backend login endpoints | Clerk owns login |
| Password handling server-side | Clerk owns credentials |
| Frontend authStore authority | Backend owns authority |
| Role logic in UI | Capabilities only |
| "Special founder paths" | Actor type from gateway |
| Console-based authorization | Console is UX only |
| Auth fallbacks or stubs | Clean separation |
| `isFounder` boolean checks | Use capabilities |
| Clerk metadata for security | Non-authoritative |

Any of these would be an architectural violation.

---

## 10. Why This Is Sustainable

This design is:
- **Boring** → low cognitive load
- **Composable** → new consoles don't matter
- **Auditable** → backend emits facts
- **Immutable** → no need to revisit
- **Scalable** → orgs, teams, billing fit cleanly
- **Replaceable** → Clerk can be swapped later

---

## Implementation Files

| File | Role |
|------|------|
| `backend/app/api/session_context.py` | Session context endpoint |
| `backend/app/auth/contexts.py` | Auth context types |
| `backend/app/auth/gateway_middleware.py` | Context injection |
| `src/hooks/useSessionContext.ts` | Frontend hook |
| `src/api/session.ts` | Frontend API client |

---

## Frontend Migration Status

| Pattern | Status |
|---------|--------|
| `useSessionContext()` for authority | Implemented |
| Route guards use session context | Implemented |
| authStore deprecated fields documented | Complete |
| API key fallback documented as transitional | Complete |
| Clerk metadata ignored for security | Complete |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-13 | Initial contract, PIN-409 implementation |
| 2026-01-13 | FINAL LOCK - capabilities-only model, forbidden patterns documented |
| 2026-01-13 | Added Section 4.1: Preflight Is NOT a Different Auth Mode - auth identical across all environments |
