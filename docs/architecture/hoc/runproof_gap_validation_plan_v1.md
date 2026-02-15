# RunProof Gap Validation Plan v1 (HOC)

**Date:** 2026-02-10  
**Scope:** Verify RunProofCoordinator trace proof in Postgres; fix blocking trace store/import issues if present.  
**Audience:** Claude execution plan  
**Goal:** Produce a fresh execution report confirming RunProof proof is PASS (HASH_CHAIN + VERIFIED) for a traced run using Postgres traces.

---

## 0. Context

The last recorded linkage report documented a **RunProof gap**:
- `PostgresTraceStore` import issue in logs driver
- Dev traces stored in SQLite, not Postgres

This plan is to **re‑validate** the RunProof path with `USE_POSTGRES_TRACES=true` and fix anything blocking Postgres trace proof.

---

## 1. Preconditions

1. Postgres reachable (PgBouncer 6432).
2. `DATABASE_URL` set for local Postgres.
3. `USE_POSTGRES_TRACES=true` in execution environment.
4. Latest migrations applied.

**Record:**
- `alembic current`
- `SELECT version_num FROM alembic_version;`

---

## 2. Static Checks (No execution yet)

### 2.1 Trace Store Import Sanity

Verify Postgres trace store imports are valid:

- File: `backend/app/hoc/cus/logs/L6_drivers/pg_store.py`
- Confirm imports resolve to real modules.

If broken:
- Fix imports to point to valid trace models.
- Keep L6 constraints (no L4/L5 imports).

### 2.2 Trace Store Selection

Confirm runtime path uses Postgres trace store when `USE_POSTGRES_TRACES=true`:

- Runner path: `backend/app/hoc/int/worker/runner.py`
- Ensure trace store used is Postgres, and writes to `aos_traces` / `aos_trace_steps`.

---

## 3. Execution: Create a Real Run

### 3.1 Run Creation (CLI)

Use the customer CLI to create a run that:
- Has explicit `tenant_id`
- Has explicit `origin_system_id`
- Executes a known skill (`http_call` ok)

**Expected:** `runs` row + `plan_json` stored, status goes to `succeeded` or `failed`.

### 3.2 Trace Presence

Confirm Postgres trace rows exist:

```sql
SELECT trace_id, run_id, status FROM aos_traces WHERE run_id = :run_id;
SELECT COUNT(*) FROM aos_trace_steps WHERE trace_id = :trace_id;
```

**Expected:** `aos_traces` = 1, `aos_trace_steps` >= 1.

---

## 4. RunProofCoordinator Validation

Execute:

```python
coordinator = get_run_proof_coordinator()
async with get_async_session() as session:
    result = await coordinator.get_run_proof(session, TENANT_ID, RUN_ID)
```

**Expected:**
- `integrity_model = HASH_CHAIN`
- `verification_status = VERIFIED`
- `trace_count >= 1`
- `step_count >= 1`

---

## 5. Fixes (If Needed)

If any step fails:

1. Capture exact error and file/line.
2. Apply minimal fix respecting HOC layer rules.
3. Re-run only the failed section(s).
4. Record all changes.

---

## 6. Output Report

Create execution report:

`docs/architecture/hoc/runproof_gap_validation_plan_v1_executed.md`

Include:
- Environment (DB, flags)
- SQL evidence
- Coordinator output
- Any fixes applied

---

## 7. Acceptance Criteria

**PASS** when all are true:
1. Postgres traces are created for the run (`aos_traces` row exists).
2. Postgres trace steps exist (`aos_trace_steps` >= 1).
3. RunProofCoordinator returns `HASH_CHAIN` + `VERIFIED`.
4. Any fixes are documented with file references.
