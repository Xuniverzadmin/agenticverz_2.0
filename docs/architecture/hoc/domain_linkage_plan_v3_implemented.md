# Domain Linkage Plan v3 — Implementation Report

**Date:** 2026-02-10
**Executed by:** Claude Opus 4.6
**Source plan:** `docs/architecture/hoc/domain_linkage_plan_v3.md`

---

## v2 Recap

**v2 execution** (2026-02-09) validated run-scoped linkage across 5 domains:

| Phase | Status | Details |
|-------|--------|---------|
| A — Schema Verification | PASS 4/4 | All required columns exist |
| B — Data Linkage | PASS 4/4 | All 4 linkage paths resolve |
| C — L4 Coordinators | PASS 1/2 | RunEvidence: PASS; RunProof: GAP (broken `pg_store.py` import) |
| D — Governance Logs | PASS | 3/3 events scoped by `run_id` |

**Blocking gap:** `PostgresTraceStore` had broken imports (`from .models import ...` — no `models.py` in `L6_drivers/`).

---

## PIN-553 Resolution (pre-v3)

PIN-553 closed the RunProof primary import gap:
- `pg_store.py` imports fixed to use `app.hoc.cus.logs.L6_drivers` path
- S6 trigger fixed
- HASH_CHAIN + VERIFIED integrity model confirmed operational

---

## v3 Fix: tenant_id Multi-Tenant Isolation

### Problem

`RunProofCoordinator.get_run_proof()` had `tenant_id` as a parameter but never passed it to `trace_store.get_trace(run_id)`. In production (`PostgresTraceStore`), this breaks multi-tenant isolation — any tenant could read any other tenant's traces.

### Fix

**File:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py` (line 72)

**Before:**
```python
trace = await trace_store.get_trace(run_id)
```

**After:**
```python
try:
    trace = await trace_store.get_trace(run_id, tenant_id=tenant_id)
except TypeError:
    trace = await trace_store.get_trace(run_id)
```

**Why try/except:** `LogsBridge.traces_store_capability()` returns either `PostgresTraceStore` (production, supports `tenant_id`) or `SQLiteTraceStore` (dev, does not). LogsBridge is at 5/5 method limit (PIN-510), so we cannot add a wrapper. The `TypeError` fallback handles dev mode gracefully without modifying LogsBridge.

### Tests Added

**File:** `backend/tests/test_run_introspection_coordinators.py`

| Test | Assertion |
|------|-----------|
| `test_passes_tenant_id_to_trace_store` | `get_trace` called with `tenant_id="tenant-abc"`, returns VERIFIED |
| `test_falls_back_when_store_rejects_tenant_id` | TypeError fallback works, second call without `tenant_id` succeeds |

---

## All-Phase Status

| Phase | Domain | Status | Evidence |
|-------|--------|--------|----------|
| A — Schema Verification | All | **PASS** | 4/4 linkage columns confirmed |
| B — Data Linkage | All | **PASS** | 4/4 run_id paths resolve |
| C — RunEvidence | Activity, Incidents, Policies, Controls | **PASS** | 2 incidents + 3 policies + 1 limit + 3 decisions |
| C — RunProof | Logs | **PASS** | HASH_CHAIN VERIFIED, tenant_id isolation fixed |
| D — Governance Logs | Logs | **PASS** | 3/3 events scoped by run_id |

**All phases: PASS**

---

## Test Output

```
tests/test_run_introspection_coordinators.py::TestRunProofCoordinator::test_returns_verified_with_valid_chain PASSED
tests/test_run_introspection_coordinators.py::TestRunProofCoordinator::test_returns_unsupported_when_no_traces PASSED
tests/test_run_introspection_coordinators.py::TestRunProofCoordinator::test_returns_unsupported_when_no_steps PASSED
tests/test_run_introspection_coordinators.py::TestRunProofCoordinator::test_passes_tenant_id_to_trace_store PASSED
tests/test_run_introspection_coordinators.py::TestRunProofCoordinator::test_falls_back_when_store_rejects_tenant_id PASSED
12 passed in 3.04s
```

Import sanity:
- `PostgresTraceStore`: OK
- `RunProofCoordinator`: OK

---

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| `RunProofCoordinator` passes `tenant_id` to `get_trace()` | **PASS** |
| TypeError fallback handles SQLiteTraceStore (dev mode) | **PASS** |
| Existing 10 tests unaffected | **PASS** (12/12 pass) |
| No new imports or layer violations introduced | **PASS** |
| LogsBridge NOT modified (stays at 5/5) | **PASS** |

---

## Files Modified

| File | Action | Lines Changed |
|------|--------|---------------|
| `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py` | Edit line 72 | +4 |
| `backend/tests/test_run_introspection_coordinators.py` | Add 2 test methods | +64 |
| `docs/architecture/hoc/domain_linkage_plan_v3_implemented.md` | Create (this report) | new |

---

## Pre-Existing CI Notes

CI check 27 (`check_l2_no_direct_l5_l6_imports`) reports 3 pre-existing L2_BYPASS_L4 violations in `app/hoc/api/cus/logs/traces.py` from PIN-553's import path migration (`app.traces` → `app.hoc.cus.logs.L6_drivers`). These are not introduced by v3 and require a separate L4 routing fix (traces_handler wiring).
