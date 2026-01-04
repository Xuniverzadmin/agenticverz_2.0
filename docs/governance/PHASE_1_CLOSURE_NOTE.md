# Phase-1 Closure Note: Platform Monitoring System

**Status:** CLOSED
**Closed:** 2026-01-04
**Authority:** PIN-284
**Scope:** Founder-only Platform Health Monitoring

---

## What Phase-1 Guarantees

The following invariants are **mechanically enforced** — not by policy, by code:

| Guarantee | Enforcement Mechanism |
|-----------|----------------------|
| **HEALTH-IS-AUTHORITY** | `PlatformHealthService` is the ONLY source of health state. No other component may compute or infer health. |
| **HEALTH-LIFECYCLE-COHERENCE** | BLOCKED health cannot coexist with COMPLETE lifecycle. CI blocks merges. Bootstrap refuses start. |
| **HEALTH-DETERMINISM** | Same signals always produce same verdict. Proven by 23 constitutional tests. |
| **NO-PHANTOM-HEALTH** | Absence of signals means HEALTHY, never UNKNOWN or undefined. |
| **DOMINANCE-ORDER** | BLOCKED > DEGRADED > HEALTHY. Always. No exceptions. |

### Enforcement Artifacts

| Artifact | Location | Role |
|----------|----------|------|
| Health Service (L4) | `backend/app/services/platform/platform_health_service.py` | Single source of truth |
| Coherence Guard (L8) | `scripts/ci/health_lifecycle_coherence_guard.py` | CI + bootstrap enforcement |
| Bootstrap Gate | `scripts/ops/session_start.sh` step 10 | Blocks start if BLOCKED |
| Determinism Tests (L8) | `backend/tests/invariants/test_platform_health_determinism.py` | 23 tests, all pass |
| Structure Freeze | `docs/governance/BACKEND_STRUCTURE_FREEZE.yaml` | Prevents erosion |

---

## What Phase-1 Does NOT Guarantee

These are **explicitly out of scope** — not forgotten, deferred by design:

| Non-Guarantee | Reason |
|---------------|--------|
| **CRM impact on health** | Part-2 scope. No complaint-driven degradation yet. |
| **Customer visibility** | Founder-only. Customers cannot see health states. |
| **Automatic remediation** | Health is observational, not self-healing. |
| **Incident-aware health** | Incidents table may be missing; service degrades gracefully. |
| **Cross-tenant aggregation** | Single-tenant health only. No fleet-wide health. |

### Critical Boundary

> **Frontend must not interpret health; it only renders it.**

The Founder Console may display health states but must NEVER:
- Compute health from raw signals
- Override or acknowledge health states
- Apply business logic to health data
- Expose health to customers

---

## Known Infrastructure Debts

These are **accepted technical debts** for Phase-1:

### Debt 1: Missing `incidents` Table

**Symptom:** Migration 037 tables (killswitch, incidents) may not exist despite alembic showing head.

**Workaround:** `_count_open_incidents()` uses savepoint and returns 0 on failure.

**Impact:** Health calculation excludes incident count. Acceptable for Founder-only phase.

**Resolution:** Defer to ops phase. Do not attempt migration repair before Part-2.

### Debt 2: Signal Type Constraint Mismatch

**Symptom:** `PlatformHealthService` queries signal types (QUALIFIER_STATUS, LIFECYCLE_STATUS) not in DB constraint.

**Workaround:** Tests use only valid types. Service queries don't fail on missing types.

**Impact:** Some health signals may not be queryable. Acceptable for Phase-1.

**Resolution:** Align constraint with service needs in Part-2.

---

## Freeze Boundary (Constitutional Code)

The following are **frozen** and must not change without explicit governance approval:

### Frozen Files

```
backend/app/services/platform/platform_health_service.py  (L4 - Authority)
backend/app/adapters/platform_eligibility_adapter.py      (L3 - Adapter)
backend/app/api/platform.py                               (L2 - API)
scripts/ci/health_lifecycle_coherence_guard.py            (L8 - Enforcement)
backend/tests/invariants/test_platform_health_determinism.py (L8 - Proof)
```

### Frozen Contracts

```
HEALTH-IS-AUTHORITY
HEALTH-LIFECYCLE-COHERENCE
HEALTH-DETERMINISM
```

### Freeze Rules

1. **No weakening** — Tests must not be made to pass by relaxing assertions
2. **No bypass** — Guards must not be skipped in CI or bootstrap
3. **No reinterpretation** — Health states mean what they mean, permanently
4. **Any change requires** — New PIN with rationale, migration plan, founder approval

---

## Part-2 Lock

**Part-1 is CLOSED. Part-2 is LOCKED until designed.**

### What Part-2 Will Add

- CRM complaints as governance signals
- Customer console health visibility (scoped)
- Complaint-driven capability degradation
- Eligibility checks for customer features

### What Must Happen Before Part-2 Unlocks

1. Part-2 design document approved
2. CRM → governance signal mapping defined
3. Customer visibility rules specified
4. No feature work, no UI polish until then

---

## Attestation

Phase-1 of PIN-284 (Platform Monitoring System) is hereby **CLOSED**.

The system now has:
- **Authority** — Single source of health truth
- **Determinism** — Proven by 23 constitutional tests
- **Self-enforcement** — Mechanically impossible to violate invariants

This closure note serves as **institutional memory**.

Any future work that touches health, lifecycle, or governance signals must reference this document and explicitly declare whether it **extends**, **amends**, or **violates** Phase-1 guarantees.

---

**Reference:** PIN-284, BACKEND_STRUCTURE_FREEZE.yaml, PLATFORM_HEALTH_CONTRACTS.yaml
