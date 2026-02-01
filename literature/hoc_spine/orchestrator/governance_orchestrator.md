# governance_orchestrator.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/governance_orchestrator.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            governance_orchestrator.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         L3 (adapters), L2 (governance APIs)
Outbound:        app.hoc.cus.hoc_spine.authority.contracts.contract_engine
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Part-2 Governance Orchestrator (L4)
Violations:      none
```

## Purpose

Part-2 Governance Orchestrator (L4)

Orchestrates the governance workflow from contract activation through
audit triggering. This is the "traffic controller" - it directs flow
but does not execute.

Components:
1. Contract Activation Service - APPROVED → ACTIVE
2. Execution Orchestrator - contract → job plan
3. Job State Tracker - observes job states
4. Audit Trigger - hands evidence to audit layer

Key Constraints (PIN-292):
- Orchestrates only; does not execute jobs
- No health or audit authority
- Contract is the sole source of execution intent
- MAY_NOT remains mechanically un-overridable

Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292, part2-design-v1

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.authority.contracts.contract_engine`

**L7 Models:**
- `app.models.contract`
- `app.models.governance_job`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `HealthLookup(Protocol)`

Protocol for capturing health state (read-only).

#### Methods

- `capture_health_snapshot() -> HealthSnapshot` — Capture current health state for evidence.

### `JobState`

In-memory representation of job state.

Used for state tracking before persistence.

### `JobStateMachine`

State machine for Governance Job lifecycle.

Enforces:
- JOB-002: Job steps execute in order
- JOB-003: Terminal states are immutable

#### Methods

- `can_transition(from_status: JobStatus, to_status: JobStatus) -> bool` — Check if a transition is valid.
- `validate_transition(state: JobState, to_status: JobStatus) -> None` — Validate a job state transition.
- `transition(state: JobState, to_status: JobStatus, reason: str, transitioned_by: str, step_index: Optional[int]) -> JobState` — Execute a job state transition.

### `ExecutionOrchestrator`

Translates contract → job plan.

This is purely a planning service. It does NOT execute.

Responsibilities:
1. Parse contract proposed_changes into JobSteps
2. Validate step ordering
3. Calculate timeouts

Reference: PART2_CRM_WORKFLOW_CHARTER.md Step 7

#### Methods

- `create_job_plan(contract_state: ContractState, timeout_minutes: int) -> list[JobStep]` — Create job execution plan from contract.
- `_parse_change_to_step(index: int, change: dict[str, Any]) -> JobStep` — Parse a single change into a JobStep.

### `JobStateTracker`

Observes job state - does NOT control execution.

This is purely an observation service.

Responsibilities:
1. Track job state transitions
2. Record step results
3. Capture evidence for audit

Key constraint: This service READS state, it doesn't DRIVE execution.
The actual execution is done by L5 Job Executor.

#### Methods

- `record_step_result(job_state: JobState, step_result: StepResult) -> JobState` — Record a step result (observation only).
- `calculate_completion_status(job_state: JobState) -> tuple[JobStatus, str]` — Calculate what the job's terminal status should be.

### `AuditEvidence`

Evidence package for audit layer.

This is what we hand to the auditor (L8).

### `AuditTrigger`

Prepares and hands evidence to audit layer.

This service does NOT make audit decisions.
It packages evidence and signals that audit should occur.

The actual audit logic is in the Audit Service (L8).

#### Methods

- `prepare_evidence(job_state: JobState) -> AuditEvidence` — Prepare evidence package for audit.
- `should_trigger_audit(job_state: JobState) -> bool` — Determine if audit should be triggered.

### `ContractActivationError(Exception)`

Raised when contract activation fails.

#### Methods

- `__init__(contract_id: UUID, reason: str)` — _No docstring._

### `ContractActivationService`

Activates approved contracts (APPROVED → ACTIVE).

This is the bridge between the contract state machine and job creation.

Responsibilities:
1. Verify contract is APPROVED
2. Create job plan from contract
3. Create job record
4. Transition contract to ACTIVE

Key constraint: Activation creates a job but does NOT execute it.

#### Methods

- `__init__(contract_service: ContractService, health_lookup: Optional[HealthLookup])` — _No docstring._
- `activate_contract(contract_state: ContractState, activated_by: str, timeout_minutes: int) -> tuple[ContractState, JobState]` — Activate an approved contract.

### `GovernanceOrchestrator`

Facade for all governance orchestration services.

This is the main entry point for governance workflow orchestration.
It combines:
- Contract Activation Service
- Execution Orchestrator
- Job State Tracker
- Audit Trigger

Key Properties (PIN-292):
- Orchestrates only; does not execute jobs
- No health or audit authority
- Contract is the sole source of execution intent

Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292

#### Methods

- `__init__(contract_service: Optional[ContractService], health_lookup: Optional[HealthLookup])` — _No docstring._
- `version() -> str` — Return orchestrator version.
- `activate_contract(contract_state: ContractState, activated_by: str, timeout_minutes: int) -> tuple[ContractState, JobState]` — Activate an approved contract, creating a job.
- `start_job(job_state: JobState, started_by: str) -> JobState` — Transition job from PENDING to RUNNING.
- `record_step_result(job_state: JobState, step_result: StepResult) -> JobState` — Record a step result from the executor.
- `complete_job(job_state: JobState, completed_by: str) -> JobState` — Transition job to terminal state based on step results.
- `cancel_job(job_state: JobState, reason: str, cancelled_by: str) -> JobState` — Cancel a job manually.
- `should_trigger_audit(job_state: JobState) -> bool` — Check if audit should be triggered for this job.
- `prepare_audit_evidence(job_state: JobState) -> AuditEvidence` — Prepare evidence package for the audit layer.
- `is_job_terminal(job_state: JobState) -> bool` — Check if job is in terminal state.
- `can_start_job(job_state: JobState) -> bool` — Check if job can be started.
- `get_job_progress(job_state: JobState) -> dict[str, Any]` — Get job execution progress.

## Domain Usage

**Callers:** L3 (adapters), L2 (governance APIs)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: HealthLookup
      methods:
        - capture_health_snapshot
      consumers: ["orchestrator"]
    - name: JobState
      methods: []
      consumers: ["orchestrator"]
    - name: JobStateMachine
      methods:
        - can_transition
        - validate_transition
        - transition
      consumers: ["orchestrator"]
    - name: ExecutionOrchestrator
      methods:
        - create_job_plan
      consumers: ["orchestrator"]
    - name: JobStateTracker
      methods:
        - record_step_result
        - calculate_completion_status
      consumers: ["orchestrator"]
    - name: AuditEvidence
      methods: []
      consumers: ["orchestrator"]
    - name: AuditTrigger
      methods:
        - prepare_evidence
        - should_trigger_audit
      consumers: ["orchestrator"]
    - name: ContractActivationError
      methods:
      consumers: ["orchestrator"]
    - name: ContractActivationService
      methods:
        - activate_contract
      consumers: ["orchestrator"]
    - name: GovernanceOrchestrator
      methods:
        - version
        - activate_contract
        - start_job
        - record_step_result
        - complete_job
        - cancel_job
        - should_trigger_audit
        - prepare_audit_evidence
        - is_job_terminal
        - can_start_job
        - get_job_progress
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: ['app.hoc.cus.hoc_spine.authority.contracts.contract_engine']
    l7_model: ['app.models.contract', 'app.models.governance_job']
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

