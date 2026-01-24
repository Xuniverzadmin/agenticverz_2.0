# PIN-399: Onboarding State Machine v1 - Linear Production-Grade Design

**Status:** DESIGN FREEZE ACTIVE
**Created:** 2026-01-12
**Last Updated:** 2026-01-12
**Category:** Architecture / Onboarding
**Reference:** docs/architecture/ONBOARDING_STATE_MACHINE_V1.md
**Freeze Reference:** docs/governance/FREEZE.md

---

## Freeze Status

> **Phases 4–8 are design-complete. Phase 6-8 mocks implemented (171 tests).**

| Phase | Status | Key Artifact |
|-------|--------|--------------|
| Phase-4 | COMPLETE | `app/api/founder_onboarding.py` |
| Phase-5 | COMPLETE | `app/auth/role_guard.py`, `app/auth/tenant_roles.py` |
| Phase-6 | IMPLEMENTED | `app/billing/` (35 tests) |
| Phase-7 | IMPLEMENTED | `app/protection/` (39 tests) |
| Phase-8 | IMPLEMENTED | `app/observability/` (53 + 15 E2E tests) |

**CI Enforcement:** `scripts/ci/check_frozen_files.py`

---

## Summary

Defines linear onboarding state machine: CREATED → IDENTITY_VERIFIED → API_KEY_CREATED → SDK_CONNECTED → COMPLETE. Monotonic, explicit, founder=customer identical.

---

## Design Principles

1. **Deterministic** - No guessing, no inference
2. **Auditable** - Every state transition is an event
3. **Founder/Customer Identical** - No special paths
4. **Impossible to Bypass** - Scanner + runtime enforcement

---

## State Enum

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

---

## State Transitions

| From | To | Trigger |
|------|----|---------|
| CREATED | IDENTITY_VERIFIED | Successful Clerk-authenticated request |
| IDENTITY_VERIFIED | API_KEY_CREATED | First API key created |
| API_KEY_CREATED | SDK_CONNECTED | First successful SDK-authenticated call |
| SDK_CONNECTED | COMPLETE | Explicit finalize or automatic promotion |

---

## Design Invariants

| ID | Invariant |
|----|-----------|
| ONBOARD-001 | Onboarding state is the sole authority for bootstrap permissions |
| ONBOARD-002 | Roles and plans do not apply before COMPLETE |
| ONBOARD-003 | Founders and customers follow identical state transitions |
| ONBOARD-004 | No endpoint may infer onboarding progress |
| ONBOARD-005 | API keys are onboarding artifacts, not permissions |

---

## Key Insight

Before this design:
> "Why does /api/v1/api-keys return 403?"
> "Is auth broken?"

After this design:
> "What onboarding_state is the tenant in?"
> Answer: CREATED (requires IDENTITY_VERIFIED)

The question becomes **answerable**.

---

## Implementation Steps

1. Add `Tenant.onboarding_state` column + default `CREATED`
2. Add pure function `allowed_operations(onboarding_state)`
3. Gate `/api/v1/api-keys` on `IDENTITY_VERIFIED`
4. Re-run onboarding as a user

---

## Out of Scope (v1)

- Rollback / reset
- Recovery states
- Partial onboarding
- Multi-user tenants
- ~~Billing gates~~ → Designed in Phase-6 (not implemented)
- ~~Plan enforcement~~ → Designed in Phase-6 (not implemented)

---

## Phase-4: Force-Complete Endpoint (COMPLETE)

**Status:** COMPLETE
**Date:** 2026-01-12

### Scope

Single escape hatch for founders to bypass onboarding for enterprise customers.

### Implementation

- **Endpoint:** `POST /fdr/onboarding/force-complete`
- **Guard:** `verify_fops_token` (founder-only)
- **Audit:** Mandatory audit event before transition
- **Target:** Always `COMPLETE` (fixed target)

### Key Files

| File | Purpose |
|------|---------|
| `app/api/founder_onboarding.py` | Force-complete endpoint |
| `app/auth/console_auth.py` | Founder token verification |
| `tests/api/test_founder_onboarding_force_complete.py` | 16 tests |

### Hard Constraints (Phase-4)

- Founder-only (RBAC enforced)
- Explicit justification required (min 10 chars)
- Fully audited (action fails if audit fails)
- Forward-only (advances to COMPLETE, never backward)

---

## Phase-5: Post-Onboarding Permissions & Roles (COMPLETE)

**Status:** COMPLETE
**Date:** 2026-01-12

### Design Decision

**Dependency-based role enforcement** (not middleware).

Rationale: Explicit, reviewable, CI-scannable. Endpoints must declare authorization.

### Role Hierarchy

```
OWNER (4)  → Full control of tenant
ADMIN (3)  → Manage config, users
MEMBER (2) → Operate product
VIEWER (1) → Read-only
```

### Design Invariants (LOCKED)

| ID | Invariant |
|----|-----------|
| ROLE-001 | Roles do not exist before onboarding COMPLETE |
| ROLE-002 | Permissions are derived, not stored |
| ROLE-003 | Human roles never affect machine scopes |
| ROLE-004 | Console origin never grants authority |
| ROLE-005 | Role enforcement never mutates state |

### Key Files

| File | Purpose |
|------|---------|
| `app/auth/tenant_roles.py` | TenantRole enum + permission derivation |
| `app/auth/role_guard.py` | `require_role()` dependency |
| `app/api/policy_proposals.py` | First guarded endpoints (approve/reject) |
| `scripts/ops/check_role_guards.py` | CI guard scanner |
| `tests/auth/test_role_guard.py` | 28 tests |

### Permission Model

Permissions are **derived** from roles at runtime, never stored in DB.

```python
ROLE_PERMISSIONS = {
    TenantRole.VIEWER: frozenset({
        "runs:read", "policies:read", "agents:read", ...
    }),
    TenantRole.MEMBER: frozenset({
        # All VIEWER + write permissions
        "runs:write", "policies:write", "agents:write", ...
    }),
    TenantRole.ADMIN: frozenset({
        # All MEMBER + management permissions
        "users:manage", "api_keys:manage", "tenant:write", ...
    }),
    TenantRole.OWNER: frozenset({
        # All ADMIN + billing management
        "billing:manage",
    }),
}
```

### Usage Pattern

```python
from app.auth.role_guard import require_role
from app.auth.tenant_roles import TenantRole

@router.post("/{proposal_id}/approve")
async def approve_proposal(
    request: Request,
    proposal_id: str,
    role: TenantRole = Depends(require_role(TenantRole.MEMBER, TenantRole.ADMIN, TenantRole.OWNER)),
):
    ...
```

### CI Guard Scanner

`scripts/ops/check_role_guards.py` enforces:
- All POST/PUT/PATCH/DELETE under /api/v1/* must have role guards
- Exceptions must be explicitly allowlisted with justification
- Failure = CI hard fail

**Current Status:** Scanner detected 266 unguarded endpoints (baseline). Guards will be added incrementally.

---

## Test Hygiene (HYGIENE-001)

**Status:** LOCKED

> No test may assert behavior that the architecture already forbids structurally.

### Banned Terms (in new Phase-5 tests)

| Banned | Replacement |
|--------|-------------|
| permission | role or role-derived permission |
| admin user | user with ADMIN role |
| superuser | founder (separate auth) |
| console access | UI surface |
| bypass (role context) | explicit exception |

### CI Enforcement

- `scripts/ci/check_test_terminology.py` - Warns on banned terms
- `scripts/ops/check_role_guards.py` - Fails on unguarded endpoints

### Documentation

- `tests/TESTING.md` - Test architecture guide (LOCKED)

---

## Phase-6: Billing, Plans & Limits (DESIGN-ONLY)

**Status:** DESIGN LOCKED (No implementation)
**Date:** 2026-01-12
**Reference:** `docs/architecture/PHASE_6_BILLING_LIMITS.md`

### Prime Directive

> **Billing never blocks onboarding.**
> **Limits never block identity or setup.**

### Dependency

Phase-6 applies **only if** `tenant.onboarding_state == COMPLETE`.

Before COMPLETE:
- Billing APIs return neutral placeholders
- Limits are not enforced
- Usage is tracked but not blocked

### Design Invariants (LOCKED)

| ID | Invariant |
|----|-----------|
| BILLING-001 | Billing never blocks onboarding |
| BILLING-002 | Limits are derived, not stored |
| BILLING-003 | Billing state does not affect roles |
| BILLING-004 | No billing mutation without audit |
| BILLING-005 | Mock provider must satisfy same interface as real provider |

### Billing State Model

```
BillingState:
  TRIAL      → Default after COMPLETE
  ACTIVE     → Valid paid plan
  PAST_DUE   → Payment issue, grace period
  SUSPENDED  → Usage blocked, data intact
```

### Plan Model (Abstract)

```
Plan:
  id: string
  name: string
  tier: enum (FREE, PRO, ENTERPRISE)
  limits_profile: string
```

No prices. No currency. No gateway IDs. Those are Phase-7+.

### Explicit Non-Goals (Phase-6)

- No pricing math
- No subscriptions
- No coupons / proration / invoices
- No taxes
- No gateway webhooks

### Implementation Sequence (When Ready)

1. Create `BillingState` enum
2. Create `Plan` model (no DB)
3. Create `Limits` derivation (code only)
4. Create `MockBillingProvider`
5. Create read-only APIs
6. Add tests (no gateway)

---

## Phase-7: Abuse & Protection Layer (DESIGN-ONLY)

**Status:** DESIGN LOCKED (No implementation)
**Date:** 2026-01-12
**Reference:** `docs/architecture/PHASE_7_ABUSE_PROTECTION.md`

### Prime Directive

> **Abuse protection constrains behavior, not identity.**

This layer never authenticates, authorizes, mutates onboarding, assigns roles, or changes billing state.

### Protection Dimensions

| Dimension       | Scope         | Example          |
| --------------- | ------------- | ---------------- |
| Rate limits     | Time-based    | 1000 req/min     |
| Burst control   | Short window  | 100 req/sec      |
| Cost guards     | Value-based   | $500/day compute |
| Anomaly signals | Pattern-based | Sudden 10x jump  |

### Decision Outcomes (Finite, Locked)

| Outcome  | Meaning             |
| -------- | ------------------- |
| ALLOW    | Proceed             |
| THROTTLE | Delay / slow        |
| REJECT   | Hard stop           |
| WARN     | Allow + emit signal |

### Design Invariants (LOCKED)

| ID | Invariant |
|----|-----------|
| ABUSE-001 | Protection does not affect onboarding, roles, or billing state |
| ABUSE-002 | All enforcement outcomes are explicit (no silent failure) |
| ABUSE-003 | Anomaly detection never blocks user traffic |
| ABUSE-004 | Protection providers are swappable behind a fixed interface |
| ABUSE-005 | Mock provider must be behavior-compatible with real provider |

### Explicit Non-Goals (Phase-7)

- No ML models
- No adaptive pricing
- No auto-suspension
- No cross-tenant scoring
- No blacklists / IP blocking

### Implementation Sequence (When Ready)

1. Create `Decision` enum
2. Create `AbuseProtectionProvider` protocol
3. Create `MockAbuseProtectionProvider`
4. Create middleware integration
5. Add tests (deterministic)

---

## Phase-8: Observability Unification (DESIGN-ONLY)

**Status:** DESIGN LOCKED (No implementation)
**Date:** 2026-01-12
**Reference:** `docs/architecture/PHASE_8_OBSERVABILITY_UNIFICATION.md`

### Prime Directive

> **Observability answers "what happened?" — never "what should happen?"**

Phase-8 records truth, correlates signals, and preserves causality. It does not enforce, alert, or mutate state.

### Core Concept

All system signals become **unified events**:
- Append-only
- Immutable
- Tenant-scoped
- Temporally ordered

### Event Sources

| Source | Events |
|--------|--------|
| Onboarding | `onboarding_state_transition`, `onboarding_force_complete` |
| Billing | `billing_state_changed`, `billing_limit_evaluated` |
| Protection | `protection_decision`, `protection_anomaly_detected` |
| Auth | `role_violation`, `unauthorized_access_attempt` |

### Design Invariants (LOCKED)

| ID | Invariant |
|----|-----------|
| OBSERVE-001 | Observability never mutates system state |
| OBSERVE-002 | Events are immutable once accepted |
| OBSERVE-003 | All events are tenant-scoped |
| OBSERVE-004 | Failure to emit must not block execution |
| OBSERVE-005 | Mock provider must be interface-compatible with real provider |

### Explicit Non-Goals (Phase-8)

- No dashboards
- No alerting / paging
- No SLAs / SLOs
- No metrics math
- No UI endpoints
- No external integrations

### Implementation Sequence (When Ready)

1. Create `UnifiedEvent` model
2. Create `ObservabilityProvider` protocol
3. Create `MockObservabilityProvider`
4. Create emitter helpers for each source
5. Wire emitters into existing systems
6. Add tests (deterministic, correlation)

---

## Related PINs

- PIN-398: Auth Design Sanitization
- PIN-377: Console-Clerk Auth Unification
- PIN-271: RBAC Architecture Directive

---

## Phase-6 & Phase-7 Mock Implementation (COMPLETE)

**Status:** COMPLETE
**Date:** 2026-01-12

### Implementation Summary

Both mock providers implemented together per Option 3 (one clean thaw).

### Phase-6 Files Created

| File | Purpose |
|------|---------|
| `app/billing/__init__.py` | Package exports |
| `app/billing/state.py` | BillingState enum |
| `app/billing/plan.py` | Plan model (no DB) |
| `app/billing/limits.py` | Limits derivation (code only) |
| `app/billing/provider.py` | BillingProvider protocol + MockBillingProvider |
| `app/billing/dependencies.py` | FastAPI dependencies for billing context |

### Phase-7 Files Created

| File | Purpose |
|------|---------|
| `app/protection/__init__.py` | Package exports |
| `app/protection/decisions.py` | Decision enum, ProtectionResult, AnomalySignal |
| `app/protection/provider.py` | AbuseProtectionProvider protocol + MockAbuseProtectionProvider |
| `app/protection/dependencies.py` | FastAPI dependencies for protection context |

### Tests Added

| Test File | Count | Purpose |
|-----------|-------|---------|
| `tests/billing/test_mock_billing_provider.py` | 35 | Phase-6 billing tests |
| `tests/protection/test_mock_protection_provider.py` | 39 | Phase-7 protection tests |
| `tests/e2e/test_phase6_7_e2e_validation.py` | 23 | E2E validation checklist |
| **Total** | **97** | All passing |

### E2E Validation Checklist (COMPLETE)

- [x] Tenant CREATED
- [x] Complete onboarding (all states)
- [x] Verify TRIAL billing state (mock)
- [x] Hit a limit → observe correct failure
- [x] Force-complete still works
- [x] Roles unchanged throughout

### Cross-Phase Invariant Checks (COMPLETE)

- [x] No role logic assumes billing state
- [x] No role derives from plan tier
- [x] No onboarding path references billing
- [x] Force-complete does not set billing state
- [x] TRIAL assigned after COMPLETE, not during
- [x] Protection does not affect auth, onboarding, or roles
- [x] Protection reads billing state but never writes
- [x] Anomaly signals are non-blocking

---

## Next Action

**Freeze Exit Criteria Met:**
- [x] Both mock providers exist
- [x] Both satisfy their interface contracts
- [x] E2E checklist passes
- [x] No frozen file modified without PIN
- [x] No invariant added or weakened

**Next Phase Options:**
1. **Phase-8 Observability** - Unify signals and dashboards
2. **Production Wiring** - Enable protection middleware on SDK endpoints
3. **Billing Read APIs** - Implement customer-facing billing status endpoints

**Background Work:**
- Incrementally add role guards to remaining 266 unprotected endpoints as they are modified
