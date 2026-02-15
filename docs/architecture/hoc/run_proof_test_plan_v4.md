# Run Proof Test Plan v4 (HOC) — CLI Canonical Path Validation

**Date:** 2026-02-09  
**Audience:** Claude execution plan  
**Goal:** Validate the customer CLI run path after canonicalization and worker relocation, using the same plan generation flow as the API, with no workarounds.  
**Policy:** No manual DB inserts. No SQLite fallback. Stop on failure and report evidence.

---

## 0. Scope and Preconditions

**Scope**
- Customer CLI run path only.
- RunProofCoordinator verification + coordinator tests.

**Preconditions**
- Local DB is reachable and migrated to head.
- `USE_POSTGRES_TRACES=true`.
- Skill registry includes `http_call` or the selected run plan will not use `http_call`.
- `cus_cli.py` imports:
  - `generate_plan_for_run` from `app.hoc.cus.policies.L5_engines.plan_generation`
  - `RunRunner` from `app.hoc.int.worker.runner`

---

## 1. Static Verification (No Execution Yet)

**File checks**
- `backend/app/hoc/cus/integrations/cus_cli.py` contains:
  - Required CLI arg `--tenant-id`
  - Optional CLI arg `--origin-system-id` with default
  - Plan generation via `generate_plan_for_run`
  - Execution via `RunRunner`
- `backend/app/hoc/int/integrations/int_cli.py` contains no customer run creation.

**Command**
```bash
rg -n "generate_plan_for_run|RunRunner|tenant-id|origin-system-id" \
  backend/app/hoc/cus/integrations/cus_cli.py
```

---

## 2. Customer CLI Run (Production Path)

**Command**
```bash
PYTHONPATH=. USE_POSTGRES_TRACES=true DATABASE_URL='<db_url>' \
python3 -m app.hoc.cus.integrations.cus_cli run \
  --agent-id '<agent_id>' \
  --goal "Run proof v4 validation run" \
  --tenant-id '<tenant_id>' \
  --origin-system-id "run-proof-v4" \
  --verbose
```

**Record**
- Run ID
- Tenant ID
- Status
- Error (if any)

---

## 3. Run Record Validation

**Run has plan**
```sql
SELECT id, tenant_id, origin_system_id, status, plan_json IS NOT NULL AS has_plan
FROM runs
WHERE id = '<run_id>';
```

**Trace exists**
```sql
SELECT run_id, tenant_id, started_at, status
FROM aos_traces
WHERE run_id = '<run_id>';
```

**Steps exist**
```sql
SELECT COUNT(*) AS step_count
FROM aos_trace_steps
WHERE run_id = '<run_id>';
```

---

## 4. RunProofCoordinator Validation

```bash
RUN_ID='<run_id>' TENANT_ID='<tenant_id>' DATABASE_URL='<db_url>' \
PYTHONPATH=. USE_POSTGRES_TRACES=true python3 - <<'PY'
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

---

## 5. Coordinator Tests

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

---

## 6. Acceptance Criteria

1. Customer CLI creates a run with explicit `tenant_id` and `origin_system_id`.
2. Plan generation occurs before execution and `plan_json` is stored.
3. Postgres trace rows exist for the run.
4. `RunProofCoordinator` returns `HASH_CHAIN` and `VERIFIED`.
5. Coordinator tests pass.

---

## 7. Output Template

**Run ID:** `<run_id>`  
**Tenant ID:** `<tenant_id>`  
**Run status:** `<status>`  
**Plan JSON stored:** `<true/false>`  
**Trace rows:** `<n>`  
**Trace step_count:** `<n>`  
**Integrity model:** `<value>`  
**Verification status:** `<value>`  
**chain_length:** `<value>`  
**root_hash:** `<value>`  
**Pytest:** `<pass/fail>`  

