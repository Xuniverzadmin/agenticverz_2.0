# dag_executor.py

**Path:** `backend/app/hoc/hoc_spine/drivers/dag_executor.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            dag_executor.py
Lives in:        drivers/
Role:            Drivers
Inbound:         policy engine, workers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         DAG-based executor for PLang v2.0.
Violations:      none
```

## Purpose

DAG-based executor for PLang v2.0.

Executes policies in topologically sorted order:
- Parallel execution within stages
- Sequential execution across stages
- Governance-aware ordering
- Full execution trace

## Import Analysis

**External:**
- `app.policy.compiler.grammar`
- `app.policy.ir.ir_nodes`
- `app.policy.optimizer.dag_sorter`
- `app.policy.runtime.deterministic_engine`
- `app.policy.runtime.intent`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `StageResult`

Result of executing a single stage.

#### Methods

- `success() -> bool` — Check if all policies in stage succeeded.
- `was_blocked() -> bool` — Check if execution was blocked by a DENY action.

### `ExecutionTrace`

Full execution trace across all stages.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary for audit logging.

### `DAGExecutor`

Executes policies in DAG order.

Features:
- Parallel execution within stages
- Early termination on DENY
- Governance-aware execution order
- Full audit trail

#### Methods

- `__init__(engine: Optional[DeterministicEngine])` — _No docstring._
- `async execute(module: IRModule, context: ExecutionContext, plan: Optional[ExecutionPlan]) -> ExecutionTrace` — Execute all policies in DAG order.
- `async _execute_stage(stage_index: int, policies: List[str], module: IRModule, context: ExecutionContext) -> StageResult` — Execute a single stage (potentially in parallel).
- `async _execute_policy(policy_name: str, module: IRModule, context: ExecutionContext) -> ExecutionResult` — Execute a single policy.
- `_is_more_restrictive(action: ActionType, compared_to: ActionType) -> bool` — Check if an action is more restrictive than another.
- `get_execution_plan(module: IRModule) -> ExecutionPlan` — Get the execution plan for a module.
- `visualize_plan(module: IRModule) -> str` — Get a visual representation of the execution plan.

## Domain Usage

**Callers:** policy engine, workers

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: StageResult
      methods:
        - success
        - was_blocked
      consumers: ["orchestrator"]
    - name: ExecutionTrace
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DAGExecutor
      methods:
        - execute
        - get_execution_plan
        - visualize_plan
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
    l7_model: []
    external: ['app.policy.compiler.grammar', 'app.policy.ir.ir_nodes', 'app.policy.optimizer.dag_sorter', 'app.policy.runtime.deterministic_engine', 'app.policy.runtime.intent']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

