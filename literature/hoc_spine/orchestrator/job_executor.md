# job_executor.py

**Path:** `backend/app/hoc/hoc_spine/orchestrator/execution/job_executor.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            job_executor.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         workers, governance orchestrator (via message queue)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Part-2 Job Executor (L5)
Violations:      none
```

## Purpose

Part-2 Job Executor (L5)

Executes governance job steps in order and emits evidence.

This is a MACHINE that performs declared steps. It does not:
- Decide what to execute (that's Contract + Orchestrator)
- Retry failures (failed = done)
- Interpret results (that's Audit)
- Modify health (that's PlatformHealthService)

The Executor is "just physics" - it runs the plan and records what happened.

Invariants:
- EXEC-001: Execute steps in declared order
- EXEC-002: Emit evidence per step
- EXEC-003: Stop on first failure
- EXEC-004: Health is observed, never modified
- EXEC-005: No eligibility or contract mutation
- EXEC-006: No retry logic

Reference: PIN-294, PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

## Import Analysis

**L7 Models:**
- `app.models.governance_job`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `create_default_executor() -> JobExecutor`

Create a JobExecutor with default handlers.

Default handlers are no-ops for testing.
Production handlers should be registered separately.

### `execution_result_to_evidence(result: ExecutionResult) -> dict[str, Any]`

Convert ExecutionResult to audit evidence format.

This is what gets passed to the Audit Trigger.

## Classes

### `HealthObserver(Protocol)`

Protocol for observing health state (read-only).

JOB EXECUTOR RULE: Health is OBSERVED, not MODIFIED.

#### Methods

- `observe_health() -> dict[str, Any]` — Capture current health state.

### `StepHandler(Protocol)`

Protocol for step type handlers.

Each step type (capability_enable, capability_disable, etc.)
has a handler that performs the actual operation.

#### Methods

- `execute(step: JobStep, context: 'ExecutionContext') -> 'StepOutput'` — Execute a single step.

### `StepOutput`

Output from executing a single step.

This is the raw output from the step handler,
before it becomes a StepResult.

### `ExecutionContext`

Context passed to step handlers during execution.

Contains information the handler needs without
giving it authority to change governance state.

### `ExecutionResult`

Result of executing a job.

Contains the final status and all step results.

### `JobExecutor`

Part-2 Job Executor (L5)

Executes governance job steps in order and emits evidence.

Key Properties (PIN-294):
- Consumes job plans only
- No eligibility, no approval, no contract mutation
- Emits evidence per step
- Stops on failure
- Health is observed, never modified

Usage:
    executor = JobExecutor()
    result = executor.execute_job(job_state, health_observer)

#### Methods

- `__init__(handlers: Optional[dict[str, StepHandler]], executor_version: str)` — Initialize Job Executor.
- `version() -> str` — Return executor version.
- `register_handler(step_type: str, handler: StepHandler) -> None` — Register a handler for a step type.
- `execute_job(job_id: UUID, contract_id: UUID, steps: list[JobStep], health_observer: Optional[HealthObserver], executed_by: str) -> ExecutionResult` — Execute a job's steps in order.
- `_execute_step(step: JobStep, job_id: UUID, contract_id: UUID, health_observer: Optional[HealthObserver], executed_by: str) -> StepResult` — Execute a single step and return result.

### `NoOpHandler`

No-op handler for testing.

Always succeeds without doing anything.

#### Methods

- `execute(step: JobStep, context: ExecutionContext) -> StepOutput` — Execute no-op step.

### `FailingHandler`

Failing handler for testing.

Always fails with a configurable error.

#### Methods

- `__init__(error_message: str)` — _No docstring._
- `execute(step: JobStep, context: ExecutionContext) -> StepOutput` — Execute failing step.

## Domain Usage

**Callers:** workers, governance orchestrator (via message queue)

## Export Contract

```yaml
exports:
  functions:
    - name: create_default_executor
      signature: "create_default_executor() -> JobExecutor"
      consumers: ["orchestrator"]
    - name: execution_result_to_evidence
      signature: "execution_result_to_evidence(result: ExecutionResult) -> dict[str, Any]"
      consumers: ["orchestrator"]
  classes:
    - name: HealthObserver
      methods:
        - observe_health
      consumers: ["orchestrator"]
    - name: StepHandler
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: StepOutput
      methods: []
      consumers: ["orchestrator"]
    - name: ExecutionContext
      methods: []
      consumers: ["orchestrator"]
    - name: ExecutionResult
      methods: []
      consumers: ["orchestrator"]
    - name: JobExecutor
      methods:
        - version
        - register_handler
        - execute_job
      consumers: ["orchestrator"]
    - name: NoOpHandler
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: FailingHandler
      methods:
        - execute
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
    spine_internal: []
    l7_model: ['app.models.governance_job']
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

