# hoc_models_governance_job

| Field | Value |
|-------|-------|
| Path | `backend/app/models/governance_job.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Governance Job database models

## Intent

**Role:** Governance Job database models
**Reference:** PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
**Callers:** governance/*, L4 domain services

## Purpose

Governance Job Models (Part-2 CRM Workflow)

---

## Classes

### `JobStatus(str, Enum)`
- **Docstring:** Governance Job lifecycle states.

### `StepStatus(str, Enum)`
- **Docstring:** Status of a single job step.

### `GovernanceJob(Base)`
- **Docstring:** Governance Job database model.

### `JobStep(BaseModel)`
- **Docstring:** Single step in a governance job.
- **Class Variables:** step_index: int, step_type: str, target: str, parameters: dict[str, Any], timeout_seconds: int

### `StepResult(BaseModel)`
- **Docstring:** Result of executing a single step.
- **Class Variables:** step_index: int, status: StepStatus, started_at: Optional[datetime], completed_at: Optional[datetime], output: Optional[dict[str, Any]], error: Optional[str], health_after: Optional[dict[str, Any]]

### `HealthSnapshot(BaseModel)`
- **Docstring:** Point-in-time health state capture.
- **Class Variables:** captured_at: datetime, capabilities: dict[str, dict[str, Any]], system_health: dict[str, Any]

### `JobCreate(BaseModel)`
- **Docstring:** Input model for creating a job from activated contract.
- **Class Variables:** contract_id: UUID, steps: list[JobStep], timeout_minutes: int, created_by: str

### `JobResponse(BaseModel)`
- **Docstring:** Output model for job data.
- **Class Variables:** job_id: UUID, contract_id: UUID, status: str, status_reason: Optional[str], steps: list[dict[str, Any]], current_step_index: int, total_steps: int, step_results: list[dict[str, Any]], execution_evidence: Optional[dict[str, Any]], health_snapshot_before: Optional[dict[str, Any]], health_snapshot_after: Optional[dict[str, Any]], created_at: datetime, started_at: Optional[datetime], completed_at: Optional[datetime], timeout_at: Optional[datetime], created_by: str

### `JobTransitionRecord(BaseModel)`
- **Docstring:** Record of a job state transition.
- **Class Variables:** from_status: str, to_status: str, step_index: Optional[int], reason: str, transitioned_by: str, transitioned_at: datetime

### `InvalidJobTransitionError(Exception)`
- **Docstring:** Raised when an invalid job state transition is attempted.
- **Methods:** __init__

### `JobImmutableError(Exception)`
- **Docstring:** Raised when attempting to modify an immutable job.
- **Methods:** __init__

### `OrphanJobError(Exception)`
- **Docstring:** Raised when attempting to create a job without a contract.
- **Methods:** __init__

## Attributes

- `JOB_TERMINAL_STATES` (line 75)
- `JOB_VALID_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]]` (line 325)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql` |

## Callers

governance/*, L4 domain services

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: JobStatus
      methods: []
    - name: StepStatus
      methods: []
    - name: GovernanceJob
      methods: []
    - name: JobStep
      methods: []
    - name: StepResult
      methods: []
    - name: HealthSnapshot
      methods: []
    - name: JobCreate
      methods: []
    - name: JobResponse
      methods: []
    - name: JobTransitionRecord
      methods: []
    - name: InvalidJobTransitionError
      methods: []
    - name: JobImmutableError
      methods: []
    - name: OrphanJobError
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
