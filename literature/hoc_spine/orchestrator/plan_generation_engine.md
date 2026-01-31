# plan_generation_engine.py

**Path:** `backend/app/hoc/hoc_spine/orchestrator/plan_generation_engine.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            plan_generation_engine.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         API endpoints (L2), run creation flow
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Domain engine for plan generation.
Violations:      none
```

## Purpose

Domain engine for plan generation.

This L4 engine contains the authoritative logic for:
1. Memory context retrieval
2. Plan generation via planner
3. Plan validation

L5 workers must receive plans from this engine (via run.plan_json),
not generate their own plans.

Reference: PIN-257 Phase R-2
Governance: PHASE_R_L5_L4_VIOLATIONS.md

## Import Analysis

**External:**
- `app.memory`
- `app.planners`
- `app.skills`
- `app.utils.budget_tracker`
- `app.utils.plan_inspector`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `generate_plan_for_run(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult`

Convenience function to generate a plan for a run.

This is the L4 entry point for plan generation. It should be called
by the run creation flow (in L2 API) to generate plans before
the run is queued for execution.

Args:
    agent_id: Agent ID
    goal: Run goal
    run_id: Run ID

Returns:
    PlanGenerationResult with the generated plan

Reference: PIN-257 Phase R-2

## Classes

### `PlanGenerationContext`

Context for plan generation.

### `PlanGenerationResult`

Result of plan generation.

### `PlanGenerationEngine`

L4 Domain Engine for plan generation.

This engine contains ALL plan generation logic that was previously
scattered in L5 runner.py. It generates plans from goals using
memory context and the configured planner.

L5 workers must NOT:
- Import memory.get_retriever()
- Import planners.get_planner()
- Generate plans inline

L5 workers must ONLY:
- Execute plans provided via run.plan_json
- Fail if no plan is provided

Reference: PIN-257 Phase R-2
Governance: PHASE_R_L5_L4_VIOLATIONS.md Section 3.2

#### Methods

- `__init__()` — Initialize the plan generation engine.
- `generate(context: PlanGenerationContext) -> PlanGenerationResult` — Generate a plan for a run.

## Domain Usage

**Callers:** API endpoints (L2), run creation flow

## Export Contract

```yaml
exports:
  functions:
    - name: generate_plan_for_run
      signature: "generate_plan_for_run(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult"
      consumers: ["orchestrator"]
  classes:
    - name: PlanGenerationContext
      methods: []
      consumers: ["orchestrator"]
    - name: PlanGenerationResult
      methods: []
      consumers: ["orchestrator"]
    - name: PlanGenerationEngine
      methods:
        - generate
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
    l7_model: []
    external: ['app.memory', 'app.planners', 'app.skills', 'app.utils.budget_tracker', 'app.utils.plan_inspector']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

