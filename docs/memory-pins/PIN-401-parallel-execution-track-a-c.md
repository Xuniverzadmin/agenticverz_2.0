# PIN-401: Parallel Execution Plan — Track A + Track C

**Status:** ACTIVE
**Created:** 2026-01-12
**Phase:** Post Phase-9 (Lifecycle Complete)
**Reference:** PIN-399, PIN-400, FREEZE.md

---

## Summary

Parallel execution of production wiring (Track A) and org expansion design (Track C), with strict decoupling. Track A leads and ships. Track C is design-only until proven safe.

---

## Foundation (Frozen)

Phases 4-9 are complete with 269 tests passing:

| Phase | Domain | Status |
|-------|--------|--------|
| 4 | Onboarding | FROZEN |
| 5 | Roles | FROZEN |
| 6 | Billing | FROZEN (mock) |
| 7 | Protection | FROZEN (mock) |
| 8 | Observability | FROZEN (mock) |
| 9 | Lifecycle | FROZEN (mock) |

---

## TRACK A — Production Wiring

**Goal:** Turn the already-correct system into a live, observable, enforceable system WITHOUT changing behavior.

**Rule:** Track A is pure wiring. No new states. No new permissions. No new logic.

### A1. Runtime Gates Activation

Wire what already exists:

**Lifecycle Gate**
- Enforce `TenantLifecycleState` on:
  - SDK execution (`allows_sdk_execution()`)
  - Token refresh (`allows_token_refresh()`)
  - Background workers (`allows_writes()`)

**Protection Gate**
- Apply `AbuseProtectionProvider` decisions to SDK paths
- Use existing `check_all()` at execution boundaries

**Billing Gate**
- Apply `Limits.derive()` at execution boundaries
- Still mock → behavior identical, but path exercised

**Invariants Preserved:**
- OBSERVE-004 (non-blocking observability)
- OFFBOARD-002 (termination irreversible)

### A2. Observability Sink Wiring

Keep Phase-8 guarantees intact.

- Plug `ObservabilityProvider` into:
  - Log sink
  - Columnar store / event DB
- Enable query-only access for internal consoles:
  - preflight-agenticverz.com
  - preflight-fops.com

**Hard Rule:**
- No dashboards
- No alerts
- No customer exposure

Just truth.

### A3. Kill-Switch & Safety Nets

Production safety mechanisms:

- Global disable flags (env-only, founder-only)
- Rate-limit ceilings (even with mock)
- Emergency lifecycle override (force-complete / terminate)

Nothing new — just surfaced.

### A4. Silent Production Dry Run

- Onboard real tenants
- Do NOT explain the system
- Watch:
  - Onboarding stalls
  - Lifecycle transitions
  - Protection decisions
  - Billing limit hits

If something breaks → observe, not patch.

---

## TRACK C — Org Expansion (Design Only)

**Goal:** Ensure current system does not block future org/multi-user support.

**Rule:** Track C MUST NOT modify runtime code yet.

### C1. Org Model Draft (Design Only)

Concepts without implementation:

```
Organization
 ├─ org_id
 ├─ billing_anchor
 └─ tenants[]

OrganizationMembership
 ├─ user_id
 ├─ org_id
 └─ org_role
```

**Critical Rules:**
- `TenantMembership` stays primary
- Org does NOT replace tenant auth
- No auth changes

### C2. Role Inheritance Rules (Design Only)

Define but don't implement:

- Org role → default tenant role
- Tenant role can override org role
- Founder role remains separate

This sits ABOVE Phase-5, not inside it.

### C3. Org Lifecycle Mapping (Design Only)

Explicit mapping (no code):

```
Org ACTIVE
 ├─ Tenant A ACTIVE
 ├─ Tenant B SUSPENDED
 └─ Tenant C TERMINATED
```

**Rules:**
- Org state never mutates tenant history
- Tenant lifecycle remains authoritative

### C4. Org Offboarding Thought Exercise

Answer before coding:

- What happens if org is terminated?
- What happens to tenant archives?
- Who owns data retention?

Document only.

---

## Coordination Rules (CRITICAL)

| Rule | Meaning |
|------|---------|
| Track A can ship | Track C cannot |
| Track A modifies wiring | Track C modifies docs only |
| No shared files | Zero |
| No enum reuse | Ever |
| No "just add this now" | Forbidden |

---

## Success Criteria

### After Track A

- System runs end-to-end
- Every action is observable
- Every failure is explainable
- No founder intervention needed

### After Track C

- Can add orgs later WITHOUT refactoring
- No regrets baked into auth or lifecycle
- Zero pressure to "just hack it"

---

## Immediate Next Steps

**Next 48 hours:**

1. Start A1: lifecycle + protection + billing gates
2. Start C1: org model design doc (no code)

---

## Files (Track A - To Be Created)

```
backend/app/api/middleware/lifecycle_gate.py
backend/app/api/middleware/protection_gate.py
backend/app/api/middleware/billing_gate.py
```

## Files (Track C - Design Only)

```
docs/architecture/PHASE_10_ORG_EXPANSION.md
```

---

## Related Documents

- PIN-399: Onboarding State Machine
- PIN-400: Offboarding & Tenant Lifecycle
- FREEZE.md: Design freeze status
- LAYER_MODEL.md: Function-Route separation

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Initial creation after Phase-9 completion |
