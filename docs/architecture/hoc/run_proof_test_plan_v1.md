# Run Proof Test Plan v1 (HOC)

**Date:** 2026-02-09  
**Audience:** Claude execution plan  
**Goal:** Validate `RunProofCoordinator` end-to-end on a traced run using the Postgres trace store (production path) after the `pg_store.py` import fix.  
**No Workarounds:** Do not bypass failures or switch to SQLite traces. If any step fails, stop and report the exact error and evidence.

---

## 1. Preconditions (Required)

- Postgres is reachable for the target DB (`DATABASE_URL` points to staging/local DB).
- `USE_POSTGRES_TRACES=true` is set for the test session.
- The DB contains at least one run with trace data in `aos_traces` and `aos_trace_steps`.

---

## 2. Evidence Sources (Read Before Running)

- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`
- `backend/app/hoc/cus/logs/L6_drivers/pg_store.py`
- `backend/app/hoc/cus/logs/L5_schemas/traces_models.py`

---

## 3. Step-by-Step Execution

### Step 1 — Confirm trace data exists

Run in the target DB:

```sql
SELECT run_id, tenant_id, started_at, status
FROM aos_traces
ORDER BY started_at DESC
LIMIT 1;
```

Record:
- `run_id`
- `tenant_id`
- `started_at`
- `status`

If this returns zero rows, stop and report: "No trace data available in aos_traces."

---

### Step 2 — Confirm trace steps exist for that run

```sql
SELECT COUNT(*) AS step_count
FROM aos_trace_steps
WHERE run_id = '<run_id>';
```

Record `step_count`. If `step_count = 0`, stop and report: "Trace exists but has no steps."

---

### Step 3 — Verify run proof via coordinator (production path)

Run from `backend/`:

```bash
PYTHONPATH=. USE_POSTGRES_TRACES=true python - <<'PY'
import asyncio
import os

from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import (
    get_run_proof_coordinator,
)
from app.db import get_session

RUN_ID = os.environ["RUN_ID"]
TENANT_ID = os.environ["TENANT_ID"]

async def main():
    coordinator = get_run_proof_coordinator()
    async with get_session() as session:
        result = await coordinator.get_run_proof(session, TENANT_ID, RUN_ID)
        print("integrity_model:", result.integrity.model)
        print("verification_status:", result.integrity.verification_status)
        print("chain_length:", result.integrity.chain_length)
        print("root_hash:", result.integrity.root_hash)
        print("trace_count:", len(result.aos_traces))
        print("step_count:", len(result.aos_trace_steps))

asyncio.run(main())
PY
```

Run with:

```bash
RUN_ID='<run_id>' TENANT_ID='<tenant_id>' DATABASE_URL='<db_url>' \
PYTHONPATH=. USE_POSTGRES_TRACES=true python <script above>
```

Record the printed values.

---

### Step 4 — Verify integrity result is HASH_CHAIN

Expected:
- `integrity_model` = `HASH_CHAIN`
- `verification_status` = `VERIFIED`
- `chain_length` equals `step_count` from Step 2
- `trace_count >= 1`

If any expectation fails, stop and report the exact output.

---

### Step 5 — Run the coordinator test

From `backend/`:

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

Record pass/fail result and any errors.

---

## 4. Output Report (Fill In)

**DB URL:** `<db_url>`  
**Run ID:** `<run_id>`  
**Tenant ID:** `<tenant_id>`  
**Trace started_at:** `<timestamp>`  
**Trace status:** `<status>`  
**Trace step_count (DB):** `<n>`  
**Coordinator integrity_model:** `<value>`  
**Coordinator verification_status:** `<value>`  
**Coordinator chain_length:** `<value>`  
**Coordinator root_hash:** `<value>`  
**Coordinator trace_count:** `<value>`  
**Coordinator step_count:** `<value>`  
**Pytest result:** `<pass/fail + error>`

---

## 5. Acceptance Criteria

- Coordinator returns `HASH_CHAIN` integrity with `VERIFIED` status.
- `chain_length` matches DB `step_count`.
- `trace_count >= 1` and `step_count >= 1`.
- `tests/test_run_introspection_coordinators.py` passes.

