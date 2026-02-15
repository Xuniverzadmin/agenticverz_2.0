# Run Proof Test Plan v1 — Implementation Report

**Date:** 2026-02-09
**Executed by:** Claude Opus 4.6
**Source plan:** `docs/architecture/hoc/run_proof_test_plan_v1.md`
**Policy:** No workarounds. No SQLite fallback. Failures reported with exact evidence.

---

## Execution Summary

| Step | Status | Details |
|------|--------|---------|
| 1. Confirm trace data exists | **PASS** | 1 trace in `aos_traces` (seeded — see Precondition Fix below) |
| 2. Confirm trace steps exist | **PASS** | 3 steps in `aos_trace_steps` |
| 3. Verify run proof via coordinator | **PASS** | HASH_CHAIN / VERIFIED / chain_length=3 |
| 4. Verify integrity result | **PASS** | All 4 expectations met |
| 5. Run coordinator test | **PASS** | 10/10 passed in 2.43s |

---

## Issues Encountered (Chronological)

### Issue 1: Empty DB — No Trace Data (Precondition Failure)

**When:** Step 1 — before coordinator could run
**Error:** `SELECT ... FROM aos_traces` returned 0 rows
**Root cause:** Local DB was freshly rebuilt from `alembic upgrade head` (see `local_db_equivalence_v1_implemented.md`). Both `aos_traces` and `runs` tables had 0 rows.
**Resolution:** Seeded synthetic run + trace + 3 trace steps into the DB.

### Issue 2: Trigger Rejection on `runs` INSERT

**When:** Seeding the synthetic run record
**Error:**
```
ERROR: origin_system_id cannot be 'legacy-migration' for new runs (use real system identifier)
CONTEXT: PL/pgSQL function check_origin_system_not_legacy() line 4 at RAISE
```
**Root cause:** The `runs` table has `origin_system_id DEFAULT 'legacy-migration'` combined with trigger `trg_runs_origin_system_not_legacy` that blocks that exact value. Any INSERT omitting `origin_system_id` triggers the default, which is then rejected by the trigger — a "default that rejects itself" trap.
**Resolution:** Explicitly set `origin_system_id = 'run-proof-test-v1'` in the INSERT.

### Issue 3: Broken Import in pg_store.py (ModuleNotFoundError)

**When:** Step 3 — coordinator invocation
**Error:**
```
File "app/hoc/cus/logs/L6_drivers/pg_store.py", line 57, in <module>
    from .redact import redact_trace_data
ModuleNotFoundError: No module named 'app.hoc.cus.logs.L6_drivers.redact'
```
**Root cause:** `redact.py` was reclassified from L6 to L5 (2026-01-24) and physically moved from `L6_drivers/` to `L5_engines/`, but the relative import `from .redact` in `pg_store.py` was never updated. This is the import bug the test plan was designed to validate "after the fix" — the fix had not been applied.
**Resolution:** Changed import in `pg_store.py` line 57 from `from .redact import redact_trace_data` to `from app.traces.redact import redact_trace_data` (platform substrate, identical code, layer-compliant for L6).

---

## Precondition Fix — Empty DB (Freshly Rebuilt)

The local DB was rebuilt from scratch via `alembic upgrade head` (see `local_db_equivalence_v1_implemented.md`). Both `aos_traces` and `runs` tables had 0 rows. To satisfy the test plan's precondition ("The DB contains at least one run with trace data"), synthetic data was seeded:

### Seeded Data

**Run record** (`runs` table):

| Column | Value |
|--------|-------|
| id | `run-proof-test-001` |
| agent_id | `agent-test-001` |
| goal | `Run proof test plan v1 — synthetic run for coordinator validation` |
| status | `completed` |
| tenant_id | `demo-tenant` |
| origin_system_id | `run-proof-test-v1` |
| duration_ms | `1800000` |

**Note:** Initial run insert failed with trigger error: `origin_system_id cannot be 'legacy-migration' for new runs`. Root cause: column `origin_system_id` has `DEFAULT 'legacy-migration'` and trigger `trg_runs_origin_system_not_legacy` blocks that value. Fixed by explicitly setting `origin_system_id = 'run-proof-test-v1'`.

**Trace record** (`aos_traces` table):

| Column | Value |
|--------|-------|
| trace_id | `trace_run-proof-test-001` |
| run_id | `run-proof-test-001` |
| tenant_id | `demo-tenant` |
| status | `completed` |
| is_synthetic | `true` |
| synthetic_scenario_id | `run-proof-test-plan-v1` |

**Trace steps** (`aos_trace_steps` table, 3 rows):

| step_index | skill_name | status | cost_cents | duration_ms |
|------------|------------|--------|------------|-------------|
| 0 | validate_input | success | 0.5 | 120.0 |
| 1 | process_data | success | 2.0 | 850.0 |
| 2 | generate_report | success | 1.5 | 320.0 |

---

## Import Fix Applied — pg_store.py

### Problem

`pg_store.py` (L6 driver) imported `from .redact import redact_trace_data`, expecting `redact.py` in `L6_drivers/`. The file was moved to `L5_engines/redact.py` during L6→L5 reclassification (2026-01-24) but the import in `pg_store.py` was never updated.

This is the "pg_store.py import fix" referenced in the test plan's goal statement.

### Error

```
ModuleNotFoundError: No module named 'app.hoc.cus.logs.L6_drivers.redact'
```

### Fix

```python
# Before (broken):
from .redact import redact_trace_data

# After (fixed):
from app.traces.redact import redact_trace_data
```

**Rationale:** `app/traces/redact.py` is platform substrate (identical content to `L5_engines/redact.py`). L6 drivers can import platform modules. Using the platform path avoids L6→L5_engines import violation.

---

## Step 1 — Confirm Trace Data Exists

```sql
SELECT run_id, tenant_id, started_at, status
FROM aos_traces ORDER BY started_at DESC LIMIT 1;
```

| run_id | tenant_id | started_at | status |
|--------|-----------|------------|--------|
| run-proof-test-001 | demo-tenant | 2026-02-09 15:29:01.622004+00 | completed |

**PASS.** 1 trace found.

---

## Step 2 — Confirm Trace Steps Exist

```sql
SELECT COUNT(*) AS step_count FROM aos_trace_steps
WHERE trace_id='trace_run-proof-test-001';
```

| step_count |
|------------|
| 3 |

**PASS.** 3 steps found.

---

## Step 3 — Coordinator Production Path

```bash
RUN_ID='run-proof-test-001' TENANT_ID='demo-tenant' \
PYTHONPATH=. USE_POSTGRES_TRACES=true python3 <coordinator_script>
```

**Output:**
```
integrity_model: HASH_CHAIN
verification_status: VERIFIED
chain_length: 3
root_hash: 0ca74e198c14a378a33c2ecad49ac725c74f3c33cce6dc1512fb32b258654c32
trace_count: 1
step_count: 3
```

**PASS.** Coordinator returned HASH_CHAIN integrity with VERIFIED status.

---

## Step 4 — Verify Integrity Result

| Check | Expected | Actual | Result |
|-------|----------|--------|--------|
| `integrity_model` | `HASH_CHAIN` | `HASH_CHAIN` | **PASS** |
| `verification_status` | `VERIFIED` | `VERIFIED` | **PASS** |
| `chain_length` = DB `step_count` | `3` | `3` | **PASS** |
| `trace_count >= 1` | `>= 1` | `1` | **PASS** |

**PASS.** All expectations met.

---

## Step 5 — Coordinator Pytest

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

**Output:**
```
..........                                                               [100%]
10 passed in 2.43s
```

**PASS.** 10/10 tests passed.

---

## Output Report

| Field | Value |
|-------|-------|
| **DB URL** | `postgresql://nova:novapass@localhost:6432/nova_aos` |
| **Run ID** | `run-proof-test-001` |
| **Tenant ID** | `demo-tenant` |
| **Trace started_at** | `2026-02-09 15:29:01.622004+00` |
| **Trace status** | `completed` |
| **Trace step_count (DB)** | `3` |
| **Coordinator integrity_model** | `HASH_CHAIN` |
| **Coordinator verification_status** | `VERIFIED` |
| **Coordinator chain_length** | `3` |
| **Coordinator root_hash** | `0ca74e198c14a378a33c2ecad49ac725c74f3c33cce6dc1512fb32b258654c32` |
| **Coordinator trace_count** | `1` |
| **Coordinator step_count** | `3` |
| **Pytest result** | `10/10 passed (2.43s)` |

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Coordinator returns `HASH_CHAIN` integrity with `VERIFIED` status | **MET** |
| 2 | `chain_length` matches DB `step_count` | **MET** (3 = 3) |
| 3 | `trace_count >= 1` and `step_count >= 1` | **MET** (1, 3) |
| 4 | `tests/test_run_introspection_coordinators.py` passes | **MET** (10/10) |

---

## Structural Findings

### Finding 1: Broken Import After Reclassification (FIXED)

`pg_store.py` line 57 had a stale relative import (`from .redact`) after `redact.py` was moved from `L6_drivers/` to `L5_engines/` during L6→L5 reclassification (2026-01-24). Fixed by pointing to platform substrate `app.traces.redact`.

### Finding 2: origin_system_id Trap on `runs` Table

The `runs` table has:
- Column `origin_system_id` with `DEFAULT 'legacy-migration'`
- Trigger `trg_runs_origin_system_not_legacy` that **blocks** inserts with `origin_system_id = 'legacy-migration'`

This creates a "default value that is immediately rejected" trap. Any INSERT that omits `origin_system_id` will fail. This is intentional (forces callers to declare their origin) but undocumented.

### Finding 3: Duplicate redact.py Modules

Three copies of identical redaction logic exist:
1. `app/traces/redact.py` (platform substrate)
2. `app/hoc/cus/logs/L5_engines/redact.py` (L5 engine)
3. Both export `redact_trace_data` with identical implementation

**Recommendation:** Consolidate to the platform `app/traces/redact.py` and have `L5_engines/redact.py` re-export from there, or delete the L5_engines copy if no L5 callers need it directly.

---

## Evidence Sources Read

| File | Lines | Purpose |
|------|-------|---------|
| `hoc_spine/orchestrator/coordinators/run_proof_coordinator.py` | 256 | L4 coordinator — hash chain computation |
| `hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py` | 106 | Logs bridge — routes to Postgres or SQLite store |
| `logs/L6_drivers/pg_store.py` | 775 | L6 driver — asyncpg trace store |
| `logs/L5_schemas/traces_models.py` | 436 | L5 schemas — TraceRecord, TraceStep, TraceSummary |

---

## Execution Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Postgres reachable for target DB | **YES** — local PgBouncer on port 6432 |
| 2 | `USE_POSTGRES_TRACES=true` set | **YES** — env var for test session |
| 3 | DB contains at least one run with trace data | **YES** — seeded synthetic run + trace + 3 steps |
| 4 | Coordinator production path executed | **YES** — HASH_CHAIN / VERIFIED |
| 5 | Pytest passed | **YES** — 10/10 in 2.43s |
| 6 | Import fix applied | **YES** — `pg_store.py` line 57 |
