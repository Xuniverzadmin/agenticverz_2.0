# Onboarding State Machine - v1 (Linear, Production-Grade)

**Status:** APPROVED DESIGN
**PIN:** PIN-399
**Date:** 2026-01-12
**Scope:** Tenant onboarding only
**Applies to:** All humans (founders = customers)

---

## Executive Summary

This document defines the **authoritative onboarding state machine** for Agenticverz tenants. It is:

- **Deterministic** - No guessing, no inference
- **Auditable** - Every state transition is an event
- **Founder/Customer Identical** - No special paths
- **Impossible to Bypass** - Scanner + runtime enforcement

---

## 1. Core Object

```
Tenant.onboarding_state
```

| Property | Value |
|----------|-------|
| Owner | Tenant model |
| Source of Truth | Single, persisted |
| Inference | FORBIDDEN |
| Bypass | FORBIDDEN |

---

## 2. State Enum (Linear)

```
CREATED
    ↓
IDENTITY_VERIFIED
    ↓
API_KEY_CREATED
    ↓
SDK_CONNECTED
    ↓
COMPLETE
```

**Constraints:**
- No branching
- No skipping
- No parallel states
- Monotonic forward only

---

## 3. State Semantics

### 3.1 CREATED

**Meaning:**
- Tenant record exists
- User authenticated via Clerk
- Tenant ↔ user association exists
- No trust established yet

**Allowed Operations:**
- Read tenant metadata (self)
- Read onboarding status
- Begin identity verification (implicit via Clerk)

**Forbidden:**
- API key access (read/create/delete)
- SDK access
- Any non-onboarding API

---

### 3.2 IDENTITY_VERIFIED

**Meaning:**
- Human identity verified via Clerk
- Tenant ownership confirmed
- Bootstrap may begin

**Allowed Operations:**
- Create first API key
- Read API keys (own tenant only)
- Delete API keys (own tenant only)
- Fetch SDK instructions

**Forbidden:**
- SDK data ingestion
- Agent execution
- Any non-onboarding workload

**This is where `/api/v1/api-keys` is allowed.**

---

### 3.3 API_KEY_CREATED

**Meaning:**
- At least one valid API key exists
- Machine identity bootstrap complete
- SDK can authenticate

**Allowed Operations:**
- Read / rotate API keys
- SDK authentication
- SDK handshake / registration endpoint

**Forbidden:**
- Full production workloads
- Policy enforcement
- Cost simulation, incidents, etc.

---

### 3.4 SDK_CONNECTED

**Meaning:**
- SDK authenticated successfully at least once
- Tenant has proven machine access
- System trust established

**Allowed Operations:**
- All core APIs (within limits)
- Policy creation
- Cost simulation
- Telemetry
- Incidents
- Reports

**Forbidden:**
- None related to onboarding

---

### 3.5 COMPLETE

**Meaning:**
- Onboarding is finished
- Tenant is production-ready
- Future permissions (roles, plans, billing) apply here

**Allowed Operations:**
- Everything allowed by plan / policy / role
- Normal production behavior

---

## 4. State Transition Table

| From | To | Trigger |
|------|----|---------|
| CREATED | IDENTITY_VERIFIED | Successful Clerk-authenticated request |
| IDENTITY_VERIFIED | API_KEY_CREATED | First API key created |
| API_KEY_CREATED | SDK_CONNECTED | First successful SDK-authenticated call |
| SDK_CONNECTED | COMPLETE | Explicit finalize or automatic promotion |

---

## 5. Transition Rules (Non-Negotiable)

### Rule 1: Transitions are Monotonic
- Never go backwards
- Never skip forward
- State only increases

### Rule 2: Transitions are Explicit
- Caused by a real event
- Not by time
- Not by assumption

### Rule 3: Transitions are Idempotent
- Repeating the same trigger does nothing
- No duplicate side effects

---

## 6. Failure Semantics

Every failure must answer one question:

> "What state are you in, and what state is required?"

### Error Format

```json
{
  "status": 403,
  "error": "onboarding_state_insufficient",
  "current_state": "CREATED",
  "required_state": "IDENTITY_VERIFIED",
  "message": "Operation requires onboarding_state >= IDENTITY_VERIFIED"
}
```

### Example Errors

**API key read too early:**
```
403 Forbidden
reason: onboarding_state = CREATED
required: IDENTITY_VERIFIED
```

**SDK call too early:**
```
403 Forbidden
reason: onboarding_state = API_KEY_CREATED
required: SDK_CONNECTED
```

**Invariants:**
- No generic "permission denied"
- No silent failure
- No ambiguity

---

## 7. Design Invariants

| ID | Invariant |
|----|-----------|
| ONBOARD-001 | Onboarding state is the sole authority for bootstrap permissions |
| ONBOARD-002 | Roles and plans do not apply before COMPLETE |
| ONBOARD-003 | Founders and customers follow identical state transitions |
| ONBOARD-004 | No endpoint may infer onboarding progress |
| ONBOARD-005 | API keys are onboarding artifacts, not permissions |

---

## 8. Endpoint → State Mapping (To Be Implemented)

| Endpoint Pattern | Required State |
|------------------|----------------|
| `GET /api/v1/me` | CREATED |
| `GET /api/v1/onboarding/status` | CREATED |
| `POST /api/v1/api-keys` | IDENTITY_VERIFIED |
| `GET /api/v1/api-keys` | IDENTITY_VERIFIED |
| `DELETE /api/v1/api-keys/{id}` | IDENTITY_VERIFIED |
| `POST /api/v1/sdk/register` | API_KEY_CREATED |
| `POST /api/v1/runs` | SDK_CONNECTED |
| `GET /api/v1/runs` | SDK_CONNECTED |
| `POST /api/v1/policies` | SDK_CONNECTED |
| `*` (all other endpoints) | COMPLETE |

---

## 9. Implementation Plan

### Step 1: Schema
Add `Tenant.onboarding_state` column with default `CREATED`

### Step 2: Pure Function
```python
def allowed_operations(onboarding_state: OnboardingState) -> Set[str]:
    """Return set of allowed operation patterns for given state."""
    ...
```

### Step 3: Middleware Gate
Gate endpoints on required onboarding_state

### Step 4: Verify
Re-run onboarding as a user, observe correct 403s

---

## 10. Explicitly Out of Scope (v1)

| Feature | Status | When |
|---------|--------|------|
| Rollback / reset | OUT | v2 |
| Recovery states | OUT | v2 |
| Partial onboarding | OUT | v2 |
| Multi-user tenants | OUT | v2 |
| Billing gates | OUT | v2 |
| Plan enforcement | OUT | v2 |

These come **after v1 is proven**.

---

## 11. Why This Solves the 403 Problem

Before this design:
> "Is auth broken?"

After this design:
> "What onboarding_state is the tenant in?"

And there is exactly one correct answer.

---

## References

- PIN-399: Onboarding State Machine v1
- PIN-398: Auth Design Sanitization
- docs/AUTH_DESIGN.md: Auth invariants
