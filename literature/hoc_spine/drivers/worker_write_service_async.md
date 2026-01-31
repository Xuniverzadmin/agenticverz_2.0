# worker_write_service_async.py

**Path:** `backend/app/hoc/hoc_spine/drivers/worker_write_service_async.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            worker_write_service_async.py
Lives in:        drivers/
Role:            Drivers
Inbound:         api/workers.py
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Worker Write Service (Async) - DB write operations for Worker API.
Violations:      none
```

## Purpose

Worker Write Service (Async) - DB write operations for Worker API.

Phase 2B Batch 4: Extracted from api/workers.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
- Preserve async semantics exactly

## Import Analysis

**L7 Models:**
- `app.models.tenant`

**External:**
- `sqlalchemy`
- `sqlalchemy.ext.asyncio`
- `app.db`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `WorkerWriteServiceAsync`

Async DB write operations for Worker API.

Write-only facade. No policy logic, no branching beyond DB operations.
All methods preserve existing async execution model.

#### Methods

- `__init__(session: AsyncSession)` — _No docstring._
- `async upsert_worker_run(run_id: str, tenant_id: str, data: Dict[str, Any]) -> WorkerRun` — Upsert a WorkerRun record.
- `async insert_cost_record(run_id: str, tenant_id: str, model: str, input_tokens: int, output_tokens: int, cost_cents: int) -> CostRecord` — Insert a cost record for a worker run.
- `async insert_cost_advisory(tenant_id: str, run_id: str, daily_spend: int, warn_threshold: float, budget_snapshot: Dict[str, Any]) -> CostAnomaly` — Insert a cost advisory (BUDGET_WARNING anomaly).
- `async delete_worker_run(run: WorkerRun) -> None` — Delete a WorkerRun record.
- `async get_worker_run(run_id: str) -> Optional[WorkerRun]` — Get a WorkerRun by ID (read operation for upsert check).

## Domain Usage

**Callers:** api/workers.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: WorkerWriteServiceAsync
      methods:
        - upsert_worker_run
        - insert_cost_record
        - insert_cost_advisory
        - delete_worker_run
        - get_worker_run
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.tenant']
    external: ['sqlalchemy', 'sqlalchemy.ext.asyncio', 'app.db']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

