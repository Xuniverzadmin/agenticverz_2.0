# plan.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/plan.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            plan.py
Lives in:        schemas/
Role:            Schemas
Inbound:         API routes, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Plan API schemas (pure Pydantic DTOs)
Violations:      none
```

## Purpose

Plan API schemas (pure Pydantic DTOs)

## Import Analysis

**External:**
- `pydantic`
- `retry`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_utc_now() -> datetime`

UTC timestamp (inlined to keep schemas pure — no service imports).

## Classes

### `OnErrorPolicy(str, Enum)`

What to do when a step fails.

### `StepStatus(str, Enum)`

Execution status of a plan step.

### `ConditionOperator(str, Enum)`

Operators for step conditions.

### `StepCondition(BaseModel)`

Condition for conditional step execution.

Allows steps to be skipped based on previous step outputs.

### `PlanStep(BaseModel)`

A single step in an execution plan.

Defines what skill to run, with what parameters,
dependencies, conditions, and error handling.

#### Methods

- `validate_fallback(v, info)` — Validate fallback_skill requires on_error=fallback.

### `PlanMetadata(BaseModel)`

Metadata about the plan and how it was created.

### `Plan(BaseModel)`

Complete execution plan for achieving a goal.

The plan is the contract between planner and executor.
It defines what steps to run and in what order.

#### Methods

- `validate_step_ids_unique(v: List[PlanStep]) -> List[PlanStep]` — Ensure all step IDs are unique.
- `validate_dependencies(v: List[PlanStep]) -> List[PlanStep]` — Ensure dependencies reference valid step IDs.
- `get_step(step_id: str) -> Optional[PlanStep]` — Get a step by ID.
- `get_ready_steps() -> List[PlanStep]` — Get steps that are ready to execute (dependencies met).

## Domain Usage

**Callers:** API routes, engines

## Export Contract

```yaml
exports:
  functions:
    - name: _utc_now
      signature: "_utc_now() -> datetime"
      consumers: ["orchestrator"]
  classes:
    - name: OnErrorPolicy
      methods: []
      consumers: ["orchestrator"]
    - name: StepStatus
      methods: []
      consumers: ["orchestrator"]
    - name: ConditionOperator
      methods: []
      consumers: ["orchestrator"]
    - name: StepCondition
      methods: []
      consumers: ["orchestrator"]
    - name: PlanStep
      methods:
        - validate_fallback
      consumers: ["orchestrator"]
    - name: PlanMetadata
      methods: []
      consumers: ["orchestrator"]
    - name: Plan
      methods:
        - validate_step_ids_unique
        - validate_dependencies
        - get_step
        - get_ready_steps
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic', 'retry']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

