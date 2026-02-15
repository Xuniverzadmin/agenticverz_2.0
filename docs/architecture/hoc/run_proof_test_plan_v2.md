# Run Proof Test Plan v2 (HOC) — No Workarounds

**Date:** 2026-02-09  
**Audience:** Claude execution plan  
**Goal:** Validate `RunProofCoordinator` on a real run produced by the production execution path, after fixing the `origin_system_id` default/trigger design bug.  
**Policy:** No manual DB inserts. No SQLite fallback. Stop on failure and report evidence.

---

## 0. Non‑Negotiables

- Do **not** insert into `runs`, `aos_traces`, or `aos_trace_steps` directly.
- Do **not** use `SQLiteTraceStore` or local trace files.
- Fix the `origin_system_id` default/trigger contradiction **before** attempting any test run.

---

## 1. Design Fixes (Required Before Testing)

### Fix A — `origin_system_id` Default vs Trigger (Design Bug)

**Problem:**  
`runs.origin_system_id` has `DEFAULT 'legacy-migration'` (from migration 104), but trigger `trg_runs_origin_system_not_legacy` (migration 105) rejects that value for **new** runs. This makes the schema self‑contradictory.

**Required Fix (No Workaround):**

1. **DB Migration (new migration file):**
   - `ALTER TABLE runs ALTER COLUMN origin_system_id DROP DEFAULT;`
   - Keep `NOT NULL` and the trigger (105) to enforce explicit values.

2. **ORM Model Fix:**
   - Remove the default from `origin_system_id` in:
     - `backend/app/db.py`
     - `backend/app/hoc/int/agent/drivers/db.py`
   - Field must be explicitly provided on `Run` creation.

3. **Run Creation Paths (must set origin_system_id explicitly):**
   - Update **all** run creation paths to pass a real identifier.
   - Minimum known touchpoints:
     - `backend/app/hoc/cus/integrations/cus_cli.py` (`Run(...)` in `create_run`)
     - `backend/app/hoc/int/integrations/int_cli.py` (if it creates runs)
     - `backend/app/hoc/cus/policies/L6_drivers/workers_read_driver.py` (`INSERT INTO runs`)
   - **Verification step:** `rg -n "INSERT INTO runs|Run\\(" backend/app` and patch all creation sites.

**Acceptance for Fix A:**
- Insert without `origin_system_id` fails with a NOT NULL violation.
- Insert with `origin_system_id='legacy-migration'` fails via trigger.
- Normal run creation with explicit `origin_system_id` succeeds.

---

## 2. Generate a Real Run (Production Path)

**Canonical path:** Use the CLI which invokes `RunRunner` (same execution path as API).

1. **Create or pick an agent:**
   - `python -m app.hoc.cus.integrations.cus_cli list-agents`
   - If none, create: `python -m app.hoc.cus.integrations.cus_cli create-agent --name "run-proof-v2-agent"`

2. **Run a goal (real execution, not DB seed):**
   - Example:
     ```bash
     PYTHONPATH=. DATABASE_URL='<db_url>' \
     python -m app.hoc.cus.integrations.cus_cli run \
       --agent-id '<agent_id>' \
       --goal "Run proof v2 validation run" \
       --tenant-id '<tenant_id>' \
       --origin-system-id "run-proof-v2"
     ```

3. **Record the resulting `run_id`** and **wait for completion** (status `succeeded` or `failed`).

---

## 3. Verify Trace Data Exists (DB Read‑Only)

```sql
SELECT run_id, tenant_id, started_at, status
FROM aos_traces
WHERE run_id = '<run_id>';
```

```sql
SELECT COUNT(*) AS step_count
FROM aos_trace_steps
WHERE run_id = '<run_id>';
```

**Expected:** 1 trace row, `step_count >= 1`.

---

## 4. RunProofCoordinator Validation

Execute from `backend/`:

```bash
RUN_ID='<run_id>' TENANT_ID='<tenant_id>' DATABASE_URL='<db_url>' \
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

**Expected:**
- `integrity_model = HASH_CHAIN`
- `verification_status = VERIFIED`
- `chain_length == step_count`

---

## 5. Coordinator Tests

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

---

## 6. Acceptance Criteria

- `origin_system_id` schema is no longer self‑contradictory (default removed, trigger enforced).
- All run creation paths set `origin_system_id` explicitly.
- A real run (not DB seed) produces trace rows in Postgres.
- `RunProofCoordinator` returns `HASH_CHAIN` + `VERIFIED`.
- Coordinator tests pass.

---

## 7. Output Report Template (Fill In)

**Migration applied:** `<rev_id>`  
**origin_system_id default removed:** `<yes/no>`  
**Run creation paths patched:** `<files>`  
**Run ID:** `<run_id>`  
**Tenant ID:** `<tenant_id>`  
**Trace rows:** `<n>`  
**Trace step_count:** `<n>`  
**Integrity model:** `<value>`  
**Verification status:** `<value>`  
**chain_length:** `<value>`  
**root_hash:** `<value>`  
**Pytest:** `<pass/fail>`
