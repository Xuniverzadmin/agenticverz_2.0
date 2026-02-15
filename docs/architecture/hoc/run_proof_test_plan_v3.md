# Run Proof Test Plan v3 (HOC) — CLI Fix + No Workarounds

**Date:** 2026-02-09  
**Audience:** Claude execution plan  
**Goal:** Fix the CLI run path correctly (tenant_id + plan generation) and validate RunProof with a real run.  
**Policy:** No manual DB inserts. No SQLite fallback. Stop on failure and report evidence.

---

## Appendix A — Prior Plan (Captured As‑Is)

Here’s the plan before fixing the CLI path (no changes applied yet):

**Root cause summary**
- `aos_cli.py` and `hoc/api/int/account/aos_cli.py` create bare `Run` records without `tenant_id` and without L4 plan generation.
- Result: CLI‑created runs fail in production trace path (no tenant_id + no plan).

**Fix plan (no workarounds)**

1. Add explicit CLI inputs  
   - Add `--tenant-id` and `--origin-system-id` arguments to the run command  
     - `backend/app/aos_cli.py`  
     - `backend/app/hoc/api/int/account/aos_cli.py`  
   - Require `--tenant-id` for run; `--origin-system-id` can default to `"aos-cli"` / `"hoc-cli"` but should be overridable.

2. Create run with required fields  
   - Update `create_run()` in both files to set:
     - `tenant_id`
     - `origin_system_id`
   - This aligns with the new NOT NULL constraint and trigger.

3. Generate plan before execution (same as API path)  
   - After creating the run, generate plan with the same L4/L5 path as API:  
     - Use `generate_plan_for_run` (the same function used in `backend/app/main.py`).  
   - Persist `plan_json` to the run before calling `RunRunner`.

4. Execute via `RunRunner` (unchanged)  
   - Run the existing execution path, now with a valid tenant_id and plan.

5. Verify end‑to‑end  
   - Run CLI:  
     - `python -m app.aos_cli run --agent-id <id> --goal "..." --tenant-id <tenant> --origin-system-id aos-cli`  
   - Confirm:  
     - A row exists in `aos_traces` for the run.  
     - `RunProofCoordinator` returns `HASH_CHAIN / VERIFIED`.

**Files to change**
- `backend/app/aos_cli.py`
- `backend/app/hoc/api/int/account/aos_cli.py`

**Acceptance criteria**
- CLI run succeeds without manual DB inserts.
- `aos_traces` contains a row for the run.
- `RunProofCoordinator` returns `HASH_CHAIN` and `VERIFIED`.

---

## 1. Updated Design (No Shims, New Locations)

**Rule enforced:** Customer‑facing CLI must live under `hoc/cus`, internal under `hoc/int`.  
**No shims allowed:** Legacy root CLI files are removed.

**Target files**
- Customer CLI: `backend/app/hoc/cus/integrations/cus_cli.py`
- Internal CLI: `backend/app/hoc/int/integrations/int_cli.py`

**Legacy deletions**
- `backend/app/aos_cli.py` (deleted)
- `backend/app/hoc/api/int/account/aos_cli.py` (deleted)

---

## 2. Customer CLI Fix (Production Run Path)

Customer CLI must:
1. Require `--tenant-id`
2. Accept optional `--origin-system-id` (default `cus-cli`)
3. Create run with `tenant_id` + `origin_system_id`
4. Generate plan via L4 `generate_plan_for_run` before execution
5. Execute via `RunRunner`

**Run command (customer)**
```bash
PYTHONPATH=. DATABASE_URL='<db_url>' \
python -m app.hoc.cus.integrations.cus_cli run \
  --agent-id '<agent_id>' \
  --goal "Run proof v3 validation run" \
  --tenant-id '<tenant_id>' \
  --origin-system-id "run-proof-v3"
```

---

## 3. Internal CLI (Ops/Demo Only)

Internal CLI is for demo and internal checks only. It must **not** create customer runs.

**Demo command (internal)**
```bash
python -m app.hoc.int.integrations.int_cli demo
```

---

## 4. RunProof Validation (Same As v2)

### Verify trace data exists
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

### RunProofCoordinator
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

### Tests
```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

---

## 5. Acceptance Criteria

- Customer CLI creates a real run with explicit `tenant_id` and `origin_system_id`.
- Plan generation occurs before execution (stored in `run.plan_json`).
- Postgres trace rows exist for the run (`aos_traces`, `aos_trace_steps`).
- `RunProofCoordinator` returns `HASH_CHAIN` + `VERIFIED`.
- Coordinator tests pass.

---

## 6. Output Template

**Run ID:** `<run_id>`  
**Tenant ID:** `<tenant_id>`  
**Trace rows:** `<n>`  
**Trace step_count:** `<n>`  
**Integrity model:** `<value>`  
**Verification status:** `<value>`  
**chain_length:** `<value>`  
**root_hash:** `<value>`  
**Pytest:** `<pass/fail>`  

