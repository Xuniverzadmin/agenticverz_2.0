# scheduler_facade.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/scheduler_facade.py`  
**Layer:** L4 — HOC Spine (Facade)  
**Component:** Services

---

## Placement Card

```
File:            scheduler_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 scheduler.py API, SDK, Worker
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Scheduler Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Scheduler Facade (L4 Domain Logic)

This facade provides the external interface for scheduled job operations.
All scheduler APIs MUST use this facade instead of directly importing
internal scheduler modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes job scheduling logic
- Provides unified access to job management
- Single point for audit emission

L2 API Routes (GAP-112):
- POST /api/v1/scheduler/jobs (create job)
- GET /api/v1/scheduler/jobs (list jobs)
- GET /api/v1/scheduler/jobs/{id} (get job)
- PUT /api/v1/scheduler/jobs/{id} (update job)
- DELETE /api/v1/scheduler/jobs/{id} (delete job)
- POST /api/v1/scheduler/jobs/{id}/trigger (trigger job)
- POST /api/v1/scheduler/jobs/{id}/pause (pause job)
- POST /api/v1/scheduler/jobs/{id}/resume (resume job)
- GET /api/v1/scheduler/jobs/{id}/runs (job run history)

Usage:
    # L5 engine import (V2.0.0 - hoc_spine)
    from app.hoc.cus.hoc_spine.services.scheduler_facade import get_scheduler_facade

    facade = get_scheduler_facade()

    # Create scheduled job
    job = await facade.create_job(
        tenant_id="...",
        name="Daily Report",
        schedule="0 9 * * *",
        action={"type": "run_agent", "agent_id": "..."},
    )

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_scheduler_facade() -> SchedulerFacade`

Get the scheduler facade instance.

This is the recommended way to access scheduler operations
from L2 APIs and the SDK.

Returns:
    SchedulerFacade instance

## Classes

### `JobStatus(str, Enum)`

Job status.

### `JobRunStatus(str, Enum)`

Job run status.

### `ScheduledJob`

Scheduled job definition.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `JobRun`

Job run history entry.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `SchedulerFacade`

Facade for scheduled job operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
scheduler services.

Layer: L4 (Domain Logic)
Callers: scheduler.py (L2), aos_sdk, Worker

#### Methods

- `__init__()` — Initialize facade.
- `async create_job(tenant_id: str, name: str, schedule: str, action: Dict[str, Any], description: Optional[str], enabled: bool, metadata: Optional[Dict[str, Any]]) -> ScheduledJob` — Create a scheduled job.
- `async list_jobs(tenant_id: str, status: Optional[str], limit: int, offset: int) -> List[ScheduledJob]` — List scheduled jobs.
- `async get_job(job_id: str, tenant_id: str) -> Optional[ScheduledJob]` — Get a specific job.
- `async update_job(job_id: str, tenant_id: str, name: Optional[str], schedule: Optional[str], action: Optional[Dict[str, Any]], description: Optional[str], metadata: Optional[Dict[str, Any]]) -> Optional[ScheduledJob]` — Update a scheduled job.
- `async delete_job(job_id: str, tenant_id: str) -> bool` — Delete a scheduled job.
- `async trigger_job(job_id: str, tenant_id: str) -> Optional[JobRun]` — Trigger a job to run immediately.
- `async pause_job(job_id: str, tenant_id: str) -> Optional[ScheduledJob]` — Pause a scheduled job.
- `async resume_job(job_id: str, tenant_id: str) -> Optional[ScheduledJob]` — Resume a paused job.
- `async list_runs(job_id: str, tenant_id: str, status: Optional[str], limit: int, offset: int) -> List[JobRun]` — List job runs.
- `async get_run(run_id: str, tenant_id: str) -> Optional[JobRun]` — Get a specific job run.
- `_calculate_next_run(schedule: str, from_time: datetime) -> datetime` — Calculate next run time from cron expression.

## Domain Usage

**Callers:** L2 scheduler.py API, SDK, Worker

## Export Contract

```yaml
exports:
  functions:
    - name: get_scheduler_facade
      signature: "get_scheduler_facade() -> SchedulerFacade"
      consumers: ["orchestrator"]
  classes:
    - name: JobStatus
      methods: []
      consumers: ["orchestrator"]
    - name: JobRunStatus
      methods: []
      consumers: ["orchestrator"]
    - name: ScheduledJob
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: JobRun
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: SchedulerFacade
      methods:
        - create_job
        - list_jobs
        - get_job
        - update_job
        - delete_job
        - trigger_job
        - pause_job
        - resume_job
        - list_runs
        - get_run
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

