# Design Freeze — Phases 4–9

**Status:** ACTIVE
**Effective:** 2026-01-12
**Scope:** Onboarding, Roles, Billing, Abuse Protection, Observability, Lifecycle
**Reference:** PIN-399, PIN-400

---

## Freeze Declaration

> Phases 4–9 are design-complete. Phases 6-9 mocks implemented.

This freeze exists to:
1. Catch emergent contradictions between phases
2. Prevent billing from leaking into auth/onboarding
3. Validate mental model continuity before implementation

---

## Frozen Files (Read-Only by Policy)

These files must not change without explicit PIN reference and design review:

### Onboarding (Phase-4)

```
backend/app/auth/onboarding_state.py
backend/app/auth/onboarding_gate.py
backend/app/hoc/cus/account/L5_schemas/onboarding_enums.py
backend/app/hoc/cus/account/L5_engines/onboarding_engine.py
backend/app/hoc/cus/account/L6_drivers/onboarding_driver.py
backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py
backend/app/hoc/api/fdr/incidents/founder_onboarding.py
```

### Roles (Phase-5)

```
backend/app/auth/role_guard.py
backend/app/auth/tenant_roles.py
```

### Billing Design (Phase-6)

```
docs/architecture/PHASE_6_BILLING_LIMITS.md
```

### Abuse Protection Design (Phase-7)

```
docs/architecture/PHASE_7_ABUSE_PROTECTION.md
```

### Observability Design (Phase-8)

```
docs/architecture/PHASE_8_OBSERVABILITY_UNIFICATION.md
```

### Lifecycle (Phase-9)

```
backend/app/hoc/cus/account/L5_schemas/tenant_lifecycle_state.py
backend/app/hoc/cus/hoc_spine/authority/lifecycle_provider.py
backend/app/hoc/api/fdr/account/founder_lifecycle.py
```

---

## Frozen Invariants

### Onboarding (ONBOARD-001 to ONBOARD-005)

| ID | Invariant |
|----|-----------|
| ONBOARD-001 | Onboarding state is the sole authority for bootstrap permissions |
| ONBOARD-002 | Roles and plans do not apply before COMPLETE |
| ONBOARD-003 | Founders and customers follow identical state transitions |
| ONBOARD-004 | No endpoint may infer onboarding progress |
| ONBOARD-005 | API keys are onboarding artifacts, not permissions |

### Roles (ROLE-001 to ROLE-005)

| ID | Invariant |
|----|-----------|
| ROLE-001 | Roles do not exist before onboarding COMPLETE |
| ROLE-002 | Permissions are derived, not stored |
| ROLE-003 | Human roles never affect machine scopes |
| ROLE-004 | Console origin never grants authority |
| ROLE-005 | Role enforcement never mutates state |

### Billing (BILLING-001 to BILLING-005)

| ID | Invariant |
|----|-----------|
| BILLING-001 | Billing never blocks onboarding |
| BILLING-002 | Limits are derived, not stored |
| BILLING-003 | Billing state does not affect roles |
| BILLING-004 | No billing mutation without audit |
| BILLING-005 | Mock provider must satisfy same interface as real provider |

### Abuse Protection (ABUSE-001 to ABUSE-005)

| ID | Invariant |
|----|-----------|
| ABUSE-001 | Protection does not affect onboarding, roles, or billing state |
| ABUSE-002 | All enforcement outcomes are explicit (no silent failure) |
| ABUSE-003 | Anomaly detection never blocks user traffic |
| ABUSE-004 | Protection providers are swappable behind a fixed interface |
| ABUSE-005 | Mock provider must be behavior-compatible with real provider |

### Observability (OBSERVE-001 to OBSERVE-005)

| ID | Invariant |
|----|-----------|
| OBSERVE-001 | Observability never mutates system state |
| OBSERVE-002 | Events are immutable once accepted |
| OBSERVE-003 | All events are tenant-scoped |
| OBSERVE-004 | Failure to emit must not block execution |
| OBSERVE-005 | Mock provider must be interface-compatible with real provider |

### Lifecycle (OFFBOARD-001 to OFFBOARD-010)

| ID | Invariant |
|----|-----------|
| OFFBOARD-001 | Lifecycle transitions are monotonic |
| OFFBOARD-002 | TERMINATED is irreversible |
| OFFBOARD-003 | ARCHIVED is unreachable from ACTIVE |
| OFFBOARD-004 | No customer-initiated offboarding mutations |
| OFFBOARD-005 | All API keys must be revoked on TERMINATED |
| OFFBOARD-006 | SDK execution must be blocked before termination completes |
| OFFBOARD-007 | No new auth tokens after TERMINATED |
| OFFBOARD-008 | Offboarding emits unified observability events |
| OFFBOARD-009 | Observability never blocks offboarding |
| OFFBOARD-010 | All offboarding actions are auditable |

---

## Cross-Phase Invariant Checks (COMPLETE)

Verified on 2026-01-12 via `tests/e2e/test_phase6_7_e2e_validation.py`.

### Phase-5 ↔ Phase-6

- [x] No role logic assumes billing state
- [x] No role derives from plan tier
- [x] `require_role()` has no billing dependency

### Phase-4 ↔ Phase-6

- [x] No onboarding path references billing
- [x] Force-complete does not set billing state
- [x] TRIAL is assigned *after* COMPLETE, not during

### Phase-5 ↔ Phase-4

- [x] Roles only exist after COMPLETE (ROLE-001)
- [x] Force-complete does not grant roles
- [x] Role guard checks onboarding state (defense in depth)

### Phase-7 ↔ All Previous

- [x] Protection does not affect auth, onboarding, or roles
- [x] Protection reads billing state but never writes
- [x] Anomaly signals are non-blocking
- [x] Decision outcomes are explicit (no silent failure)

### Phase-8 ↔ All Previous (COMPLETE)

Verified on 2026-01-12 via `tests/e2e/test_phase8_observability_e2e.py`.

- [x] Observability never mutates any system state
- [x] Events from all sources share unified schema
- [x] Emit failures never block main operations
- [x] Query results are tenant-scoped only

### Phase-9 ↔ All Previous (COMPLETE)

Verified on 2026-01-12 via `tests/e2e/test_phase9_lifecycle_e2e.py`.

- [x] Lifecycle does not affect onboarding state (semantic mapping only)
- [x] Lifecycle does not affect roles
- [x] Lifecycle reads billing but never writes
- [x] Lifecycle reads protection but never writes
- [x] Lifecycle emits observability events (non-blocking)
- [x] TERMINATED is irreversible
- [x] ARCHIVED is unreachable from ACTIVE
- [x] Customer cannot initiate lifecycle mutations

---

## What's Allowed During Freeze

| Action | Allowed? |
|--------|----------|
| Bug fixes in frozen files | Yes (with PIN reference) |
| Test additions | Yes |
| Documentation improvements | Yes |
| Role guards on new endpoints | Yes |
| New billing code | **No** |
| Billing state mutations | **No** |
| Onboarding shortcuts | **No** |
| Role derivation changes | **No** |
| New abuse protection code | **No** (until approved) |
| Auto-blocking protection | **No** |
| Phase-8 mock implementation | Yes (approved) |
| Observability event emission | Yes (non-blocking) |
| Dashboards / alerting | **No** (Phase-9+) |

---

## Freeze Exit Criteria (MET)

Freeze can end when approved. All criteria met:

1. [x] Cross-phase invariant checks pass (2026-01-12)
2. [x] E2E validation complete (294 tests passing, 4485 total)
3. [x] Mock providers implemented (Phase-6 + Phase-7 + Phase-8 + Phase-9)
4. [x] Runtime gates implemented (A1 complete)

---

## E2E Validation Checklist (COMPLETE)

Validated on 2026-01-12. All tests pass (269 total).

### Phase 6-7 Checklist
- [x] Tenant CREATED
- [x] Complete onboarding (all states)
- [x] Verify TRIAL billing state (mock)
- [x] Hit a limit → observe correct failure
- [x] Force-complete still works
- [x] Roles unchanged throughout

### Phase-8 Checklist
- [x] Observability never mutates system state
- [x] Events from all sources share unified schema
- [x] Emit failures never block main operations
- [x] Query results are tenant-scoped only
- [x] Correlation works across requests (request_id, trace_id)
- [x] Full tenant journey timeline queryable

### Phase-9 Checklist
- [x] Lifecycle states are monotonic
- [x] TERMINATED is irreversible
- [x] ARCHIVED unreachable from ACTIVE
- [x] Customer cannot initiate mutations
- [x] API key revocation callback works
- [x] Worker blocking callback works
- [x] Observability events emitted on transitions
- [x] Observability failure non-blocking
- [x] Full tenant journey (ACTIVE → SUSPENDED → ACTIVE → TERMINATED → ARCHIVED)

**Test Files:**
- `tests/billing/test_mock_billing_provider.py` (35 tests)
- `tests/protection/test_mock_protection_provider.py` (39 tests)
- `tests/e2e/test_phase6_7_e2e_validation.py` (23 tests)
- `tests/observability/test_mock_observability_provider.py` (38 tests)
- `tests/e2e/test_phase8_observability_e2e.py` (15 tests)
- `tests/lifecycle/test_mock_lifecycle_provider.py` (59 tests)
- `tests/e2e/test_phase9_lifecycle_e2e.py` (24 tests)
- `tests/architecture/test_layer_boundaries.py` (9 tests)
- `tests/middleware/test_runtime_gates.py` (25 tests)

---

## Track A: Production Wiring (ACTIVE)

### A1: Runtime Gates (COMPLETE)

Implemented on 2026-01-12 per PIN-401.

**New Files:**
```
backend/app/api/middleware/__init__.py
backend/app/api/middleware/lifecycle_gate.py
backend/app/api/middleware/protection_gate.py
backend/app/api/middleware/billing_gate.py
tests/middleware/test_runtime_gates.py (25 tests)
```

**Gate Enforcement:**
- Lifecycle Gate: Enforces TenantLifecycleState at request boundaries (403)
- Protection Gate: Applies AbuseProtectionProvider decisions (429/503)
- Billing Gate: Enforces billing state and limits (402)

All gates respect exempt paths (/health, /fdr/, /docs, etc.)
BILLING-001 preserved: Billing never blocks onboarding.

### A2-A4: Pending

| Track | Task | Status |
|-------|------|--------|
| A2 | Observability Sink Wiring | PENDING |
| A3 | Kill-Switch & Safety Nets | PENDING |
| A4 | Silent Production Dry Run | PENDING |

---

## Track C: Org Expansion Design (COMPLETE)

### Phase-10 Design Document

Created on 2026-01-12 per PIN-401 Track C (design only, no code).

**Design Document:**
```
backend/docs/design/PHASE-10-ORG-EXPANSION-DESIGN.md
```

**Key Concepts:**
- Organization as billing anchor
- OrganizationMembership separate from TenantMembership
- ORG-001: TenantMembership is ONLY source of tenant access
- ORG-002: Every tenant has exactly one billing anchor
- ORG-003: Org-tenant attachment is one-way
- ORG-004: OrgRole and TenantRole are independent

**Critical Invariant:**
> Tenant is the execution boundary. Org is the billing boundary.

---

## Production Readiness Failure Audit (COMPLETE)

Created on 2026-01-12 per PIN-401.

**Audit Document:**
```
backend/docs/design/PRODUCTION-READINESS-FAILURE-AUDIT.md
```

**Key Findings:**

| Provider | Failure Impact | Current Mitigation | Gap |
|----------|---------------|-------------------|-----|
| Lifecycle | HIGH | Mock returns ACTIVE | No metrics |
| Billing | MEDIUM | Mock returns TRIAL | No cache |
| Protection | MEDIUM | Mock allows | No circuit breaker |
| Observability | LOW | Logs locally | Lost events uncounted |

**Recommended Actions:**
- Add circuit breakers (3-5 failure threshold)
- Add explicit timeouts (100-500ms)
- Add metrics for gate decisions
- All gates fail-open (except auth)

---

## Next Phase Preview

### Phase-10: Production Wiring

With Phases 4-9 complete (mocks implemented), the next phase focuses on:

- Production observability storage (Postgres, ClickHouse, etc.)
- Real billing gateway integration
- Production protection middleware
- Real lifecycle triggers (billing, abuse, compliance)
- Dashboards and alerting

Phase-10 is **production integration**, not design. It builds on the frozen mock foundation.

---

## Change Request Process (During Freeze)

Any change to frozen files must:

1. Reference a specific PIN
2. State which invariant is affected
3. Explain why change is necessary
4. Get explicit approval before merge

Template:

```
FREEZE CHANGE REQUEST

PIN Reference: PIN-XXX
Frozen File: backend/app/auth/role_guard.py
Invariant Affected: ROLE-002
Reason: [explanation]
Approval: [pending/approved]
```

---

## Related Documents

- PIN-399: Onboarding State Machine (master PIN)
- PIN-400: Offboarding & Tenant Lifecycle (Phase-9)
- PHASE_6_BILLING_LIMITS.md: Billing design
- LAYER_MODEL.md: Function-Route separation (enforced by CI)
- tests/TESTING.md: Test architecture
