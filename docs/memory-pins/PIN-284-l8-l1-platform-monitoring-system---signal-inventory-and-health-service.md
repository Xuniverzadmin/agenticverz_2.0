# PIN-284: L8-L1 Platform Monitoring System - Signal Inventory and Health Service

**Status:** ✅ PHASE_1_CLOSED (Ratified 2026-01-04)
**Closure Note:** `docs/governance/PHASE_1_CLOSURE_NOTE.md`
**Created:** 2026-01-04
**Updated:** 2026-01-04
**Category:** Architecture / Platform Monitoring

---

## Summary

Documents the L8→L1 signal inventory findings and tracks implementation of platform_health_service (L4) to bridge monitoring signals to governance enforcement. Phase 1 (Founder-only Platform Monitoring) is COMPLETE.

---

## Details

## Overview

This PIN tracks the Platform Monitoring System implementation, starting with the signal inventory and proceeding to the platform_health_service (L4) that converts runtime signals into governance-actionable states.

## Signal Inventory Findings (2026-01-04)

### What Exists

| Layer | Signals Found | Status |
|-------|--------------|--------|
| L8 | CI guards, validators, contract tests | ✅ Enforced |
| L7 | Health endpoints, session checks | ✅ Exposed |
| L6 | Incidents, errors, traces, events | ✅ Persisted |
| L5 | Error envelope, workers | ✅ Complete |
| L4 | Domain services | ⚠️ No interpretation layer |
| L3 | Customer adapters | ⚠️ No eligibility adapter |
| L2 | API endpoints | ⚠️ No health/eligibility APIs |

### Critical Gaps Identified

1. **INTERPRETATION-GAP**: No L4 service converts runtime signals to governance states
2. **ELIGIBILITY-GAP**: No eligibility service consuming health signals
3. **CRM-GAP**: No CRM/complaint system feeding governance
4. **DEGRADATION-GAP**: Incidents don't trigger capability degradation
5. **HEALTH-DISCONNECT**: /health doesn't feed into governance

### Key Finding

> Signals exist but nobody owns the meaning of the system's health.

## Implementation Plan

### Phase 1: Platform Health Service (L4) ✅ COMPLETE

Created `platform_health_service.py`:
- Aggregates signals from governance_signals table
- Evaluates capability health (HEALTHY/DEGRADED/BLOCKED)
- Feeds into qualifier and lifecycle systems
- **Artifacts:**
  - `backend/app/services/platform/platform_health_service.py` (L4)
  - `backend/app/adapters/platform_eligibility_adapter.py` (L3)
  - `backend/app/api/platform.py` (L2)
  - `docs/governance/PLATFORM_HEALTH_CONTRACTS.yaml`
  - `scripts/ops/record_governance_signal.py` (CLI)

### Phase 1 Completed Items

| Item | Status | Artifact |
|------|--------|----------|
| PlatformHealthService (L4) | ✅ | `services/platform/platform_health_service.py` |
| Signal wiring (BLCA, lifecycle) | ✅ | `session_start.sh`, `record_governance_signal.py` |
| Governance contracts | ✅ | `PLATFORM_HEALTH_CONTRACTS.yaml` |
| Eligibility adapter (L3) | ✅ | `adapters/platform_eligibility_adapter.py` |
| L2 APIs | ✅ | `api/platform.py` |
| Platform events table | ✅ | Uses existing `governance_signals` |
| **Hard Enforcement** | ✅ | `health_lifecycle_coherence_guard.py` |
| **Bootstrap Health Gate** | ✅ | `session_start.sh` step 10 |
| **Health Determinism Tests** | ✅ | `tests/invariants/test_platform_health_determinism.py` |
| **Backend Structure Freeze** | ✅ | `docs/governance/BACKEND_STRUCTURE_FREEZE.yaml` |

### Phase 1 Hard Enforcement (2026-01-04)

The following hard enforcement mechanisms ensure health-lifecycle coherence:

1. **Health-Lifecycle Coherence Guard** (`scripts/ci/health_lifecycle_coherence_guard.py`)
   - Enforces: BLOCKED health state cannot coexist with COMPLETE lifecycle
   - Fails CI if violation detected
   - Fails bootstrap if system health is BLOCKED

2. **Bootstrap Health Gate** (`session_start.sh` step 10)
   - Runs health_lifecycle_coherence_guard.py with --bootstrap flag
   - Refuses session start if health is BLOCKED
   - Logs violation reason for debugging

3. **Governance Invariants Enforced**
   - `HEALTH-IS-AUTHORITY`: PlatformHealthService is the ONLY source of health state
   - `HEALTH-LIFECYCLE-COHERENCE`: BLOCKED + COMPLETE is illegal
   - `LIFECYCLE-DERIVED-FROM-QUALIFIER`: COMPLETE requires QUALIFIED qualifier

4. **Health Determinism Tests** (`tests/invariants/test_platform_health_determinism.py`)
   - **23 constitutional law tests** proving PlatformHealthService is deterministic
   - Tests verify: Idempotence, Order Independence, Dominance, Scope Aggregation, No Phantom Health
   - All tests MUST pass for Phase 1 closure
   - **Test Results (2026-01-04): 23 passed, 0 failed**

5. **Backend Structure Freeze** (`docs/governance/BACKEND_STRUCTURE_FREEZE.yaml`)
   - Declares frozen directories and files
   - Guard script: `scripts/ci/backend_structure_guard.py`
   - Prevents accidental erosion of platform monitoring system
   - Frozen: L4 service, L3 adapter, L2 API, L8 guards and tests

### Phase 1 Constitutional Tests (2026-01-04)

| Test Class | Tests | Invariant |
|------------|-------|-----------|
| TestHealthIdempotence | 4 | Same signals → same verdict |
| TestHealthOrderIndependence | 2 | Signal A then B == B then A |
| TestHealthDominance | 4 | BLOCKED > DEGRADED > HEALTHY |
| TestHealthScopeAggregation | 4 | Capability → Domain → System |
| TestNoPhantomHealth | 4 | No signals → HEALTHY |
| TestEligibilityConsistency | 4 | Eligibility matches health |
| TestHealthDeterminismSummary | 1 | All invariants hold |

### Phase 1 API Endpoints

- `GET /platform/health` - System health overview
- `GET /platform/capabilities` - Capability eligibility list
- `GET /platform/domains/{name}` - Domain health detail
- `GET /platform/capabilities/{name}` - Capability health detail
- `GET /platform/eligibility/{name}` - Quick eligibility check

### Phase 2: CRM Integration (FUTURE)

Add CRM as governance signal source:
- `crm_events` store
- CRM → governance rule mapping
- Complaint-driven degradation

### Phase 3: Customer Exposure (FUTURE)

Expose health to Customer Console:
- Customer-scoped health views
- Eligibility checks for customer features

## Governance Hooks

The platform_health_service MUST feed:
- `QUALIFIER_EVALUATION.yaml` (via evaluate_qualifiers.py)
- `CAPABILITY_LIFECYCLE.yaml` (via lifecycle_qualifier_guard.py)
- Session bootstrap checks

## Success Criteria

### Phase 1 (Founder-only) ✅ COMPLETE WITH HARD ENFORCEMENT & DETERMINISM TESTS

- [x] platform_health_service created (L4)
- [x] Health states derive from governance_signals
- [x] BLCA/lifecycle signals wired to health service
- [x] Eligibility adapter created (L3)
- [x] API endpoints exposed (L2)
- [x] Frontend (Founder Console) can consume health
- [x] **Hard enforcement: health_lifecycle_coherence_guard.py**
- [x] **Bootstrap health gate: session_start.sh step 10**
- [x] **BLOCKED + COMPLETE is mechanically impossible**
- [x] **Health determinism tests: 23 tests pass (L8)**
- [x] **Constitutional invariants proven: idempotence, order independence, dominance**
- [x] **Backend structure freeze: BACKEND_STRUCTURE_FREEZE.yaml**
- [x] **Structure guard: backend_structure_guard.py**

### Phase 2 (CRM + Customer)

- [ ] CRM complaints affect eligibility
- [ ] Customer console can view capability eligibility
- [ ] Unhealthy capabilities automatically downgraded

## Reference

- **PHASE_1_CLOSURE_NOTE.md** — Institutional memory, guarantees, non-guarantees, debts
- **BACKEND_STRUCTURE_FREEZE.yaml** — Frozen files and contracts
- PIN-283: LIFECYCLE-DERIVED-FROM-QUALIFIER Rule
- PIN-282: PIN-281 L2 Promotion Governance Completion
- Signal Inventory: 47+ signals across L8-L2

---

## Related PINs

- [PIN-283](PIN-283-.md)
- [PIN-282](PIN-282-.md)
- [PIN-281](PIN-281-.md)
